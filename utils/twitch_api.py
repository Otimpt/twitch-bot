"""Funções para interação com a API da Twitch"""

import aiohttp
from typing import Optional, List
from datetime import datetime

from config.settings import *
from utils.helpers import log, debug_log

async def get_twitch_token() -> Optional[str]:
    """Obtém token de acesso da Twitch"""
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_SECRET,
        "grant_type": "client_credentials"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=params, timeout=CLIP_API_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.json()
                token = data.get("access_token")
                debug_log(f"Token obtido: {token[:10]}..." if token else "Falha ao obter token")
                return token
    except Exception as e:
        log(f"Erro ao obter token da Twitch: {e}", "ERROR")
        return None

def parse_twitch_username(raw_input: str) -> str:
    """Extrai username da Twitch de diferentes formatos"""
    username = raw_input.strip().replace("@", "").lower()

    # Remove URL parts
    if "//" in username:
        username = username.split("//", 1)[1]
    if username.startswith("www."):
        username = username[4:]
    if username.startswith("twitch.tv/"):
        username = username[10:]
    if "/" in username:
        username = username.split("/", 1)[0]
    if "?" in username:
        username = username.split("?", 1)[0]

    return username

async def get_broadcaster_id(username: str, token: str) -> Optional[str]:
    """Busca ID do broadcaster pelo username"""
    url = "https://api.twitch.tv/helix/users"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    params = {"login": username}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=CLIP_API_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.json()

                if data.get("data") and len(data["data"]) > 0:
                    broadcaster_id = data["data"][0]["id"]
                    log(f"Broadcaster encontrado: {username} -> ID {broadcaster_id}")
                    return broadcaster_id
                else:
                    log(f"Usuário não encontrado: {username}", "ERROR")
                    return None
    except Exception as e:
        log(f"Erro ao buscar broadcaster {username}: {e}", "ERROR")
        return None

async def check_stream_status(broadcaster_id: str, token: str) -> bool:
    """Verifica se o streamer está online"""
    url = "https://api.twitch.tv/helix/streams"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    params = {"user_id": broadcaster_id}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=CLIP_API_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.json()
                is_live = len(data.get("data", [])) > 0
                debug_log(f"Stream status para {broadcaster_id}: {'LIVE' if is_live else 'OFFLINE'}")
                return is_live
    except Exception as e:
        log(f"Erro ao verificar status da live: {e}", "ERROR")
        return False

async def fetch_clips(broadcaster_id: str, token: str, start_time: datetime, end_time: datetime) -> List[dict]:
    """Busca clips de um broadcaster em um período"""
    url = "https://api.twitch.tv/helix/clips"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    params = {
        "broadcaster_id": broadcaster_id,
        "first": 100,
        "started_at": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ended_at": end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }

    debug_log(f"Buscando clips de {start_time} até {end_time}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=CLIP_API_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.json()
                clips = data.get("data", [])
                debug_log(f"Encontrados {len(clips)} clips")
                return clips
    except Exception as e:
        log(f"Erro ao buscar clips: {e}", "ERROR")
        return []

async def get_user_info(username: str, token: str) -> Optional[dict]:
    """Obtém informações detalhadas de um usuário"""
    url = "https://api.twitch.tv/helix/users"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    params = {"login": username}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=CLIP_API_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.json()

                if data.get("data") and len(data["data"]) > 0:
                    user_info = data["data"][0]
                    debug_log(f"Informações do usuário {username} obtidas")
                    return user_info
                else:
                    log(f"Informações do usuário {username} não encontradas", "ERROR")
                    return None
    except Exception as e:
        log(f"Erro ao obter informações do usuário {username}: {e}", "ERROR")
        return None

async def get_stream_info(broadcaster_id: str, token: str) -> Optional[dict]:
    """Obtém informações detalhadas da stream"""
    url = "https://api.twitch.tv/helix/streams"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    params = {"user_id": broadcaster_id}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=CLIP_API_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.json()
                
                if data.get("data") and len(data["data"]) > 0:
                    stream_info = data["data"][0]
                    debug_log(f"Informações da stream para {broadcaster_id} obtidas")
                    return stream_info
                else:
                    debug_log(f"Stream offline para {broadcaster_id}")
                    return None
    except Exception as e:
        log(f"Erro ao obter informações da stream: {e}", "ERROR")
        return None