#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import discord
from discord.ext import commands, tasks
import asyncio
import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import base64


# Armazenamento de dados (em produção, use um banco de dados)
active_games = {}
twitch_configs = {}
last_clips = {}
last_check_time = {}

# Quantas horas de clips anteriores devem ser enviados ao configurar (0 = apenas novos)
CLIP_LOOKBACK_HOURS = int(os.environ.get("CLIP_LOOKBACK_HOURS", 0))
# Intervalo entre verificações da Twitch em segundos
CLIP_CHECK_SECONDS = int(os.environ.get("CLIP_CHECK_SECONDS", 15))
# Quantas páginas da API devem ser buscadas a cada verificação
CLIP_MAX_PAGES = int(os.environ.get("CLIP_MAX_PAGES", 1))
# Exibir views, criador e data nos embeds de clips
CLIP_SHOW_DETAILS = os.environ.get("CLIP_SHOW_DETAILS", "1") != "0"
# Segundos extras para compensar atrasos da API
CLIP_API_LAG_SECONDS = int(os.environ.get("CLIP_API_LAG_SECONDS", 15))
# Tempo limite das requisições HTTP
CLIP_API_TIMEOUT = int(os.environ.get("CLIP_API_TIMEOUT", 10))
# Enviar o vídeo do clip como anexo
CLIP_ATTACH_VIDEO = os.environ.get("CLIP_ATTACH_VIDEO", "0") != "0"

class ChessGame:
    def __init__(self, player1, player2):
        self.board = chess.Board()
        self.players = [player1, player2]
        self.current_player = 0
        self.game_id = f"{player1.id}_{player2.id}"

    def get_current_player(self):
        return self.players[self.current_player]

    def make_move(self, move_str):
        try:
            move = chess.Move.from_uci(move_str)
            if move in self.board.legal_moves:
                self.board.push(move)
                self.current_player = 1 - self.current_player
                return True, None
            else:
                return False, "Movimento inválido!"
        except:
            return False, "Formato de movimento inválido! Use formato UCI (ex: e2e4)"

    def is_game_over(self):
        return self.board.is_game_over()

    def get_result(self):
        if self.board.is_checkmate():
            winner = self.players[1 - self.current_player]
            return f"Xeque-mate! {winner.mention} venceu!"
        elif self.board.is_stalemate():
            return "Empate por afogamento!"
        elif self.board.is_insufficient_material():
            return "Empate por material insuficiente!"
        elif self.board.is_fifty_moves():
            return "Empate pela regra dos 50 movimentos!"
        else:
            return "Jogo terminado!"

@bot.event
async def on_ready():
    print(f'{bot.user} está online!')
    try:
        synced = await bot.tree.sync()
        print(f'Sincronizados {len(synced)} comando(s)')
        # Inicia o monitoramento de clips
        if not check_twitch_clips.is_running():
            check_twitch_clips.start()
    except Exception as e:
        print(f'Erro ao sincronizar comandos: {e}')

# ==================== COMANDOS DE JOGOS ====================

@bot.tree.command(name="xadrez", description="Inicia um jogo de xadrez")
async def xadrez(interaction: discord.Interaction, oponente: discord.Member):
    if interaction.user.id == oponente.id:
        await interaction.response.send_message("❌ Você não pode jogar contra si mesmo!", ephemeral=True)
        return

    game_id = f"{min(interaction.user.id, oponente.id)}_{max(interaction.user.id, oponente.id)}"

    if game_id in active_games:
        await interaction.response.send_message("❌ Já existe um jogo ativo entre vocês!", ephemeral=True)
        return

    # Cria novo jogo
    game = ChessGame(interaction.user, oponente)
    active_games[game_id] = game

    embed = discord.Embed(
        title="♟️ Jogo de Xadrez Iniciado!",
        description=f"**{interaction.user.display_name}** (Brancas) vs **{oponente.display_name}** (Pretas)",
        color=0x00ff00
    )
    embed.add_field(
        name="🎯 Como jogar", 
        value="Use `/mover` para fazer suas jogadas\nExemplo: `/mover e2e4`\nUse `/tabuleiro` para ver o estado atual", 
        inline=False
    )
    embed.add_field(
        name="🔄 Turno atual", 
        value=f"{game.get_current_player().mention}", 
        inline=True
    )
    embed.add_field(
        name="📋 Comandos úteis", 
        value="`/desistir` - Desiste do jogo\n`/tabuleiro` - Mostra o tabuleiro", 
        inline=True
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="mover", description="Faz uma jogada no xadrez")
async def mover(interaction: discord.Interaction, movimento: str):
    # Encontra o jogo do usuário
    user_game = None
    for game_id, game in active_games.items():
        if interaction.user in game.players:
            user_game = game_id
            break

    if not user_game:
        await interaction.response.send_message("❌ Você não está em nenhum jogo ativo!", ephemeral=True)
        return

    game = active_games[user_game]

    if game.get_current_player() != interaction.user:
        await interaction.response.send_message("❌ Não é seu turno!", ephemeral=True)
        return

    # Tenta fazer o movimento
    success, error = game.make_move(movimento.lower())

    if not success:
        await interaction.response.send_message(f"❌ {error}", ephemeral=True)
        return

    # Verifica se o jogo terminou
    if game.is_game_over():
        result = game.get_result()
        embed = discord.Embed(
            title="🏁 Jogo Finalizado!",
            description=f"**Último movimento:** {movimento}\n\n{result}",
            color=0xff6b6b
        )
        del active_games[user_game]
    else:
        embed = discord.Embed(
            title="♟️ Movimento Realizado",
            description=f"**{interaction.user.display_name}** jogou: `{movimento}`",
            color=0x0099ff
        )
        embed.add_field(
            name="🔄 Próximo turno", 
            value=game.get_current_player().mention, 
            inline=True
        )

        # Verifica xeque
        if game.board.is_check():
            embed.add_field(name="⚠️ Status", value="**XEQUE!**", inline=True)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="tabuleiro", description="Mostra o estado atual do tabuleiro")
