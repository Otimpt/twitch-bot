"""Comandos de temas visuais"""

import discord
from discord.ext import commands

from config.settings import *
from models.dataclasses import *
from utils.cache import save_cache
from utils.helpers import is_admin_or_mod

async def theme_commands(bot):
    """Registra comandos de temas"""

    class ThemeStyleSelect(discord.ui.Select):
        def __init__(self):
            options = [
                discord.SelectOption(
                    label="Padrão",
                    value="padrao",
                    description="Estilo equilibrado com informações essenciais",
                    emoji="📊"
                ),
                discord.SelectOption(
                    label="Minimalista",
                    value="minimalista",
                    description="Apenas as informações básicas",
                    emoji="⚡"
                ),
                discord.SelectOption(
                    label="Detalhado",
                    value="detalhado",
                    description="Todas as informações disponíveis",
                    emoji="📋"
                )
            ]
            
            super().__init__(placeholder="Escolha um estilo de tema...", options=options)
        
        async def callback(self, interaction: discord.Interaction):
            server_id = interaction.guild.id
            
            if server_id not in server_themes:
                server_themes[server_id] = ThemeConfig()
            
            server_themes[server_id].style = self.values[0]
            save_cache()
            
            style_names = {
                "padrao": "Padrão",
                "minimalista": "Minimalista", 
                "detalhado": "Detalhado"
            }
            
            embed = discord.Embed(
                title="✅ Tema Configurado",
                description=f"Estilo **{style_names[self.values[0]]}** aplicado com sucesso!",
                color=0x00ff00
            )
            
            await interaction.response.edit_message(embed=embed, view=None)

    class ThemeColorSelect(discord.ui.Select):
        def __init__(self):
            options = [
                discord.SelectOption(
                    label="Roxo Twitch",
                    value="0x9146FF",
                    description="Cor oficial da Twitch",
                    emoji="💜"
                ),
                discord.SelectOption(
                    label="Azul",
                    value="0x0099ff",
                    description="Azul clássico",
                    emoji="💙"
                ),
                discord.SelectOption(
                    label="Verde",
                    value="0x00ff00",
                    description="Verde vibrante",
                    emoji="💚"
                ),
                discord.SelectOption(
                    label="Vermelho",
                    value="0xff0000",
                    description="Vermelho intenso",
                    emoji="❤️"
                ),
                discord.SelectOption(
                    label="Dourado",
                    value="0xffd700",
                    description="Dourado elegante",
                    emoji="💛"
                )
            ]
            
            super().__init__(placeholder="Escolha uma cor...", options=options)
        
        async def callback(self, interaction: discord.Interaction):
            server_id = interaction.guild.id
            
            if server_id not in server_themes:
                server_themes[server_id] = ThemeConfig()
            
            server_themes[server_id].color = int(self.values[0], 16)
            save_cache()
            
            color_names = {
                "0x9146FF": "Roxo Twitch",
                "0x0099ff": "Azul",
                "0x00ff00": "Verde", 
                "0xff0000": "Vermelho",
                "0xffd700": "Dourado"
            }
            
            embed = discord.Embed(
                title="✅ Cor Configurada",
                description=f"Cor **{color_names[self.values[0]]}** aplicada com sucesso!",
                color=int(self.values[0], 16)
            )
            
            await interaction.response.edit_message(embed=embed, view=None)

    class ThemeConfigView(discord.ui.View):
        def __init__(self, config_type: str):
            super().__init__(timeout=60)
            if config_type == "style":
                self.add_item(ThemeStyleSelect())
            elif config_type == "color":
                self.add_item(ThemeColorSelect())

    @bot.tree.command(name="tema", description="Configura aparência dos embeds com seletor visual")
    @is_admin_or_mod()
    async def tema_command(
        interaction: discord.Interaction,
        configurar: str = "style"  # style, color, thumbnail, details
    ):
        """Configura tema visual dos embeds"""
        server_id = interaction.guild.id
        
        if server_id not in server_themes:
            server_themes[server_id] = ThemeConfig()
        
        current_theme = server_themes[server_id]
        
        if configurar == "style":
            embed = discord.Embed(
                title="🎨 Configurar Estilo do Tema",
                description="Escolha como as informações dos clips serão exibidas:",
                color=current_theme.color
            )
            
            embed.add_field(
                name="📊 Padrão",
                value="Mostra canal, views, criador e duração",
                inline=False
            )
            embed.add_field(
                name="⚡ Minimalista", 
                value="Apenas canal e views (se habilitado)",
                inline=False
            )
            embed.add_field(
                name="📋 Detalhado",
                value="Todas as informações disponíveis + timestamp",
                inline=False
            )
            
            view = ThemeConfigView("style")
            await interaction.response.send_message(embed=embed, view=view)
            
        elif configurar == "color":
            embed = discord.Embed(
                title="🌈 Configurar Cor do Tema",
                description="Escolha a cor dos embeds:",
                color=current_theme.color
            )
            
            embed.add_field(
                name="🎨 Cores Disponíveis",
                value="💜 Roxo Twitch (padrão)\n💙 Azul clássico\n💚 Verde vibrante\n❤️ Vermelho intenso\n💛 Dourado elegante",
                inline=False
            )
            
            view = ThemeConfigView("color")
            await interaction.response.send_message(embed=embed, view=view)
            
        elif configurar == "thumbnail":
            current_theme.show_thumbnail = not current_theme.show_thumbnail
            save_cache()
            
            status = "✅ Ativado" if current_theme.show_thumbnail else "❌ Desativado"
            embed = discord.Embed(
                title="🖼️ Thumbnail Configurado",
                description=f"Exibição de thumbnails: **{status}**",
                color=current_theme.color
            )
            await interaction.response.send_message(embed=embed)
            
        elif configurar == "details":
            current_theme.show_details = not current_theme.show_details
            save_cache()
            
            status = "✅ Ativado" if current_theme.show_details else "❌ Desativado"
            embed = discord.Embed(
                title="📊 Detalhes Configurado",
                description=f"Exibição de detalhes: **{status}**",
                color=current_theme.color
            )
            await interaction.response.send_message(embed=embed)
            
        else:
            # Mostrar configuração atual
            embed = discord.Embed(
                title="🎨 Configuração Atual do Tema",
                color=current_theme.color
            )
            
            style_names = {
                "padrao": "📊 Padrão",
                "minimalista": "⚡ Minimalista",
                "detalhado": "📋 Detalhado"
            }
            
            embed.add_field(name="🎨 Estilo", value=style_names.get(current_theme.style, "📊 Padrão"), inline=True)
            embed.add_field(name="🌈 Cor", value=f"#{current_theme.color:06x}", inline=True)
            embed.add_field(name="🖼️ Thumbnail", value="✅ Sim" if current_theme.show_thumbnail else "❌ Não", inline=True)
            embed.add_field(name="📊 Detalhes", value="✅ Sim" if current_theme.show_details else "❌ Não", inline=True)
            
            embed.add_field(
                name="⚙️ Comandos Disponíveis",
                value="`/tema configurar:style` - Alterar estilo\n`/tema configurar:color` - Alterar cor\n`/tema configurar:thumbnail` - Toggle thumbnail\n`/tema configurar:details` - Toggle detalhes",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)