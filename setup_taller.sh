#!/bin/bash

# Script de configuración completa para Burger Cloud (Taller Serverless)
#
# Este script configura toda la infraestructura necesaria para el taller:
# - Genera datos de prueba
# - Crea y puebla tablas DynamoDB
# - Despliega todos los servicios serverless

set -e

echo "=========================================="
echo "🍔 BURGER CLOUD - SETUP COMPLETO"
echo "=========================================="
echo ""

# Verificar que existe .env
if [ ! -f .env ]; then
    echo "❌ Error: No existe archivo .env"
    echo "   Copia .env.example y configúralo primero"
    exit 1
fi

# Cargar variables de entorno
export $(cat .env | grep -v '^#' | xargs)

echo "📋 Configuración cargada:"
echo "   AWS Account: $AWS_ACCOUNT_ID"
echo "   AWS Region: $AWS_REGION"
echo "   Org Name: $ORG_NAME"
echo ""

# Paso 1: Instalar dependencias de Python
echo "📦 Instalando dependencias de Python..."
pip3 install -q boto3 python-dotenv
echo "✅ Dependencias instaladas"
echo ""

# Paso 2: Generar datos de prueba
echo "🎲 Generando datos de prueba..."
cd data-setup
python3 DataGenerator.py
if [ $? -eq 0 ]; then
    echo "✅ Datos generados exitosamente"
else
    echo "❌ Error al generar datos"
    exit 1
fi
cd ..
echo ""

# Paso 3: Crear tablas y poblar con datos
echo "🗄️  Creando tablas DynamoDB y poblando datos..."
cd data-setup
python3 DataPoblator.py
if [ $? -eq 0 ]; then
    echo "✅ Tablas creadas y pobladas exitosamente"
else
    echo "❌ Error al crear o poblar tablas"
    exit 1
fi
cd ..
echo ""

# Paso 4: Verificar que serverless está instalado
if ! command -v serverless &> /dev/null; then
    echo "⚠️  Serverless Framework no encontrado. Instalando..."
    npm install -g serverless
fi

# Paso 5: Desplegar servicios
echo "🚀 Desplegando servicios serverless..."
echo ""

# Función para desplegar un servicio
deploy_service() {
    local service_name=$1
    local service_path=$2
    
    echo "📦 Desplegando $service_name..."
    cd $service_path
    serverless deploy --verbose
    if [ $? -eq 0 ]; then
        echo "✅ $service_name desplegado"
    else
        echo "❌ Error al desplegar $service_name"
        return 1
    fi
    cd - > /dev/null
    echo ""
}

# Desplegar en orden: primero los servicios que exportan Lambdas,
# luego workflow-service que las importa

# Desplegar kitchen-service (exporta validateStock)
deploy_service "Kitchen Service" "kitchen-service"

# Desplegar auth-service (exporta registerToken)
deploy_service "Auth Service" "auth-service"

# Desplegar workflow-service (importa validateStock y registerToken, crea tablas y Step Functions)
deploy_service "Workflow Service" "workflow-service"

# Desplegar order-service
deploy_service "Order Service" "order-service"

# Desplegar delivery-service
deploy_service "Delivery Service" "delivery-service"

echo "=========================================="
echo "✅ DESPLIEGUE COMPLETADO"
echo "=========================================="
echo ""
echo "🎉 Taller configurado exitosamente!"
echo ""
echo "📊 Tablas creadas:"
echo "   - $TABLE_USUARIOS"
echo "   - $TABLE_EMPLEADOS"
echo "   - $TABLE_LOCALES"
echo "   - $TABLE_PRODUCTOS"
echo "   - $TABLE_PEDIDOS"
echo "   - $TABLE_HISTORIAL_ESTADOS"
echo "   - $TABLE_TOKENS_USUARIOS"
echo ""
echo "🔗 API Endpoints desplegados. Revisa los outputs de Serverless arriba."
echo ""
echo "📖 Consulta GUIA_TALLER.md para instrucciones de uso."
echo ""
