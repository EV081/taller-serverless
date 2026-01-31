#!/bin/bash
set -Eeuo pipefail

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# -------- Utilidades --------
die() { echo -e "${RED}❌ $*${NC}"; exit 1; }
log() { echo -e "$*"; }

show_menu() {
  echo "=========================================="
  echo "🍔 BURGER CLOUD - SETUP BACKEND"
  echo "=========================================="
  echo ""
  echo "Selecciona una opción:"
  echo ""
  echo "  1) 🏗️  Desplegar todo (Infraestructura + Microservicios)"
  echo "  2) 🗑️  Eliminar todo (Microservicios + Infraestructura)"
  echo "  3) 📊 Solo crear infraestructura y poblar datos"
  echo "  4) 🚀 Solo desplegar microservicios"
  echo "  5) ❌ Salir"
  echo ""
}

check_env() {
  if [[ ! -f .env ]]; then
    echo -e "${YELLOW}⚠️  Archivo .env no encontrado${NC}"
    echo "Copia .env.example a .env y configura tus variables."
    exit 1
  fi
  
  # Carga segura de variables del .env
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a

  # Validaciones mínimas
  : "${AWS_ACCOUNT_ID:?Falta AWS_ACCOUNT_ID en .env}"
  : "${ORG_NAME:?Falta ORG_NAME en .env}"
  : "${TABLE_USUARIOS:?Falta TABLE_USUARIOS en .env}"
  : "${TABLE_EMPLEADOS:?Falta TABLE_EMPLEADOS en .env}"
  : "${TABLE_LOCALES:?Falta TABLE_LOCALES en .env}"
  : "${TABLE_PRODUCTOS:?Falta TABLE_PRODUCTOS en .env}"
  : "${TABLE_PEDIDOS:?Falta TABLE_PEDIDOS en .env}"
  : "${TABLE_HISTORIAL_ESTADOS:?Falta TABLE_HISTORIAL_ESTADOS en .env}"
  : "${TABLE_TOKENS_USUARIOS:?Falta TABLE_TOKENS_USUARIOS en .env}"

  export AWS_REGION="${AWS_REGION:-us-east-1}"
}

check_prereqs() {
  command -v aws >/dev/null 2>&1 || die "AWS CLI no encontrado. Instálalo y ejecuta 'aws configure'."
  command -v python3 >/dev/null 2>&1 || die "python3 no encontrado."
  command -v pip3 >/dev/null 2>&1 || die "pip3 no encontrado."
  command -v serverless >/dev/null 2>&1 || die "Serverless Framework no encontrado. Instala con: npm i -g serverless"
}

deploy_infrastructure() {
  echo -e "\n${BLUE}=========================================${NC}"
  echo -e "${BLUE}🍔 BURGER CLOUD - SETUP DE DATOS${NC}"
  echo -e "${BLUE}=========================================${NC}\n"
  
  # Paso 1: Instalar dependencias de Python
  echo -e "${YELLOW}📦 Instalando dependencias de Python...${NC}"
  pip3 install -q boto3 python-dotenv 2>/dev/null || pip3 install boto3 python-dotenv
  echo -e "${GREEN}✅ Dependencias instaladas${NC}\n"
  
  # Paso 2: Generar datos de prueba
  if [[ -f "data-setup/DataGenerator.py" ]]; then
    echo -e "${BLUE}🎲 Generando datos de prueba...${NC}"
    cd data-setup
    python3 DataGenerator.py
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✅ Datos generados exitosamente${NC}"
    else
      echo -e "${RED}❌ Error al generar datos${NC}"
      exit 1
    fi
    cd ..
    echo ""
  else
    echo -e "${YELLOW}ℹ️  No se encontró DataGenerator.py. Saltando generación de datos.${NC}\n"
  fi
  
  # Paso 3: Crear tablas y poblar con datos
  if [[ -f "data-setup/DataPoblator.py" ]]; then
    echo -e "${BLUE}🗄️  Creando tablas DynamoDB y poblando datos...${NC}"
    cd data-setup
    python3 DataPoblator.py
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✅ Tablas creadas y pobladas exitosamente${NC}"
    else
      echo -e "${RED}❌ Error al crear o poblar tablas${NC}"
      exit 1
    fi
    cd ..
    echo ""
  else
    echo -e "${YELLOW}ℹ️  No se encontró DataPoblator.py. Saltando población de datos.${NC}\n"
  fi

  echo -e "${GREEN}✅ Infraestructura lista${NC}"
}

