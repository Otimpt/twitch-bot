import discord
from discord.ext import commands, tasks
import asyncio
import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import chess
import chess.svg
from io import BytesIO
import base64

# Configurações do bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Carrega variáveis definidas em um arquivo .env (opcional)
load_dotenv()

# Variáveis de ambiente
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
TWITCH_CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
TWITCH_SECRET = os.environ.get("TWITCH_SECRET")

# Armazenamento de dados (em produção, use um banco de dados)
active_games = {}
twitch_configs = {}
last_clips = {}

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

    # Cria representação ASCII do tabuleiro
    board_str = str(game.board)

    embed = discord.Embed(
        title="♟️ Tabuleiro Atual",
        description=f"```\n{board_str}\n```",
        color=0x9146ff
    )
    embed.add_field(
        name="🔄 Turno atual", 
        value=game.get_current_player().mention, 
        inline=True
    )
    embed.add_field(
        name="📊 Movimentos", 
        value=f"{len(game.board.move_stack)} jogadas", 
        inline=True
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
            user_game = game_id
            break

    if not user_game:
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
        name="🔴 Damas", 
        value="Em desenvolvimento... 🚧", 
        inline=False
    )
    embed.add_field(
        name="🎯 Outros jogos", 
        value="Mais jogos serão adicionados em breve!", 
        inline=False
    )

    await interaction.response.send_message(embed=embed)

# ==================== INTEGRAÇÃO TWITCH ====================

async def get_twitch_token():
    """Obtém token de acesso da Twitch"""
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_SECRET,
        'grant_type': 'client_credentials'
    }

    try:
        response = requests.post(url, params=params)
        if response.status_code == 200:
            return response.json()['access_token']
    except Exception as e:
        print(f"Erro ao obter token da Twitch: {e}")
    return None

async def get_broadcaster_id(username):
    """Obtém o ID do broadcaster pelo username"""
    token = await get_twitch_token()
    if not token:
        return None

    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {token}'
    }

    try:
        response = requests.get(f"https://api.twitch.tv/helix/users?login={username}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data['data']:
                return data['data'][0]['id']
    except Exception as e:
        print(f"Erro ao obter broadcaster ID: {e}")
    return None

async def get_latest_clips(broadcaster_id, limit=5):
    """Obtém os clips mais recentes de um canal"""
    token = await get_twitch_token()
    if not token:
        return []

    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {token}'
    }

    try:
        url = f"https://api.twitch.tv/helix/clips?broadcaster_id={broadcaster_id}&first={limit}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()['data']
    except Exception as e:
        print(f"Erro ao obter clips: {e}")
    return []

@bot.tree.command(name="twitch_setup", description="Configura monitoramento de clips da Twitch")
async def twitch_setup(interaction: discord.Interaction, canal_twitch: str, canal_discord: discord.TextChannel):
    await interaction.response.defer()

    # Remove @ se o usuário incluiu
    username = canal_twitch.replace('@', '').lower()

    # Obtém o ID do broadcaster
    broadcaster_id = await get_broadcaster_id(username)
    if not broadcaster_id:
        embed = discord.Embed(
            title="❌ Erro",
            description=f"Não foi possível encontrar o canal **{username}** na Twitch.",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)
        return

    # Salva a configuração
    server_id = interaction.guild.id
    twitch_configs[server_id] = {
        'username': username,
        'broadcaster_id': broadcaster_id,
        'discord_channel': canal_discord.id
    }

    # Inicializa o controle de clips
    last_clips[server_id] = set()

    embed = discord.Embed(
        title="📺 Twitch Configurado!",
        description=f"**Canal Twitch:** {username}\n**Canal Discord:** {canal_discord.mention}",
        color=0x9146ff
    )
    embed.add_field(name="✅ Status", value="Monitoramento ativo", inline=False)
    embed.add_field(name="🔄 Frequência", value="Verifica novos clips a cada 5 minutos", inline=False)

    await interaction.followup.send(embed=embed)

@tasks.loop(minutes=5)
async def check_twitch_clips():
    """Verifica novos clips da Twitch periodicamente"""
    for server_id, config in twitch_configs.items():
        try:
            clips = await get_latest_clips(config['broadcaster_id'], 3)

            if server_id not in last_clips:
                last_clips[server_id] = set()

            for clip in clips:
                clip_id = clip['id']
                if clip_id not in last_clips[server_id]:
                    # Novo clip encontrado!
                    channel = bot.get_channel(config['discord_channel'])
                    if channel:
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

                        if clip.get('thumbnail_url'):
                            embed.set_image(url=clip['thumbnail_url'])

                        await channel.send(embed=embed)

                    last_clips[server_id].add(clip_id)

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
        embed.add_field(name="🔄 Última verificação", value="A cada 5 minutos", inline=True)
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
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN não encontrado nas variáveis de ambiente!")
    else:
        bot.run(DISCORD_TOKEN)
