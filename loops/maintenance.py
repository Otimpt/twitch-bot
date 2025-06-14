"""Loop de manutenção e limpeza"""

import asyncio
from datetime import datetime, timedelta
from discord.ext import tasks

from config.settings import *
from utils.cache import save_cache, cleanup_old_clips, backup_cache
from utils.helpers import log, debug_log

@tasks.loop(hours=24)  # Executar diariamente
async def maintenance_loop():
    """Loop de manutenção diária"""
    log("🧹 Iniciando manutenção diária")
    
    try:
        # Limpeza de clips antigos
        await cleanup_old_data()
        
        # Backup do cache
        await create_daily_backup()
        
        # Reset de estatísticas se necessário
        await reset_statistics()
        
        # Verificar integridade dos dados
        await verify_data_integrity()
        
        log("✅ Manutenção diária concluída")
        
    except Exception as e:
        log(f"Erro na manutenção: {e}", "ERROR")

async def cleanup_old_data():
    """Limpa dados antigos"""
    try:
        # Limpar clips antigos (mais de 30 dias)
        cleanup_old_clips(30)
        
        # Limpar streamers inativos há muito tempo
        await cleanup_inactive_streamers()
        
        log("🗑️ Limpeza de dados concluída")
        
    except Exception as e:
        log(f"Erro na limpeza: {e}", "ERROR")

async def cleanup_inactive_streamers():
    """Remove streamers que não têm clips há muito tempo"""
    cutoff_date = datetime.now() - timedelta(days=90)
    removed_count = 0
    
    for server_id, streamers in list(server_streamers.items()):
        for broadcaster_id, config in list(streamers.items()):
            # Verificar se o streamer teve atividade recente
            # (Esta é uma implementação simplificada)
            if not config.enabled:
                # Remover streamers desabilitados há mais de 90 dias
                # Aqui você poderia adicionar lógica mais sofisticada
                pass
    
    if removed_count > 0:
        save_cache()
        log(f"🗑️ Removidos {removed_count} streamers inativos")

async def create_daily_backup():
    """Cria backup diário"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d")
        backup_file = f"backup_daily_{timestamp}_{CACHE_FILE}"
        
        if backup_cache(backup_file):
            log(f"💾 Backup diário criado: {backup_file}")
        
    except Exception as e:
        log(f"Erro no backup: {e}", "ERROR")

async def reset_statistics():
    """Reseta estatísticas quando necessário"""
    try:
        reset_count = 0
        
        for server_id, stats in server_stats.items():
            # Verificar se precisa resetar estatísticas
            if stats.should_reset_daily():
                stats.reset_daily_stats()
                reset_count += 1
            
            if stats.should_reset_weekly():
                stats.reset_weekly_stats()
                reset_count += 1
                
            if stats.should_reset_monthly():
                stats.reset_monthly_stats()
                reset_count += 1
        
        if reset_count > 0:
            save_cache()
            log(f"📊 Estatísticas resetadas para {reset_count} períodos")
            
    except Exception as e:
        log(f"Erro no reset de estatísticas: {e}", "ERROR")

async def verify_data_integrity():
    """Verifica integridade dos dados"""
    try:
        issues_found = 0
        
        # Verificar se todos os canais Discord ainda existem
        from bot import bot  # Import local
        
        for server_id, streamers in server_streamers.items():
            guild = bot.get_guild(server_id)
            if not guild:
                log(f"⚠️ Servidor {server_id} não encontrado", "WARNING")
                continue
                
            for broadcaster_id, config in streamers.items():
                # Verificar canal de clips
                clip_channel = bot.get_channel(config.discord_channel)
                if not clip_channel:
                    log(f"⚠️ Canal de clips não encontrado: {config.discord_channel} para {config.username}", "WARNING")
                    issues_found += 1
                
                # Verificar canal de lives
                if config.live_notifications and config.live_channel:
                    live_channel = bot.get_channel(config.live_channel)
                    if not live_channel:
                        log(f"⚠️ Canal de lives não encontrado: {config.live_channel} para {config.username}", "WARNING")
                        issues_found += 1
        
        if issues_found == 0:
            log("✅ Integridade dos dados verificada - tudo OK")
        else:
            log(f"⚠️ Encontrados {issues_found} problemas de integridade")
            
    except Exception as e:
        log(f"Erro na verificação de integridade: {e}", "ERROR")

@maintenance_loop.before_loop
async def before_maintenance():
    """Aguarda o bot estar pronto"""
    from bot import bot  # Import local
    await bot.wait_until_ready()
    
    # Aguardar 1 hora após o bot iniciar para primeira manutenção
    await asyncio.sleep(3600)
    log("🧹 Loop de manutenção iniciado")

@maintenance_loop.error
async def maintenance_error(error):
    """Trata erros do loop de manutenção"""
    log(f"Erro no loop de manutenção: {error}", "ERROR")
    # Continuar mesmo com erro - manutenção não é crítica
