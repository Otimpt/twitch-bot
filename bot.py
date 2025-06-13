#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Discord bot que monitora clips recentes da Twitch."""

import os
import io
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Set, List, Optional

import aiohttp
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# ---- Configuração ----
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_SECRET = os.getenv("TWITCH_SECRET")

# Intervalo entre verificações de novos clips (segundos)
CLIP_CHECK_SECONDS = int(os.getenv("CLIP_CHECK_SECONDS", "30"))
# Quantas horas no passado considerar ao iniciar o monitoramento
CLIP_LOOKBACK_HOURS = float(os.getenv("CLIP_LOOKBACK_HOURS", "2.0"))
# Tempo limite de chamadas HTTP
CLIP_API_TIMEOUT = int(os.getenv("CLIP_API_TIMEOUT", "10"))
# Enviar video mp4 como anexo
CLIP_ATTACH_VIDEO = os.getenv("CLIP_ATTACH_VIDEO", "false").lower() == "true"
# Debug mode
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# ---- Cache ----
CACHE_FILE = "posted_clips.json"

def load_cache() -> Dict[int, Set[str]]:
    """Carrega o cache do arquivo JSON."""
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_cache(cache: Dict[int, Set[str]]):
    """Salva o cache no arquivo JSON."""
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Por servidor: configurações, ids de clips enviados e horário da última verificação
TwitchConfig = Dict[str, str]
twitch_configs: Dict[int, TwitchConfig] = {}
posted_clips: Dict[int, Set[str]] = {}  # Inicializado aqui, mas será carregado do arquivo
last_check_time: Dict[int, datetime] = {}

def debug_print(message: str):
    """Print debug messages if debug mode is enabled."""
    if DEBUG_MODE:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[DEBUG {timestamp}] {message}")

