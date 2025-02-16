FROM python:3.12

# Define o diretório de trabalho
WORKDIR /app

# Instala Poetry
RUN pip install --no-cache-dir poetry

# Copia apenas os arquivos do Poetry para evitar reinstalações desnecessárias
COPY pyproject.toml poetry.lock /app/

# Instala as dependências do projeto
RUN poetry config virtualenvs.create false && poetry install --no-root

# Copia o restante do projeto
COPY . /app/

# Expõe a porta 8080 para o Cloud Run
EXPOSE 8080

# Comando de inicialização
CMD ["poetry", "run", "gunicorn", "--bind", "0.0.0.0:8080", "core.wsgi"]
