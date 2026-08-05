# JobApplicationIASystem

## Visão geral

Projeto de automação de descoberta, avaliação e registro de vagas baseado em FastAPI, scraping e um workflow n8n. O sistema coleta vagas, processa detalhes de cada vaga, avalia aderência com um currículo canônico e registra resultados aprovados em Google Sheets.

## Arquitetura do código

### Componentes principais

- `app/main.py`
  - API FastAPI responsável por expor endpoints de pesquisa e processamento de vaga.
  - Utiliza `ResumeRepository` para carregar perfis de currículo canônicos.
- `app/config/settings.py`
  - Configurações do aplicativo (`APP_NAME`, ambiente, nível de log, perfil padrão, thresholds).
- `app/models/`
  - `api.py`: modelos de requisição e resposta da API.
  - `job.py`: modelos de descrição de vaga, metadados e resultado de busca.
  - `resume.py`: modelos de perfil de currículo com experiência, educação e certificações.
- `app/scraper/`
  - `base.py`: contrato abstrato para scrapers de vagas.
  - `linkedin.py`: scraper real usando Playwright, BeautifulSoup e HTTPX para capturar detalhes de vagas do LinkedIn.
  - `data_mock.py`: scraper mock para testes e desenvolvimento offline.
- `app/storage/resume_repository.py`
  - Gestão de perfis de currículo em memória e persistência JSON no diretório `data/`.
- `scripts/ingest_resumes.py`
  - Script de ingestão que cria perfis de currículo e salva `data/resume_<profile_id>.json`.
- `data/`
  - Armazena os perfis de currículo gerados como JSON.

## Endpoints da API

### `POST /api/v1/search-jobs`

Retorna uma lista de vagas encontradas pelo scraper.

Request body esperado:

```json
{
  "keywords": "Technical Support",
  "location": "Brazil",
  "limit": 15
}
```

Resposta:

- `count`: número de vagas retornadas
- `jobs`: lista de `job_id`, `job_url`, `title`, `company`

### `POST /api/v1/process-job`

Processa uma vaga específica e retorna detalhes completos do job scraping.

Request body esperado:

```json
{
  "job_url": "...",
  "job_id": "...",
  "profile_id": "support_ops_engineer"
}
```

Resposta:

- `job_id`
- `job_url`
- `company`
- `title`
- `description_text`
- `company_url`
- `metadata`

### `GET /health`

Retorna estado da aplicação e ambiente ativo.

## Como os perfis são gerenciados

- `scripts/ingest_resumes.py` cria dois perfis de currículo:
  - `software_engineer_java`
  - `support_ops_engineer`
- O `ResumeRepository` carrega e salva esses perfis no diretório `data/`.
- O `profile_id` padrão usado pela API é `support_ops_engineer`.

## Fluxo do workflow n8n

O workflow `Pipeline Autônomo de Vagas - IA e Workspace no n8n` orquestra a automação:

1. `Schedule - Every 6 Hours`
   - Dispara a cada 6 horas.
2. `FastAPI: Search Jobs1`
   - Faz `POST` para `http://host.docker.internal:8000/api/v1/search-jobs`.
   - Busca vagas com `keywords`, `location` e `limit` definidos.
3. `Code in JavaScript`
   - Converte a resposta em múltiplos itens de vaga separados.
4. `FastAPI: Process Job Dynamic`
   - Faz `POST` para `http://host.docker.internal:8000/api/v1/process-job` para cada vaga.
5. `Basic LLM Chain` + `Google Gemini Chat Model`
   - Avalia o job contra o currículo fixo no prompt.
   - Gera JSON contendo:
     - `vaga_titulo`
     - `empresa`
     - `score`
     - `status_recomendacao`
     - `company_url`
6. `Code in JavaScript1`
   - Converte a resposta de texto do LLM em JSON válido.
7. `If`
   - Verifica se `score >= 80`.
8. `Append row in sheet`
   - Registra vagas aprovadas em um Google Sheets.

### Observações sobre o workflow do n8n

- O prompt LLM está configurado para agir como um recrutador sênior e retornar apenas um JSON válido.
- O branch de `If` garante que somente vagas com score alto sejam documentadas.
- Existem nós adicionais não conectados diretamente (`Create a document`, `Get a document`, `Merge`), indicando possibilidade de evolução para geração de documentos ou combinação de dados.

## Requisitos e execução

### Dependências principais esperadas

Embora `requirements.text` esteja vazio no repositório, o projeto exige ao menos:

- `fastapi`
- `uvicorn`
- `httpx`
- `playwright`
- `beautifulsoup4`
- `pydantic`
- `pydantic-settings`

### Executando localmente

1. Instale dependências.
2. Execute o script de ingestão de perfis:

```bash
python scripts/ingest_resumes.py
```

3. Inicie a API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Importe o workflow n8n e configure:
   - Credenciais Google Sheets / Google Docs
   - URL de chamada HTTP para a API (`http://host.docker.internal:8000` se n8n estiver em Docker)

## Melhorias futuras

- Consolidar dependências em `requirements.txt` ou `pyproject.toml`.
- Conectar e ativar nós Google Docs e `Merge` no workflow n8n.
- Adicionar endpoint de criação de currículo dinâmico ou exportação de documentos.
- Implementar scraping real com autenticação e tratamento robusto de bloqueios LinkedIn.
- Adicionar mais plataformas para scraping

## Resumo

Este projeto une:

- backend Python com FastAPI,
- scraping de vagas LinkedIn,
- perfis de currículo canônicos,
- IA para avaliação de aderência,
- automação de fluxo n8n,
- integração com Google Sheets.


