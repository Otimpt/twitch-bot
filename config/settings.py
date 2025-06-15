"""Configurações e variáveis do bot"""

import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# ==== TOKENS E CREDENCIAIS ====
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_SECRET = os.getenv("TWITCH_SECRET")

# ==== CONFIGURAÇÕES DO BOT ====
CLIP_CHECK_SECONDS = int(os.getenv("CLIP_CHECK_SECONDS", "60"))
CLIP_LOOKBACK_HOURS = float(os.getenv("CLIP_LOOKBACK_HOURS", "1.0"))
CLIP_SHOW_DETAILS = os.getenv("CLIP_SHOW_DETAILS", "true").lower() == "true"
CLIP_API_TIMEOUT = int(os.getenv("CLIP_API_TIMEOUT", "15"))
CLIP_ATTACH_VIDEO = os.getenv("CLIP_ATTACH_VIDEO", "false").lower() == "true"
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
MAX_CLIP_SIZE_MB = int(os.getenv("MAX_CLIP_SIZE_MB", "25"))

# ==== ARQUIVOS ====
CACHE_FILE = "twitch_bot_data.json"

# ==== ARMAZENAMENTO GLOBAL ====
# Dicionários para armazenar dados de todos os servidores
server_streamers = {}      # Dict[int, Dict[str, StreamerConfig]]
server_filters = {}        # Dict[int, FilterConfig]
server_themes = {}         # Dict[int, ThemeConfig]
server_templates = {}      # Dict[int, TemplateConfig]
server_stats = {}          # Dict[int, ServerStats]
posted_clips = {}          # Dict[int, Set[str]]
last_check_time = {}       # Dict[int, datetime]
live_streamers = {}        # Dict[str, bool]
