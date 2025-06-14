"""Loop de verificação de clips"""

import io
import aiohttp
import discord
from datetime import datetime, timezone, timedelta
from discord.ext import tasks

from config.settings import *
from models.dataclasses import FilterConfig, ThemeConfig, TemplateConfig
from utils.twitch_api import get_twitch_token, fetch_clips
from utils.filters import apply_filters
from utils.helpers import (
    log, debug_log, format_template, create_clip_embed, 
    update_stats, clip_video_url
)
from utils.cache import save_cache

@tasks.loop(seconds=CLIP_CHECK_SECONDS)
async def check_clips_loop():
    """Loop principal que verifica novos clips"""
    if not server_streamers:
        debug_log("Nenhuma configuração ativa")
        return

    token = await get_twitch_token()
    if not token:
        log("Erro ao obter token da Twitch", "ERROR")
        return

    now = datetime.now(timezone.utc)
    debug_log(f"Verificando clips - {now.strftime('%H:%M:%S')}")

    for server_id, streamers in list(server_streamers.items()):
        try:
            # Definir período de busca
            start_time = last_check_time.get(server_id, now - timedelta(hours=CLIP_LOOKBACK_HOURS))
            
            # Obter configurações do servidor
            filter_config = server_filters.get(server_id, FilterConfig())
            theme_config = server_themes.get(server_id, ThemeConfig())
            template_config = server_templates.get(server_id, TemplateConfig())

            for broadcaster_id, streamer_config in streamers.items():
                if not streamer_config.enabled:
                    continue

                # Buscar clips
                clips = await fetch_clips(broadcaster_id, token, start_time, now)

                if not clips:
                    debug_log(f"Nenhum clip para {streamer_config.username}")
                    continue

                # Processar clips
                new_clips = await process_clips(
                    clips, server_id, broadcaster_id, streamer_config,
                    filter_config, theme_config, template_config, start_time
                )

                if new_clips > 0:
                    log(f"📺 {new_clips} novos clips enviados para {streamer_config.username}")

            if any(streamers.values()):  # Se há streamers ativos
                save_cache()

        except Exception as e:
            log(f"Erro ao verificar clips do servidor {server_id}: {e}", "ERROR")

async def process_clips(clips, server_id, broadcaster_id, streamer_config, 
                       filter_config, theme_config, template_config, start_time):
    """Processa lista de clips e envia os novos"""
    from bot import bot  # Import local para evitar circular import
    
    new_clips = 0
    
    for clip in sorted(clips, key=lambda c: c.get("created_at", "")):
        clip_id = clip["id"]
        created_time = datetime.fromisoformat(clip["created_at"].replace("Z", "+00:00"))

        # Verificar se já foi enviado
        if clip_id in posted_clips.get(server_id, set()):
            continue

        # Verificar se está no período
        if created_time < start_time:
            continue

        # Aplicar filtros
        if not apply_filters(clip, filter_config):
            debug_log(f"Clip filtrado: {clip.get('title', 'Sem título')}")
            continue

        # Enviar clip
        success = await send_clip_message(
            clip, streamer_config, theme_config, template_config, server_id, bot
        )
        
        if success:
            new_clips += 1
            # Atualizar último tempo
            if created_time > last_check_time.get(server_id, start_time):
                last_check_time[server_id] = created_time

    return new_clips

async def send_clip_message(clip, streamer_config, theme_config, template_config, server_id, bot):
    """Envia mensagem do clip para o Discord"""
    channel = bot.get_channel(streamer_config.discord_channel)
    if not channel:
        log(f"Canal Discord não encontrado: {streamer_config.discord_channel}", "ERROR")
        return False

    try:
        # Criar embed
        embed = create_clip_embed(clip, streamer_config, theme_config, template_config)
        files = []

        # Baixar vídeo se configurado
        if CLIP_ATTACH_VIDEO and clip.get("thumbnail_url"):
            video_file = await download_clip_video(clip["thumbnail_url"])
            if video_file:
                files.append(video_file)

        # Preparar mensagem
        display_name = streamer_config.display_name
        message_content = format_template(template_config.message_format, clip, display_name)

        # Adicionar ping de role se configurado
        if template_config.ping_role:
            message_content = f"<@&{template_config.ping_role}> {message_content}"

        # Enviar mensagem
        await channel.send(content=message_content, embed=embed, files=files)

        # Marcar como enviado
        posted_clips.setdefault(server_id, set()).add(clip["id"])

        # Atualizar estatísticas
        update_stats(server_id, display_name, clip.get("creator_name", "Desconhecido"))

        log(f"✅ Clip enviado: {clip.get('title', 'Sem título')} - {display_name}")
        return True

    except Exception as e:
        log(f"Erro ao enviar clip: {e}", "ERROR")
        return False

async def download_clip_video(thumbnail_url):
    """Baixa vídeo do clip se possível"""
    try:
        video_url = clip_video_url(thumbnail_url)
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url, timeout=CLIP_API_TIMEOUT * 2) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    if len(data) > 0 and len(data) < MAX_CLIP_SIZE_MB * 1024 * 1024:
                        return discord.File(io.BytesIO(data), filename="clip.mp4")
        return None
    except Exception as e:
        debug_log(f"Erro ao baixar vídeo: {e}")
        return None

@check_clips_loop.before_loop
async def before_check_clips():
    """Aguarda o bot estar pronto"""
    from bot import bot  # Import local para evitar circular import
    await bot.wait_until_ready()
    log("🔄 Loop de verificação de clips iniciado")

@check_clips_loop.error
async def check_clips_error(error):
    """Trata erros do loop de clips"""
    log(f"Erro no loop de clips: {error}", "ERROR")
    # Tentar reiniciar o loop após 60 segundos
    await asyncio.sleep(60)
    if not check_clips_loop.is_running():
        check_clips_loop.start()
        log("🔄 Loop de clips reiniciado após erro")
