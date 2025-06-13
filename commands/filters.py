"""Comandos de filtros"""

import discord
from discord.ext import commands

from config.settings import *
from models.dataclasses import *
from utils.cache import save_cache

async def filter_commands(bot):
    """Registra comandos de filtros"""

    @bot.tree.command(name="filtros", description="Configura filtros de clips com interface visual")
    async def filtros_command(
        interaction: discord.Interaction,
        acao: str = "ver",  # ver, views, duracao, palavras, criadores
        valor: str = ""
    ):
        """Configura filtros de clips"""
        server_id = interaction.guild.id
        
        if server_id not in server_filters:
            server_filters[server_id] = FilterConfig()
        
        filter_config = server_filters[server_id]
        
        if acao == "ver":
            # Mostrar configuração atual
            embed = discord.Embed(
                title="🔍 Filtros Configurados",
                description="Configuração atual dos filtros de clips:",
                color=0x9146FF
            )
            
            embed.add_field(
                name="👀 Views",
                value=f"Mín: {filter_config.min_views} | Máx: {filter_config.max_views}",
                inline=True
            )
            embed.add_field(
                name="⏱️ Duração",
                value=f"Mín: {filter_config.min_duration}s | Máx: {filter_config.max_duration}s",
                inline=True
            )
            embed.add_field(name="📝 Status", value="✅ Ativo", inline=True)
            
            if filter_config.keywords_include:
                embed.add_field(
                    name="✅ Palavras Obrigatórias",
                    value=", ".join(filter_config.keywords_include),
                    inline=False
                )
            
            if filter_config.keywords_exclude:
                embed.add_field(
                    name="❌ Palavras Proibidas", 
                    value=", ".join(filter_config.keywords_exclude),
                    inline=False
                )
            
            if filter_config.creators_whitelist:
                embed.add_field(
                    name="👤 Criadores Permitidos",
                    value=", ".join(filter_config.creators_whitelist),
                    inline=False
                )
            
            if filter_config.creators_blacklist:
                embed.add_field(
                    name="🚫 Criadores Bloqueados",
                    value=", ".join(filter_config.creators_blacklist),
                    inline=False
                )
            
            embed.add_field(
                name="⚙️ Comandos Disponíveis",
                value="`/filtros acao:views valor:\"10-1000\"` - Filtro de views\n`/filtros acao:duracao valor:\"5-60\"` - Filtro de duração\n`/filtros acao:palavras valor:\"palavra1,palavra2\"` - Palavras obrigatórias\n`/filtros acao:criadores valor:\"user1,user2\"` - Criadores permitidos",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
        elif acao == "views" and valor:
            try:
                if "-" in valor:
                    min_val, max_val = valor.split("-", 1)
                    filter_config.min_views = int(min_val.strip())
                    filter_config.max_views = int(max_val.strip())
                else:
                    filter_config.min_views = int(valor)
                
                save_cache()
                
                embed = discord.Embed(
                    title="✅ Filtro de Views Configurado",
                    description=f"Views: {filter_config.min_views} - {filter_config.max_views}",
                    color=0x00ff00
                )
                await interaction.response.send_message(embed=embed)
                
            except ValueError:
                embed = discord.Embed(
                    title="❌ Formato Inválido",
                    description="Use: `10-1000` ou apenas `10` para mínimo",
                    color=0xff0000
                )
                await interaction.response.send_message(embed=embed)
        
        elif acao == "duracao" and valor:
            try:
                if "-" in valor:
                    min_val, max_val = valor.split("-", 1)
                    filter_config.min_duration = float(min_val.strip())
                    filter_config.max_duration = float(max_val.strip())
                else:
                    filter_config.min_duration = float(valor)
                
                save_cache()
                
                embed = discord.Embed(
                    title="✅ Filtro de Duração Configurado",
                    description=f"Duração: {filter_config.min_duration}s - {filter_config.max_duration}s",
                    color=0x00ff00
                )
                await interaction.response.send_message(embed=embed)
                
            except ValueError:
                embed = discord.Embed(
                    title="❌ Formato Inválido",
                    description="Use: `5.0-60.0` ou apenas `5.0` para mínimo",
                    color=0xff0000
                )
                await interaction.response.send_message(embed=embed)
        
        elif acao == "palavras" and valor:
            keywords = [k.strip() for k in valor.split(",") if k.strip()]
            filter_config.keywords_include = keywords
            save_cache()
            
            embed = discord.Embed(
                title="✅ Palavras Obrigatórias Configuradas",
                description=f"Palavras: {', '.join(keywords)}",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed)
        
        elif acao == "criadores" and valor:
            creators = [c.strip() for c in valor.split(",") if c.strip()]
            filter_config.creators_whitelist = creators
            save_cache()
            
            embed = discord.Embed(
                title="✅ Criadores Permitidos Configurados",
                description=f"Criadores: {', '.join(creators)}",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed)
        
        else:
            embed = discord.Embed(
                title="🔍 Como Usar Filtros",
                description="Configure filtros para personalizar quais clips são enviados:",
                color=0x9146FF
            )
            
            embed.add_field(
                name="👀 Filtro de Views",
                value="`/filtros acao:views valor:\"10-1000\"`\nApenas clips com 10-1000 views",
                inline=False
            )
            embed.add_field(
                name="⏱️ Filtro de Duração",
                value="`/filtros acao:duracao valor:\"5-60\"`\nApenas clips de 5-60 segundos",
                inline=False
            )
            embed.add_field(
                name="📝 Palavras Obrigatórias",
                value="`/filtros acao:palavras valor:\"epic,win,clutch\"`\nApenas clips com essas palavras no título",
                inline=False
            )
            embed.add_field(
                name="👤 Criadores Permitidos",
                value="`/filtros acao:criadores valor:\"user1,user2\"`\nApenas clips desses criadores",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)