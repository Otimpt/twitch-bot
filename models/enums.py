"""Enumerações utilizadas no bot"""

from enum import Enum, auto

class TemplateType(Enum):
    """Tipos de template disponíveis"""
    CLIPS = "clips"
    LIVES = "lives"

class ThemeStyle(Enum):
    """Estilos de tema disponíveis"""
    PADRAO = "padrao"
    MINIMALISTA = "minimalista"
    DETALHADO = "detalhado"

class FilterType(Enum):
    """Tipos de filtro disponíveis"""
    VIEWS = "views"
    DURATION = "duracao"
    KEYWORDS_INCLUDE = "palavras"
    KEYWORDS_EXCLUDE = "palavras_excluir"
    CREATORS_WHITELIST = "criadores"
    CREATORS_BLACKLIST = "criadores_bloquear"

class LogLevel(Enum):
    """Níveis de log"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ClipPreset(Enum):
    """Presets de templates para clips"""
    SIMPLES = "simples"
    DETALHADO = "detalhado"
    GAMING = "gaming"
    MINIMALISTA = "minimalista"
    HYPE = "hype"
    CUSTOM = "custom"

class LivePreset(Enum):
    """Presets de templates para lives"""
    SIMPLES = "simples"
    DETALHADO = "detalhado"
    GAMING = "gaming"
    HYPE = "hype"
    CHILL = "chill"

class NotificationType(Enum):
    """Tipos de notificação"""
    CLIP = auto()
    LIVE_START = auto()
    LIVE_END = auto()
    ERROR = auto()
    SUCCESS = auto()