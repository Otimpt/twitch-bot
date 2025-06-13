#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Discord para monitorar e enviar clips recentes da Twitch
Autor: Assistant
Versão: 1.0
"""

import os
import io
import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Set, List, Optional

import aiohttp
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# ==================== CONFIGURAÇÕES ====================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_SECRET = os.getenv("TWITCH_SECRET")

# Configurações do bot
CLIP_CHECK_SECONDS = int(os.getenv("CLIP_CHECK_SECONDS", "60"))  # Verificar a cada 60s
CLIP_LOOKBACK_HOURS = float(os.getenv("CLIP_LOOKBACK_HOURS", "1.0"))  # Buscar clips da última 1h
CLIP_SHOW_DETAILS = os.getenv("CLIP_SHOW_DETAILS", "true").lower() == "true"
CLIP_API_TIMEOUT = int(os.getenv("CLIP_API_TIMEOUT", "15"))
CLIP_ATTACH_VIDEO = os.getenv("CLIP_ATTACH_VIDEO", "false").lower() == "true"
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# ==================== CONFIGURAÇÃO DO BOT ====================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Armazenamento de dados
twitch_configs: Dict[int, Dict[str, str]] = {}  # {server_id: {username, broadcaster_id, discord_channel}}
posted_clips: Dict[int, Set[str]] = {}  # {server_id: {clip_ids}}
last_check_time: Dict[int, datetime] = {}  # {server_id: datetime}

# Cache persistente
CACHE_FILE = "twitch_clips_cache.json"

def log(message: str, level: str = "INFO"):
    """Sistema de log simples"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{level} {timestamp}] {message}")

def debug_log(message: str):
    """Log apenas se debug estiver ativado"""
    if DEBUG_MODE:
        log(message, "DEBUG")

# ==================== CACHE PERSISTENTE ====================
def load_cache():
    """Carrega cache do arquivo"""
    global posted_clips
    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
            posted_clips = {int(k): set(v) for k, v in data.items()}
        log(f"Cache carregado: {sum(len(clips) for clips in posted_clips.values())} clips")
    except FileNotFoundError:
        log("Cache não encontrado, iniciando vazio")
        posted_clips = {}
    except Exception as e:
        log(f"Erro ao carregar cache: {e}", "ERROR")
        posted_clips = {}

def save_cache():
    """Salva cache no arquivo"""
    try:
        data = {str(k): list(v) for k, v in posted_clips.items()}
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
        debug_log("Cache salvo com sucesso")
    except Exception as e:
        log(f"Erro ao salvar cache: {e}", "ERROR")

# ==================== FUNÇÕES DA TWITCH ====================
async def get_twitch_token() -> Optional[str]:
    """Obtém token de acesso da Twitch"""
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
                debug_log(f"Token obtido: {token[:10]}..." if token else "Falha ao obter token")
                return token
    except Exception as e:
        log(f"Erro ao obter token da Twitch: {e}", "ERROR")
        return None

def parse_twitch_username(raw_input: str) -> str:
    """Extrai username da Twitch de diferentes formatos"""
    username = raw_input.strip().replace("@", "").lower()

    # Remove URL parts
    if "//" in username:
        username = username.split("//", 1)[1]
    if username.startswith("www."):
        username = username[4:]
    if username.startswith("twitch.tv/"):
        username = username[10:]
    if "/" in username:
        username = username.split("/", 1)[0]
    if "?" in username:
        username = username.split("?", 1)[0]

    return username

async def get_broadcaster_id(username: str, token: str) -> Optional[str]:
    """Busca ID do broadcaster pelo username"""
    url = "https://api.twitch.tv/helix/users"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    params = {"login": username}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=CLIP_API_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.json()

                if data.get("data") and len(data["data"]) > 0:
                    broadcaster_id = data["data"][0]["id"]
                    log(f"Broadcaster encontrado: {username} -> ID {broadcaster_id}")
                    return broadcaster_id
                else:
                    log(f"Usuário não encontrado: {username}", "ERROR")
                    return None
    except Exception as e:
        log(f"Erro ao buscar broadcaster {username}: {e}", "ERROR")
        return None

