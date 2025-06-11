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

### Utilidades
- `/ping` - Verifica latência do bot
- `/help` - Lista todos os comandos

## Configuração

1. **Clone o repositório**
2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure as variáveis de ambiente:**
   - Copie `.env.example` para `.env`
   - Preencha com suas credenciais

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
1. Instale o CLI do Fly.io
2. Execute `fly launch`
3. Configure as variáveis com `fly secrets set`

## Credenciais Necessárias

### Discord
1. Acesse https://discord.com/developers/applications
2. Crie uma nova aplicação
3. Vá em "Bot" e copie o token

### Twitch
1. Acesse https://dev.twitch.tv/console
2. Registre uma nova aplicação
3. Copie Client ID e Client Secret

## Estrutura do Projeto

```
bot-discord/
├── bot.py              # Código principal do bot
├── requirements.txt    # Dependências Python
├── .env.example       # Exemplo de variáveis de ambiente
├── README.md          # Este arquivo
└── .gitignore         # Arquivos ignorados pelo Git
```

## Contribuição

Sinta-se livre para contribuir com melhorias, correções de bugs ou novas funcionalidades!

## Licença

MIT License
