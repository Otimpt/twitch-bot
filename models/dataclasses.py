"""Classes de dados do bot"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class StreamerConfig:
    """Configuração de um streamer monitorado"""
    username: str
    broadcaster_id: str
    discord_channel: int
    enabled: bool = True
    nickname: str = ""
    live_notifications: bool = False
    live_channel: int = 0
    live_template: str = "simples"
    live_message: str = ""
    
    def __post_init__(self):
        """Validações após inicialização"""
        if not self.username:
            raise ValueError("Username não pode estar vazio")
        if not self.broadcaster_id:
            raise ValueError("Broadcaster ID não pode estar vazio")
        if self.discord_channel <= 0:
            raise ValueError("Canal Discord deve ser um ID válido")
    
    @property
    def display_name(self) -> str:
        """Retorna o nome de exibição (nickname ou username)"""
        return self.nickname or self.username
    
    def is_live_enabled(self) -> bool:
        """Verifica se notificações de live estão ativas"""
        return self.live_notifications and self.live_channel > 0

@dataclass
class FilterConfig:
    """Configuração de filtros para clips"""
    min_views: int = 0
    max_views: int = 9999
    min_duration: float = 0.0
    max_duration: float = 300.0
    keywords_include: List[str] = field(default_factory=list)
    keywords_exclude: List[str] = field(default_factory=list)
    creators_whitelist: List[str] = field(default_factory=list)
    creators_blacklist: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validações e inicializações após criação"""
        # Garantir que as listas não sejam None
        if self.keywords_include is None:
            self.keywords_include = []
        if self.keywords_exclude is None:
            self.keywords_exclude = []
        if self.creators_whitelist is None:
            self.creators_whitelist = []
        if self.creators_blacklist is None:
            self.creators_blacklist = []
        
        # Validações
        if self.min_views < 0:
            self.min_views = 0
        if self.max_views < self.min_views:
            self.max_views = self.min_views
        if self.min_duration < 0:
            self.min_duration = 0.0
        if self.max_duration < self.min_duration:
            self.max_duration = self.min_duration
    
    def has_view_filter(self) -> bool:
        """Verifica se há filtro de views ativo"""
        return self.min_views > 0 or self.max_views < 9999
    
    def has_duration_filter(self) -> bool:
        """Verifica se há filtro de duração ativo"""
        return self.min_duration > 0 or self.max_duration < 300
    
    def has_keyword_filter(self) -> bool:
        """Verifica se há filtro de palavras-chave ativo"""
        return len(self.keywords_include) > 0 or len(self.keywords_exclude) > 0
    
    def has_creator_filter(self) -> bool:
        """Verifica se há filtro de criadores ativo"""
        return len(self.creators_whitelist) > 0 or len(self.creators_blacklist) > 0
    
    def is_active(self) -> bool:
        """Verifica se algum filtro está ativo"""
        return (self.has_view_filter() or 
                self.has_duration_filter() or 
                self.has_keyword_filter() or 
                self.has_creator_filter())

@dataclass
class ThemeConfig:
    """Configuração de tema visual dos embeds"""
    color: int = 0x9146FF
    style: str = "padrao"
    show_thumbnail: bool = True
    show_details: bool = True
    custom_footer: str = ""
    custom_icon: str = ""
    
    def __post_init__(self):
        """Validações após inicialização"""
        # Validar cor (deve ser um valor hexadecimal válido)
        if not (0x000000 <= self.color <= 0xFFFFFF):
            self.color = 0x9146FF
        
        # Validar estilo
        valid_styles = ["padrao", "minimalista", "detalhado"]
        if self.style not in valid_styles:
            self.style = "padrao"
    
    @property
    def color_hex(self) -> str:
        """Retorna a cor em formato hexadecimal"""
        return f"#{self.color:06x}"
    
    def get_style_name(self) -> str:
        """Retorna o nome formatado do estilo"""
        style_names = {
            "padrao": "📊 Padrão",
            "minimalista": "⚡ Minimalista",
            "detalhado": "📋 Detalhado"
        }
        return style_names.get(self.style, "📊 Padrão")