cleanup_failed_stacks() {
  echo -e "${BLUE}🧹 Limpiando stacks fallidos...${NC}"
  
  local stacks=(
    "burger-workflow-dev"
    "burger-order-dev"
    "burger-delivery-dev"
    "burger-auth-dev"
    "burger-kitchen-dev"
  )
  
  for stack in "${stacks[@]}"; do
    local status=$(aws cloudformation describe-stacks --stack-name "$stack" --region "${AWS_REGION}" --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "NOT_FOUND")
    
    if [[ "$status" == "DELETE_FAILED" ]] || [[ "$status" == "ROLLBACK_FAILED" ]] || [[ "$status" == "UPDATE_ROLLBACK_FAILED" ]]; then
      echo -e "${YELLOW}   Limpiando stack fallido: $stack (estado: $status)${NC}"
      aws cloudformation delete-stack --stack-name "$stack" --region "${AWS_REGION}" 2>/dev/null || true
      sleep 2
    fi
  done
  
  echo -e "${GREEN}✅ Limpieza de stacks completada${NC}\n"
}

deploy_service() {
  local service_name=$1
  local service_path=$2
  
  echo -e "${YELLOW}📦 Desplegando $service_name...${NC}"
  cd "$service_path"
  serverless deploy
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ $service_name desplegado${NC}\n"
  else
    echo -e "${RED}❌ Error al desplegar $service_name${NC}"
    return 1
  fi
  cd - > /dev/null
}

deploy_services() {
  echo -e "\n${BLUE}=========================================${NC}"
  echo -e "${BLUE}🚀 DESPLEGANDO SERVICIOS${NC}"
  echo -e "${BLUE}=========================================${NC}\n"
  
  # Verificar que serverless está instalado
  if ! command -v serverless &> /dev/null; then
    echo -e "${YELLOW}⚠️  Serverless Framework no encontrado. Instalando...${NC}"
    npm install -g serverless
  fi
  
  # Limpiar stacks fallidos
  cleanup_failed_stacks
  
  # Desplegar todos los servicios usando Serverless Compose
  echo -e "${YELLOW}📦 Desplegando todos los servicios con Serverless Compose...${NC}\n"
  
  serverless deploy
  
  if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ Todos los servicios desplegados exitosamente${NC}\n"
  else
    echo -e "\n${RED}❌ Error al desplegar servicios${NC}"
    return 1
  fi
  
  echo -e "${BLUE}=========================================${NC}"
  echo -e "${GREEN}✅ DESPLIEGUE COMPLETADO${NC}"
  echo -e "${BLUE}=========================================${NC}\n"
}

remove_services() {
  echo -e "\n${RED}🗑️  ELIMINANDO SERVICIOS${NC}\n"
  
  # Eliminar todos los servicios usando Serverless Compose
  echo -e "${YELLOW}Eliminando todos los servicios con Serverless Compose...${NC}\n"
  
  serverless remove 2>/dev/null || true
  
  echo -e "${GREEN}✅ Servicios eliminados${NC}"
}

delete_tables() {
  echo -e "${YELLOW}🗑️  Eliminando tablas DynamoDB...${NC}"
  
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
    echo -e "   Eliminando tabla: $table"
    aws dynamodb delete-table --table-name "$table" --region "$AWS_REGION" 2>/dev/null || \
      echo -e "${YELLOW}   ⚠️  Tabla $table no existe o ya fue eliminada${NC}"
  done
  
  echo -e "${GREEN}✅ Tablas DynamoDB eliminadas${NC}\n"
}

remove_infrastructure() {
  echo -e "\n${RED}🗑️  ELIMINANDO INFRAESTRUCTURA${NC}\n"
  delete_tables
  echo -e "${GREEN}✅ Infraestructura eliminada${NC}"
}

