# city-ongs

# SITTS - Sistema Integrado de Transparência e Transferências Sociais

## Configuração do Ambiente

### Pré-requisitos
- Python 3.12+
- PostgreSQL
- Google Cloud SDK

### Instalação
1. Clone o repositório
2. Instale as dependências:
```bash
poetry install
```

3. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite .env com suas configurações
```

4. Execute as migrações:
```bash
poetry run python manage.py migrate
```

5. Inicie o servidor:
```bash
poetry run python manage.py runserver
```

## Logs

Os logs são armazenados em:
- `logs/django.log`: Logs gerais da aplicação

Em produção, os logs são enviados para o Cloud Logging do GCP.

