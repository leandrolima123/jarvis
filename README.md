# Jarvis Alexa Skill (Alexa-Hosted)

Skill Alexa customizada em Python (AWS Lambda) que processa perguntas com Google Gemini e mantém histórico de conversa em memória (até 20 turnos por sessão).

## Estrutura do projeto

```
jarvis-skill/
├── lambda/
│   ├── lambda_function.py      # Handler Lambda (entry point)
│   ├── gemini_service.py       # Integração Gemini
│   ├── conversation_cache.py   # Cache em memória
│   ├── requirements.txt
│   └── (somente codigo Lambda)
├── scripts/
│   └── test_local.py           # Teste local do handler
├── skill-package/
│   ├── skill.json              # Manifest da skill
│   └── interactionModels/custom/pt-BR.json
└── examples/                   # Payloads JSON para testes
```

Compatível com [import Git de Alexa-Hosted Skill](https://developer.amazon.com/en-US/docs/alexa/hosted-skills/alexa-hosted-skills-git-import.html).

## Importar na Alexa Developer Console

> **Importante:** import Git funciona apenas ao **criar skill nova**. Se voce ja tem `amzn1.ask.skill.bd6515fd-...`, use a aba **Code** para colar o codigo (nao tente importar de novo).

1. Repo publico: `https://github.com/leandrolima123/jarvis.git`
2. [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask) → **Create Skill** (nova)
3. Custom → **Alexa-Hosted (Python)** → **Import skill**
4. Cole a URL `.git` exata acima
5. Idioma padrao: **Portuguese (BR)** (deve existir `skill-package/interactionModels/custom/pt-BR.json`)
6. **Code** → **Environment Variables** → `GEMINI_API_KEY`
7. **Deploy** → teste no simulador

### Erro "tente novamente mais tarde"

| Verificacao | Status do seu repo |
|-------------|-------------------|
| Repo publico | OK |
| Tamanho < 50 MB | OK (~150 KB) |
| `lambda/lambda_function.py` | OK |
| `skill-package/skill.json` | OK (corrigido) |
| Idioma pt-BR na criacao | Voce precisa selecionar |
| Skill ja existente | **Provavel causa** — import nao atualiza skill existente |

**Alternativa (recomendada para voce):** abra a skill existente → aba **Code** → substitua arquivos de `lambda/` → **Deploy** → **Build Model**.

### Skill ja existente

1. **Code** → copie arquivos de `lambda/` do GitHub
2. **Environment Variables** → `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-2.5-flash`
3. **Deploy**
4. **Build** → invocation `assistente jarvis` → **Build Model**

## Teste local

```bash
cd lambda
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..

export GEMINI_API_KEY=sua_chave

python scripts/test_local.py examples/alexa_launch_request.json
python scripts/test_local.py examples/alexa_intent_request.json
```

## Fluxo

```
Alexa → AWS Lambda (lambda_handler) → ConversationCache → Gemini → resposta JSON
```

- **LaunchRequest** → boas-vindas
- **AskJarvisIntent** → pergunta processada com histórico
- **AMAZON.StopIntent** / **SessionEndedRequest** → limpa cache da sessão
- **AMAZON.HelpIntent** → instruções de uso

O histórico é indexado por `session.sessionId`. Cada sessão mantém até 20 pares pergunta/resposta.

## Invocation name

A skill se chama **Jarvis**, mas o nome de invocação é **`assistente jarvis`** (a Amazon não permite usar o mesmo nome da skill).

Exemplos:
- "Alexa, abra assistente jarvis"
- "Alexa, abra assistente jarvis e pergunte o que é inteligência artificial"

## Variáveis de ambiente (Lambda)

| Variável | Obrigatória | Default | Descrição |
|----------|-------------|---------|-----------|
| `GEMINI_API_KEY` | Sim | — | Chave da API Gemini |
| `GEMINI_MODEL` | Não | `gemini-2.5-flash` | Modelo Gemini |
| `MAX_HISTORY_TURNS` | Não | `20` | Turnos em cache por sessão |

Configure em **Alexa Developer Console → Code → Environment Variables**.

## Limitações

- Cache em memória por instância Lambda (pode resetar entre invocações frias ou instâncias diferentes)
- Para persistência robusta, migrar cache para DynamoDB (fase futura)
- Respostas otimizadas para voz (curtas, sem markdown)

## ASK CLI (opcional)

```bash
ask deploy
```

Requer [ASK CLI](https://developer.amazon.com/en-US/docs/alexa/smapi/ask-cli-intro.html) configurado com a skill importada.
