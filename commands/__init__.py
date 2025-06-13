"""Módulo de comandos do bot"""

from .setup import setup_commands
from .templates import template_commands
from .notifications import notification_commands
from .themes import theme_commands
from .filters import filter_commands
from .stats import stats_commands
from .management import management_commands

__all__ = [
    'setup_commands',
    'template_commands', 
    'notification_commands',
    'theme_commands',
    'filter_commands',
    'stats_commands',
    'management_commands'
]