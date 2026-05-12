# city-ongs

# SITTS - Sistema Integrado de Transparência e Transferências Sociais

## Configuração do Ambiente

### Pré-requisitos
- Docker e Docker Compose
- [uv](https://docs.astral.sh/uv/) (apenas se for rodar fora do container)
- Google Cloud SDK (para deploy)

### Setup com Docker (recomendado)

1. Clone o repositório
2. Copie o arquivo de ambiente:
```bash
cp .env.example .env
# Edite .env com suas configurações
```

3. Suba o banco e a aplicação:
```bash
make up
# ou: docker compose up --build
```

4. Em outro terminal, rode as migrações:
```bash
docker compose exec app python manage.py migrate
```

A aplicação estará disponível em http://localhost:8000.

### Setup local (sem Docker)

1. Instale as dependências:
```bash
uv sync
```

2. Configure o `.env` apontando para um Postgres acessível.

3. Rode as migrações e o servidor:
```bash
make migrate
make run
```

## Logs

Os logs são armazenados em:
- `logs/django.log`: Logs gerais da aplicação

Em produção, os logs são enviados para o Cloud Logging do GCP.