async def fetch_clips(broadcaster_id: str, token: str, start_time: datetime, end_time: datetime) -> List[dict]:
    """Busca clips de um broadcaster em um período"""
    url = "https://api.twitch.tv/helix/clips"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    params = {
        "broadcaster_id": broadcaster_id,
        "first": 100,
        "started_at": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ended_at": end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }

    debug_log(f"Buscando clips de {start_time} até {end_time}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=CLIP_API_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.json()
                clips = data.get("data", [])
                debug_log(f"Encontrados {len(clips)} clips")
                return clips
    except Exception as e:
        log(f"Erro ao buscar clips: {e}", "ERROR")
        return []

def clip_video_url(thumbnail_url: str) -> str:
    """Converte URL da thumbnail para URL do vídeo"""
    return thumbnail_url.split("-preview-", 1)[0] + ".mp4"

def create_clip_embed(clip: dict, username: str) -> discord.Embed:
    """Cria embed do Discord para o clip"""
    embed = discord.Embed(
        title=clip.get("title", "Novo Clip"),
        url=clip.get("url"),
        color=0x9146FF,  # Cor roxa da Twitch
        timestamp=datetime.fromisoformat(clip.get("created_at", "").replace("Z", "+00:00"))
    )

    embed.add_field(name="📺 Canal", value=username, inline=True)

    if CLIP_SHOW_DETAILS:
        embed.add_field(name="👀 Views", value=str(clip.get("view_count", 0)), inline=True)
        embed.add_field(name="👤 Criador", value=clip.get("creator_name", "Desconhecido"), inline=True)
        embed.add_field(name="⏱️ Duração", value=f"{clip.get('duration', 0):.1f}s", inline=True)

    if clip.get("thumbnail_url"):
        embed.set_image(url=clip["thumbnail_url"])

    embed.set_footer(text="Twitch Clips Bot", icon_url="https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-70x70.png")

    return embed

# ==================== EVENTOS DO BOT ====================
@bot.event
async def on_ready():
    """Evento quando o bot fica online"""
    log(f"🤖 Bot {bot.user} está online!")
    log(f"📊 Conectado a {len(bot.guilds)} servidor(es)")

    # Carregar cache
    load_cache()

    # Sincronizar comandos slash
    try:
        synced = await bot.tree.sync()
        log(f"✅ {len(synced)} comandos sincronizados")
    except Exception as e:
        log(f"Erro ao sincronizar comandos: {e}", "ERROR")

    # Iniciar loop de verificação
    if not check_clips_loop.is_running():
        check_clips_loop.start()
        log("🔄 Loop de verificação iniciado")

@bot.event
async def on_guild_join(guild):
    """Evento quando o bot entra em um servidor"""
    log(f"➕ Bot adicionado ao servidor: {guild.name} (ID: {guild.id})")

@bot.event
async def on_guild_remove(guild):
    """Evento quando o bot sai de um servidor"""
    log(f"➖ Bot removido do servidor: {guild.name} (ID: {guild.id})")
    # Limpar dados do servidor
    if guild.id in twitch_configs:
        del twitch_configs[guild.id]
    if guild.id in posted_clips:
        del posted_clips[guild.id]
    if guild.id in last_check_time:
        del last_check_time[guild.id]

# ==================== COMANDOS SLASH ====================
@bot.tree.command(name="setup", description="Configura o monitoramento de clips da Twitch")
async def setup_command(
    interaction: discord.Interaction,
    canal_twitch: str,
    canal_discord: discord.TextChannel
):
    """Comando para configurar monitoramento"""
    await interaction.response.defer()

    username = parse_twitch_username(canal_twitch)
    server_id = interaction.guild.id

    log(f"⚙️ Configurando {username} no servidor {interaction.guild.name}")

    # Verificar token
    token = await get_twitch_token()
    if not token:
        embed = discord.Embed(
            title="❌ Erro de Configuração",
            description="Não foi possível obter token da Twitch. Verifique as configurações do bot.",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)
        return

    # Buscar broadcaster ID
    broadcaster_id = await get_broadcaster_id(username, token)
    if not broadcaster_id:
        embed = discord.Embed(
            title="❌ Canal não encontrado",
            description=f"Não foi possível encontrar o canal **{username}** na Twitch.\n\nVerifique se o nome está correto.",
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

    # Inicializar dados
    posted_clips[server_id] = set()
    last_check_time[server_id] = datetime.now(timezone.utc) - timedelta(hours=CLIP_LOOKBACK_HOURS)

    # Salvar cache
    save_cache()

    embed = discord.Embed(
        title="✅ Configuração Concluída!",
        description=f"Monitorando clips de **{username}** em {canal_discord.mention}",
        color=0x00ff00
    )
    embed.add_field(name="🔄 Verificação", value=f"A cada {CLIP_CHECK_SECONDS}s", inline=True)
    embed.add_field(name="📅 Período", value=f"Últimas {CLIP_LOOKBACK_HOURS}h", inline=True)
    embed.add_field(name="🎬 Vídeo", value="✅ Sim" if CLIP_ATTACH_VIDEO else "❌ Não", inline=True)

    await interaction.followup.send(embed=embed)
    log(f"✅ Configuração salva para {username}")

@bot.tree.command(name="status", description="Mostra o status do monitoramento")
async def status_command(interaction: discord.Interaction):
    """Comando para ver status"""
    server_id = interaction.guild.id

    if server_id not in twitch_configs:
        embed = discord.Embed(
            title="❌ Não Configurado",
            description="Use `/setup` para configurar o monitoramento primeiro.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)
        return

    config = twitch_configs[server_id]
    channel = bot.get_channel(config["discord_channel"])
    clips_count = len(posted_clips.get(server_id, set()))

    embed = discord.Embed(
        title="📊 Status do Monitoramento",
        color=0x9146FF
    )
    embed.add_field(name="📺 Canal Twitch", value=config["username"], inline=True)
    embed.add_field(name="💬 Canal Discord", value=channel.mention if channel else "❌ Não encontrado", inline=True)
    embed.add_field(name="📈 Clips Enviados", value=str(clips_count), inline=True)
    embed.add_field(name="🔄 Verificação", value=f"{CLIP_CHECK_SECONDS}s", inline=True)
    embed.add_field(name="📅 Período", value=f"{CLIP_LOOKBACK_HOURS}h", inline=True)
    embed.add_field(name="🎬 Vídeo", value="✅ Sim" if CLIP_ATTACH_VIDEO else "❌ Não", inline=True)

    last_check = last_check_time.get(server_id)
    if last_check:
        embed.add_field(
            name="🕐 Última Verificação", 
            value=f"<t:{int(last_check.timestamp())}:R>", 
            inline=False
        )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="test", description="Testa a busca de clips manualmente")
async def test_command(interaction: discord.Interaction):
    """Comando para testar busca"""
    server_id = interaction.guild.id

    if server_id not in twitch_configs:
        embed = discord.Embed(
            title="❌ Não Configurado",
            description="Use `/setup` primeiro.",
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

    # Buscar clips das últimas 24h
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=24)

    clips = await fetch_clips(config["broadcaster_id"], token, start, now)

    embed = discord.Embed(
        title="🧪 Teste de Clips",
        description=f"Encontrados **{len(clips)}** clips nas últimas 24h para **{config['username']}**",
        color=0x9146FF
    )

    if clips:
        # Mostrar os 5 clips mais recentes
        recent_clips = sorted(clips, key=lambda c: c.get("created_at", ""), reverse=True)[:5]
        for i, clip in enumerate(recent_clips, 1):
            created = clip.get("created_at", "")
            if created:
                timestamp = int(datetime.fromisoformat(created.replace("Z", "+00:00")).timestamp())
                embed.add_field(
                    name=f"#{i} {clip.get('title', 'Sem título')[:40]}",
                    value=f"👤 {clip.get('creator_name', '?')} • <t:{timestamp}:R>",
                    inline=False
                )
    else:
        embed.add_field(name="📭", value="Nenhum clip encontrado", inline=False)

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="clear", description="Limpa o cache de clips enviados")
async def clear_command(interaction: discord.Interaction):
    """Comando para limpar cache"""
    server_id = interaction.guild.id

    if server_id not in twitch_configs:
        embed = discord.Embed(
            title="❌ Não Configurado",
            description="Use `/setup` primeiro.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)
        return

    # Limpar cache do servidor
    clips_count = len(posted_clips.get(server_id, set()))
    posted_clips[server_id] = set()
    save_cache()

    embed = discord.Embed(
        title="🗑️ Cache Limpo",
        description=f"Removidos **{clips_count}** clips do cache.\n\nClips antigos podem ser reenviados na próxima verificação.",
        color=0x00ff00
    )

    await interaction.response.send_message(embed=embed)
    log(f"Cache limpo para servidor {server_id}: {clips_count} clips removidos")

@bot.tree.command(name="help", description="Mostra todos os comandos disponíveis")
async def help_command(interaction: discord.Interaction):
    """Comando de ajuda"""
    embed = discord.Embed(
        title="🤖 Comandos do Bot",
        description="Bot para monitorar clips recentes da Twitch",
        color=0x0099ff
    )

    embed.add_field(
        name="⚙️ Configuração",
        value="`/setup` - Configura monitoramento\n`/status` - Mostra status atual\n`/clear` - Limpa cache",
        inline=False
    )

    embed.add_field(
        name="🧪 Testes",
        value="`/test` - Testa busca de clips\n`/help` - Mostra esta ajuda",
        inline=False
    )

    embed.add_field(
        name="📋 Como usar",
        value="1. Use `/setup` com o nome do canal da Twitch\n2. O bot verificará automaticamente novos clips\n3. Use `/status` para acompanhar",
        inline=False
    )

    await interaction.response.send_message(embed=embed)

# ==================== LOOP DE VERIFICAÇÃO ====================
@tasks.loop(seconds=CLIP_CHECK_SECONDS)
async def check_clips_loop():
    """Loop principal que verifica novos clips"""
    if not twitch_configs:
        debug_log("Nenhuma configuração ativa")
        return

    token = await get_twitch_token()
    if not token:
        log("Erro ao obter token da Twitch", "ERROR")
        return

    now = datetime.now(timezone.utc)
    debug_log(f"Verificando clips - {now.strftime('%H:%M:%S')}")

    for server_id, config in list(twitch_configs.items()):
        try:
            # Definir período de busca
            start_time = last_check_time.get(server_id, now - timedelta(hours=CLIP_LOOKBACK_HOURS))

            # Buscar clips
            clips = await fetch_clips(config["broadcaster_id"], token, start_time, now)

            if not clips:
                debug_log(f"Nenhum clip para {config['username']}")
                continue

            # Processar clips
            new_clips = 0
            for clip in sorted(clips, key=lambda c: c.get("created_at", "")):
                clip_id = clip["id"]
                created_time = datetime.fromisoformat(clip["created_at"].replace("Z", "+00:00"))

                # Verificar se já foi enviado
                if clip_id in posted_clips.get(server_id, set()):
                    continue

                # Verificar se está no período
                if created_time < start_time:
                    continue

                # Enviar clip
                channel = bot.get_channel(config["discord_channel"])
                if not channel:
                    log(f"Canal Discord não encontrado: {config['discord_channel']}", "ERROR")
                    continue

                try:
                    embed = create_clip_embed(clip, config["username"])
                    files = []

                    # Baixar vídeo se configurado
                    if CLIP_ATTACH_VIDEO and clip.get("thumbnail_url"):
                        try:
                            video_url = clip_video_url(clip["thumbnail_url"])
                            async with aiohttp.ClientSession() as session:
                                async with session.get(video_url, timeout=CLIP_API_TIMEOUT * 2) as resp:
                                    if resp.status == 200:
                                        data = await resp.read()
                                        if len(data) > 0:
                                            files.append(discord.File(io.BytesIO(data), filename="clip.mp4"))
                        except Exception as e:
                            debug_log(f"Erro ao baixar vídeo: {e}")

                    # Enviar mensagem
                    await channel.send(content=clip.get("url"), embed=embed, files=files)

                    # Marcar como enviado
                    posted_clips.setdefault(server_id, set()).add(clip_id)
                    new_clips += 1

                    log(f"✅ Clip enviado: {clip.get('title', 'Sem título')} - {config['username']}")

                    # Atualizar último tempo
                    if created_time > last_check_time.get(server_id, start_time):
                        last_check_time[server_id] = created_time

                except Exception as e:
                    log(f"Erro ao enviar clip: {e}", "ERROR")

            if new_clips > 0:
                log(f"📺 {new_clips} novos clips enviados para {config['username']}")
                save_cache()

        except Exception as e:
            log(f"Erro ao verificar clips do servidor {server_id}: {e}", "ERROR")

@check_clips_loop.before_loop
async def before_check_clips():
    """Aguarda o bot estar pronto"""
    await bot.wait_until_ready()

# ==================== EXECUÇÃO ====================
if __name__ == "__main__":
    # Verificar variáveis obrigatórias
    missing_vars = []
    if not DISCORD_TOKEN:
        missing_vars.append("DISCORD_TOKEN")
    if not TWITCH_CLIENT_ID:
        missing_vars.append("TWITCH_CLIENT_ID")
    if not TWITCH_SECRET:
        missing_vars.append("TWITCH_SECRET")

    if missing_vars:
        log(f"❌ Variáveis faltando: {', '.join(missing_vars)}", "ERROR")
        log("Configure o arquivo .env com as variáveis necessárias", "ERROR")
        exit(1)

    log("🚀 Iniciando bot...")
    log(f"⚙️ Configurações: Verificação={CLIP_CHECK_SECONDS}s, Lookback={CLIP_LOOKBACK_HOURS}h, Vídeo={CLIP_ATTACH_VIDEO}")

    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        log(f"Erro fatal: {e}", "ERROR")
