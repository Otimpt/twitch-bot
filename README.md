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
- Número de páginas da API configurável (padrão 1), do mais novo para o mais antigo

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
2. A cada 15 segundos (padrão) o bot consulta a API da Twitch em busca de novos clips do canal configurado.
3. Para compensar atrasos da API, o bot revisita os últimos `CLIP_API_LAG_SECONDS` segundos e também aceita clipes que apareçam um pouco antes do último horário conhecido. Assim, mesmo que a Twitch demore para listar um clip, ele não será perdido. O tempo máximo de espera de cada requisição pode ser ajustado via `CLIP_API_TIMEOUT`. Por padrão apenas a primeira página é consultada, mas `CLIP_MAX_PAGES` pode aumentar esse limite.
4. Somente clips criados após a configuração (por padrão, nas últimas 2 horas) são enviados. A busca usa `started_at` em UTC para detectar até clips feitos segundos atrás sem repetir conteúdo antigo.
5. O horário do último clip processado só avança quando um clip realmente mais novo é encontrado, garantindo que itens atrasados ainda sejam considerados.
6. Clips criados no mesmo segundo do último processado ou alguns segundos antes também são enviados, evitando lacunas.
7. Sempre que um clip novo for encontrado, o bot envia o link do clip, o que faz o Discord gerar automaticamente a prévia em vídeo. As informações sobre views, autor e data são adicionadas no texto e, se `CLIP_ATTACH_VIDEO` estiver definido como `1`, o vídeo também é enviado como anexo.
8. Os clips são enviados do mais novo para o mais antigo, reduzindo a espera por conteúdo recente.
9. Voce pode usar `/twitch_status` para verificar se o monitoramento esta ativo.
10. O monitoramento continua funcionando mesmo se `/twitch_setup` for executado novamente,
    pois o bot lida com a troca de configurações sem interromper a verificação.

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
   - (Opcional) Ajuste `CLIP_MAX_PAGES` para definir quantas páginas da API são consultadas a cada ciclo (padrão 1)
   - (Opcional) Defina `CLIP_SHOW_DETAILS` como `0` para esconder views, criador e data dos embeds
   - (Opcional) Ajuste `CLIP_API_LAG_SECONDS` para considerar atrasos da API (padrão 15s)
   - (Opcional) Ajuste `CLIP_API_TIMEOUT` para definir o tempo limite das requisições à API (padrão 10s)
   - (Opcional) Defina `CLIP_ATTACH_VIDEO` como `1` para anexar o vídeo do clip no chat em vez de apenas o thumbnail

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
5. Por fim, execute `fly deploy` para enviar o contêiner ao Fly.io.
   - O arquivo `fly.toml` já inclui a seção `[build]` apontando para o
     `Dockerfile`, garantindo que a imagem seja montada com o Docker e não com o
     Nixpacks.
   - Caso o build falhe com mensagens do **mise** ao tentar instalar o Python,
     rode `fly deploy --dockerfile Dockerfile` para forçar explicitamente o uso
     do Dockerfile e evitar esses erros.

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
8. (Opcional) Defina `CLIP_MAX_PAGES` para escolher quantas páginas da API serão consultadas (padrão 1)
9. (Opcional) Defina `CLIP_SHOW_DETAILS` como `0` para ocultar views, criador e data dos embeds
10. (Opcional) Ajuste `CLIP_API_LAG_SECONDS` para compensar possíveis atrasos da API (padrão 15s)
11. (Opcional) Ajuste `CLIP_API_TIMEOUT` para definir o tempo limite das requisições (padrão 10s)
12. (Opcional) Defina `CLIP_ATTACH_VIDEO` como `1` para enviar o vídeo do clip como anexo (pode aumentar o uso de dados)

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