async def tabuleiro(interaction: discord.Interaction):
    # Encontra o jogo do usuário
    user_game = None
    for game_id, game in active_games.items():
        if interaction.user in game.players:
            user_game = game_id
            break

    if not user_game:
        await interaction.response.send_message("❌ Você não está em nenhum jogo ativo!", ephemeral=True)
        return

    game = active_games[user_game]

    """Permite que o usuário desista do jogo atual."""

    # Identifica se há um jogo em andamento para o usuário
    if user_game is None:
        await interaction.response.send_message(
            "❌ Você não está em nenhum jogo ativo!", ephemeral=True
        )
    game = active_games.pop(user_game)
    opponent = (
        game.players[1] if game.players[0] == interaction.user else game.players[0]
    )
        description=(
            f"**{interaction.user.display_name}** desistiu do jogo!\n\n"
            f"🏆 **{opponent.display_name}** venceu por desistência!"
        ),
        color=0xff6b6b,
    )
        name="🔄 Turno atual", 
        value=game.get_current_player().mention, 
        inline=True
    )
    description = (
        f"**{interaction.user.display_name}** desistiu do jogo!\n\n"
        f"🏆 **{opponent.display_name}** venceu por desistência!"
    )
        description=description,
    )

    if game.board.is_check():
        embed.add_field(name="⚠️ Status", value="**XEQUE!**", inline=True)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="desistir", description="Desiste do jogo atual")
