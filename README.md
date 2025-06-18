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
- `/twitch-setup canal_twitch #canal_discord` - Configura monitoramento
- `/status` - Mostra status do monitoramento
  - `canal_twitch` pode ser apenas o nome ou uma URL do canal
  - Apenas quem possui permissão **Gerenciar Servidor** pode executar os comandos de configuração

#### Como funciona
1. O comando `/twitch-setup` define qual canal da Twitch **será** monitorado e em qual canal do Discord os clipes **serão** postados.
2. A cada `CLIP_CHECK_SECONDS` segundos o bot consulta a API da Twitch em busca dos 100 clipes mais recentes do canal (60s por padrão).
3. O bot filtra os clipes por data e envia apenas aqueles que ainda não foram postados.
4. **Você** pode usar `/status` para verificar se o monitoramento **está** ativo.
5. Caso o canal já esteja em live quando o bot iniciar, a notificação será enviada na primeira verificação.

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

Para executar os comandos de configuração do bot é necessário ter a permissão **Gerenciar Servidor** ou ser administrador.


## Estrutura do Projeto

```
twitch-bot/
├── bot.py            # Código principal do bot
├── requirements.txt  # Dependências Python
├── .env.example      # Exemplo de variáveis de ambiente
└── README.md         # Este arquivo
```

## Contribuição

Sinta-se livre para contribuir com melhorias, correções de bugs ou novas funcionalidades!

## Licença

MIT License
