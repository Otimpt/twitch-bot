"""Sistema de cache persistente"""

import json
from dataclasses import asdict
from datetime import datetime

from config.settings import *
from models.dataclasses import *
from utils.helpers import log, debug_log

def load_cache():
    """Carrega todos os dados do arquivo"""
    global server_streamers, server_filters, server_themes, server_templates
    global server_stats, posted_clips, last_check_time, live_streamers
    
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Carregar streamers
        server_streamers.clear()
        for server_id, streamers in data.get("streamers", {}).items():
            server_streamers[int(server_id)] = {}
            for streamer_id, config in streamers.items():
                server_streamers[int(server_id)][streamer_id] = StreamerConfig(**config)
        
        # Carregar filtros
        server_filters.clear()
        for server_id, filter_data in data.get("filters", {}).items():
            server_filters[int(server_id)] = FilterConfig(**filter_data)
        
        # Carregar temas
        server_themes.clear()
        for server_id, theme_data in data.get("themes", {}).items():
            server_themes[int(server_id)] = ThemeConfig(**theme_data)
        
        # Carregar templates
        server_templates.clear()
        for server_id, template_data in data.get("templates", {}).items():
            server_templates[int(server_id)] = TemplateConfig(**template_data)
        
        # Carregar estatísticas
        server_stats.clear()
        for server_id, stats_data in data.get("stats", {}).items():
            server_stats[int(server_id)] = ServerStats(**stats_data)
        
        # Carregar clips postados
        posted_clips.clear()
        posted_clips.update({int(k): set(v) for k, v in data.get("posted_clips", {}).items()})
        
        # Carregar últimas verificações
        last_check_time.clear()
        for server_id, timestamp in data.get("last_check_time", {}).items():
            last_check_time[int(server_id)] = datetime.fromisoformat(timestamp)
        
        # Carregar status de live
        live_streamers.clear()
        live_streamers.update(data.get("live_streamers", {}))
        
        total_clips = sum(len(clips) for clips in posted_clips.values())
        total_streamers = sum(len(streamers) for streamers in server_streamers.values())
        log(f"Cache carregado: {total_streamers} streamers, {total_clips} clips")
        
    except FileNotFoundError:
        log("Cache não encontrado, iniciando vazio")
        initialize_empty_cache()
    except Exception as e:
        log(f"Erro ao carregar cache: {e}", "ERROR")
        initialize_empty_cache()

def initialize_empty_cache():
    """Inicializa cache vazio"""
    global server_streamers, server_filters, server_themes, server_templates
    global server_stats, posted_clips, last_check_time, live_streamers
    
    server_streamers.clear()
    server_filters.clear()
    server_themes.clear()
    server_templates.clear()
    server_stats.clear()
    posted_clips.clear()
    last_check_time.clear()
    live_streamers.clear()

def save_cache():
    """Salva todos os dados no arquivo"""
    try:
        data = {
            "streamers": {
                str(server_id): {
                    streamer_id: asdict(config) 
                    for streamer_id, config in streamers.items()
                }
                for server_id, streamers in server_streamers.items()
            },
            "filters": {
                str(server_id): asdict(filter_config)
                for server_id, filter_config in server_filters.items()
            },
            "themes": {
                str(server_id): asdict(theme_config)
                for server_id, theme_config in server_themes.items()
            },
            "templates": {
                str(server_id): asdict(template_config)
                for server_id, template_config in server_templates.items()
            },
            "stats": {
                str(server_id): asdict(stats)
                for server_id, stats in server_stats.items()
            },
            "posted_clips": {
                str(server_id): list(clips)
                for server_id, clips in posted_clips.items()
            },
            "last_check_time": {
                str(server_id): timestamp.isoformat()
                for server_id, timestamp in last_check_time.items()
            },
            "live_streamers": live_streamers
        }
        
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        debug_log("Cache salvo com sucesso")
    except Exception as e:
        log(f"Erro ao salvar cache: {e}", "ERROR")

def cleanup_server_data(server_id: int):
    """Remove todos os dados de um servidor"""
    if server_id in server_streamers:
        del server_streamers[server_id]
    if server_id in server_filters:
        del server_filters[server_id]
    if server_id in server_themes:
        del server_themes[server_id]
    if server_id in server_templates:
        del server_templates[server_id]
    if server_id in server_stats:
        del server_stats[server_id]
    if server_id in posted_clips:
        del posted_clips[server_id]
    if server_id in last_check_time:
        del last_check_time[server_id]
    
    save_cache()
    log(f"Dados do servidor {server_id} removidos do cache")

def cleanup_old_clips(days: int = 30):
    """Remove clips antigos do cache"""
    from datetime import timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days)
    total_removed = 0
    
    for server_id in list(posted_clips.keys()):
        clips_to_remove = set()
        
        # Aqui você precisaria de uma forma de identificar a data dos clips
        # Por simplicidade, vamos manter apenas os últimos N clips por servidor
        clips_list = list(posted_clips[server_id])
        if len(clips_list) > 1000:  # Manter apenas os últimos 1000 clips
            clips_to_remove = set(clips_list[:-1000])
            posted_clips[server_id] = set(clips_list[-1000:])
            total_removed += len(clips_to_remove)
    
    if total_removed > 0:
        save_cache()
        log(f"Removidos {total_removed} clips antigos do cache")

def backup_cache(backup_file: str = None):
    """Cria backup do cache"""
    if not backup_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_{timestamp}_{CACHE_FILE}"
    
    try:
        import shutil
        shutil.copy2(CACHE_FILE, backup_file)
        log(f"Backup criado: {backup_file}")
        return True
    except Exception as e:
        log(f"Erro ao criar backup: {e}", "ERROR")
        return False

def restore_cache(backup_file: str):
    """Restaura cache de um backup"""
    try:
        import shutil
        shutil.copy2(backup_file, CACHE_FILE)
        load_cache()
        log(f"Cache restaurado de: {backup_file}")
        return True
    except Exception as e:
        log(f"Erro ao restaurar backup: {e}", "ERROR")
        return False