async def desistir(interaction: discord.Interaction):
    # Encontra o jogo do usuário
    user_game = None
    for game_id, game in active_games.items():
        if interaction.user in game.players:
    xadrez_text = "\n".join([
        "`/xadrez @oponente` - Inicia um jogo de xadrez",
        "`/mover e2e4` - Faz uma jogada",
        "`/tabuleiro` - Mostra o tabuleiro",
        "`/desistir` - Desiste do jogo",
    ])
        value=xadrez_text,
    """Obtem token de acesso da Twitch"""
    data = response.json()
    return data.get('access_token')
        inline=False,
        await interaction.response.send_message("❌ Você não está em nenhum jogo ativo!", ephemeral=True)
        return

    game = active_games[user_game]
    opponent = game.players[1] if game.players[0] == interaction.user else game.players[0]

    embed = discord.Embed(
        title="🏳️ Desistência",
        description=f"**{interaction.user.display_name}** desistiu do jogo!\n\n🏆 **{opponent.display_name}** venceu por desistência!",
        color=0xff6b6b
    )

    del active_games[user_game]
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="jogos", description="Lista todos os jogos disponíveis")
async def jogos(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 Jogos Disponíveis",
        description="Aqui estão os jogos que você pode jogar:",
        color=0xff6b6b
    )
    embed.add_field(
        name="♟️ Xadrez", 
        value="`/xadrez @oponente` - Inicia um jogo de xadrez\n`/mover e2e4` - Faz uma jogada\n`/tabuleiro` - Mostra o tabuleiro\n`/desistir` - Desiste do jogo", 
        inline=False
    )
    embed.add_field(
        response = requests.post(url, data=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return None

    return response.json().get('access_token')
            f"https://api.twitch.tv/helix/users?login={username}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
    except requests.RequestException as e:
        return None

    data = response.json()
    if data.get('data'):
        return data['data'][0]['id']

    print("Canal não encontrado na resposta da API.")
    """Obtém os clips mais recentes de um canal"""
    token = await get_twitch_token()
    if not token:
        url = f"https://api.twitch.tv/helix/clips?broadcaster_id={broadcaster_id}&first={limit}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()['data']
    # Inicializa o controle de clips
    embed.add_field(name="🔄 Frequência", value="Verifica novos clips a cada 5 minutos", inline=False)
@tasks.loop(minutes=5)
    for server_id, config in twitch_configs.items():
            clips = await get_latest_clips(config['broadcaster_id'], 3)


                if clip_id not in last_clips[server_id]:
                    # Novo clip encontrado!
                        embed = discord.Embed(
                            title="🎬 Novo Clip da Twitch!",
                            description=f"**{clip['title']}**",
                            url=clip['url'],
                            color=0x9146ff
                        )
                        embed.add_field(name="📺 Canal", value=config['username'], inline=True)
                        embed.add_field(name="👀 Views", value=clip['view_count'], inline=True)
                        embed.add_field(name="⏱️ Duração", value=f"{clip['duration']}s", inline=True)
                        embed.add_field(name="🎮 Jogo", value=clip.get('game_name', 'N/A'), inline=True)
                        embed.add_field(name="👤 Criado por", value=clip['creator_name'], inline=True)
                        embed.add_field(name="📅 Data", value=clip['created_at'][:10], inline=True)
        url = (
            f"https://api.twitch.tv/helix/clips?"
            f"broadcaster_id={broadcaster_id}&first={limit}"
        )
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return []

    return response.json().get("data", [])
        print("❌ DISCORD_TOKEN não encontrado nas variáveis de ambiente!")
    else:
    )
    embed.add_field(name="✅ Status", value="Monitoramento ativo", inline=False)
    embed.add_field(name="🔄 Frequência", value=f"Verifica novos clips a cada {CLIP_CHECK_SECONDS}s", inline=False)

    await interaction.followup.send(embed=embed)

@tasks.loop(seconds=CLIP_CHECK_SECONDS, reconnect=True)
async def check_twitch_clips():
    """Verifica novos clips da Twitch periodicamente"""
    # Copia as configurações para evitar erros caso sejam alteradas
    # enquanto a iteração estiver em andamento
    for server_id, config in list(twitch_configs.items()):
        try:
            print(
                f"[DEBUG] Checando clips para {config['username']} em {datetime.now(timezone.utc).isoformat()}"
            )
            # Busca clips criados após a última verificação (com margem para atrasos)
            started_at = (
                last_check_time.get(
                    server_id,
                    datetime.now(timezone.utc) - timedelta(hours=CLIP_LOOKBACK_HOURS),
                )
                - timedelta(seconds=CLIP_API_LAG_SECONDS)
            )
            clips = await get_latest_clips(
                config['broadcaster_id'], started_at, max_pages=CLIP_MAX_PAGES
            )
            print(f"[DEBUG] {len(clips)} clip(s) encontrados")

            if server_id not in last_clips:
                last_clips[server_id] = set()
            if server_id not in last_check_time:
                last_check_time[server_id] = (
                    datetime.now(timezone.utc) - timedelta(hours=CLIP_LOOKBACK_HOURS)
                )

            latest_time = last_check_time[server_id]
            for clip in clips:
                clip_id = clip['id']
                created_at = datetime.fromisoformat(
                    clip['created_at'].replace('Z', '+00:00')
                ).astimezone(timezone.utc)
                if created_at >= last_check_time[server_id] and clip_id not in last_clips[server_id]:
                    channel = bot.get_channel(config['discord_channel'])
                    if channel:
                        message = f"{clip['url']}\n**{clip['title']}**"
                        details = []
                        if CLIP_SHOW_DETAILS:
                            details.append(f"👀 {clip['view_count']} views")
                            details.append(f"👤 {clip['creator_name']}")
                            details.append(f"📅 {clip['created_at'][:10]}")
                        details.append(f"⏱️ {clip['duration']}s")
                        details.append(f"🎮 {clip.get('game_name', 'N/A')}")
                        message += "\n" + " | ".join(details)

                        file = None
                        if CLIP_ATTACH_VIDEO and clip.get('thumbnail_url'):
                            mp4_url = clip_video_url(clip['thumbnail_url'])
                            if mp4_url:
                                try:
                                    timeout = aiohttp.ClientTimeout(total=CLIP_API_TIMEOUT)
                                    async with aiohttp.ClientSession(timeout=timeout) as session:
                                        async with session.get(mp4_url) as resp:
                                            if resp.status == 200:
                                                data = await resp.read()
                                                file = discord.File(BytesIO(data), filename=f"{clip_id}.mp4")
                                            else:
                                                print(f"Erro ao baixar vídeo: {resp.status}")
                                except Exception as e:
                                    print(f"Erro ao baixar vídeo do clip {clip_id}: {e}")

                        if file:
                            print(f"[DEBUG] Enviando vídeo do clip {clip_id}")
                            await channel.send(content=message, file=file)
                        else:
                            print(f"[DEBUG] Enviando link do clip {clip_id}")
                            await channel.send(content=message)

                    last_clips[server_id].add(clip_id)

                if created_at >= latest_time:
                    latest_time = created_at

            # Avança somente se algum clip mais novo foi encontrado
            if latest_time > last_check_time[server_id]:
                last_check_time[server_id] = latest_time

            # Mantém apenas os últimos 50 clips na memória
            if len(last_clips[server_id]) > 50:
                last_clips[server_id] = set(list(last_clips[server_id])[-50:])

        except Exception as e:
            print(f"Erro ao verificar clips para servidor {server_id}: {e}")

@bot.tree.command(name="twitch_status", description="Mostra o status do monitoramento da Twitch")
async def twitch_status(interaction: discord.Interaction):
    server_id = interaction.guild.id

    if server_id not in twitch_configs:
        embed = discord.Embed(
            title="❌ Twitch não configurado",
            description="Use `/twitch_setup` para configurar o monitoramento de clips.",
            color=0xff0000
        )
    else:
        config = twitch_configs[server_id]
        channel = bot.get_channel(config['discord_channel'])

        embed = discord.Embed(
            title="📺 Status do Monitoramento Twitch",
            color=0x9146ff
        )
        embed.add_field(name="📺 Canal", value=config['username'], inline=True)
        embed.add_field(name="💬 Canal Discord", value=channel.mention if channel else "Canal não encontrado", inline=True)
        embed.add_field(name="✅ Status", value="Ativo", inline=True)
        embed.add_field(name="🔄 Última verificação", value=f"A cada {CLIP_CHECK_SECONDS}s", inline=True)
        embed.add_field(name="📊 Clips monitorados", value=len(last_clips.get(server_id, [])), inline=True)

    await interaction.response.send_message(embed=embed)

# ==================== COMANDOS GERAIS ====================

@bot.tree.command(name="ping", description="Verifica a latência do bot")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latência: **{latency}ms**",
        color=0x00ff00
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="Mostra todos os comandos disponíveis")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Comandos do Bot",
        description="Aqui estão todos os comandos disponíveis:",
        color=0x0099ff
    )

    embed.add_field(
        name="🎮 Jogos",
        value="`/xadrez` - Inicia jogo de xadrez\n`/mover` - Faz uma jogada\n`/tabuleiro` - Mostra tabuleiro\n`/desistir` - Desiste do jogo\n`/jogos` - Lista jogos",
        inline=False
    )

    embed.add_field(
        name="📺 Twitch",
        value="`/twitch_setup` - Configura monitoramento\n`/twitch_status` - Status do monitoramento",
        inline=False
    )

    embed.add_field(
        name="🔧 Utilidades",
        value="`/ping` - Verifica latência\n`/help` - Mostra esta mensagem",
        inline=False
    )

    await interaction.response.send_message(embed=embed)

# Inicia o bot
if __name__ == "__main__":
    missing = []
        missing.append("DISCORD_TOKEN")
    if not TWITCH_CLIENT_ID:
        missing.append("TWITCH_CLIENT_ID")
    if not TWITCH_SECRET:
        missing.append("TWITCH_SECRET")

    if missing:
        print("❌ Variáveis de ambiente faltando: " + ", ".join(missing))
    if not DISCORD_TOKEN:
        missing_vars.append("DISCORD_TOKEN")
    if not TWITCH_CLIENT_ID:
        missing_vars.append("TWITCH_CLIENT_ID")
    if not TWITCH_SECRET:
        missing_vars.append("TWITCH_SECRET")

    if missing_vars:
        print(f"❌ Variáveis de ambiente faltando: {', '.join(missing_vars)}")
        if "DISCORD_TOKEN" in missing_vars:
            print("Bot não pode iniciar sem DISCORD_TOKEN.")
            exit(1)
        else:
            print("⚠️ Twitch desabilitado. Defina TWITCH_CLIENT_ID e TWITCH_SECRET para habilitar.")

    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
