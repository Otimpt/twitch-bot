"""Comandos de configuração básica"""

import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta

from utils.twitch_api import get_twitch_token, get_broadcaster_id, parse_twitch_username
from utils.cache import save_cache
from utils.helpers import log, is_admin_or_mod
from config.settings import *
from models.dataclasses import *

async def setup_commands(bot):
    """Registra comandos de configuração"""
    
    @bot.tree.command(name="twitch-setup", description="Adiciona um streamer para monitoramento")
    @is_admin_or_mod()
    async def setup_command(
        interaction: discord.Interaction,
        canal_twitch: str,
        canal_discord: discord.TextChannel,
        nickname: str = ""
    ):
        """Comando para adicionar streamer"""
        await interaction.response.defer()

        username = parse_twitch_username(canal_twitch)
        server_id = interaction.guild.id

        log(f"⚙️ Adicionando {username} no servidor {interaction.guild.name}")

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

        # Inicializar estruturas se necessário
        if server_id not in server_streamers:
            server_streamers[server_id] = {}
        if server_id not in server_filters:
            server_filters[server_id] = FilterConfig()
        if server_id not in server_themes:
            server_themes[server_id] = ThemeConfig()
        if server_id not in server_templates:
            server_templates[server_id] = TemplateConfig()
        if server_id not in server_stats:
            server_stats[server_id] = ServerStats()

        # Verificar se já existe
        if broadcaster_id in server_streamers[server_id]:
            embed = discord.Embed(
                title="⚠️ Streamer já existe",
                description=f"O streamer **{username}** já está sendo monitorado neste servidor.",
                color=0xffaa00
            )
            await interaction.followup.send(embed=embed)
            return

        # Salvar configuração
        server_streamers[server_id][broadcaster_id] = StreamerConfig(
            username=username,
            broadcaster_id=broadcaster_id,
            discord_channel=canal_discord.id,
            nickname=nickname
        )

        # Inicializar dados
        if server_id not in posted_clips:
            posted_clips[server_id] = set()
        if server_id not in last_check_time:
            last_check_time[server_id] = datetime.now(timezone.utc) - timedelta(hours=CLIP_LOOKBACK_HOURS)

        # Salvar cache
        save_cache()

        display_name = nickname or username
        embed = discord.Embed(
            title="✅ Streamer Adicionado!",
            description=f"Monitorando clips de **{display_name}** em {canal_discord.mention}",
            color=0x00ff00
        )
        embed.add_field(name="🔄 Verificação", value=f"A cada {CLIP_CHECK_SECONDS}s", inline=True)
        embed.add_field(name="📅 Período", value=f"Últimas {CLIP_LOOKBACK_HOURS}h", inline=True)
        embed.add_field(name="🎬 Vídeo", value="✅ Sim" if CLIP_ATTACH_VIDEO else "❌ Não", inline=True)

        await interaction.followup.send(embed=embed)
        log(f"✅ Streamer {username} adicionado ao servidor {server_id}")

    # REMOVIDO: comando help duplicado que estava aqui
