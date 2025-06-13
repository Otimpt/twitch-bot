#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Discord bot que monitora clips recentes da Twitch."""

import os
import io
import asyncio
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
CLIP_LOOKBACK_HOURS = float(os.getenv("CLIP_LOOKBACK_HOURS", "0.2"))
# Tempo limite de chamadas HTTP
CLIP_API_TIMEOUT = int(os.getenv("CLIP_API_TIMEOUT", "30"))
# Enviar video mp4 como anexo
CLIP_ATTACH_VIDEO = os.getenv("CLIP_ATTACH_VIDEO", "false").lower() == "true"
# Debug mode
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

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
        print(f"[DEBUG] {message}")

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
        print(f"Erro ao obter token: {e}")
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

    debug_print(f"Buscando ID do broadcaster para: {username}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=CLIP_API_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.json()

                debug_print(f"Resposta da API Twitch: {data}")

                if data.get("data") and len(data["data"]) > 0:
                    broadcaster_id = data["data"][0]["id"]
                    debug_print(f"ID do broadcaster encontrado: {broadcaster_id}")
                    return broadcaster_id
                else:
                    debug_print(f"Nenhum usuário encontrado para: {username}")
                    return None
    except Exception as e:
        print(f"Erro ao buscar ID do canal '{username}': {e}")
        return None

def clip_video_url(thumbnail_url: str) -> str:
    """Converte URL da thumbnail para URL do vídeo."""
    base = thumbnail_url.split("-preview-", 1)[0]
    return base + ".mp4"

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

    debug_print(f"Buscando clips de {start} até {end} para broadcaster {broadcaster_id}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=CLIP_API_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.json()
                clips = data.get("data", [])
                debug_print(f"Encontrados {len(clips)} clips")
                return clips
    except Exception as e:
        print(f"Erro ao buscar clips: {e}")
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
    if not clip.get("thumbnail_url"):
        return None

    video_url = clip_video_url(clip["thumbnail_url"])
    debug_print(f"Baixando vídeo do clip: {video_url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url, timeout=CLIP_API_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.read()

                # Verifica se o arquivo não está vazio
                if len(data) == 0:
                    print(f"Vídeo do clip está vazio: {video_url}")
                    return None

                debug_print(f"Vídeo baixado com sucesso: {len(data)} bytes")
                return discord.File(io.BytesIO(data), filename=f"clip_{clip['id']}.mp4")

    except Exception as e:
        print(f"Erro ao baixar vídeo do clip: {e}")
        return None

# ---- Eventos do Bot ----
@bot.event
async def on_ready():
    """Evento executado quando o bot fica online."""
    print(f"{bot.user} está online!")
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comando(s)")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

    if not check_twitch_clips.is_running():
        check_twitch_clips.start()
        print("Loop de verificação de clips iniciado")

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
        print(f"Erro ao responder interação: {e}")
        return

    username = parse_twitch_username(canal_twitch)
    server_id = interaction.guild.id

    print(f"Configurando monitoramento para '{username}' no servidor {server_id}")

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
    print(f"Configuração salva para {username} (ID: {broadcaster_id})")

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
        return

    token = await get_twitch_token()
    if not token:
        print("Erro: Não foi possível obter token da Twitch")
        return

    now = datetime.now(timezone.utc)
    debug_print(f"Verificando clips às {now}")

    for server_id, cfg in list(twitch_configs.items()):
        try:
            start = last_check_time.get(server_id, now - timedelta(hours=CLIP_LOOKBACK_HOURS))
            debug_print(f"Servidor {server_id}: Buscando clips de {start} até {now}")

            clips = await fetch_clips(cfg["broadcaster_id"], token, start, now)

            if not clips:
                debug_print(f"Nenhum clip encontrado para {cfg['username']}")
                # Atualizar tempo mesmo sem clips
                if server_id not in last_check_time:
                    last_check_time[server_id] = now
                continue

            # Ordenar clips por data de criação (mais antigos primeiro)
            clips.sort(key=lambda c: c.get("created_at", ""))
            debug_print(f"Processando {len(clips)} clips para {cfg['username']}")

            new_clips_count = 0
            for clip in clips:
                clip_id = clip["id"]
                created = datetime.fromisoformat(clip["created_at"].replace("Z", "+00:00"))

                debug_print(f"Clip {clip_id}: criado em {created} (start={start}, now={now})")

                # Pular clips já enviados
                if clip_id in posted_clips.get(server_id, set()):
                    debug_print(f"Clip {clip_id} já foi enviado")
                    continue

                # Pular clips muito antigos
                if created < start:
                    debug_print(f"Clip {clip_id} é muito antigo ({created} < {start})")
                    continue

                channel = bot.get_channel(cfg["discord_channel"])
                if not channel:
                    print(f"Canal Discord não encontrado: {cfg['discord_channel']}")
                    continue

                # Criar embed simplificado
                embed = create_clip_embed(clip, cfg["username"])
                files = []

                # Baixar e anexar vídeo se configurado
                if CLIP_ATTACH_VIDEO:
                    video_file = await download_clip_video(clip)
                    if video_file:
                        files.append(video_file)
                        debug_print(f"Vídeo do clip baixado: {clip.get('title', 'Sem título')}")

                try:
                    # Mensagem principal com título e link
                    clip_title = clip.get("title", "Clip sem título")
                    message_content = f"**Novo clip de {cfg['username']}:** {clip_title}\n{clip.get('url')}"

                    await channel.send(content=message_content, embed=embed, files=files)

                    posted_clips.setdefault(server_id, set()).add(clip_id)
                    new_clips_count += 1

                    if CLIP_ATTACH_VIDEO and files:
                        print(f"✅ Novo clip enviado com vídeo: {clip_title} de {cfg['username']}")
                    else:
                        print(f"✅ Novo clip enviado: {clip_title} de {cfg['username']}")

                    # Atualizar último tempo de verificação
                    if created > last_check_time.get(server_id, start):
                        last_check_time[server_id] = created

                except Exception as e:
                    print(f"Erro ao enviar clip: {e}")

            if new_clips_count > 0:
                print(f"📺 {new_clips_count} novos clips enviados para {cfg['username']}")
            else:
                debug_print(f"Nenhum clip novo para {cfg['username']}")

        except Exception as e:
            print(f"Erro ao verificar clips para servidor {server_id}: {e}")

@check_twitch_clips.before_loop
async def before_check_twitch_clips():
    """Aguarda o bot estar pronto antes de iniciar o loop."""
    await bot.wait_until_ready()

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
        print(f"❌ Variáveis de ambiente faltando: {', '.join(missing_vars)}")
        if "DISCORD_TOKEN" in missing_vars:
            print("Bot não pode iniciar sem DISCORD_TOKEN.")
            exit(1)
        else:
            print("⚠️ Twitch desabilitado. Defina TWITCH_CLIENT_ID e TWITCH_SECRET para habilitar.")

    if DISCORD_TOKEN:
        print("🚀 Iniciando bot...")
        if DEBUG_MODE:
            print("🐛 Modo debug ativado")
        if CLIP_ATTACH_VIDEO:
            print("🎬 Anexo de vídeo ativado")
        bot.run(DISCORD_TOKEN)
