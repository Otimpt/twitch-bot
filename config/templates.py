"""Templates pré-prontos para clips e lives"""

PRESET_TEMPLATES = {
    "clips": {
        "simples": {
            "message_format": "{url}",
            "embed_title": "{title}",
            "embed_description": "Novo clip de **{streamer}**!",
            "name": "Simples",
            "description": "Template básico e limpo"
        },
        "detalhado": {
            "message_format": "🎬 **Novo Clip!** {url}",
            "embed_title": "🎯 {title}",
            "embed_description": "**{streamer}** fez um clip épico!\n👤 Criado por: {creator}\n👀 Views: {views}\n⏱️ Duração: {duration}",
            "name": "Detalhado",
            "description": "Com todas as informações do clip"
        },
        "gaming": {
            "message_format": "🎮 CLIP ÉPICO! {url}",
            "embed_title": "⚡ {title}",
            "embed_description": "**{streamer}** mandou bem! 🔥\nClip criado por {creator}",
            "name": "Gaming",
            "description": "Focado em jogos com emojis"
        },
        "minimalista": {
            "message_format": "{url}",
            "embed_title": "{title}",
            "embed_description": "{streamer}",
            "name": "Minimalista",
            "description": "Apenas o essencial"
        },
        "hype": {
            "message_format": "🚨 **CLIP INSANO!** 🚨 {url}",
            "embed_title": "🔥 {title} 🔥",
            "embed_description": "**{streamer}** está ON FIRE! 🎯\n\n👤 **Criador:** {creator}\n👀 **Views:** {views}\n⏱️ **Duração:** {duration}",
            "name": "Hype",
            "description": "Muito animado e cheio de energia"
        }
    },
    "lives": {
        "simples": {
            "embed_title": "🔴 {streamer} está ao vivo!",
            "embed_description": "**{streamer}** começou a transmitir na Twitch!\n\n🔗 [Assistir agora](https://twitch.tv/{username})",
            "name": "Simples",
            "description": "Notificação básica de live",
            "style": "clean"
        },
        "detalhado": {
            "embed_title": "📺 LIVE INICIADA - {streamer}",
            "embed_description": "🎮 **{streamer}** está ao vivo na Twitch!\n\n📊 **Detalhes da Live:**\n🔗 **Link:** https://twitch.tv/{username}\n⏰ **Iniciada:** <t:{timestamp}:R>\n🎯 **Status:** 🔴 AO VIVO",
            "name": "Detalhado",
            "description": "Com informações completas da live",
            "style": "detailed"
        },
        "gaming": {
            "embed_title": "🎮 {streamer} entrou no jogo!",
            "embed_description": "🔥 **{streamer}** está online e pronto para a ação!\n\n🎯 **A diversão começou!**\n🎮 Venha assistir: https://twitch.tv/{username}\n⚡ Não perca a gameplay!",
            "name": "Gaming",
            "description": "Focado em jogos e ação",
            "style": "gaming"
        },
        "hype": {
            "embed_title": "🚨 {streamer} ESTÁ AO VIVO! 🚨",
            "embed_description": "🔥🔥🔥 **{streamer}** COMEÇOU A LIVE! 🔥🔥🔥\n\n🚨 **ALERTA MÁXIMO!** 🚨\n🎯 **NÃO PERCA:** https://twitch.tv/{username}\n⚡ **CORRE LÁ AGORA!**\n🔥 **HYPE TOTAL!**",
            "name": "Hype",
            "description": "Muito animado e chamativo",
            "style": "hype"
        },
        "chill": {
            "embed_title": "✨ {streamer} está transmitindo",
            "embed_description": "💜 **{streamer}** está ao vivo para uma sessão relaxante\n\n🌙 **Vibe tranquila**\n✨ Venha relaxar: https://twitch.tv/{username}\n🎵 Momento zen começou...",
            "name": "Chill",
            "description": "Relaxante e tranquilo",
            "style": "chill"
        }
    }
}

# ==== CONFIGURAÇÕES DE CORES POR TEMPLATE ====
TEMPLATE_COLORS = {
    "clips": {
        "simples": 0x9146FF,      # Roxo Twitch padrão
        "detalhado": 0x0099ff,    # Azul informativo
        "gaming": 0x00ff41,       # Verde gaming
        "minimalista": 0x666666,  # Cinza minimalista
        "hype": 0xff6b35         # Laranja vibrante
    },
    "lives": {
        "simples": 0xff0000,      # Vermelho padrão Twitch
        "detalhado": 0x9146FF,    # Roxo Twitch
        "gaming": 0x00ff41,       # Verde gaming
        "hype": 0xff6b35,         # Laranja vibrante
        "chill": 0x9d4edd        # Roxo suave
    }
}

# ==== EMOJIS POR TEMPLATE ====
TEMPLATE_EMOJIS = {
    "clips": {
        "simples": "📝",
        "detalhado": "📊",
        "gaming": "🎮",
        "minimalista": "⚡",
        "hype": "🔥"
    },
    "lives": {
        "simples": "🔴",
        "detalhado": "📺",
        "gaming": "🎮",
        "hype": "🚨",
        "chill": "✨"
    }
}

# ==== VARIÁVEIS DISPONÍVEIS PARA TEMPLATES ====
TEMPLATE_VARIABLES = {
    "clips": [
        "{title}",      # Título do clip
        "{streamer}",   # Nome do streamer
        "{creator}",    # Criador do clip
        "{views}",      # Número de views
        "{duration}",   # Duração do clip
        "{url}"         # URL do clip
    ],
    "lives": [
        "{streamer}",   # Nome do streamer
        "{username}",   # Username da Twitch
        "{timestamp}"   # Timestamp da live
    ]
}

# ==== CONFIGURAÇÕES DE FILTROS PADRÃO ====
DEFAULT_FILTER_CONFIG = {
    "min_views": 0,
    "max_views": 9999,
    "min_duration": 0.0,
    "max_duration": 300.0,
    "keywords_include": [],
    "keywords_exclude": [],
    "creators_whitelist": [],
    "creators_blacklist": []
}

# ==== CONFIGURAÇÕES DE TEMA PADRÃO ====
DEFAULT_THEME_CONFIG = {
    "color": 0x9146FF,
    "style": "padrao",
    "show_thumbnail": True,
    "show_details": True,
    "custom_footer": "",
    "custom_icon": ""
}

# ==== CONFIGURAÇÕES DE TEMPLATE PADRÃO ====
DEFAULT_TEMPLATE_CONFIG = {
    "message_format": "{url}",
    "embed_title": "{title}",
    "embed_description": "Novo clip de **{streamer}**!",
    "use_custom_message": False,
    "ping_role": "",
    "preset_name": "simples"
}
