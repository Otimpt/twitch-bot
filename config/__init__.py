"""Módulo de configurações do bot"""

from .settings import *
from .templates import PRESET_TEMPLATES

__all__ = [
    'DISCORD_TOKEN',
    'TWITCH_CLIENT_ID', 
    'TWITCH_SECRET',
    'CLIP_CHECK_SECONDS',
    'CLIP_LOOKBACK_HOURS',
    'CLIP_SHOW_DETAILS',
    'CLIP_API_TIMEOUT',
    'CLIP_ATTACH_VIDEO',
    'DEBUG_MODE',
    'MAX_CLIP_SIZE_MB',
    'CACHE_FILE',
    'PRESET_TEMPLATES',
    'server_streamers',
    'server_filters',
    'server_themes',
    'server_templates',
    'server_stats',
    'posted_clips',
    'last_check_time',
    'live_streamers'
]