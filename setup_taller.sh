#!/bin/bash

# Script de configuración completa para Burger Cloud (Taller Serverless)
#
# Uso:
#   ./setup_taller.sh           - Setup completo (datos + despliegue)
#   ./setup_taller.sh --deploy  - Solo desplegar servicios
#   ./setup_taller.sh --delete  - Eliminar todos los recursos AWS
#   ./setup_taller.sh --help    - Mostrar ayuda

set -e

# ==============================================
# FUNCIONES AUXILIARES
# ==============================================

show_help() {
    echo "=========================================="
    echo "🍔 BURGER CLOUD - SETUP SCRIPT"
    echo "=========================================="
    echo ""
    echo "Uso: $0 [OPCIÓN]"
    echo ""
    echo "Opciones:"
    echo "  (sin opción)    Setup completo: datos + despliegue"
    echo "  --deploy        Solo desplegar servicios serverless"
    echo "  --delete        Eliminar todos los recursos AWS"
    echo "  --help          Mostrar esta ayuda"
    echo ""
}

load_env() {
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
}

setup_data() {
    echo "=========================================="
    echo "🍔 BURGER CLOUD - SETUP DE DATOS"
    echo "=========================================="
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
}

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

deploy_services() {
    echo "=========================================="
    echo "🚀 DESPLEGANDO SERVICIOS"
    echo "=========================================="
    echo ""
    
    # Verificar que serverless está instalado
    if ! command -v serverless &> /dev/null; then
        echo "⚠️  Serverless Framework no encontrado. Instalando..."
        npm install -g serverless
    fi
    
    # Desplegar en orden: primero los servicios que exportan Lambdas,
    # luego los que las importan
    
    # Desplegar kitchen-service (exporta validateStock)
    deploy_service "Kitchen Service" "kitchen-service"
    
    # Desplegar auth-service (exporta registerToken)
    deploy_service "Auth Service" "auth-service"
    
    # Desplegar workflow-service (NO crea tablas, solo configuración)
    deploy_service "Workflow Service" "workflow-service"
    
    # Desplegar order-service
    deploy_service "Order Service" "order-service"
    
    # Desplegar delivery-service
    deploy_service "Delivery Service" "delivery-service"
    
    echo "=========================================="
    echo "✅ DESPLIEGUE COMPLETADO"
    echo "=========================================="
    echo ""
    echo "🔗 API Endpoints desplegados. Revisa los outputs de Serverless arriba."
    echo ""
}

remove_service() {
    local service_name=$1
    local service_path=$2
    
    echo "🗑️  Eliminando $service_name..."
    cd $service_path
    serverless remove --verbose || true
    cd - > /dev/null
    echo ""
}

delete_tables() {
    echo "🗑️  Eliminando tablas DynamoDB..."
    
    local tables=(
        "$TABLE_USUARIOS"
        "$TABLE_EMPLEADOS"
        "$TABLE_LOCALES"
        "$TABLE_PRODUCTOS"
        "$TABLE_PEDIDOS"
        "$TABLE_HISTORIAL_ESTADOS"
        "$TABLE_TOKENS_USUARIOS"
    )
    
    for table in "${tables[@]}"; do
        echo "   Eliminando tabla: $table"
        aws dynamodb delete-table --table-name "$table" --region "$AWS_REGION" 2>/dev/null || \
            echo "   ⚠️  Tabla $table no existe o ya fue eliminada"
    done
    
    echo "✅ Tablas DynamoDB eliminadas"
    echo ""
}

delete_all() {
    echo "=========================================="
    echo "🗑️  ELIMINANDO TODOS LOS RECURSOS"
    echo "=========================================="
    echo ""
    
    read -p "⚠️  ¿Estás seguro de eliminar TODOS los recursos? (s/N): " confirm
    if [[ ! $confirm =~ ^[sS]$ ]]; then
        echo "Operación cancelada"
        exit 0
    fi
    
    echo ""
    
    # Eliminar servicios serverless (en orden inverso)
    remove_service "Delivery Service" "delivery-service"
    remove_service "Order Service" "order-service"
    remove_service "Workflow Service" "workflow-service"
    remove_service "Auth Service" "auth-service"
    remove_service "Kitchen Service" "kitchen-service"
    
    # Eliminar tablas DynamoDB
    delete_tables
    
    echo "=========================================="
    echo "✅ ELIMINACIÓN COMPLETADA"
    echo "=========================================="
    echo ""
}

full_setup() {
    echo "=========================================="
    echo "🍔 BURGER CLOUD - SETUP COMPLETO"
    echo "=========================================="
    echo ""
    
    load_env
    setup_data
    deploy_services
    
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
    echo "📖 Consulta GUIA_TALLER.md para instrucciones de uso."
    echo ""
}

# ==============================================
# MAIN
# ==============================================

case "${1:-}" in
    --help)
        show_help
        ;;
    --deploy)
        load_env
        deploy_services
        ;;
    --delete)
        load_env
        delete_all
        ;;
    "")
        full_setup
        ;;
    *)
        echo "❌ Opción desconocida: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
