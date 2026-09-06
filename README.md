# Calculadora BCP

MVP para estimar Pontos de Complexidade de Negócios (BCP) com HTML/CSS/JavaScript no front-end e Flask no back-end. A aplicação também pode classificar uma história automaticamente usando Gemini.

## Executar com Docker Compose

Pré-requisito: Docker e Docker Compose instalados no servidor.

```bash
docker compose up -d --build
```

Acesse `http://IP_DO_SERVIDOR:5000`.

Para acompanhar os logs:

```bash
docker compose logs -f
```

Para parar:

```bash
docker compose down
```

## Executar sem Docker

```bash
python -m venv .venv
.venv\\Scripts\\activate       # Windows
# source .venv/bin/activate     # Linux
pip install -r requirements.txt
python app.py
```

Acesse `http://localhost:5000`.

## Classificação automática

Configure uma chave da API Gemini no ambiente do container. Nunca coloque a chave no código ou no Git:

```bash
export GEMINI_API_KEY="sua-chave"
docker compose up -d --build
```

No Windows PowerShell:

```powershell
$env:GEMINI_API_KEY = "sua-chave"
docker compose up -d --build
```

Opcionalmente, altere o modelo com `GEMINI_MODEL`; o padrão é `gemini-2.5-flash`.

## Regra atual

O cálculo soma três dimensões, usando a sequência Fibonacci definida no documento:

- XS = 1
- S = 2
- M = 3
- L = 5
- XL = 8

Dimensões: regras de negócio, elementos de interface e integrações/fronteiras. O histórico atual fica apenas na memória do navegador; ainda não há banco de dados ou autenticação.
