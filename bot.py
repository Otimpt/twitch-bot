#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Discord bot que monitora clips recentes da Twitch - VERSÃO DEBUG ULTRA DETALHADA."""

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
# Mostrar visualizações, autor e data dos clips
CLIP_SHOW_DETAILS = os.getenv("CLIP_SHOW_DETAILS", "true").lower() == "true"
# Tempo limite de chamadas HTTP
CLIP_API_TIMEOUT = int(os.getenv("CLIP_API_TIMEOUT", "10"))
# Enviar video mp4 como anexo
CLIP_ATTACH_VIDEO = os.getenv("CLIP_ATTACH_VIDEO", "false").lower() == "true"
# Debug mode
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# ---- Cache ----
CACHE_FILE = "posted_clips.json"

def load_cache() -> Dict[str, Set[str]]:
    """Carrega o cache do arquivo JSON."""
    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
            # Converter chaves de volta para int e valores para set
            cache = {int(k): set(v) for k, v in data.items()}
            print(f"💾 Cache carregado: {sum(len(clips) for clips in cache.values())} clips em {len(cache)} servidores")
            return cache
    except FileNotFoundError:
        print("💾 Arquivo de cache não encontrado, iniciando com cache vazio")
        return {}
    except Exception as e:
        print(f"❌ Erro ao carregar cache: {e}")
        return {}

def save_cache(cache: Dict[int, Set[str]]):
    """Salva o cache no arquivo JSON."""
    try:
        # Converter sets para listas para JSON
        data = {str(k): list(v) for k, v in cache.items()}
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print(f"💾 Cache salvo: {sum(len(clips) for clips in cache.values())} clips")
    except Exception as e:
        print(f"❌ Erro ao salvar cache: {e}")

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Por servidor: configurações, ids de clips enviados e horário da última verificação
TwitchConfig = Dict[str, str]
twitch_configs: Dict[int, TwitchConfig] = {}
posted_clips: Dict[int, Set[str]] = {}
last_check_time: Dict[int, datetime] = {}

def debug_print(message: str):
    """Print debug messages if debug mode is enabled."""
    if DEBUG_MODE:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Incluir milissegundos
        print(f"[DEBUG {timestamp}] {message}")

