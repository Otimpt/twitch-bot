#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import discord
from discord.ext import commands, tasks
import json
import os
import aiohttp
from dotenv import load_dotenv
from datetime import datetime
bot = commands.Bot(command_prefix="!", intents=intents)
last_clips = {}


    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")
    else:
        print(f"Erro ao sincronizar comandos: {e}")


        "client_secret": TWITCH_SECRET,
        "grant_type": "client_credentials",
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=params, timeout=10) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("access_token")
    except aiohttp.ClientError as e:

        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}",
    url = f"https://api.twitch.tv/helix/users?login={username}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                resp.raise_for_status()
                data = await resp.json()
    except aiohttp.ClientError as e:
    if data.get("data"):
        return data["data"][0]["id"]

        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}",
    url = (
        f"https://api.twitch.tv/helix/clips?"
        f"broadcaster_id={broadcaster_id}&first={limit}"
    )

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("data", [])
    except aiohttp.ClientError as e:


@bot.tree.command(
    name="twitch_setup", description="Configura monitoramento de clips da Twitch"
)
async def twitch_setup(
    interaction: discord.Interaction,
    canal_twitch: str,
    canal_discord: discord.TextChannel,
):
    username = canal_twitch.replace("@", "").lower()
            color=0xFF0000,
        "username": username,
        "broadcaster_id": broadcaster_id,
        "discord_channel": canal_discord.id,
        color=0x9146FF,
    embed.add_field(
        name="🔄 Frequência",
        value="Verifica novos clips a cada 5 minutos",
        inline=False,
    )

    for server_id, config in twitch_configs.items():
            clips = await get_latest_clips(config["broadcaster_id"], 3)


                clip_id = clip["id"]
                    # Novo clip encontrado!
                    channel = bot.get_channel(config["discord_channel"])
                            title="🎬 Novo Clip da Twitch!",
                            description=f"**{clip['title']}**",
                            url=clip["url"],
                            color=0x9146FF,
                        )
                        embed.add_field(
                            name="📺 Canal", value=config["username"], inline=True
                        )
                        embed.add_field(
                            name="👀 Views", value=clip["view_count"], inline=True
                        )
                        embed.add_field(
                            name="⏱️ Duração", value=f"{clip['duration']}s", inline=True
                        )
                        embed.add_field(
    name="twitch_setup",
    description="Configura monitoramento de clips da Twitch",
    embed.add_field(
        name="✅ Status", value="Monitoramento ativo", inline=False
    )
                            name="📺 Canal",
                            value=config["username"],
                            inline=True,
                        )
                        embed.add_field(
                            name="👀 Views",
                            value=clip["view_count"],
                            inline=True,
                            name="⏱️ Duração",
                            value=f"{clip['duration']}s",
                            inline=True,
                            inline=True,
                        )
                        embed.add_field(
                            name="📅 Data",
                            value=clip["created_at"][:10],
                            inline=True,
                        )
                        if clip.get("thumbnail_url"):
                            embed.set_image(url=clip["thumbnail_url"])

@bot.tree.command(
    name="twitch_status",
    description="Mostra o status do monitoramento da Twitch",
)
            color=0xFF0000,
        channel = bot.get_channel(config["discord_channel"])

        embed = discord.Embed(
            title="📺 Status do Monitoramento Twitch", color=0x9146FF
        )
        embed.add_field(name="📺 Canal", value=config["username"], inline=True)
        embed.add_field(
            name="💬 Canal Discord",
            value=channel.mention if channel else "Canal não encontrado",
            inline=True,
        embed.add_field(
            name="🔄 Última verificação", value="A cada 5 minutos", inline=True
        )
        embed.add_field(
            name="📊 Clips monitorados",
            value=len(last_clips.get(server_id, [])),
            inline=True,
        )


        title="🏓 Pong!",
        description=f"Latência: **{latency}ms**",
        color=0x00FF00,

@bot.tree.command(
    name="help", description="Mostra todos os comandos disponíveis"
)

        inline=False,
        inline=False,

    """Verifica novos clips da Twitch periodicamente"""
    # Copia as configurações para evitar erros caso sejam alteradas
    # enquanto a iteração estiver em andamento
    for server_id, config in list(twitch_configs.items()):
        try:
            print(
                f"[DEBUG] Checando clips para {config['username']} em {datetime.now(timezone.utc).isoformat()}"
            )
            # Busca clips criados após a última verificação (com margem para atrasos)
            started_at = (
                last_check_time.get(
                    server_id,
                    datetime.now(timezone.utc) - timedelta(hours=CLIP_LOOKBACK_HOURS),
                )
                - timedelta(seconds=CLIP_API_LAG_SECONDS)
            )
            clips = await get_latest_clips(
                config['broadcaster_id'], started_at, max_pages=CLIP_MAX_PAGES
            )
            print(f"[DEBUG] {len(clips)} clip(s) encontrados")

            if server_id not in last_clips:
                last_clips[server_id] = set()
            if server_id not in last_check_time:
                last_check_time[server_id] = (
                    datetime.now(timezone.utc) - timedelta(hours=CLIP_LOOKBACK_HOURS)
                )

            latest_time = last_check_time[server_id]
            for clip in clips:
                clip_id = clip['id']
                created_at = datetime.fromisoformat(
                    clip['created_at'].replace('Z', '+00:00')
                ).astimezone(timezone.utc)
                if created_at >= last_check_time[server_id] and clip_id not in last_clips[server_id]:
                    channel = bot.get_channel(config['discord_channel'])
                    if channel:
                        message = f"{clip['url']}\n**{clip['title']}**"
                        details = []
                        if CLIP_SHOW_DETAILS:
                            details.append(f"👀 {clip['view_count']} views")
                            details.append(f"👤 {clip['creator_name']}")
                            details.append(f"📅 {clip['created_at'][:10]}")
                        details.append(f"⏱️ {clip['duration']}s")
                        details.append(f"🎮 {clip.get('game_name', 'N/A')}")
                        message += "\n" + " | ".join(details)

                        file = None
                        if CLIP_ATTACH_VIDEO and clip.get('thumbnail_url'):
                            mp4_url = clip_video_url(clip['thumbnail_url'])
                            if mp4_url:
                                try:
                                    timeout = aiohttp.ClientTimeout(total=CLIP_API_TIMEOUT)
                                    async with aiohttp.ClientSession(timeout=timeout) as session:
                                        async with session.get(mp4_url) as resp:
                                            if resp.status == 200:
                                                data = await resp.read()
                                                file = discord.File(BytesIO(data), filename=f"{clip_id}.mp4")
                                            else:
                                                print(f"Erro ao baixar vídeo: {resp.status}")
                                except Exception as e:
                                    print(f"Erro ao baixar vídeo do clip {clip_id}: {e}")

                        if file:
                            print(f"[DEBUG] Enviando vídeo do clip {clip_id}")
                            await channel.send(content=message, file=file)
                        else:
                            print(f"[DEBUG] Enviando link do clip {clip_id}")
                            await channel.send(content=message)

                    last_clips[server_id].add(clip_id)

                if created_at >= latest_time:
                    latest_time = created_at

            # Avança somente se algum clip mais novo foi encontrado
            if latest_time > last_check_time[server_id]:
                last_check_time[server_id] = latest_time

            # Mantém apenas os últimos 50 clips na memória
            if len(last_clips[server_id]) > 50:
                last_clips[server_id] = set(list(last_clips[server_id])[-50:])

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
            title="📺 Status do Monitoramento Twitch",
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
