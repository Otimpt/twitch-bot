# Bot Discord - Jogos e Twitch

Bot Discord com jogos de mesa (xadrez) e integração automática com clips da Twitch.

## Funcionalidades

### 🎮 Jogos
- **Xadrez completo** com validação de movimentos
- Sistema de turnos
- Comandos intuitivos com slash commands (/)

### 📺 Integração Twitch
- Monitoramento automático de novos clips
- Postagem automática no Discord
- Configuração por servidor
- Checagem a cada 15 segundos (configurável)

## Comandos

### Jogos
- `/xadrez @oponente` - Inicia um jogo de xadrez
- `/mover e2e4` - Faz uma jogada (formato UCI)
- `/tabuleiro` - Mostra o estado atual do tabuleiro
- `/desistir` - Desiste do jogo atual
- `/jogos` - Lista todos os jogos disponíveis

### Twitch
- `/twitch_setup canal_twitch #canal_discord` - Configura monitoramento
- `/twitch_status` - Mostra status do monitoramento

#### Como funciona
1. O comando `/twitch_setup` define qual canal da Twitch sera monitorado e em qual canal do Discord os clips serao postados.
2. A cada 15 segundos (por padrão) o bot consulta a API da Twitch em busca de novos clips do canal configurado.
3. Todas as páginas de resultados (até 100 clips) são percorridas para que nenhum clip recente fique de fora, mesmo em canais grandes.
4. Somente clips criados após a configuração (por padrão, nas últimas 2 horas) são enviados. A busca usa `started_at` e compara horários em UTC, garantindo que até clips feitos segundos atrás sejam detectados sem repetir conteúdo antigo.
5. O bot mantém o horário do último clip processado. Se nenhuma novidade for encontrada, o marcador não avança, evitando perder clips que demoram a aparecer na API da Twitch.
6. Sempre que um clip novo for encontrado, um embed com os detalhes e o link sera publicado automaticamente no Discord.
7. Voce pode usar `/twitch_status` para verificar se o monitoramento esta ativo.

### Utilidades
- `/ping` - Verifica latência do bot
- `/help` - Lista todos os comandos

## Configuração

1. **Clone o repositório**
2. **Prepare o ambiente Python** (recomendado Python 3.10 ou superior):
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure as variáveis de ambiente:**
   - Copie `.env.example` para `.env`
   - Preencha `DISCORD_TOKEN`, `TWITCH_CLIENT_ID` e `TWITCH_SECRET` com suas credenciais
   - (Opcional) Ajuste `CLIP_LOOKBACK_HOURS` para definir quantas horas de clips recentes serão enviados ao configurar
   - (Opcional) Ajuste `CLIP_CHECK_SECONDS` para controlar o intervalo de verificação de novos clips (padrão 15s)
   - (Opcional) Defina `CLIP_SHOW_DETAILS` como `0` para esconder views, criador e data dos embeds

4. **Execute o bot:**
   ```bash
   python bot.py
   ```

## Deploy

### Render.com (Gratuito)
1. Conecte seu repositório GitHub
2. Configure as variáveis de ambiente no painel
3. Deploy automático!

### Fly.io
1. Instale o CLI do Fly.io: `curl -L https://fly.io/install.sh | sh`
2. Faça login com `fly auth login`
3. Rode `fly launch --no-deploy` para criar o app e o arquivo `fly.toml`
4. Defina as variáveis de ambiente como segredos:
   ```bash
   fly secrets import < .env
   ```
   ou defina manualmente com `fly secrets set VAR=valor`
5. Por fim, execute `fly deploy` para enviar o contêiner ao Fly.io

## Credenciais Necessárias

### Discord
1. Acesse https://discord.com/developers/applications
2. Crie uma nova aplicação
3. Vá em "Bot" e copie o token
4. Defina esse valor em `DISCORD_TOKEN`

### Twitch
1. Acesse https://dev.twitch.tv/console
2. Registre uma nova aplicação
3. Se o console mostrar apenas credenciais para OAuth com PKCE (sem Client Secret), abra a página da aplicação e procure o campo **OAuth Client Type** ou **Application Type**. Selecione **Confidential** (também chamado de Server‑side) e salve.
4. Após salvar essa configuração, o botão **New Secret** aparecerá na aba "Manage". Gere o segredo e anote o valor.
5. Copie o Client ID e o Client Secret gerado e defina-os em `TWITCH_CLIENT_ID` e `TWITCH_SECRET`
6. (Opcional) Defina `CLIP_LOOKBACK_HOURS` para controlar quantas horas de clips recentes serão enviados ao configurar
7. (Opcional) Defina `CLIP_CHECK_SECONDS` para ajustar o intervalo de checagem de novos clips (padrão 15s)
8. (Opcional) Defina `CLIP_SHOW_DETAILS` como `0` para ocultar views, criador e data dos embeds

## Permissões Necessárias

Ao convidar o bot para o servidor, conceda pelo menos as seguintes permissões:
- **Ver Canais**
- **Enviar Mensagens**
- **Inserir Links** (Embed Links)
- **Ler Histórico de Mensagens** (opcional, mas recomendado)
- **Usar Comandos de Aplicação**


## Estrutura do Projeto

```
bot-discord/
├── bot.py            # Código principal do bot
├── requirements.txt  # Dependências Python
├── .env.example      # Exemplo de variáveis de ambiente
└── README.md         # Este arquivo
```

## Contribuição

Sinta-se livre para contribuir com melhorias, correções de bugs ou novas funcionalidades!

## Licença

MIT License