show_deployment_summary() {
  echo ""
  echo -e "${BLUE}=========================================${NC}"
  echo -e "${BLUE}📋 RESUMEN DEL DESPLIEGUE${NC}"
  echo -e "${BLUE}=========================================${NC}\n"
  
  echo -e "${GREEN}✅ Infraestructura:${NC}"
  echo "   • 7 tablas DynamoDB creadas"
  echo "   • Burger-Usuarios"
  echo "   • Burger-Empleados"
  echo "   • Burger-Locales"
  echo "   • Burger-Productos"
  echo "   • Burger-Pedidos"
  echo "   • Burger-Historial-Estados"
  echo "   • Burger-Tokens-Usuarios"
  echo ""
  
  echo -e "${GREEN}✅ Microservicios desplegados:${NC}"
  echo "   • burger-kitchen (Validación de stock)"
  echo "   • burger-auth (Autenticación y tokens)"
  echo "   • burger-workflow (Orquestación con Step Functions)"
  echo "   • burger-order (Gestión de pedidos)"
  echo "   • burger-delivery (Gestión de entregas)"
  echo ""
  
  echo -e "${GREEN}✅ EventBridge y Step Functions:${NC}"
  echo "   • EventBridge rules creadas para burger.pedidos, burger.cocina, burger.delivery"
  echo "   • Step Function BurgerFlow-dev (crear manualmente en AWS Console)"
  echo ""
  
  echo -e "${YELLOW}📡 Próximos pasos:${NC}\n"
  
  echo "1. Crear Step Function manualmente:"
  echo "   • Ve a AWS Console → Step Functions"
  echo "   • Create state machine → Standard"
  echo "   • Copia el contenido de workflow-service/step-function.json"
  echo "   • Name: BurgerFlow-dev"
  echo "   • Role: LabRole"
  echo ""
  
  echo "2. Obtener URLs de API Gateway:"
  echo "   aws apigatewayv2 get-apis --query 'Items[].{Name:Name,Endpoint:ApiEndpoint}' --output table"
  echo ""
  
  echo "3. Probar el sistema:"
  echo "   • Ver README.md de cada servicio para ejemplos"
  echo "   • Usar endpoint POST /eventos/trigger para disparar flujos"
  echo "   • Usar endpoint POST /callback/responder para callbacks"
  echo ""
  
  echo "4. Ver logs de una función:"
  echo "   aws logs tail /aws/lambda/NOMBRE_FUNCION --follow"
  echo ""
  
  echo -e "${BLUE}=========================================${NC}\n"
}

main() {
  check_env
  check_prereqs

  while true; do
    show_menu
    read -rp "Opción: " option

    case "$option" in
      1)
        echo ""
        echo "=========================================="
        echo "🏗️  DESPLIEGUE COMPLETO"
        echo "=========================================="
        deploy_infrastructure
        deploy_services
        show_deployment_summary
        echo ""
        echo -e "${GREEN}=========================================${NC}"
        echo -e "${GREEN}🎉 DESPLIEGUE COMPLETADO EXITOSAMENTE${NC}"
        echo -e "${GREEN}=========================================${NC}"
        break
        ;;
      2)
        echo ""
        echo "=========================================="
        echo "🗑️  ELIMINACIÓN COMPLETA"
        echo "=========================================="
        echo -e "${RED}⚠️  ADVERTENCIA: Esto eliminará TODOS los recursos${NC}"
        read -rp "¿Estás seguro? (escribe 'SI' para confirmar): " confirm
        if [[ "$confirm" == "SI" ]]; then
          remove_services
          remove_infrastructure
          echo ""
          echo -e "${GREEN}=========================================${NC}"
          echo -e "${GREEN}✅ ELIMINACIÓN COMPLETADA${NC}"
          echo -e "${GREEN}=========================================${NC}"
        else
          echo -e "${YELLOW}Operación cancelada${NC}"
        fi
        break
        ;;
      3)
        echo ""
        echo "=========================================="
        echo "📊 SOLO INFRAESTRUCTURA"
        echo "=========================================="
        deploy_infrastructure
        echo ""
        echo -e "${GREEN}✅ Infraestructura creada${NC}"
        break
        ;;
      4)
        echo ""
        echo "=========================================="
        echo "🚀 SOLO MICROSERVICIOS"
        echo "=========================================="
        deploy_services
        show_deployment_summary
        echo ""
        echo -e "${GREEN}✅ Microservicios desplegados${NC}"
        break
        ;;
      5)
        echo -e "${YELLOW}Saliendo...${NC}"
        exit 0
        ;;
      *)
        echo -e "${RED}Opción inválida${NC}"
        ;;
    esac
  done
}

main
