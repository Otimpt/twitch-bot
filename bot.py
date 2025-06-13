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
# ---- Configuração ----
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_SECRET = os.getenv("TWITCH_SECRET")

# Intervalo entre verificações de novos clips (segundos)
CLIP_CHECK_SECONDS = int(os.getenv("CLIP_CHECK_SECONDS", "30"))
# Quantas horas no passado considerar ao iniciar o monitoramento
CLIP_LOOKBACK_HOURS = float(os.getenv("CLIP_LOOKBACK_HOURS", "2"))
# Mostrar visualizações, autor e data dos clips
CLIP_SHOW_DETAILS = os.getenv("CLIP_SHOW_DETAILS", "true").lower() == "true"
# Tempo limite de chamadas HTTP
CLIP_API_TIMEOUT = int(os.getenv("CLIP_API_TIMEOUT", "10"))
# Enviar video mp4 como anexo
CLIP_ATTACH_VIDEO = os.getenv("CLIP_ATTACH_VIDEO", "false").lower() == "true"
# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Por servidor: configurações, ids de clips enviados e horário da última verificação
TwitchConfig = Dict[str, str]
posted_clips: Dict[int, Set[str]] = {}
last_check_time: Dict[int, datetime] = {}
# ---- Utilidades Twitch ----
        "grant_type": "client_credentials"

            async with session.post(url, data=params, timeout=CLIP_API_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("access_token")
        print(f"Erro ao obter token: {e}")
        return None
    """Busca o ID do broadcaster pelo nome de usuário."""
    url = "https://api.twitch.tv/helix/users"
        "Authorization": f"Bearer {token}"
    params = {"login": username}

            async with session.get(url, headers=headers, params=params, timeout=CLIP_API_TIMEOUT) as resp:
                return None
    except Exception as e:
        return None
    """Converte URL da thumbnail para URL do vídeo."""
    """Busca clips de um broadcaster em um período específico."""
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }

    except Exception as e:
        return []
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
    print(f"{bot.user} está online!")
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comando(s)")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

    if not check_twitch_clips.is_running():
        check_twitch_clips.start()
# ---- Comandos do Bot ----
async def twitch_setup(interaction: discord.Interaction, canal_twitch: str, canal_discord: discord.TextChannel):
    await interaction.response.defer()

    username = canal_twitch.replace("@", "").lower()
    server_id = interaction.guild.id

    # Obter token e ID do broadcaster
            color=0xff0000
            title="❌ Canal não encontrado",
            color=0xff0000
    # Salvar configuração
        "discord_channel": canal_discord.id

        title="✅ Configuração salva!",
        description=f"Monitorando clips de **{username}** em {canal_discord.mention}",
        color=0x00ff00
    await interaction.followup.send(embed=embed)

            color=0xff0000

    embed.add_field(name="📺 Canal", value=config["username"], inline=True)
    embed.add_field(name="💬 Canal Discord", value=channel.mention if channel else "?", inline=True)
    embed.add_field(name="🔄 Frequência", value=f"{CLIP_CHECK_SECONDS}s", inline=True)
    embed.add_field(name="📊 Clips enviados", value=len(posted_clips.get(server_id, set())), inline=True)
    await interaction.response.send_message(embed=embed)
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
        value="`/twitch_setup` - Configura monitoramento\n`/twitch_status` - Status do monitoramento",
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
    now = datetime.now(timezone.utc)
    for server_id, cfg in list(twitch_configs.items()):
        try:
            start = last_check_time.get(server_id, now - timedelta(hours=CLIP_LOOKBACK_HOURS))
            clips = await fetch_clips(cfg["broadcaster_id"], start, now, token)

            # Ordenar clips por data de criação
            clips.sort(key=lambda c: c.get("created_at", ""))

            for clip in clips:
                clip_id = clip["id"]
                created = datetime.fromisoformat(clip["created_at"].replace("Z", "+00:00"))

                # Pular clips já enviados ou muito antigos
                if clip_id in posted_clips.get(server_id, set()) or created < start:
                    continue

                channel = bot.get_channel(cfg["discord_channel"])
                if not channel:
                    continue

                # Criar embed e enviar
                embed = create_clip_embed(clip, cfg["username"])
                files = []

                # Anexar vídeo se configurado
                if CLIP_ATTACH_VIDEO and clip.get("thumbnail_url"):
                    video_url = clip_video_url(clip["thumbnail_url"])
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(video_url, timeout=CLIP_API_TIMEOUT) as resp:
                                resp.raise_for_status()
                                data = await resp.read()
                                files.append(discord.File(io.BytesIO(data), filename="clip.mp4"))
                    except Exception as e:
                        print(f"Erro ao baixar vídeo do clip: {e}")

                await channel.send(content=clip.get("url"), embed=embed, files=files)
                posted_clips.setdefault(server_id, set()).add(clip_id)

                # Atualizar último tempo de verificação
                if created > last_check_time.get(server_id, start):
                    last_check_time[server_id] = created

            # Se não há clips, atualizar tempo mesmo assim
            if not clips and server_id not in last_check_time:
                last_check_time[server_id] = now

        except Exception as e:
            print(f"Erro ao verificar clips para servidor {server_id}: {e}")

