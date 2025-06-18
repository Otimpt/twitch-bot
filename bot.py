#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Discord para monitorar e enviar clips recentes da Twitch
Autor: Assistant
Versão: 3.0 - Arquitetura Modular Completa
"""

import asyncio
import discord
from discord.ext import commands

# Imports da estrutura modular
from config.settings import *
from utils.cache import load_cache
from utils.helpers import log
from loops.clip_checker import check_clips_loop
from loops.live_checker import check_live_status_loop
from loops.maintenance import maintenance_loop

# ==== CONFIGURAÇÃO DO BOT ====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==== EVENTOS DO BOT ====
@bot.event
async def on_ready():
    """Evento quando o bot fica online"""
    log(f"🤖 Bot {bot.user} está online!")
    log(f"📊 Conectado a {len(bot.guilds)} servidor(es)")

    # Carregar cache
    load_cache()

    # Registrar comandos
    await register_commands()

    # Sincronizar comandos slash
    try:
        synced = await bot.tree.sync()
        log(f"✅ {len(synced)} comandos sincronizados")
    except Exception as e:
        log(f"Erro ao sincronizar comandos: {e}", "ERROR")

    # Iniciar loops
    start_loops()

@bot.event
async def on_guild_join(guild):
    """Evento quando o bot entra em um servidor"""
    log(f"➕ Bot adicionado ao servidor: {guild.name} (ID: {guild.id})")

@bot.event
async def on_guild_remove(guild):
    """Evento quando o bot sai de um servidor"""
    from utils.cache import cleanup_server_data
    log(f"➖ Bot removido do servidor: {guild.name} (ID: {guild.id})")
    cleanup_server_data(guild.id)

# ==== REGISTRO DE COMANDOS ====
async def register_commands():
    """Registra todos os comandos do bot"""
    try:
        # Importar e registrar comandos de cada módulo
        from commands.setup import setup_commands
        from commands.templates import template_commands
        from commands.notifications import notification_commands
        from commands.themes import theme_commands
        from commands.filters import filter_commands
        from commands.stats import stats_commands
        from commands.management import management_commands

        # Registrar comandos (corrigido - usar os nomes corretos das funções)
        await setup_commands(bot)
        await template_commands(bot)
        await notification_commands(bot)
        await theme_commands(bot)
        await filter_commands(bot)
        await stats_commands(bot)
        await management_commands(bot)

        log("📋 Todos os comandos registrados com sucesso")

    except Exception as e:
        log(f"Erro ao registrar comandos: {e}", "ERROR")

def start_loops():
    """Inicia todos os loops de verificação"""
    try:
        # Loop de verificação de clips
        if not check_clips_loop.is_running():
            check_clips_loop.start()
            log("🔄 Loop de verificação de clips iniciado")
        
        # Loop de verificação de lives
        if not check_live_status_loop.is_running():
            check_live_status_loop.start()
            log("📺 Loop de verificação de lives iniciado")
        
        # Loop de manutenção
        if not maintenance_loop.is_running():
            maintenance_loop.start()
            log("🧹 Loop de manutenção iniciado")

    except Exception as e:
        log(f"Erro ao iniciar loops: {e}", "ERROR")

# ==== COMANDOS BÁSICOS INTEGRADOS ====
@bot.tree.command(name="help", description="Mostra todos os comandos disponíveis")
async def help_command(interaction: discord.Interaction):
    """Comando de ajuda principal"""
    embed = discord.Embed(
        title="🤖 Twitch Clips Bot - Versão 3.0",
        description="Bot avançado para monitorar clips da Twitch com arquitetura modular",
        color=0x9146FF
    )

    embed.add_field(
        name="⚙️ Configuração Básica",
        value="`/twitch-setup` - Adiciona streamer para monitoramento\n`/list` - Lista streamers configurados\n`/remove` - Remove streamer\n`/toggle` - Ativa/desativa streamer",
        inline=False
    )

    embed.add_field(
        name="🎨 Personalização Visual",
        value="`/template` - Templates com seletor visual\n`/notificacoes` - Notificações de live\n`/tema` - Personaliza aparência dos embeds",
        inline=False
    )

    embed.add_field(
        name="🔧 Funcionalidades Avançadas",
        value="`/filtros` - Configura filtros de clips\n`/stats` - Estatísticas detalhadas\n`/test` - Testa busca de clips",
        inline=False
    )

    embed.add_field(
        name="🆕 Novidades v3.0",
        value="✅ Arquitetura modular completa\n✅ Sistema de manutenção automática\n✅ Melhor tratamento de erros\n✅ Performance otimizada\n✅ Código organizado em módulos",
        inline=False
    )

    embed.add_field(
        name="📊 Informações do Sistema",
        value=f"🔄 **Verificação:** A cada {CLIP_CHECK_SECONDS}s\n📅 **Período:** Últimas {CLIP_LOOKBACK_HOURS}h\n🎬 **Vídeos:** {'✅ Ativado' if CLIP_ATTACH_VIDEO else '❌ Desativado'}\n🐛 **Debug:** {'✅ Ativado' if DEBUG_MODE else '❌ Desativado'}",
        inline=False
    )

    embed.set_footer(
        text="Use os comandos acima para configurar o bot",
        icon_url="https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-70x70.png"
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="status", description="Mostra status atual do bot")
async def status_command(interaction: discord.Interaction):
    """Comando de status do bot"""
    from loops.live_checker import get_live_streamers_count
    from models.dataclasses import ServerStats
    
    server_id = interaction.guild.id
    
    # Contar streamers configurados
    total_streamers = len(server_streamers.get(server_id, {}))
    active_streamers = sum(1 for config in server_streamers.get(server_id, {}).values() if config.enabled)
    
    # Contar clips enviados hoje
    clips_today = server_stats.get(server_id, ServerStats()).clips_sent_today
    
    # Streamers online
    live_count = get_live_streamers_count()
    
    embed = discord.Embed(
        title="📊 Status do Bot",
        description=f"Informações do bot em **{interaction.guild.name}**",
        color=0x00ff00
    )
    
    embed.add_field(
        name="📺 Streamers",
        value=f"**Ativos:** {active_streamers}/{total_streamers}\n**Online:** {live_count}",
        inline=True
    )
    
    embed.add_field(
        name="🎬 Clips Hoje",
        value=str(clips_today),
        inline=True
    )
    
    embed.add_field(
        name="🔄 Loops",
        value=f"**Clips:** {'✅' if check_clips_loop.is_running() else '❌'}\n**Lives:** {'✅' if check_live_status_loop.is_running() else '❌'}\n**Manutenção:** {'✅' if maintenance_loop.is_running() else '❌'}",
        inline=True
    )
    
    embed.add_field(
        name="⚙️ Configurações",
        value=f"**Verificação:** {CLIP_CHECK_SECONDS}s\n**Período:** {CLIP_LOOKBACK_HOURS}h\n**Timeout:** {CLIP_API_TIMEOUT}s",
        inline=True
    )
    
    embed.add_field(
        name="💾 Cache",
        value=f"**Arquivo:** {CACHE_FILE}\n**Servidores:** {len(server_streamers)}\n**Clips:** {sum(len(clips) for clips in posted_clips.values())}",
        inline=True
    )
    
    embed.add_field(
        name="🌐 Discord",
        value=f"**Servidores:** {len(bot.guilds)}\n**Latência:** {round(bot.latency * 1000)}ms\n**Versão:** discord.py {discord.__version__}",
        inline=True
    )
    
    await interaction.response.send_message(embed=embed)

# ==== TRATAMENTO DE ERROS GLOBAL ====
@bot.event
async def on_command_error(ctx, error):
    """Tratamento global de erros de comandos"""
    if isinstance(error, commands.CommandNotFound):
        return  # Ignorar comandos não encontrados
    
    log(f"Erro em comando: {error}", "ERROR")

@bot.event
async def on_application_command_error(interaction: discord.Interaction, error):
    """Tratamento global de erros de slash commands"""
    log(f"Erro em slash command: {error}", "ERROR")
    
    if not interaction.response.is_done():
        embed = discord.Embed(
            title="❌ Erro",
            description="Ocorreu um erro ao executar o comando. Tente novamente.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ==== FUNÇÕES AUXILIARES ====
def validate_environment():
    """Valida variáveis de ambiente obrigatórias"""
    missing_vars = []
    
    if not DISCORD_TOKEN:
        missing_vars.append("DISCORD_TOKEN")
    if not TWITCH_CLIENT_ID:
        missing_vars.append("TWITCH_CLIENT_ID")
    if not TWITCH_SECRET:
        missing_vars.append("TWITCH_SECRET")
    
    return missing_vars

async def graceful_shutdown():
    """Desligamento gracioso do bot"""
    log("🔄 Iniciando desligamento gracioso...")
    
    try:
        # Parar loops
        if check_clips_loop.is_running():
            check_clips_loop.stop()
        if check_live_status_loop.is_running():
            check_live_status_loop.stop()
        if maintenance_loop.is_running():
            maintenance_loop.stop()
        
        # Salvar cache final
        from utils.cache import save_cache
        save_cache()
        
        log("✅ Desligamento concluído")
        
    except Exception as e:
        log(f"Erro durante desligamento: {e}", "ERROR")

# ==== EXECUÇÃO PRINCIPAL ====
async def main():
    """Função principal do bot"""
    # Validar ambiente
    missing_vars = validate_environment()
    if missing_vars:
        log(f"❌ Variáveis de ambiente faltando: {', '.join(missing_vars)}", "ERROR")
        log("Configure o arquivo .env com as variáveis necessárias", "ERROR")
        return

    log("🚀 Iniciando Twitch Clips Bot v3.0...")
    log(f"⚙️ Configurações:")
    log(f"   🔄 Verificação: {CLIP_CHECK_SECONDS}s")
    log(f"   📅 Período: {CLIP_LOOKBACK_HOURS}h")
    log(f"   🎬 Vídeos: {'✅ Ativado' if CLIP_ATTACH_VIDEO else '❌ Desativado'}")
    log(f"   🐛 Debug: {'✅ Ativado' if DEBUG_MODE else '❌ Desativado'}")
    log(f"   ⏱️ Timeout: {CLIP_API_TIMEOUT}s")
    log(f"   📦 Tamanho máximo: {MAX_CLIP_SIZE_MB}MB")

    try:
        # Executar bot
        await bot.start(DISCORD_TOKEN)
    except KeyboardInterrupt:
        log("⚠️ Interrupção pelo usuário")
    except Exception as e:
        log(f"❌ Erro fatal: {e}", "ERROR")
    finally:
        await graceful_shutdown()
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("⚠️ Bot interrompido pelo usuário")
    except Exception as e:
        log(f"❌ Erro na execução: {e}", "ERROR")
