"""Comandos de estatísticas"""

import discord
from discord.ext import commands

from config.settings import *
from models.dataclasses import *

async def stats_commands(bot):
    """Registra comandos de estatísticas"""

    @bot.tree.command(name="stats", description="Mostra estatísticas detalhadas do servidor")
    async def stats_command(interaction: discord.Interaction):
        """Mostra estatísticas do servidor"""
        server_id = interaction.guild.id
        
        if server_id not in server_stats:
            embed = discord.Embed(
                title="📊 Sem Estatísticas",
                description="Ainda não há clips enviados neste servidor.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            return
        
        stats = server_stats[server_id]
        
        embed = discord.Embed(
            title="📊 Estatísticas do Servidor",
            description=f"Dados de clips enviados em **{interaction.guild.name}**",
            color=0x9146FF
        )
        
        # Estatísticas gerais
        embed.add_field(name="📅 Hoje", value=str(stats.clips_sent_today), inline=True)
        embed.add_field(name="📆 Esta Semana", value=str(stats.clips_sent_week), inline=True)
        embed.add_field(name="🗓️ Este Mês", value=str(stats.clips_sent_month), inline=True)
        embed.add_field(name="🎯 Total", value=str(stats.clips_sent_total), inline=True)
        
        # Top streamers
        if stats.top_streamers:
            top_streamers = sorted(stats.top_streamers.items(), key=lambda x: x[1], reverse=True)[:5]
            streamers_text = "\n".join([f"{i+1}. **{name}**: {count} clips" for i, (name, count) in enumerate(top_streamers)])
            embed.add_field(name="🏆 Top Streamers", value=streamers_text, inline=False)
        
        # Top criadores
        if stats.top_creators:
            top_creators = sorted(stats.top_creators.items(), key=lambda x: x[1], reverse=True)[:5]
            creators_text = "\n".join([f"{i+1}. **{name}**: {count} clips" for i, (name, count) in enumerate(top_creators)])
            embed.add_field(name="👑 Top Criadores", value=creators_text, inline=False)
        
        # Informações do sistema
        total_streamers = len(server_streamers.get(server_id, {}))
        active_streamers = sum(1 for config in server_streamers.get(server_id, {}).values() if config.enabled)
        
        embed.add_field(
            name="⚙️ Configuração",
            value=f"📺 Streamers: {active_streamers}/{total_streamers}\n🔄 Verificação: {CLIP_CHECK_SECONDS}s\n📅 Período: {CLIP_LOOKBACK_HOURS}h",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)