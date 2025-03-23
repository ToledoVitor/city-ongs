#!/bin/bash

# Configuração de variáveis
PROJECT_ID="sitts-project"
REGION="southamerica-east1"  # São Paulo
NETWORK="default"
RANGE="10.0.0.0/28"
INSTANCE_NAME="redis-cache"

# Criar VPC connector para App Engine se conectar ao Redis
gcloud compute networks vpc-access connectors create redis-connector \
    --network $NETWORK \
    --region $REGION \
    --range $RANGE \
    --project $PROJECT_ID

# Criar instância do Redis
gcloud redis instances create $INSTANCE_NAME \
    --size=1 \
    --region=$REGION \
    --network=$NETWORK \
    --redis-version=redis_7_0 \
    --project=$PROJECT_ID \
    --tier=basic

# Obter informações da instância Redis
REDIS_IP=$(gcloud redis instances describe $INSTANCE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='get(host)')

echo "Redis instance created successfully!"
echo "Redis IP: $REDIS_IP"
echo "Redis Port: 6379"
echo ""
echo "Please update the following in your app.yaml:"
echo "env_variables:"
echo "    REDIS_HOST: '$REDIS_IP'"
echo "    REDIS_PORT: '6379'" 