def log_print(message: str):
    """Print important log messages always."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Incluir milissegundos
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

    debug_print("🔑 Solicitando token da Twitch...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=params, timeout=CLIP_API_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.json()
                token = data.get("access_token")
                if token:
                    debug_print(f"✅ Token obtido: {token[:10]}...{token[-5:]}")
                else:
                    log_print("❌ Token não encontrado na resposta")
                return token
    except Exception as e:
        log_print(f"❌ Erro ao obter token: {e}")
        return None

def parse_twitch_username(raw: str) -> str:
    """Extrai o nome de usuário de diferentes formatos de entrada."""
    original = raw
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

    log_print(f"📝 Username parseado: '{original}' -> '{username}'")
    return username

async def get_broadcaster_id(username: str, token: str) -> Optional[str]:
    """Busca o ID do broadcaster pelo nome de usuário."""
    url = "https://api.twitch.tv/helix/users"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    params = {"login": username}

    log_print(f"🔍 Buscando ID do broadcaster para: '{username}'")
    debug_print(f"📡 URL: {url}")
    debug_print(f"📡 Headers: Client-ID={TWITCH_CLIENT_ID[:8]}..., Authorization=Bearer {token[:10]}...")
    debug_print(f"📡 Params: {params}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=CLIP_API_TIMEOUT) as resp:
                debug_print(f"📡 Status da resposta: {resp.status}")
                resp.raise_for_status()
                data = await resp.json()

                log_print(f"📡 Resposta da API Users: {data}")

                if data.get("data") and len(data["data"]) > 0:
                    broadcaster_id = data["data"][0]["id"]
                    broadcaster_name = data["data"][0]["display_name"]
                    log_print(f"✅ Broadcaster encontrado: '{username}' -> ID: {broadcaster_id} (Nome: {broadcaster_name})")
                    return broadcaster_id
                else:
                    log_print(f"❌ Nenhum usuário encontrado para: '{username}'")
                    log_print(f"   Verifique se o nome está correto e se o canal existe")
                    return None
    except Exception as e:
        log_print(f"❌ Erro ao buscar ID do canal '{username}': {e}")
        return None

def clip_video_url(thumbnail_url: str) -> str:
    """Converte URL da thumbnail para URL do vídeo."""
    base = thumbnail_url.split("-preview-", 1)[0]
    video_url = base + ".mp4"
    debug_print(f"🎬 URL do vídeo gerada: {thumbnail_url} -> {video_url}")
    return video_url

async def fetch_clips(broadcaster_id: str, token: str, start: datetime, end: datetime) -> List[dict]:
    """Busca clips de um broadcaster em um período específico."""

    # Converter para strings ISO com timezone
    start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {
        "broadcaster_id": broadcaster_id,
        "first": 100,
        "started_at": start_str,
        "ended_at": end_str,
    }
    url = "https://api.twitch.tv/helix/clips"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }

    log_print(f"🔍 === BUSCANDO CLIPS ===")
    log_print(f"   🆔 Broadcaster ID: {broadcaster_id}")
    log_print(f"   📅 Período:")
    log_print(f"      🕐 Início: {start.strftime('%d/%m/%Y %H:%M:%S UTC')} ({start_str})")
    log_print(f"      🕐 Fim:    {end.strftime('%d/%m/%Y %H:%M:%S UTC')} ({end_str})")
    log_print(f"      ⏰ Duração: {(end - start).total_seconds() / 60:.1f} minutos")

    debug_print(f"📡 URL completa: {url}")
    debug_print(f"📡 Headers: {headers}")
    debug_print(f"📡 Params: {params}")

    try:
        async with aiohttp.ClientSession() as session:
            debug_print("📡 Fazendo requisição para API da Twitch...")
            async with session.get(url, headers=headers, params=params, timeout=CLIP_API_TIMEOUT) as resp:
                debug_print(f"📡 Status da resposta: {resp.status}")
                resp.raise_for_status()
                data = await resp.json()
                clips = data.get("data", [])

                log_print(f"📊 Resposta da API: {len(clips)} clips encontrados")

                if DEBUG_MODE:
                    log_print(f"📡 Resposta completa da API:")
                    log_print(f"   Data: {len(clips)} clips")
                    if "pagination" in data:
                        log_print(f"   Pagination: {data['pagination']}")

                # ANÁLISE DETALHADA DE CADA CLIP
                now_utc = datetime.now(timezone.utc)
                log_print(f"🕐 Horário atual para comparação: {now_utc.strftime('%d/%m/%Y %H:%M:%S UTC')}")

                for i, clip in enumerate(clips, 1):
                    created_at = clip.get("created_at", "")
                    title = clip.get("title", "Sem título")[:50]
                    creator = clip.get("creator_name", "?")
                    clip_id = clip.get("id", "?")
                    view_count = clip.get("view_count", 0)

                    log_print(f"   🎬 CLIP #{i}: {title}")
                    log_print(f"      🆔 ID: {clip_id}")
                    log_print(f"      👤 Criador: {creator}")
                    log_print(f"      👀 Views: {view_count}")

                    if created_at:
                        try:
                            created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                            created_str = created_dt.strftime("%d/%m/%Y %H:%M:%S UTC")

                            # Calcular diferenças de tempo
                            diff_from_now = (now_utc - created_dt).total_seconds()
                            diff_from_start = (created_dt - start).total_seconds()
                            diff_from_end = (end - created_dt).total_seconds()

                            log_print(f"      📅 Criado: {created_str}")
                            log_print(f"      ⏰ Há {diff_from_now:.1f}s atrás ({diff_from_now/60:.1f} min)")

                            # Verificar se está no range
                            in_range = start <= created_dt <= end
                            if in_range:
                                log_print(f"      ✅ DENTRO DO RANGE")
                                log_print(f"         📊 {diff_from_start:.1f}s após início do range")
                                log_print(f"         📊 {diff_from_end:.1f}s antes do fim do range")
                            else:
                                log_print(f"      ❌ FORA DO RANGE")
                                if created_dt < start:
                                    log_print(f"         📊 {abs(diff_from_start):.1f}s ANTES do início")
                                elif created_dt > end:
                                    log_print(f"         📊 {abs(diff_from_end):.1f}s DEPOIS do fim")

                            # Verificar se é muito recente (pode ser problema de indexação)
                            if diff_from_now < 60:  # Menos de 1 minuto
                                log_print(f"      ⚠️ CLIP MUITO RECENTE! Pode ter problema de indexação da Twitch")

                        except Exception as e:
                            log_print(f"      ❌ Erro ao processar data: {e}")
                            log_print(f"      📅 Data original: {created_at}")
                    else:
                        log_print(f"      ❌ SEM DATA DE CRIAÇÃO")

                return clips

    except Exception as e:
        log_print(f"❌ Erro ao buscar clips: {e}")
        import traceback
        log_print(f"❌ Traceback completo: {traceback.format_exc()}")
        return []

def create_clip_embed(clip: dict, username: str) -> discord.Embed:
    """Cria embed do Discord para um clip."""
    embed = discord.Embed(
        title=clip.get("title", "Clip"),
        url=clip.get("url"),
        color=0x9146FF,
    )
    embed.add_field(name="📺 Canal", value=username, inline=True)

    if CLIP_SHOW_DETAILS:
        embed.add_field(name="👀 Views", value=str(clip.get("view_count", 0)), inline=True)
        embed.add_field(name="👤 Criado por", value=clip.get("creator_name", "?"), inline=True)

    created = clip.get("created_at", "")
    if created:
        dt = datetime.fromisoformat(created.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
        embed.add_field(name="📅 Data", value=dt, inline=True)

    if clip.get("thumbnail_url"):
        embed.set_image(url=clip["thumbnail_url"])

    return embed

# ---- Eventos do Bot ----
@bot.event
async def on_ready():
    """Evento executado quando o bot fica online."""
    log_print(f"🤖 {bot.user} está online!")
    log_print(f"🆔 Bot ID: {bot.user.id}")
    log_print(f"🌐 Conectado a {len(bot.guilds)} servidor(es)")

    # Mostrar configurações
    log_print(f"⚙️ CONFIGURAÇÕES:")
    log_print(f"   🐛 Debug mode: {'✅ ATIVADO' if DEBUG_MODE else '❌ DESATIVADO'}")
    log_print(f"   🎬 Anexo de vídeo: {'✅ ATIVADO' if CLIP_ATTACH_VIDEO else '❌ DESATIVADO'}")
    log_print(f"   ⏰ Verificação a cada: {CLIP_CHECK_SECONDS}s")
    log_print(f"   📅 Lookback: {CLIP_LOOKBACK_HOURS}h")
    log_print(f"   ⏱️ Timeout API: {CLIP_API_TIMEOUT}s")
    log_print(f"   🔑 Twitch Client ID: {TWITCH_CLIENT_ID[:8] if TWITCH_CLIENT_ID else 'NÃO DEFINIDO'}...")
    log_print(f"   🔐 Twitch Secret: {'DEFINIDO' if TWITCH_SECRET else 'NÃO DEFINIDO'}")

    # Carregar o cache
    global posted_clips
    posted_clips = load_cache()

    try:
        synced = await bot.tree.sync()
        log_print(f"🔄 Sincronizados {len(synced)} comando(s)")
    except Exception as e:
        log_print(f"❌ Erro ao sincronizar comandos: {e}")

    if not check_twitch_clips.is_running():
        check_twitch_clips.start()
        log_print("🔄 Loop de verificação de clips iniciado")
    else:
        log_print("⚠️ Loop de verificação já estava rodando")

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

    log_print(f"⚙️ === CONFIGURANDO MONITORAMENTO ===")
    log_print(f"   🏠 Servidor: {interaction.guild.name} (ID: {server_id})")
    log_print(f"   📺 Canal Twitch: {username}")
    log_print(f"   💬 Canal Discord: #{canal_discord.name} (ID: {canal_discord.id})")

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

    # Inicializar cache e tempo
    posted_clips[server_id] = set()
    now_utc = datetime.now(timezone.utc)
    initial_time = now_utc - timedelta(hours=CLIP_LOOKBACK_HOURS)
    last_check_time[server_id] = initial_time

    log_print(f"✅ Configuração salva:")
    log_print(f"   📺 Username: {username}")
    log_print(f"   🆔 Broadcaster ID: {broadcaster_id}")
    log_print(f"   💬 Canal Discord: {canal_discord.id}")
    log_print(f"   🕐 Tempo inicial: {initial_time.strftime('%d/%m/%Y %H:%M:%S UTC')}")

    embed = discord.Embed(
        title="✅ Configuração salva!",
        description=f"Monitorando clips de **{username}** em {canal_discord.mention}",
        color=0x00ff00
    )
    embed.add_field(name="🔄 Frequência", value=f"A cada {CLIP_CHECK_SECONDS}s", inline=True)
    embed.add_field(name="📅 Lookback", value=f"Últimas {CLIP_LOOKBACK_HOURS}h", inline=True)
    embed.add_field(name="🎬 Vídeo anexo", value="✅ Ativado" if CLIP_ATTACH_VIDEO else "❌ Desativado", inline=True)

    await interaction.followup.send(embed=embed)

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

    log_print(f"🧪 === TESTE MANUAL INICIADO ===")
    log_print(f"   📺 Canal: {config['username']}")
    log_print(f"   🆔 Broadcaster ID: {config['broadcaster_id']}")

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
    log_print(f"🔄 ==================== VERIFICAÇÃO DE CLIPS ====================")
    log_print(f"🕐 Horário atual (UTC): {now.strftime('%d/%m/%Y %H:%M:%S.%f')[:-3]}")
    log_print(f"📊 Configurações ativas: {len(twitch_configs)}")

    for server_id, cfg in list(twitch_configs.items()):
        try:
            start = last_check_time.get(server_id, now - timedelta(hours=CLIP_LOOKBACK_HOURS))

            log_print(f"🔍 === SERVIDOR {server_id} - {cfg['username']} ===")
            log_print(f"   📅 Última verificação: {start.strftime('%d/%m/%Y %H:%M:%S UTC')}")
            log_print(f"   📅 Verificação atual:  {now.strftime('%d/%m/%Y %H:%M:%S UTC')}")
            log_print(f"   ⏰ Intervalo: {(now - start).total_seconds():.1f} segundos ({(now - start).total_seconds()/60:.1f} min)")

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

                log_print(f"   🎬 === ANALISANDO CLIP ===")
                log_print(f"      📝 Título: {title}")
                log_print(f"      🆔 ID: {clip_id}")
                log_print(f"      📅 Criado: {created.strftime('%d/%m/%Y %H:%M:%S UTC')}")
                log_print(f"      👤 Por: {clip.get('creator_name', '?')}")

                # Verificar se já foi enviado
                if clip_id in posted_clips.get(server_id, set()):
                    log_print(f"      ⏭️ IGNORADO: Clip já foi enviado anteriormente")
                    continue

                # Verificar se está no range de tempo
                if created < start:
                    log_print(f"      ⏭️ IGNORADO: Clip muito antigo")
                    log_print(f"         📊 Criado: {created.strftime('%H:%M:%S')}")
                    log_print(f"         📊 Início: {start.strftime('%H:%M:%S')}")
                    log_print(f"         📊 Diferença: {(start - created).total_seconds():.1f}s")
                    continue

                # Verificar se não é futuro
                if created > now:
                    log_print(f"      ⚠️ AVISO: Clip do futuro detectado!")
                    log_print(f"         📊 Criado: {created.strftime('%H:%M:%S')}")
                    log_print(f"         📊 Agora:  {now.strftime('%H:%M:%S')}")

                channel = bot.get_channel(cfg["discord_channel"])
                if not channel:
                    log_print(f"      ❌ ERRO: Canal Discord não encontrado: {cfg['discord_channel']}")
                    continue

                log_print(f"      ✅ NOVO CLIP DETECTADO! Preparando envio...")

                # Criar embed e enviar
                embed = create_clip_embed(clip, cfg["username"])
                files = []

                # Anexar vídeo se configurado
                if CLIP_ATTACH_VIDEO and clip.get("thumbnail_url"):
                    log_print(f"      📥 Baixando vídeo...")
                    video_url = clip_video_url(clip["thumbnail_url"])
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(video_url, timeout=CLIP_API_TIMEOUT * 2) as resp:
                                if resp.status == 200:
                                    data = await resp.read()
                                    if len(data) > 0:
                                        files.append(discord.File(io.BytesIO(data), filename="clip.mp4"))
                                        log_print(f"      ✅ Vídeo baixado: {len(data)} bytes")
                                    else:
                                        log_print(f"      ❌ Vídeo vazio")
                                else:
                                    log_print(f"      ❌ Erro HTTP {resp.status} ao baixar vídeo")
                    except Exception as e:
                        log_print(f"      ❌ Erro ao baixar vídeo: {e}")

                try:
                    log_print(f"      📤 Enviando para Discord...")
                    await channel.send(content=clip.get("url"), embed=embed, files=files)

                    # CORREÇÃO: Só adicionar ao cache APÓS envio bem-sucedido
                    posted_clips.setdefault(server_id, set()).add(clip_id)
                    new_clips_count += 1

                    # Salvar o cache
                    save_cache(posted_clips)

                    log_print(f"      🎉 CLIP ENVIADO COM SUCESSO!")
                    if CLIP_ATTACH_VIDEO and files:
                        log_print(f"         📎 Com vídeo anexado")
                    else:
                        log_print(f"         📎 Sem vídeo anexado")

                    # Atualizar último tempo de verificação
                    if created > last_check_time.get(server_id, start):
                        last_check_time[server_id] = created
                        log_print(f"      🕐 Último check atualizado para: {created.strftime('%H:%M:%S')}")

                except Exception as e:
                    log_print(f"      ❌ ERRO AO ENVIAR CLIP: {e}")
                    import traceback
                    log_print(f"      ❌ Traceback: {traceback.format_exc()}")

            if new_clips_count > 0:
                log_print(f"   🎉 RESULTADO: {new_clips_count} novos clips enviados para {cfg['username']}")
            else:
                log_print(f"   📭 RESULTADO: Nenhum clip novo para {cfg['username']}")

        except Exception as e:
            log_print(f"❌ Erro geral ao verificar clips para servidor {server_id}: {e}")
            import traceback
            log_print(f"❌ Traceback completo: {traceback.format_exc()}")

    log_print(f"🔄 ==================== FIM DA VERIFICAÇÃO ====================\n")

@check_twitch_clips.before_loop
async def before_check_twitch_clips():
    """Aguarda o bot estar pronto antes de iniciar o loop."""
    log_print("⏳ Aguardando bot ficar pronto...")
    await bot.wait_until_ready()
    log_print("✅ Bot pronto, iniciando loop de verificação")

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
            log_print("🐛 Modo debug ULTRA DETALHADO ativado")
        if CLIP_ATTACH_VIDEO:
            log_print("🎬 Anexo de vídeo ativado")
        bot.run(DISCORD_TOKEN)
