"""Loop de verificação de status de lives"""

from datetime import datetime
from discord.ext import tasks

from config.settings import *
from config.templates import PRESET_TEMPLATES
from utils.twitch_api import get_twitch_token, check_stream_status
from utils.helpers import log, debug_log, format_live_template
from utils.cache import save_cache

@tasks.loop(seconds=300)  # Verificar a cada 5 minutos
async def check_live_status_loop():
    """Loop para verificar status de lives"""
    if not server_streamers:
        debug_log("Nenhum streamer configurado para verificação de lives")
        return

    token = await get_twitch_token()
    if not token:
        log("Erro ao obter token para verificação de lives", "ERROR")
        return

    debug_log("Verificando status de lives")

    for server_id, streamers in server_streamers.items():
        for broadcaster_id, streamer_config in streamers.items():
            if not streamer_config.enabled or not streamer_config.live_notifications:
                continue

            await check_streamer_live_status(broadcaster_id, streamer_config, token)

    # Salvar status atualizado
    save_cache()

async def check_streamer_live_status(broadcaster_id, streamer_config, token):
    """Verifica status de live de um streamer específico"""
    from utils.helpers import get_running_bot
    bot = get_running_bot()

    channel = bot.get_channel(streamer_config.live_channel)
    if not channel:
        debug_log(f"Canal de notificação não encontrado para {streamer_config.username}")
        return

    try:
        is_live = await check_stream_status(broadcaster_id, token)
        was_live = live_streamers.get(broadcaster_id, False)

        if is_live and not was_live:
            # Streamer ficou online
            await send_live_notification(streamer_config, channel, token)
            live_streamers[broadcaster_id] = True
            log(f"📺 {streamer_config.display_name} ficou online")
            
        elif not is_live and was_live:
            # Streamer ficou offline
            live_streamers[broadcaster_id] = False
            debug_log(f"📺 {streamer_config.display_name} ficou offline")

    except Exception as e:
        log(f"Erro ao verificar live de {streamer_config.username}: {e}", "ERROR")

async def send_live_notification(streamer_config, channel, token):
    """Envia notificação de live"""
    try:
        display_name = streamer_config.display_name

        from utils.twitch_api import get_stream_info
        stream_info = await get_stream_info(streamer_config.broadcaster_id, token)
        game = stream_info.get("game_name", "") if stream_info else ""
        thumbnail = stream_info.get("thumbnail_url", "") if stream_info else ""

        template = PRESET_TEMPLATES["lives"].get(
            streamer_config.live_template,
            PRESET_TEMPLATES["lives"]["simples"]
        )

        embed = format_live_template(
            template,
            display_name,
            streamer_config.username,
            game_name=game,
            thumbnail_url=thumbnail,
        )
        
        # Adicionar informações extras baseadas no template
        if streamer_config.live_template == "detalhado":
            embed.add_field(
                name="🎮 Plataforma", 
                value="Twitch", 
                inline=True
            )
            embed.add_field(
                name="⏰ Iniciado", 
                value=f"<t:{int(datetime.now().timestamp())}:R>", 
                inline=True
            )
        
        await channel.send(
            content=streamer_config.live_message or None,
            embed=embed,
        )
        log(f"📺 Notificação de live enviada: {display_name}")
        
    except Exception as e:
        log(f"Erro ao enviar notificação de live: {e}", "ERROR")

@check_live_status_loop.before_loop
async def before_check_live():
    """Aguarda o bot estar pronto"""
    from utils.helpers import get_running_bot
    bot = get_running_bot()
    if bot:
        await bot.wait_until_ready()
    log("📺 Loop de verificação de lives iniciado")

@check_live_status_loop.error
async def check_live_error(error):
    """Trata erros do loop de lives"""
    log(f"Erro no loop de lives: {error}", "ERROR")
    # Tentar reiniciar o loop após 60 segundos
    import asyncio
    await asyncio.sleep(60)
    if not check_live_status_loop.is_running():
        check_live_status_loop.start()
        log("📺 Loop de lives reiniciado após erro")

def get_live_streamers_count():
    """Retorna número de streamers online"""
    return sum(1 for is_live in live_streamers.values() if is_live)

def get_live_streamers_list():
    """Retorna lista de streamers online"""
    online_streamers = []
    for broadcaster_id, is_live in live_streamers.items():
        if is_live:
            # Encontrar configuração do streamer
            for server_streamers_dict in server_streamers.values():
                if broadcaster_id in server_streamers_dict:
                    config = server_streamers_dict[broadcaster_id]
                    online_streamers.append(config.display_name)
                    break
    return online_streamers

async def force_check_all_lives():
    """Força verificação de todas as lives (útil para comandos manuais)"""
    if not server_streamers:
        return []

    token = await get_twitch_token()
    if not token:
        return []

    results = []
    for server_id, streamers in server_streamers.items():
        for broadcaster_id, streamer_config in streamers.items():
            if not streamer_config.enabled:
                continue
                
            try:
                is_live = await check_stream_status(broadcaster_id, token)
                results.append({
                    'streamer': streamer_config.display_name,
                    'username': streamer_config.username,
                    'is_live': is_live
                })
            except Exception as e:
                log(f"Erro ao verificar {streamer_config.username}: {e}", "ERROR")
    
    return results
