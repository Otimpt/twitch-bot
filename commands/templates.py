"""Comandos de templates visuais"""

import discord
from discord.ext import commands

from config.templates import PRESET_TEMPLATES
from config.settings import *
from models.dataclasses import *
from utils.cache import save_cache

async def template_commands(bot):
    """Registra comandos de templates"""

    class ClipTemplateSelect(discord.ui.Select):
        def __init__(self):
            options = []
            for key, template in PRESET_TEMPLATES["clips"].items():
                emoji = "📝" if key == "simples" else "📊" if key == "detalhado" else "🎮" if key == "gaming" else "⚡" if key == "minimalista" else "🔥"
                options.append(discord.SelectOption(
                    label=template["name"],
                    value=key,
                    description=template["description"],
                    emoji=emoji
                ))
            
            super().__init__(placeholder="Escolha um template para clips...", options=options)
        
        async def callback(self, interaction: discord.Interaction):
            server_id = interaction.guild.id
            selected_template = PRESET_TEMPLATES["clips"][self.values[0]]
            
            # Aplicar template de clips
            if server_id not in server_templates:
                server_templates[server_id] = TemplateConfig()
            
            template_config = server_templates[server_id]
            template_config.message_format = selected_template["message_format"]
            template_config.embed_title = selected_template["embed_title"]
            template_config.embed_description = selected_template["embed_description"]
            template_config.preset_name = self.values[0]

            # Aplicar estilo associado ao template
            template_style = selected_template.get("style")
            if template_style:
                if server_id not in server_themes:
                    server_themes[server_id] = ThemeConfig()
                server_themes[server_id].style = template_style

            save_cache()

            embed = discord.Embed(
                title="✅ Template de Clips Aplicado",
                description=f"Template **{selected_template['name']}** configurado com sucesso!",
                color=0x00ff00
            )
            embed.add_field(name="💬 Mensagem", value=f"`{selected_template['message_format']}`", inline=False)
            embed.add_field(name="📝 Título", value=f"`{selected_template['embed_title']}`", inline=False)
            embed.add_field(name="📄 Descrição", value=f"`{selected_template['embed_description']}`", inline=False)
            if template_style:
                style_names = {"padrao": "Padrão", "minimalista": "Minimalista", "detalhado": "Detalhado"}
                embed.add_field(
                    name="🎨 Estilo",
                    value=style_names.get(template_style, template_style),
                    inline=False,
                )
            
            await interaction.response.edit_message(embed=embed, view=None)

    class ClipTemplateView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.add_item(ClipTemplateSelect())

    @bot.tree.command(name="clips-template", description="Configura templates de mensagem com seletor visual")
    async def template_command(
        interaction: discord.Interaction,
        tipo: str = "clips",
        mensagem_custom: str = "",
        titulo_custom: str = "",
        descricao_custom: str = "",
    ):
        """Configura templates com seletor visual"""
        server_id = interaction.guild.id
        
        if tipo not in ["clips", "custom"]:
            tipo = "clips"
        
        if tipo == "custom" and (mensagem_custom or titulo_custom or descricao_custom):
            # Template personalizado
            if server_id not in server_templates:
                server_templates[server_id] = TemplateConfig()
            
            template_config = server_templates[server_id]
            
            if mensagem_custom:
                template_config.message_format = mensagem_custom
            if titulo_custom:
                template_config.embed_title = titulo_custom
            if descricao_custom:
                template_config.embed_description = descricao_custom
            
            template_config.preset_name = "custom"
            save_cache()
            
            embed = discord.Embed(
                title="✅ Template Personalizado Configurado",
                description="Seu template personalizado foi salvo!",
                color=0x00ff00
            )
            embed.add_field(name="💬 Mensagem", value=f"`{template_config.message_format}`", inline=False)
            embed.add_field(name="📝 Título", value=f"`{template_config.embed_title}`", inline=False)
            embed.add_field(name="📄 Descrição", value=f"`{template_config.embed_description}`", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        else:
            # Mostrar seletor de templates
            embed = discord.Embed(
                title="🎨 Escolha um Template para Clips",
                description="Selecione um template pré-pronto para personalizar como os clips são exibidos:",
                color=0x9146FF
            )
            
            # Mostrar templates disponíveis com descrições
            template_list = []
            for key, template in PRESET_TEMPLATES["clips"].items():
                emoji = "📝" if key == "simples" else "📊" if key == "detalhado" else "🎮" if key == "gaming" else "⚡" if key == "minimalista" else "🔥"
                template_list.append(f"{emoji} **{template['name']}** - {template['description']}")
            
            embed.add_field(name="📋 Templates Disponíveis", value="\n".join(template_list), inline=False)
            embed.add_field(
                name="🔧 Variáveis disponíveis",
                value="`{title}` `{streamer}` `{creator}` `{views}` `{duration}` `{url}`",
                inline=False
            )
            embed.add_field(
                name="💡 Dica",
                value="Para template personalizado use: `/template tipo:custom mensagem_custom:\"sua mensagem\"`",
                inline=False
            )
            
            view = ClipTemplateView()
            await interaction.response.send_message(embed=embed, view=view)