@dataclass
class TemplateConfig:
    """Configuração de templates de mensagem"""
    message_format: str = ""
    embed_title: str = "{title}"
    embed_description: str = "Novo clip de **{streamer}**!"
    use_custom_message: bool = False
    ping_role: str = ""
    preset_name: str = "simples"
    
    def __post_init__(self):
        """Validações após inicialização"""
        # Garantir que os campos não estejam vazios
        if self.message_format is None:
            self.message_format = ""
        if not self.embed_title:
            self.embed_title = "{title}"
        if not self.embed_description:
            self.embed_description = "Novo clip de **{streamer}**!"
        
        # Validar preset_name
        valid_presets = ["simples", "detalhado", "gaming", "minimalista", "hype", "custom"]
        if self.preset_name not in valid_presets:
            self.preset_name = "simples"
    
    def is_custom(self) -> bool:
        """Verifica se é um template personalizado"""
        return self.preset_name == "custom"
    
    def get_preset_emoji(self) -> str:
        """Retorna o emoji do preset atual"""
        emoji_map = {
            "simples": "📝",
            "detalhado": "📊",
            "gaming": "🎮",
            "minimalista": "⚡",
            "hype": "🔥",
            "custom": "🛠️"
        }
        return emoji_map.get(self.preset_name, "📝")

@dataclass
class ServerStats:
    """Estatísticas de um servidor"""
    clips_sent_today: int = 0
    clips_sent_week: int = 0
    clips_sent_month: int = 0
    clips_sent_total: int = 0
    last_reset_day: str = ""
    last_reset_week: str = ""
    last_reset_month: str = ""
    top_streamers: Dict[str, int] = field(default_factory=dict)
    top_creators: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Inicializações após criação"""
        # Garantir que os dicionários não sejam None
        if self.top_streamers is None:
            self.top_streamers = {}
        if self.top_creators is None:
            self.top_creators = {}
        
        # Garantir que os contadores não sejam negativos
        self.clips_sent_today = max(0, self.clips_sent_today)
        self.clips_sent_week = max(0, self.clips_sent_week)
        self.clips_sent_month = max(0, self.clips_sent_month)
        self.clips_sent_total = max(0, self.clips_sent_total)
    
    def reset_daily_stats(self):
        """Reseta estatísticas diárias"""
        self.clips_sent_today = 0
        self.last_reset_day = datetime.now().strftime("%Y-%m-%d")
    
    def reset_weekly_stats(self):
        """Reseta estatísticas semanais"""
        self.clips_sent_week = 0
        self.last_reset_week = datetime.now().strftime("%Y-W%U")
    
    def reset_monthly_stats(self):
        """Reseta estatísticas mensais"""
        self.clips_sent_month = 0
        self.last_reset_month = datetime.now().strftime("%Y-%m")
    
    def add_clip(self, streamer_name: str, creator_name: str):
        """Adiciona um clip às estatísticas"""
        # Incrementar contadores
        self.clips_sent_today += 1
        self.clips_sent_week += 1
        self.clips_sent_month += 1
        self.clips_sent_total += 1
        
        # Atualizar tops
        self.top_streamers[streamer_name] = self.top_streamers.get(streamer_name, 0) + 1
        self.top_creators[creator_name] = self.top_creators.get(creator_name, 0) + 1
    
    def get_top_streamers(self, limit: int = 5) -> List[tuple]:
        """Retorna os top streamers ordenados"""
        return sorted(self.top_streamers.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def get_top_creators(self, limit: int = 5) -> List[tuple]:
        """Retorna os top criadores ordenados"""
        return sorted(self.top_creators.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def should_reset_daily(self) -> bool:
        """Verifica se deve resetar estatísticas diárias"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.last_reset_day != today
    
    def should_reset_weekly(self) -> bool:
        """Verifica se deve resetar estatísticas semanais"""
        week = datetime.now().strftime("%Y-W%U")
        return self.last_reset_week != week
    
    def should_reset_monthly(self) -> bool:
        """Verifica se deve resetar estatísticas mensais"""
        month = datetime.now().strftime("%Y-%m")
        return self.last_reset_month != month