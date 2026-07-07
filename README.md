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
│   └── test_local.py           # Teste local do handler
├── skill-package/
│   ├── skill.json              # Manifest da skill
│   └── interactionModels/custom/pt-BR.json
└── examples/                   # Payloads JSON para testes
```

Compatível com [import Git de Alexa-Hosted Skill](https://developer.amazon.com/en-US/docs/alexa/hosted-skills/alexa-hosted-skills-git-import.html).

## Importar na Alexa Developer Console

1. Publique este repositório no **GitHub** (público)
2. Acesse [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask)
3. **Create Skill** → Custom → **Alexa-Hosted (Python)**
4. Clique em **Import skill** e cole a URL `.git` do repositório
5. Idioma padrão: **Portuguese (BR)**
6. Após importar, vá em **Code** → **Environment Variables** e adicione:
   - `GEMINI_API_KEY` = sua chave ([Google AI Studio](https://aistudio.google.com/apikey))
   - `GEMINI_MODEL` = `gemini-2.0-flash` (opcional)
   - `MAX_HISTORY_TURNS` = `20` (opcional)
7. Clique em **Deploy** e teste no simulador

## Teste local

```bash
cd lambda
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export GEMINI_API_KEY=sua_chave

python test_local.py ../examples/alexa_launch_request.json
python test_local.py ../examples/alexa_intent_request.json
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

A skill responde a: **"Alexa, abra Jarvis"**

Exemplos:
- "Alexa, abra Jarvis e pergunte o que é inteligência artificial"
- "Alexa, abra Jarvis"

## Variáveis de ambiente (Lambda)

| Variável | Obrigatória | Default | Descrição |
|----------|-------------|---------|-----------|
| `GEMINI_API_KEY` | Sim | — | Chave da API Gemini |
| `GEMINI_MODEL` | Não | `gemini-2.0-flash` | Modelo Gemini |
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
