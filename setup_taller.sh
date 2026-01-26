#!/bin/bash
set -e

echo "🍔 Iniciando Setup del Taller Burger Cloud..."

# 1. Instalar dependencias de Serverless
echo "📦 Instalando plugins de Serverless..."
if ! command -v sls &> /dev/null; then
    echo "Serverless Framework no encontrado. Instalando..."
    npm install -g serverless
fi

sls plugin install -n serverless-python-requirements
sls plugin install -n serverless-step-functions

# 2. Desplegar con Compose
echo "🚀 Desplegando servicios con Serverless Compose (Stage: dev)..."
npx serverless deploy --verbose

# 3. Poblar Datos
echo "🌱 Poblando base de datos con usuarios y productos de prueba..."
export STAGE=dev
# Ejecutamos seed_data desde root
pip3 install boto3
python3 seed_data.py

echo "✅ Setup Completo!"
echo "---------------------------------------------------"
echo "Usuarios de prueba:"
echo " - Cliente: cliente1 / password123"
echo " - Cocina: cocinero1 / password123"
echo " - Driver: driver1 / password123"
echo "---------------------------------------------------"
echo "Obtén las URLs del output de 'sls deploy' arriba."
