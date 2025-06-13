"""Constantes e configurações fixas do bot"""

# ==== URLs E ENDPOINTS ====
TWITCH_API_BASE = "https://api.twitch.tv/helix"
TWITCH_OAUTH_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_CLIPS_ENDPOINT = f"{TWITCH_API_BASE}/clips"
TWITCH_USERS_ENDPOINT = f"{TWITCH_API_BASE}/users"
TWITCH_STREAMS_ENDPOINT = f"{TWITCH_API_BASE}/streams"

# ==== LIMITES E TIMEOUTS ====
MAX_CLIPS_PER_REQUEST = 100
MAX_STREAMERS_PER_SERVER = 50
MAX_TEMPLATE_LENGTH = 2000
MAX_EMBED_TITLE_LENGTH = 256
MAX_EMBED_DESCRIPTION_LENGTH = 4096
MAX_EMBED_FIELD_VALUE_LENGTH = 1024

# ==== INTERVALOS DE VERIFICAÇÃO ====
MIN_CLIP_CHECK_SECONDS = 30
MAX_CLIP_CHECK_SECONDS = 3600
MIN_LIVE_CHECK_SECONDS = 60
MAX_LIVE_CHECK_SECONDS = 1800

# ==== CONFIGURAÇÕES DE CACHE ====
CACHE_CLEANUP_DAYS = 30
MAX_POSTED_CLIPS_PER_SERVER = 10000

# ==== MENSAGENS DE ERRO PADRÃO ====
ERROR_MESSAGES = {
    "no_token": "❌ Não foi possível obter token da Twitch",
    "streamer_not_found": "❌ Streamer não encontrado na Twitch",
    "channel_not_found": "❌ Canal Discord não encontrado",
    "no_permission": "❌ Sem permissão para enviar mensagens neste canal",
    "api_error": "❌ Erro na API da Twitch",
    "invalid_format": "❌ Formato inválido",
    "server_error": "❌ Erro interno do servidor"
}

# ==== MENSAGENS DE SUCESSO PADRÃO ====
SUCCESS_MESSAGES = {
    "streamer_added": "✅ Streamer adicionado com sucesso",
    "streamer_removed": "✅ Streamer removido com sucesso",
    "template_applied": "✅ Template aplicado com sucesso",
    "notifications_enabled": "✅ Notificações ativadas",
    "notifications_disabled": "✅ Notificações desativadas",
    "filters_updated": "✅ Filtros atualizados",
    "theme_updated": "✅ Tema atualizado"
}

# ==== ÍCONES E IMAGENS PADRÃO ====
DEFAULT_TWITCH_ICON = "https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-70x70.png"
DEFAULT_TWITCH_LOGO = "https://brand.twitch.tv/assets/logos/svg/glitch/purple.svg"

# ==== REGEX PATTERNS ====
TWITCH_USERNAME_PATTERN = r"^[a-zA-Z0-9_]{4,25}$"
TWITCH_URL_PATTERN = r"(?:https?://)?(?:www\.)?twitch\.tv/([a-zA-Z0-9_]{4,25})"

# ==== CONFIGURAÇÕES DE LOG ====
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LOG_FORMAT = "[{level} {timestamp}] {message}"