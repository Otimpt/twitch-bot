# Bot Discord - Twitch Clips

Bot do Discord para enviar automaticamente clips recentes da Twitch.

## Pré-requisitos
- Python 3.10 ou superior
- Conta no Discord e na Twitch para obter as credenciais
## Funcionalidades

### 📺 Integração Twitch
- Monitoramento automático de novos clips
- Postagem automática no Discord
- Configuração por servidor
- Checagem a cada 5 minutos

## Comandos

### Twitch
- `/twitch_setup canal_twitch #canal_discord` - Configura monitoramento
- `/twitch_status` - Mostra status do monitoramento

#### Como funciona
1. O comando `/twitch_setup` define qual canal da Twitch sera monitorado e em qual canal do Discord os clips serao postados.
2. A cada `CLIP_CHECK_SECONDS` segundos o bot consulta a API da Twitch em busca de novos clips do canal configurado (30s por padrão).
3. Sempre que um clip novo for encontrado, ele é enviado ao Discord com o link e um embed contendo os detalhes.
4. Voce pode usar `/twitch_status` para verificar se o monitoramento esta ativo.

### Utilidades
- `/ping` - Verifica latência do bot
- `/help` - Lista todos os comandos

## Configuração

1. **Clone o repositório**
2. **Instale as dependências com Python 3:**
   ```bash
   python3 -m pip install -r requirements.txt
   ```

3. **Configure as variáveis de ambiente:**
   - Copie `.env.example` para `.env`
   - Defina `DISCORD_TOKEN`, `TWITCH_CLIENT_ID` e `TWITCH_SECRET`
   - Opcionalmente ajuste `CLIP_CHECK_SECONDS`, `CLIP_LOOKBACK_HOURS`, `CLIP_SHOW_DETAILS`, `CLIP_ATTACH_VIDEO` e `CLIP_API_TIMEOUT`

4. **Execute o bot usando Python 3:**
   ```bash
   python3 bot.py
   ```

## Deploy

### Render.com (Gratuito)
1. Conecte seu repositório GitHub
2. Configure as variáveis de ambiente no painel
3. Deploy automático!

### Fly.io
1. Instale o CLI do Fly.io
2. Execute `fly launch`
3. Configure as variáveis com `fly secrets set`

## Credenciais Necessárias

### Discord
1. Acesse https://discord.com/developers/applications
2. Crie uma nova aplicação
3. Vá em "Bot" e copie o token
4. Defina esse valor em `DISCORD_TOKEN`

### Twitch
1. Acesse https://dev.twitch.tv/console
2. Registre uma nova aplicação
3. Copie Client ID e Client Secret
4. Defina esses valores em `TWITCH_CLIENT_ID` e `TWITCH_SECRET`
5. Demais variáveis de configuração estão documentadas em `.env.example` e no passo de configuração.


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
