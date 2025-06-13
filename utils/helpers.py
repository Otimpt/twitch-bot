"""Funções auxiliares e utilitários gerais"""

import discord
from datetime import datetime
from typing import Dict, Any

from config.settings import DEBUG_MODE
from config.templates import PRESET_TEMPLATES, TEMPLATE_COLORS
from models.dataclasses import StreamerConfig, ThemeConfig, TemplateConfig, ServerStats

def log(message: str, level: str = "INFO"):
    """Sistema de log simples"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{level} {timestamp}] {message}")

def debug_log(message: str):
    """Log apenas se debug estiver ativado"""
    if DEBUG_MODE:
        log(message, "DEBUG")

def format_template(template: str, clip: dict, streamer_name: str, **kwargs) -> str:
    """Formata template com dados do clip"""
    replacements = {
        "{title}": clip.get("title", "Clip sem título"),
        "{streamer}": streamer_name,
        "{creator}": clip.get("creator_name", "Desconhecido"),
        "{views}": str(clip.get("view_count", 0)),
        "{duration}": f"{clip.get('duration', 0):.1f}s",
        "{url}": clip.get("url", ""),
        **kwargs
    }
    
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, str(value))
    
    return result

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
    
    # Determinar qual template está sendo usado
    template_key = "simples"  # padrão
    for key, tmpl in PRESET_TEMPLATES["lives"].items():
        if tmpl["title"] == template["title"] and tmpl["description"] == template["description"]:
            template_key = key
            break
    
    # Obter cor do template
    color = TEMPLATE_COLORS["lives"].get(template_key, 0xff0000)
    
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

def create_clip_embed(clip: dict, streamer_config: StreamerConfig, theme: ThemeConfig, template: TemplateConfig) -> discord.Embed:
    """Cria embed personalizado do Discord para o clip"""
    display_name = streamer_config.display_name
    
    # Título personalizado
    title = format_template(template.embed_title, clip, display_name)
    
    # Descrição personalizada
    description = format_template(template.embed_description, clip, display_name)
    
    embed = discord.Embed(
        title=title,
        description=description if template.embed_description else None,
        url=clip.get("url"),
        color=theme.color,
        timestamp=datetime.fromisoformat(clip.get("created_at", "").replace("Z", "+00:00"))
    )

    # Campos baseados no estilo
    if theme.style == "minimalista":
        embed.add_field(name="📺", value=display_name, inline=True)
        if theme.show_details:
            embed.add_field(name="👀", value=str(clip.get("view_count", 0)), inline=True)
    
    elif theme.style == "detalhado":
        embed.add_field(name="📺 Canal", value=display_name, inline=True)
        embed.add_field(name="👤 Criador", value=clip.get("creator_name", "Desconhecido"), inline=True)
        embed.add_field(name="👀 Views", value=str(clip.get("view_count", 0)), inline=True)
        embed.add_field(name="⏱️ Duração", value=f"{clip.get('duration', 0):.1f}s", inline=True)
        embed.add_field(name="📅 Criado", value=f"<t:{int(datetime.fromisoformat(clip.get('created_at', '').replace('Z', '+00:00')).timestamp())}:R>", inline=True)
    
    else:  # padrão
        embed.add_field(name="📺 Canal", value=display_name, inline=True)
        if theme.show_details:
            embed.add_field(name="👀 Views", value=str(clip.get("view_count", 0)), inline=True)
            embed.add_field(name="👤 Criador", value=clip.get("creator_name", "Desconhecido"), inline=True)
            embed.add_field(name="⏱️ Duração", value=f"{clip.get('duration', 0):.1f}s", inline=True)

    # Thumbnail
    if theme.show_thumbnail and clip.get("thumbnail_url"):
        embed.set_image(url=clip["thumbnail_url"])

    # Footer personalizado
    footer_text = theme.custom_footer or "Twitch Clips Bot"
    footer_icon = theme.custom_icon or "https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-70x70.png"
    embed.set_footer(text=footer_text, icon_url=footer_icon)

    return embed

def update_stats(server_id: int, streamer_name: str, creator_name: str):
    """Atualiza estatísticas do servidor"""
    from config.settings import server_stats
    
    if server_id not in server_stats:
        server_stats[server_id] = ServerStats()
    
    stats = server_stats[server_id]
    
    # Verificar se precisa resetar estatísticas
    if stats.should_reset_daily():
        stats.reset_daily_stats()
    if stats.should_reset_weekly():
        stats.reset_weekly_stats()
    if stats.should_reset_monthly():
        stats.reset_monthly_stats()
    
    # Adicionar clip
    stats.add_clip(streamer_name, creator_name)

def clip_video_url(thumbnail_url: str) -> str:
    """Converte URL da thumbnail para URL do vídeo"""
    return thumbnail_url.split("-preview-", 1)[0] + ".mp4"

def format_duration(seconds: float) -> str:
    """Formata duração em formato legível"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m{secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h{minutes}m"

def format_number(number: int) -> str:
    """Formata números grandes de forma legível"""
    if number < 1000:
        return str(number)
    elif number < 1000000:
        return f"{number/1000:.1f}K"
    else:
        return f"{number/1000000:.1f}M"

def sanitize_filename(filename: str) -> str:
    """Remove caracteres inválidos de nomes de arquivo"""
    import re
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Trunca texto se exceder o limite"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def get_emoji_for_template(template_type: str, template_key: str) -> str:
    """Retorna emoji apropriado para um template"""
    from config.templates import TEMPLATE_EMOJIS
    return TEMPLATE_EMOJIS.get(template_type, {}).get(template_key, "📝")

def validate_discord_permissions(channel, required_permissions: list) -> tuple:
    """Valida se o bot tem as permissões necessárias no canal"""
    missing_permissions = []
    
    if not channel:
        return False, ["Canal não encontrado"]
    
    bot_permissions = channel.permissions_for(channel.guild.me)
    
    permission_map = {
        "send_messages": bot_permissions.send_messages,
        "embed_links": bot_permissions.embed_links,
        "attach_files": bot_permissions.attach_files,
        "read_message_history": bot_permissions.read_message_history,
        "use_external_emojis": bot_permissions.use_external_emojis
    }
    
    for perm in required_permissions:
        if perm in permission_map and not permission_map[perm]:
            missing_permissions.append(perm)
    
    return len(missing_permissions) == 0, missing_permissions