# ---- Execução ----
    missing_vars = []

        missing_vars.append("DISCORD_TOKEN")
        missing_vars.append("TWITCH_CLIENT_ID")
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


# -------------------- Execução --------------------
        print("❌ Variáveis faltando: " + ", ".join(missing))
                        else:
                            print(f"[DEBUG] Enviando link do clip {clip_id}")
                            await channel.send(content=message)

                    last_clips[server_id].add(clip_id)

                if created_at >= latest_time:
                    latest_time = created_at

        embed = discord.Embed(title="📺 Status do Monitoramento Twitch", color=0x9146FF)

@bot.tree.command(name="help", description="Mostra todos os comandos disponíveis")

        except Exception as e:
            print(f"Erro ao verificar clips para servidor {server_id}: {e}")

@bot.tree.command(name="twitch_status", description="Mostra o status do monitoramento da Twitch")
async def twitch_status(interaction: discord.Interaction):
    server_id = interaction.guild.id

    if server_id not in twitch_configs:
        embed = discord.Embed(
            title="❌ Twitch não configurado",
            description="Use `/twitch_setup` para configurar o monitoramento de clips.",
            color=0xff0000
        )
    else:
        config = twitch_configs[server_id]
        channel = bot.get_channel(config['discord_channel'])

        embed = discord.Embed(
    if not twitch_configs:
        return

    token = await get_twitch_token()
    if not token:
        print("Erro: Não foi possível obter token da Twitch")
        return

        clips = await fetch_clips(cfg["broadcaster_id"], start, now, token)
            color=0x9146ff
        )
        embed.add_field(name="📺 Canal", value=config['username'], inline=True)
        embed.add_field(name="💬 Canal Discord", value=channel.mention if channel else "Canal não encontrado", inline=True)
        embed.add_field(name="✅ Status", value="Ativo", inline=True)
        embed.add_field(name="🔄 Última verificação", value=f"A cada {CLIP_CHECK_SECONDS}s", inline=True)
        embed.add_field(name="📊 Clips monitorados", value=len(last_clips.get(server_id, [])), inline=True)

    await interaction.response.send_message(embed=embed)

# ==================== COMANDOS GERAIS ====================

@bot.tree.command(name="ping", description="Verifica a latência do bot")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latência: **{latency}ms**",
        color=0x00ff00
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="Mostra todos os comandos disponíveis")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Comandos do Bot",
        description="Aqui estão todos os comandos disponíveis:",
        color=0x0099ff
    )

    embed.add_field(
        name="📺 Twitch",
        value="`/twitch_setup` - Configura monitoramento\n`/twitch_status` - Status do monitoramento",
        inline=False
    )

    embed.add_field(
        name="🔧 Utilidades",
        value="`/ping` - Verifica latência\n`/help` - Mostra esta mensagem",
        inline=False
    )

    await interaction.response.send_message(embed=embed)

# Inicia o bot
if __name__ == "__main__":
    missing = []
        missing.append("DISCORD_TOKEN")
    if not TWITCH_CLIENT_ID:
        missing.append("TWITCH_CLIENT_ID")
    if not TWITCH_SECRET:
        missing.append("TWITCH_SECRET")

    if missing:
        print("❌ Variáveis de ambiente faltando: " + ", ".join(missing))
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
        bot.run(DISCORD_TOKEN)
