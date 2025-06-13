"""Sistema de filtros para clips"""

from models.dataclasses import FilterConfig
from utils.helpers import debug_log

def apply_filters(clip: dict, filter_config: FilterConfig) -> bool:
    """Aplica filtros ao clip"""
    # Filtro de views
    views = clip.get("view_count", 0)
    if views < filter_config.min_views or views > filter_config.max_views:
        debug_log(f"Clip filtrado por views: {views} (min: {filter_config.min_views}, max: {filter_config.max_views})")
        return False
    
    # Filtro de duração
    duration = clip.get("duration", 0.0)
    if duration < filter_config.min_duration or duration > filter_config.max_duration:
        debug_log(f"Clip filtrado por duração: {duration}s (min: {filter_config.min_duration}s, max: {filter_config.max_duration}s)")
        return False
    
    title = clip.get("title", "").lower()
    creator = clip.get("creator_name", "").lower()
    
    # Filtro de palavras-chave obrigatórias
    if filter_config.keywords_include:
        if not any(keyword.lower() in title for keyword in filter_config.keywords_include):
            debug_log(f"Clip filtrado por palavras obrigatórias: '{title}' não contém {filter_config.keywords_include}")
            return False
    
    # Filtro de palavras-chave proibidas
    if filter_config.keywords_exclude:
        if any(keyword.lower() in title for keyword in filter_config.keywords_exclude):
            debug_log(f"Clip filtrado por palavras proibidas: '{title}' contém palavra proibida")
            return False
    
    # Filtro de criadores permitidos
    if filter_config.creators_whitelist:
        if not any(creator_name.lower() == creator for creator_name in filter_config.creators_whitelist):
            debug_log(f"Clip filtrado por criador não permitido: '{creator}' não está na whitelist")
            return False
    
    # Filtro de criadores bloqueados
    if filter_config.creators_blacklist:
        if any(creator_name.lower() == creator for creator_name in filter_config.creators_blacklist):
            debug_log(f"Clip filtrado por criador bloqueado: '{creator}' está na blacklist")
            return False
    
    return True

def get_filter_summary(filter_config: FilterConfig) -> str:
    """Retorna um resumo dos filtros ativos"""
    active_filters = []
    
    if filter_config.has_view_filter():
        active_filters.append(f"Views: {filter_config.min_views}-{filter_config.max_views}")
    
    if filter_config.has_duration_filter():
        active_filters.append(f"Duração: {filter_config.min_duration}s-{filter_config.max_duration}s")
    
    if filter_config.keywords_include:
        active_filters.append(f"Palavras obrigatórias: {', '.join(filter_config.keywords_include)}")
    
    if filter_config.keywords_exclude:
        active_filters.append(f"Palavras proibidas: {', '.join(filter_config.keywords_exclude)}")
    
    if filter_config.creators_whitelist:
        active_filters.append(f"Criadores permitidos: {', '.join(filter_config.creators_whitelist)}")
    
    if filter_config.creators_blacklist:
        active_filters.append(f"Criadores bloqueados: {', '.join(filter_config.creators_blacklist)}")
    
    return "; ".join(active_filters) if active_filters else "Nenhum filtro ativo"

def validate_filter_config(filter_config: FilterConfig) -> list:
    """Valida configuração de filtros e retorna lista de erros"""
    errors = []
    
    if filter_config.min_views < 0:
        errors.append("Views mínimas não podem ser negativas")
    
    if filter_config.max_views < filter_config.min_views:
        errors.append("Views máximas devem ser maiores que as mínimas")
    
    if filter_config.min_duration < 0:
        errors.append("Duração mínima não pode ser negativa")
    
    if filter_config.max_duration < filter_config.min_duration:
        errors.append("Duração máxima deve ser maior que a mínima")
    
    return errors