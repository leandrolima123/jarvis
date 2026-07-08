# Jarvis Alexa Skill (Alexa-Hosted)

Skill Alexa em Python (AWS Lambda) com Gemini via REST API. Compativel com Python 3.8 da Alexa-Hosted (sem dependencias pip).

## Estrutura (espelha AWS + git import)

```
jarvis-skill/
├── lambda/
│   ├── lambda_function.py
│   ├── requirements.txt
│   └── .env                 # so na console AWS (nao commitar)
├── skill-package/
│   ├── skill.json
│   └── interactionModels/custom/pt-BR.json
├── examples/
├── scripts/test_local.py
└── README.md
```

## Configuracao na AWS (Developer Console)

### Code

1. `lambda/lambda_function.py` — codigo principal
2. `lambda/requirements.txt` — vazio (sem pip extra)
3. `lambda/.env`:

```
GEMINI_API_KEY=sua_chave
GEMINI_MODEL=gemini-2.5-flash
```

4. **Deploy**

### Build

- Invocation name: **`modo jarvis`**
- Intent principal: `AskJarvisIntent` (slot `question`)
- **Build Model**

### Teste

```
abrir modo jarvis
o que é inteligência artificial
```

## Teste local

```bash
cp lambda/.env.example lambda/.env   # edite a chave
cd lambda && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt      # nada a instalar
cd ..
python scripts/test_local.py examples/alexa_launch_request.json
python scripts/test_local.py examples/alexa_intent_request.json
```

## Variaveis (.env na pasta lambda)

| Variavel | Obrigatoria | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Sim | — |
| `GEMINI_MODEL` | Nao | `gemini-2.5-flash` |
| `MAX_HISTORY_TURNS` | Nao | `20` |

## Git import

Repo: `https://github.com/leandrolima123/jarvis.git`

Import Git so funciona ao **criar skill nova**. Skill existente: copie arquivos manualmente na aba Code.
