# city-ongs

# SITTS - Sistema Integrado de Transparência e Transferências Sociais

## Configuração do Ambiente

### Pré-requisitos
- Python 3.12+
- PostgreSQL
- Redis (para cache)
- Google Cloud SDK

### Configuração do Redis

#### Desenvolvimento Local
1. Instale o Redis:
```bash
# macOS
brew install redis

# Ubuntu
sudo apt-get install redis-server
```

2. Inicie o Redis:
```bash
# macOS
brew services start redis

# Ubuntu
sudo systemctl start redis-server
```

#### Produção (Google Cloud Platform)
1. Configure as credenciais do GCP:
```bash
gcloud auth login
gcloud config set project sitts-project
```

2. Execute o script de configuração do Redis:
```bash
chmod +x infra/setup_redis.sh
./infra/setup_redis.sh
```

3. Atualize o `app.yaml` com o IP do Redis fornecido pelo script.

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

## Cache

O sistema utiliza Redis para cache, melhorando a performance em:
- Estatísticas de contratos
- Relatórios frequentemente acessados
- Dados de prestações de contas

Os tempos de cache são:
- Dados estáticos: 1 hora
- Relatórios: 30 minutos
- Estatísticas: 5 minutos

Para limpar o cache manualmente:
```bash
poetry run python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

## Logs

Os logs são armazenados em:
- `logs/django.log`: Logs gerais da aplicação
- `logs/cache.log`: Logs específicos do cache

Em produção, os logs são enviados para o Cloud Logging do GCP.

