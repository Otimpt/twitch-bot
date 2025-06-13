"""Comandos de notificações de live"""

import discord
from discord.ext import commands
from datetime import datetime

from config.templates import PRESET_TEMPLATES
from config.settings import *
from models.dataclasses import *
from utils.cache import save_cache
from utils.twitch_api import parse_twitch_username

async def notification_commands(bot):
    """Registra comandos de notificações"""

    def format_live_template(template: dict, streamer_name: str, username: str) -> discord.Embed:
        """Formata template de live com estilos personalizados"""
        timestamp = int(datetime.now().timestamp())
        
        replacements = {
            "{streamer}": streamer_name,
            "{username}": username,
            "{timestamp}": str(timestamp)
        }
        
        title = template["title"]
        description = template["description"]
        
        # Aplicar substituições
        for placeholder, value in replacements.items():
            title = title.replace(placeholder, value)
            description = description.replace(placeholder, value)
        
        # Cores específicas por template
        template_colors = {
            "simples": 0xff0000,      # Vermelho padrão Twitch
            "detalhado": 0x9146FF,    # Roxo Twitch
            "gaming": 0x00ff41,       # Verde gaming
            "hype": 0xff6b35,         # Laranja vibrante
            "chill": 0x9d4edd        # Roxo suave
        }
        
        # Determinar qual template está sendo usado
        template_key = "simples"  # padrão
        for key, tmpl in PRESET_TEMPLATES["lives"].items():
            if tmpl["title"] == template["title"] and tmpl["description"] == template["description"]:
                template_key = key
                break
        
        color = template_colors.get(template_key, 0xff0000)
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            url=f"https://twitch.tv/{username}",
            timestamp=datetime.now()
        )
        
        # Configurações específicas por template
        if template_key == "simples":
            embed.set_thumbnail(url="https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-70x70.png")
            embed.set_footer(text="Twitch Live", icon_url="https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-70x70.png")
        
        elif template_key == "detalhado":
            embed.set_thumbnail(url="https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-70x70.png")
            embed.add_field(name="🎮 Plataforma", value="Twitch", inline=True)
            embed.add_field(name="⏰ Iniciado", value=f"<t:{timestamp}:R>", inline=True)
            embed.add_field(name="🔗 Link Direto", value=f"[Assistir agora](https://twitch.tv/{username})", inline=True)
            embed.set_footer(text="Clique no título para assistir!", icon_url="https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-70x70.png")
        
        elif template_key == "gaming":
            embed.set_thumbnail(url="https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-70x70.png")
            embed.add_field(name="🎯 Status", value="🔴 AO VIVO", inline=True)
            embed.add_field(name="🎮 Ação", value="Começou agora!", inline=True)
            embed.set_footer(text="Game On! 🎮", icon_url="https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-70x70.png")
        
        elif template_key == "hype":
            # Template mais chamativo
            embed.set_thumbnail(url="https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-70x70.png")
            embed.add_field(name="🚨 ALERTA", value="LIVE INICIADA!", inline=True)
            embed.add_field(name="🔥 HYPE", value="MÁXIMO!", inline=True)
            embed.add_field(name="⚡ ENERGIA", value="100%", inline=True)
            embed.set_footer(text="NÃO PERCA! 🚨🔥", icon_url="https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-70x70.png")
        
        elif template_key == "chill":
            embed.set_thumbnail(url="https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-70x70.png")
            embed.add_field(name="✨ Vibe", value="Relaxante", inline=True)
            embed.add_field(name="🌙 Mood", value="Chill", inline=True)
            embed.set_footer(text="Momento zen 🌙✨", icon_url="https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-70x70.png")
        
        return embed

    class LiveTemplateSelect(discord.ui.Select):
        def __init__(self, streamer_config: StreamerConfig, channel: discord.TextChannel, enable: bool):
            self.streamer_config = streamer_config
            self.channel = channel
            self.enable = enable
            
            options = []
            for key, template in PRESET_TEMPLATES["lives"].items():
                emoji_map = {
                    "simples": "🔴",
                    "detalhado": "📺", 
                    "gaming": "🎮",
                    "hype": "🚨",
                    "chill": "✨"
                }
                options.append(discord.SelectOption(
                    label=template["name"],
                    value=key,
                    description=template["description"],
                    emoji=emoji_map.get(key, "🔴")
                ))
            
            super().__init__(placeholder="Escolha um template para notificações de live...", options=options)
        
        async def callback(self, interaction: discord.Interaction):
            selected_template_key = self.values[0]
            selected_template = PRESET_TEMPLATES["lives"][selected_template_key]
            
            # Atualizar configuração do streamer
            self.streamer_config.live_notifications = self.enable
            self.streamer_config.live_channel = self.channel.id if self.enable else 0
            self.streamer_config.live_template = selected_template_key
            
            save_cache()
            
            display_name = self.streamer_config.nickname or self.streamer_config.username
            
            embed = discord.Embed(
                title="✅ Notificações Configuradas",
                description=f"Notificações de live para **{display_name}**",
                color=0x00ff00
            )
            
            embed.add_field(name="📺 Status", value="✅ Ativado", inline=True)
            embed.add_field(name="📍 Canal", value=self.channel.mention, inline=True)
            embed.add_field(name="🎨 Template", value=selected_template["name"], inline=True)
            
            # Mostrar preview do template com estilo correto
            preview_embed = format_live_template(selected_template, display_name, self.streamer_config.username)
            preview_embed.title = f"📋 Preview: {preview_embed.title}"
            
            # Manter a cor original do template no preview
            template_colors = {
                "simples": 0xff0000,
                "detalhado": 0x9146FF,
                "gaming": 0x00ff41,
                "hype": 0xff6b35,
                "chill": 0x9d4edd
            }
            preview_embed.color = template_colors.get(selected_template_key, 0xff0000)
            
            await interaction.response.edit_message(embed=embed, view=None)
            await interaction.followup.send(content="**🎨 Preview do template escolhido:**", embed=preview_embed)

    class LiveTemplateView(discord.ui.View):
        def __init__(self, streamer_config: StreamerConfig, channel: discord.TextChannel, enable: bool):
            super().__init__(timeout=60)
            self.add_item(LiveTemplateSelect(streamer_config, channel, enable))

    @bot.tree.command(name="live-notifications", description="Configura notificações de live para um streamer específico")
    async def notificacoes_command(
        interaction: discord.Interaction,
        streamer: str,
        ativar: bool = True,
        canal_notificacao: discord.TextChannel = None
    ):
        """Configura notificações de live para streamer específico"""
        server_id = interaction.guild.id
        
        if server_id not in server_streamers or not server_streamers[server_id]:
            embed = discord.Embed(
                title="❌ Nenhum Streamer",
                description="Use `/setup` para adicionar streamers primeiro.",
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
                description=f"O streamer **{username}** não está sendo monitorado neste servidor.\n\nUse `/list` para ver os streamers disponíveis.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Usar canal atual se não especificado
        if not canal_notificacao:
            canal_notificacao = interaction.channel
        
        if not ativar:
            # Desativar notificações
            streamer_config.live_notifications = False
            streamer_config.live_channel = 0
            save_cache()
            
            display_name = streamer_config.nickname or streamer_config.username
            embed = discord.Embed(
                title="✅ Notificações Desativadas",
                description=f"Notificações de live para **{display_name}** foram desativadas.",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Mostrar seletor de templates
        display_name = streamer_config.nickname or streamer_config.username
        embed = discord.Embed(
            title="🎨 Escolha um Template para Lives",
            description=f"Selecione como as notificações de **{display_name}** serão exibidas em {canal_notificacao.mention}:",
            color=0x9146FF
        )
        
        # Mostrar templates disponíveis
        template_list = []
        for key, template in PRESET_TEMPLATES["lives"].items():
            emoji = "🔴" if key == "simples" else "📺" if key == "detalhado" else "🎮" if key == "gaming" else "🚨" if key == "hype" else "✨"
            template_list.append(f"{emoji} **{template['name']}** - {template['description']}")
        
        embed.add_field(name="📋 Templates Disponíveis", value="\n".join(template_list), inline=False)
        
        view = LiveTemplateView(streamer_config, canal_notificacao, ativar)
        await interaction.response.send_message(embed=embed, view=view)