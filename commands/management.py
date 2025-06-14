"""Comandos de gerenciamento"""

import discord
from discord.ext import commands
from datetime import datetime, timedelta

from utils.twitch_api import get_twitch_token, fetch_clips, parse_twitch_username
from utils.filters import apply_filters
from utils.cache import save_cache
from utils.helpers import log
from config.settings import *
from models.dataclasses import *

async def management_commands(bot):
    """Registra comandos de gerenciamento"""

    @bot.tree.command(name="list-channels", description="Lista todos os streamers monitorados")
    async def list_command(interaction: discord.Interaction):
        """Lista streamers do servidor"""
        server_id = interaction.guild.id
        
        if server_id not in server_streamers or not server_streamers[server_id]:
            embed = discord.Embed(
                title="📭 Nenhum Streamer",
                description="Use `/twitch-setup` para adicionar streamers para monitoramento.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title="📺 Streamers Monitorados",
            color=0x9146FF
        )
        
        for i, (broadcaster_id, config) in enumerate(server_streamers[server_id].items(), 1):
            channel = bot.get_channel(config.discord_channel)
            display_name = config.nickname or config.username
            status = "✅ Ativo" if config.enabled else "⏸️ Pausado"
            
            # Status de notificações
            live_status = "🔴 Live ON" if config.live_notifications else "⚫ Live OFF"
            live_channel = ""
            if config.live_notifications and config.live_channel:
                live_ch = bot.get_channel(config.live_channel)
                live_channel = f" → {live_ch.mention}" if live_ch else " → ❌ Canal não encontrado"
            
            embed.add_field(
                name=f"{i}. {display_name}",
                value=f"**Clips:** {channel.mention if channel else '❌ Não encontrado'} {status}\n**Lives:** {live_status}{live_channel}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="remove", description="Remove um streamer do monitoramento")
    async def remove_command(interaction: discord.Interaction, streamer: str):
        """Remove streamer"""
        server_id = interaction.guild.id
        
        if server_id not in server_streamers:
            embed = discord.Embed(
                title="❌ Nenhum Streamer",
                description="Não há streamers configurados neste servidor.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Buscar streamer
        username = parse_twitch_username(streamer)
        broadcaster_id = None
        
        for bid, config in server_streamers[server_id].items():
            if config.username.lower() == username.lower():
                broadcaster_id = bid
                break
        
        if not broadcaster_id:
            embed = discord.Embed(
                title="❌ Streamer não encontrado",
                description=f"O streamer **{username}** não está sendo monitorado neste servidor.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Remover
        removed_config = server_streamers[server_id].pop(broadcaster_id)
        save_cache()
        
        embed = discord.Embed(
            title="✅ Streamer Removido",
            description=f"**{removed_config.username}** foi removido do monitoramento.",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed)
        log(f"Streamer {removed_config.username} removido do servidor {server_id}")

    @bot.tree.command(name="test", description="Testa busca de clips para um streamer específico")
    async def test_command(interaction: discord.Interaction, streamer: str):
        """Testa busca de clips"""
        await interaction.response.defer()
        
        server_id = interaction.guild.id
        username = parse_twitch_username(streamer)
        
        # Verificar se o streamer está configurado
        broadcaster_id = None
        streamer_config = None
        
        if server_id in server_streamers:
            for bid, config in server_streamers[server_id].items():
                if config.username.lower() == username.lower():
                    broadcaster_id = bid
                    streamer_config = config
                    break
        
        if not broadcaster_id:
            embed = discord.Embed(
                title="❌ Streamer não encontrado",
                description=f"O streamer **{username}** não está configurado neste servidor.\n\nUse `/twitch-setup` para adicionar primeiro.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Obter token
        token = await get_twitch_token()
        if not token:
            embed = discord.Embed(
                title="❌ Erro de API",
                description="Não foi possível obter token da Twitch.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Buscar clips
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=CLIP_LOOKBACK_HOURS)
        
        clips = await fetch_clips(broadcaster_id, token, start_time, now)
        
        display_name = streamer_config.nickname or streamer_config.username
        
        if not clips:
            embed = discord.Embed(
                title="📭 Nenhum Clip Encontrado",
                description=f"Não foram encontrados clips de **{display_name}** nas últimas {CLIP_LOOKBACK_HOURS} horas.",
                color=0xffaa00
            )
            embed.add_field(name="💡 Dica", value="Tente aumentar o período de busca ou verifique se o streamer teve clips recentes.", inline=False)
            await interaction.followup.send(embed=embed)
            return
        
        # Aplicar filtros
        filter_config = server_filters.get(server_id, FilterConfig())
        filtered_clips = [clip for clip in clips if apply_filters(clip, filter_config)]
        
        embed = discord.Embed(
            title="🔍 Resultado do Teste",
            description=f"Busca de clips para **{display_name}**",
            color=0x00ff00
        )
        
        embed.add_field(name="📊 Total Encontrados", value=str(len(clips)), inline=True)
        embed.add_field(name="✅ Após Filtros", value=str(len(filtered_clips)), inline=True)
        embed.add_field(name="⏱️ Período", value=f"{CLIP_LOOKBACK_HOURS}h", inline=True)
        
        if filtered_clips:
            # Mostrar alguns clips como exemplo
            clips_text = []
            for i, clip in enumerate(filtered_clips[:3]):
                clips_text.append(f"**{i+1}.** {clip.get('title', 'Sem título')}\n👀 {clip.get('view_count', 0)} views | ⏱️ {clip.get('duration', 0):.1f}s")
            
            embed.add_field(
                name="🎬 Clips Encontrados (primeiros 3)",
                value="\n\n".join(clips_text),
                inline=False
            )
            
            if len(filtered_clips) > 3:
                embed.add_field(name="➕ Mais Clips", value=f"E mais {len(filtered_clips) - 3} clips...", inline=False)
        
        # Informações de filtros aplicados
        if filter_config.min_views > 0 or filter_config.max_views < 9999:
            embed.add_field(name="🔍 Filtro Views", value=f"{filter_config.min_views} - {filter_config.max_views}", inline=True)
        
        if filter_config.min_duration > 0 or filter_config.max_duration < 300:
            embed.add_field(name="🔍 Filtro Duração", value=f"{filter_config.min_duration}s - {filter_config.max_duration}s", inline=True)
        
        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="toggle", description="Ativa/desativa monitoramento de um streamer")
    async def toggle_command(interaction: discord.Interaction, streamer: str):
        """Toggle streamer ativo/inativo"""
        server_id = interaction.guild.id
        
        if server_id not in server_streamers:
            embed = discord.Embed(
                title="❌ Nenhum Streamer",
                description="Não há streamers configurados neste servidor.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Buscar streamer
        username = parse_twitch_username(streamer)
        broadcaster_id = None
        streamer_config = None
        
        for bid, config in server_streamers[server_id].items():
            if config.username.lower() == username.lower():
                broadcaster_id = bid
                streamer_config = config
                break
        
        if not broadcaster_id:
            embed = discord.Embed(
                title="❌ Streamer não encontrado",
                description=f"O streamer **{username}** não está sendo monitorado neste servidor.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Toggle status
        streamer_config.enabled = not streamer_config.enabled
        save_cache()
        
        display_name = streamer_config.nickname or streamer_config.username
        status = "✅ Ativado" if streamer_config.enabled else "⏸️ Pausado"
        color = 0x00ff00 if streamer_config.enabled else 0xffaa00
        
        embed = discord.Embed(
            title=f"🔄 Status Alterado",
            description=f"Monitoramento de **{display_name}**: {status}",
            color=color
        )
        await interaction.response.send_message(embed=embed)
        log(f"Streamer {username} {'ativado' if streamer_config.enabled else 'pausado'} no servidor {server_id}")