def log_print(message: str):
    """Print important log messages always."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[LOG {timestamp}] {message}")

# ---- Utilidades Twitch ----
async def get_twitch_token() -> Optional[str]:
    """Solicita um token de acesso à API da Twitch."""
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_SECRET,
        "grant_type": "client_credentials"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=params, timeout=CLIP_API_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.json()
                token = data.get("access_token")
                debug_print(f"Token obtido com sucesso: {token[:10]}..." if token else "Falha ao obter token")
                return token
    except Exception as e:
        log_print(f"❌ Erro ao obter token: {e}")
        return None

def parse_twitch_username(raw: str) -> str:
    """Extrai o nome de usuário de diferentes formatos de entrada."""
    username = raw.strip().replace("@", "").lower()

    # Remove protocolo se presente
    if "//" in username:
        username = username.split("//", 1)[1]

    # Remove www. se presente
    if username.startswith("www."):
        username = username[4:]

    # Remove twitch.tv/ se presente
    if username.startswith("twitch.tv/"):
        username = username[len("twitch.tv/"):]

    # Remove tudo após a primeira barra
    if "/" in username:
        username = username.split("/", 1)[0]

    # Remove parâmetros de query
    if "?" in username:
        username = username.split("?", 1)[0]

    debug_print(f"Username parseado: '{raw}' -> '{username}'")
    return username

async def get_broadcaster_id(username: str, token: str) -> Optional[str]:
    """Busca o ID do broadcaster pelo nome de usuário."""
    url = "https://api.twitch.tv/helix/users"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    params = {"login": username}

    debug_print(f"🔍 Buscando ID do broadcaster para: {username}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=CLIP_API_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.json()

                debug_print(f"📡 Resposta da API Twitch Users: {data}")

                if data.get("data") and len(data["data"]) > 0:
                    broadcaster_id = data["data"][0]["id"]
                    log_print(f"✅ ID do broadcaster encontrado: {username} -> {broadcaster_id}")
                    return broadcaster_id
                else:
                    log_print(f"❌ Nenhum usuário encontrado para: {username}")
                    return None
    except Exception as e:
        log_print(f"❌ Erro ao buscar ID do canal '{username}': {e}")
        return None

def get_clip_video_url(clip_data: dict) -> Optional[str]:
    """
    Extrai a URL do vídeo do clip usando múltiplas estratégias.
    A API da Twitch às vezes retorna URLs diferentes.
    """
    # Estratégia 1: Usar o campo 'video_url' se disponível
    if clip_data.get("video_url"):
        debug_print(f"📹 URL do vídeo encontrada no campo video_url: {clip_data['video_url']}")
        return clip_data["video_url"]

    # Estratégia 2: Converter thumbnail_url para video_url
    thumbnail_url = clip_data.get("thumbnail_url")
    if thumbnail_url:
        # Método original
        if "-preview-" in thumbnail_url:
            base = thumbnail_url.split("-preview-", 1)[0]
            video_url = base + ".mp4"
            debug_print(f"📹 URL do vídeo gerada (método 1): {video_url}")
            return video_url

        # Método alternativo para URLs diferentes
        if "preview-" in thumbnail_url:
            base = thumbnail_url.split("preview-", 1)[0]
            video_url = base.rstrip("-") + ".mp4"
            debug_print(f"📹 URL do vídeo gerada (método 2): {video_url}")
            return video_url

    debug_print(f"❌ Não foi possível gerar URL do vídeo para o clip")
    return None

async def fetch_clips(broadcaster_id: str, token: str, start: datetime, end: datetime) -> List[dict]:
    """Busca clips de um broadcaster em um período específico."""
    params = {
        "broadcaster_id": broadcaster_id,
        "first": 100,
        "started_at": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ended_at": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    url = "https://api.twitch.tv/helix/clips"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }

    log_print(f"🔍 Buscando clips:")
    log_print(f"   📅 De: {start.strftime('%d/%m/%Y %H:%M:%S UTC')}")
    log_print(f"   📅 Até: {end.strftime('%d/%m/%Y %H:%M:%S UTC')}")
    log_print(f"   👤 Broadcaster ID: {broadcaster_id}")
    debug_print(f"📡 URL da API: {url}")
    debug_print(f"📡 Parâmetros: {params}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=CLIP_API_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.json()
                clips = data.get("data", [])

                log_print(f"📊 Resposta da API: {len(clips)} clips encontrados")
                debug_print(f"📡 Resposta completa da API: {data}")

                # Log detalhado de cada clip encontrado (só se debug ativado)
                if DEBUG_MODE:
                    for i, clip in enumerate(clips, 1):
                        created_at = clip.get("created_at", "")
                        title = clip.get("title", "Sem título")[:50]
                        creator = clip.get("creator_name", "?")
                        clip_id = clip.get("id", "?")

                        if created_at:
                            created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                            created_str = created_dt.strftime("%d/%m %H:%M:%S")

                            # Verificar se está no range
                            in_range = start <= created_dt <= end
                            range_status = "✅ NO RANGE" if in_range else "❌ FORA DO RANGE"

                            debug_print(f"   🎬 Clip #{i}: {title}")
                            debug_print(f"      📅 Criado: {created_str} ({range_status})")
                            debug_print(f"      👤 Por: {creator} | ID: {clip_id}")

                            # Mostrar diferença de tempo
                            now_utc = datetime.now(timezone.utc)
                            time_diff = now_utc - created_dt
                            minutes_ago = int(time_diff.total_seconds() / 60)
                            debug_print(f"      ⏰ Há {minutes_ago} minutos atrás")

                            # Mostrar URLs disponíveis
                            debug_print(f"      🔗 URL do clip: {clip.get('url', 'N/A')}")
                            debug_print(f"      🖼️ Thumbnail: {clip.get('thumbnail_url', 'N/A')}")
                            if clip.get('video_url'):
                                debug_print(f"      📹 Video URL: {clip.get('video_url')}")
                        else:
                            debug_print(f"   🎬 Clip #{i}: {title} (SEM DATA)")

                return clips
    except Exception as e:
        log_print(f"❌ Erro ao buscar clips: {e}")
        return []

def create_clip_embed(clip: dict, username: str) -> discord.Embed:
    """Cria embed simplificado do Discord para um clip."""
    embed = discord.Embed(
        color=0x9146FF,
        description="🎬 Novo clip!"
    )

    embed.add_field(name="📺 Canal", value=username, inline=True)
    embed.add_field(name="👤 Criado por", value=clip.get("creator_name", "?"), inline=True)

    created = clip.get("created_at", "")
    if created:
        dt = datetime.fromisoformat(created.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
        embed.add_field(name="📅 Data", value=dt, inline=True)

    return embed

async def download_clip_video(clip: dict) -> Optional[discord.File]:
    """Baixa o vídeo do clip e retorna como arquivo do Discord."""
    video_url = get_clip_video_url(clip)

    if not video_url:
        log_print(f"❌ Não foi possível obter URL do vídeo para o clip {clip.get('id', '?')}")
        return None

    debug_print(f"📥 Tentando baixar vídeo: {video_url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url, timeout=CLIP_API_TIMEOUT * 3) as resp:  # Timeout maior para download
                if resp.status == 404:
                    log_print(f"❌ Vídeo não encontrado (404): {video_url}")

                    # Tentar URLs alternativas se a primeira falhar
                    thumbnail_url = clip.get("thumbnail_url", "")
                    if thumbnail_url and "-preview-" in thumbnail_url:
                        # Tentar diferentes formatos de URL
                        alternative_urls = []

                        # Formato 1: substituir preview por AT_
                        alt_url_1 = thumbnail_url.replace("-preview-", "-AT_")
                        alternative_urls.append(alt_url_1)

                        # Formato 2: remover preview e adicionar .mp4
                        base = thumbnail_url.split("-preview-")[0]
                        alt_url_2 = base + ".mp4"
                        alternative_urls.append(alt_url_2)

                        for alt_url in alternative_urls:
                            debug_print(f"📥 Tentando URL alternativa: {alt_url}")
                            try:
                                async with session.get(alt_url, timeout=CLIP_API_TIMEOUT * 2) as alt_resp:
                                    if alt_resp.status == 200:
                                        data = await alt_resp.read()
                                        if len(data) > 0:
                                            debug_print(f"✅ Vídeo baixado com URL alternativa: {len(data)} bytes")
                                            return discord.File(io.BytesIO(data), filename=f"clip_{clip['id']}.mp4")
                            except Exception as alt_e:
                                debug_print(f"❌ Falha na URL alternativa {alt_url}: {alt_e}")

                    return None

                resp.raise_for_status()
                data = await resp.read()

                # Verifica se o arquivo não está vazio
                if len(data) == 0:
                    log_print(f"❌ Vídeo do clip está vazio: {video_url}")
                    return None

                debug_print(f"✅ Vídeo baixado com sucesso: {len(data)} bytes")
                return discord.File(io.BytesIO(data), filename=f"clip_{clip['id']}.mp4")

    except Exception as e:
        log_print(f"❌ Erro ao baixar vídeo do clip: {e}")
        return None

# ---- Eventos do Bot ----
@bot.event
async def on_ready():
    """Evento executado quando o bot fica online."""
    log_print(f"🤖 {bot.user} está online!")
    log_print(f"🐛 Debug mode: {'✅ ATIVADO' if DEBUG_MODE else '❌ DESATIVADO'}")
    log_print(f"🎬 Anexo de vídeo: {'✅ ATIVADO' if CLIP_ATTACH_VIDEO else '❌ DESATIVADO'}")
    log_print(f"⏰ Verificação a cada: {CLIP_CHECK_SECONDS}s")
    log_print(f"📅 Lookback: {CLIP_LOOKBACK_HOURS}h")
    log_print(f"⏱️ Timeout API: {CLIP_API_TIMEOUT}s")

    # Carregar o cache
    global posted_clips
    posted_clips = load_cache()
    log_print(f"💾 Cache carregado com {sum(len(clips) for clips in posted_clips.values())} clips")

# ---- Comandos do Bot ----
@bot.tree.command(name="twitch_setup", description="Configura monitoramento de clips")
async def twitch_setup(
    interaction: discord.Interaction,
    canal_twitch: str,
    canal_discord: discord.TextChannel,
):
    try:
        await interaction.response.defer()
    except discord.NotFound:
        return
    except discord.HTTPException as e:
        log_print(f"❌ Erro ao responder interação: {e}")
        return

    username = parse_twitch_username(canal_twitch)
    server_id = interaction.guild.id

    log_print(f"⚙️ Configurando monitoramento para '{username}' no servidor {server_id}")

    # Obter token e ID do broadcaster
    token = await get_twitch_token()
    if not token:
        embed = discord.Embed(
            title="❌ Erro",
            description="Não foi possível obter token da Twitch. Verifique as variáveis TWITCH_CLIENT_ID e TWITCH_SECRET.",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)
        return

    broadcaster_id = await get_broadcaster_id(username, token)
    if not broadcaster_id:
        embed = discord.Embed(
            title="❌ Canal não encontrado",
            description=f"Não foi possível encontrar o canal **{username}** na Twitch.\n\nVerifique se o nome está correto e se o canal existe.",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)
        return

    # Salvar configuração
    twitch_configs[server_id] = {
        "username": username,
        "broadcaster_id": broadcaster_id,
        "discord_channel": canal_discord.id
    }

    posted_clips[server_id] = set()
    last_check_time[server_id] = datetime.now(timezone.utc) - timedelta(hours=CLIP_LOOKBACK_HOURS)

    embed = discord.Embed(
        title="✅ Configuração salva!",
        description=f"Monitorando clips de **{username}** em {canal_discord.mention}",
        color=0x00ff00
    )
    embed.add_field(name="🔄 Frequência", value=f"A cada {CLIP_CHECK_SECONDS}s", inline=True)
    embed.add_field(name="📅 Lookback", value=f"Últimas {CLIP_LOOKBACK_HOURS}h", inline=True)
    embed.add_field(name="🎬 Vídeo anexo", value="✅ Ativado" if CLIP_ATTACH_VIDEO else "❌ Desativado", inline=True)

    await interaction.followup.send(embed=embed)
    log_print(f"✅ Configuração salva para {username} (ID: {broadcaster_id})")

@bot.tree.command(name="twitch_status", description="Mostra status do monitoramento")
async def twitch_status(interaction: discord.Interaction):
    server_id = interaction.guild.id

    if server_id not in twitch_configs:
        embed = discord.Embed(
            title="❌ Twitch não configurado",
            description="Use `/twitch_setup` para configurar o monitoramento.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)
        return

    config = twitch_configs[server_id]
    channel = bot.get_channel(config["discord_channel"])

    embed = discord.Embed(title="📺 Status do Monitoramento", color=0x9146FF)
    embed.add_field(name="📺 Canal", value=config["username"], inline=True)
    embed.add_field(name="💬 Canal Discord", value=channel.mention if channel else "?", inline=True)
    embed.add_field(name="🔄 Frequência", value=f"{CLIP_CHECK_SECONDS}s", inline=True)
    embed.add_field(name="📊 Clips enviados", value=len(posted_clips.get(server_id, set())), inline=True)
    embed.add_field(name="🎬 Vídeo anexo", value="✅ Ativado" if CLIP_ATTACH_VIDEO else "❌ Desativado", inline=True)

    last_check = last_check_time.get(server_id)
    if last_check:
        last_check_str = last_check.strftime("%d/%m/%Y %H:%M:%S UTC")
        embed.add_field(name="🕐 Última verificação", value=last_check_str, inline=True)

    # Mostrar horário atual do sistema
    now_utc = datetime.now(timezone.utc)
    embed.add_field(name="🕐 Horário atual (UTC)", value=now_utc.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
    embed.add_field(name="📅 Lookback atual", value=f"{CLIP_LOOKBACK_HOURS}h", inline=True)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="twitch_test", description="Testa a busca de clips manualmente")
async def twitch_test(interaction: discord.Interaction):
    server_id = interaction.guild.id

    if server_id not in twitch_configs:
        embed = discord.Embed(
            title="❌ Twitch não configurado",
            description="Use `/twitch_setup` primeiro.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)
        return

    await interaction.response.defer()

    config = twitch_configs[server_id]
    token = await get_twitch_token()

    if not token:
        embed = discord.Embed(
            title="❌ Erro",
            description="Não foi possível obter token da Twitch",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)
        return

    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=24)  # Últimas 24 horas para teste

    log_print(f"🧪 Teste manual iniciado para {config['username']}")
    clips = await fetch_clips(config["broadcaster_id"], token, start, now)

    embed = discord.Embed(
        title="🧪 Teste de Clips",
        description=f"Encontrados **{len(clips)}** clips nas últimas 24h para **{config['username']}**",
        color=0x9146FF
    )

    if clips:
        # Mostrar os 3 clips mais recentes
        recent_clips = sorted(clips, key=lambda c: c.get("created_at", ""), reverse=True)[:3]
        for i, clip in enumerate(recent_clips, 1):
            created = clip.get("created_at", "")
            if created:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00")).strftime("%d/%m %H:%M")
                embed.add_field(
                    name=f"#{i} {clip.get('title', 'Sem título')[:30]}...",
                    value=f"📅 {dt} | 👤 {clip.get('creator_name', '?')}",
                    inline=False
                )

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="ping", description="Verifica a latência")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! {latency}ms")

@bot.tree.command(name="help", description="Mostra todos os comandos disponíveis")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Comandos do Bot",
        description="Aqui estão todos os comandos disponíveis:",
        color=0x0099ff
    )

    embed.add_field(
        name="📺 Twitch",
        value="`/twitch_setup` - Configura monitoramento\n`/twitch_status` - Status do monitoramento\n`/twitch_test` - Testa busca de clips",
        inline=False
    )

    embed.add_field(
        name="🔧 Utilidades",
        value="`/ping` - Verifica latência\n`/help` - Mostra esta mensagem",
        inline=False
    )

    await interaction.response.send_message(embed=embed)

# ---- Loop de Verificação de Clips ----
@tasks.loop(seconds=CLIP_CHECK_SECONDS)
async def check_twitch_clips():
    """Loop principal que verifica novos clips."""
    if not twitch_configs:
        debug_print("⏭️ Nenhuma configuração encontrada, pulando verificação")
        return

    token = await get_twitch_token()
    if not token:
        log_print("❌ Erro: Não foi possível obter token da Twitch")
        return

    now = datetime.now(timezone.utc)
    log_print(f"🔄 === VERIFICAÇÃO DE CLIPS ===")
    log_print(f"🕐 Horário atual (UTC): {now.strftime('%d/%m/%Y %H:%M:%S')}")

    for server_id, cfg in list(twitch_configs.items()):
        try:
            start = last_check_time.get(server_id, now - timedelta(hours=CLIP_LOOKBACK_HOURS))

            log_print(f"🔍 Servidor {server_id} - Canal: {cfg['username']}")
            log_print(f"   📅 Buscando de: {start.strftime('%d/%m/%Y %H:%M:%S UTC')}")
            log_print(f"   📅 Até: {now.strftime('%d/%m/%Y %H:%M:%S UTC')}")
            log_print(f"   ⏰ Diferença: {(now - start).total_seconds() / 60:.1f} minutos")

            clips = await fetch_clips(cfg["broadcaster_id"], token, start, now)

            if not clips:
                log_print(f"   📭 Nenhum clip encontrado para {cfg['username']}")
                continue

            # Ordenar clips por data de criação (mais antigos primeiro)
            clips.sort(key=lambda c: c.get("created_at", ""))
            log_print(f"   📊 Processando {len(clips)} clips para {cfg['username']}")

            new_clips_count = 0
            for clip in clips:
                clip_id = clip["id"]
                created = datetime.fromisoformat(clip["created_at"].replace("Z", "+00:00"))
                title = clip.get("title", "Sem título")

                debug_print(f"   🎬 Analisando clip: {title[:50]}")
                debug_print(f"      📅 Criado em: {created.strftime('%d/%m/%Y %H:%M:%S UTC')}")
                debug_print(f"      🆔 ID: {clip_id}")

                # Verificar se já foi enviado
                if clip_id in posted_clips.get(server_id, set()):
                    debug_print(f"      ⏭️ Clip já foi enviado anteriormente")
                    continue

                # Verificar se está no range de tempo
                if created < start:
                    debug_print(f"      ⏭️ Clip muito antigo (antes de {start.strftime('%H:%M:%S')})")
                    continue

                # Verificar se não é futuro
                if created > now:
                    debug_print(f"      ⚠️ Clip do futuro? Criado: {created}, Agora: {now}")

                channel = bot.get_channel(cfg["discord_channel"])
                if not channel:
                    log_print(f"      ❌ Canal Discord não encontrado: {cfg['discord_channel']}")
                    continue

                log_print(f"      ✅ NOVO CLIP DETECTADO! Enviando...")

                # Criar embed simplificado
                embed = create_clip_embed(clip, cfg["username"])
                files = []

                # Baixar e anexar vídeo se configurado
                if CLIP_ATTACH_VIDEO:
                    debug_print(f"      📥 Baixando vídeo...")
                    video_file = await download_clip_video(clip)
                    if video_file:
                        files.append(video_file)
                        debug_print(f"      ✅ Vídeo baixado com sucesso")
                    else:
                        debug_print(f"      ❌ Falha ao baixar vídeo")

                try:
                    # Mensagem principal com título e link
                    clip_title = clip.get("title", "Clip sem título")
                    message_content = f"**Novo clip de {cfg['username']}:** {clip_title}\n{clip.get('url')}"

                    await channel.send(content=message_content, embed=embed, files=files)

                    # CORREÇÃO: Só adicionar ao cache APÓS envio bem-sucedido
                    posted_clips.setdefault(server_id, set()).add(clip_id)
                    new_clips_count += 1

                    # Salvar o cache
                    save_cache(posted_clips)

                    if CLIP_ATTACH_VIDEO and files:
                        log_print(f"      🎉 Clip enviado COM VÍDEO: {clip_title}")
                    else:
                        log_print(f"      🎉 Clip enviado SEM VÍDEO: {clip_title}")

                    # Atualizar último tempo de verificação
                    if created > last_check_time.get(server_id, start):
                        last_check_time[server_id] = created
                        debug_print(f"      🕐 Último check atualizado para: {created.strftime('%H:%M:%S')}")

                except Exception as e:
                    log_print(f"      ❌ Erro ao enviar clip: {e}")
                    # CORREÇÃO: NÃO adicionar ao cache se falhou

            if new_clips_count > 0:
                log_print(f"   🎉 {new_clips_count} novos clips enviados para {cfg['username']}")
            else:
                debug_print(f"   📭 Nenhum clip novo para {cfg['username']}")

        except Exception as e:
            log_print(f"❌ Erro ao verificar clips para servidor {server_id}: {e}")

    log_print(f"🔄 === FIM DA VERIFICAÇÃO ===\n")

@check_twitch_clips.before_loop
async def before_check_twitch_clips():
    """Aguarda o bot estar pronto antes de iniciar o loop."""
    await bot.wait_until_ready()

    # Carregar o cache
    global posted_clips
    posted_clips = load_cache()
    log_print(f"💾 Cache carregado com {sum(len(clips) for clips in posted_clips.values())} clips")

# ---- Execução ----
if __name__ == "__main__":
    missing_vars = []

    if not DISCORD_TOKEN:
        missing_vars.append("DISCORD_TOKEN")
    if not TWITCH_CLIENT_ID:
        missing_vars.append("TWITCH_CLIENT_ID")
    if not TWITCH_SECRET:
        missing_vars.append("TWITCH_SECRET")

    if missing_vars:
        log_print(f"❌ Variáveis de ambiente faltando: {', '.join(missing_vars)}")
        if "DISCORD_TOKEN" in missing_vars:
            log_print("Bot não pode iniciar sem DISCORD_TOKEN.")
            exit(1)
        else:
            log_print("⚠️ Twitch desabilitado. Defina TWITCH_CLIENT_ID e TWITCH_SECRET para habilitar.")

    if DISCORD_TOKEN:
        log_print("🚀 Iniciando bot...")
        if DEBUG_MODE:
            log_print("🐛 Modo debug ativado - logs detalhados habilitados")
        if CLIP_ATTACH_VIDEO:
            log_print("🎬 Anexo de vídeo ativado")
        bot.run(DISCORD_TOKEN)
