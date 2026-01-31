# ✅ Proyecto Listo para Despliegue - Burger Cloud

## 📊 Estado Actual del Proyecto

### Estructura Final
```
taller-serverless/
├── data-setup/              ✅ Datos aislados
│   ├── DataGenerator.py     ✅ Sin pedidos/historial
│   ├── DataPoblator.py       ✅ Solo datos maestros
│   ├── schemas-validation/   ✅ Schemas actualizados
│   ├── example-data/         ✅ 4 archivos JSON
│   └── README.md             ✅ Documentación
├── workflow-service/         ✅ Step Function simplificado
│   ├── step-function.json    ✅ 18 estados (sin Empaquetado)
│   ├── serverless.yml        ✅ 7 tablas DynamoDB
│   ├── validate_stock.py     ✅ Imports corregidos
│   ├── register_token.py     ✅ Imports corregidos
│   └── common.py             ✅ Utilidades
├── auth-service/             ✅ Autenticación
├── order-service/            ✅ Gestión de pedidos
├── kitchen-service/          ✅ Gestión de cocina
├── delivery-service/         ✅ Gestión de delivery
├── setup_taller.sh           ✅ Script completo
├── .env                      ⚠️  CONFIGURAR antes de desplegar
└── README.md                 ✅ Documentación consolidada
```

### Estados del Step Function (18 total)
1. ValidarStock
2. PedidoFalloStock
3. EsperarConfirmacionCocina
4. DecisionCocina
5. ReintentarCocina
6. EvaluarReintentoCocina
7. CocinaFallida
8. PedidoRechazadoCocina
9. EnPreparacion
10. **ListoParaEntrega** ← NUEVO (reemplaza Empaquetado)
11. EsperarDelivery
12. DecisionDelivery
13. ReintentarDelivery
14. EvaluarReintentoDelivery
15. DeliveryFallido
16. EnCamino
17. PedidoEntregado
18. PedidoExpirado

### Datos Generados
```bash
example-data/
├── usuarios.json       (15 registros)  ✅
├── empleados.json      (10 registros)  ✅
├── locales.json        (1 registro)    ✅
└── productos.json      (11 registros)  ✅

# NO generados (intencional):
# ❌ pedidos.json
# ❌ historial_estados.json
```

## 🚀 Pasos para Desplegar

### 1. Configurar AWS Credentials

```bash
aws configure
# Ingresa tus credenciales de AWS Academy
```

Verifica:
```bash
aws sts get-caller-identity
# Debes ver tu Account ID
```

### 2. Editar .env

```bash
cd /home/vssz/UTEC/2025-2\ \(4to\)/Cloud/Proyecto-de-200-millas/taller-serverless
nano .env
```

Actualiza estos valores:
```env
AWS_ACCOUNT_ID=123456789012      # Tu Account ID real
AWS_REGION=us-east-1             # Tu región
ORG_NAME=tu-nombre-serverless    # Tu usuario serverless.com
```

### 3. Ejecutar Setup

```bash
bash setup_taller.sh
```

Este script:
1. ✅ Valida que existe .env
2. ✅ Instala dependencias Python (boto3, python-dotenv)
3. ✅ Ejecuta DataGenerator (4 archivos JSON)
4. ✅ Ejecuta DataPoblator (crea y puebla tablas)
5. ✅ Despliega workflow-service (Step Function + Tablas)
6. ✅ Despliega auth-service
7. ✅ Despliega order-service
8. ✅ Despliega kitchen-service
9. ✅ Despliega delivery-service

**Tiempo estimado:** 5-8 minutos

### 4. Verificar en AWS Console

#### DynamoDB
```bash
aws dynamodb list-tables | grep Burger
```
Debes ver:
- Burger-Usuarios
- Burger-Empleados
- Burger-Locales
- Burger-Productos
- Burger-Pedidos (vacía)
- Burger-Historial-Estados (vacía)
- Burger-Tokens-Usuarios (vacía)

#### Step Functions
```bash
aws stepfunctions list-state-machines | grep BurgerFlow
```
Debes ver: `BurgerFlow-dev`

#### Lambdas
```bash
aws lambda list-functions | grep burger | wc -l
```
Debes ver: ~10-15 funciones

### 5. Obtener API Endpoint

Después del despliegue, busca en la salida:
```
Service Endpoint: https://XXXXXXXXXX.execute-api.us-east-1.amazonaws.com/dev
```

Guarda esta URL.

## 🧪 Prueba Rápida

### 1. Ver Credenciales del Gerente

```bash
cat data-setup/example-data/locales.json | jq '.[] | .gerente'
```

Esto te dará:
```json
{
  "nombre": "Juan Pérez",
  "correo": "juan.perez@gmail.com",
  "contrasena": "ger_abc123"
}
```

### 2. Login

```bash
export API_URL="https://TU-API-URL/dev"

curl -X POST $API_URL/login \
  -H "Content-Type: application/json" \
  -d '{
    "correo": "juan.perez@gmail.com",
    "contrasena": "ger_abc123"
  }'
```

Guarda el token devuelto.

### 3. Ver Productos Disponibles

```bash
cat data-setup/example-data/productos.json | jq '.[] | {nombre, precio, producto_id}' | head -20
```

### 4. Crear un Pedido

```bash
export TOKEN="tu_token_aqui"

curl -X POST $API_URL/pedido \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "local_id": "BURGER-LOCAL-001",
    "productos": [
      {
        "producto_id": "UUID_DE_PRODUCTO",
        "cantidad": 2
      }
    ],
    "direccion": "Av. Universitaria 1801, San Miguel",
    "costo": 30.00
  }'
```

### 5. Ver Step Function Ejecutándose

1. AWS Console → Step Functions
2. Click en `BurgerFlow-dev`
3. Verás la ejecución activa
4. Click en la ejecución para ver el estado actual

## 📋 Checklist Pre-Despliegue

- [ ] AWS CLI configurado (`aws configure`)
- [ ] Credenciales verificadas (`aws sts get-caller-identity`)
- [ ] Archivo `.env` editado con valores reales
- [ ] Node.js 18+ instalado (`node --version`)
- [ ] Python 3.10+ instalado (`python3 --version`)
- [ ] pip3 instalado (`pip3 --version`)

## 🎯 Flujo Completo de Pedido

```
1. Cliente crea pedido via API
   ↓
2. [ValidarStock] - Lambda verifica disponibilidad
   ↓
3. [EsperarConfirmacionCocina] - Wait for task token (15 min timeout)
   ↓
4. Cocinero acepta/rechaza (retry hasta 3 veces)
   ↓
5. [EnPreparacion] - Wait for task token (15 min timeout)
   ↓
6. Cocinero termina preparación
   ↓
7. [ListoParaEntrega] - Pass state (sin intervención)
   ↓
8. [EsperarDelivery] - Wait for task token (30 min timeout)
   ↓
9. Repartidor acepta/rechaza (retry hasta 3 veces)
   ↓
10. [EnCamino] - Wait for task token (30 min timeout)
   ↓
11. Repartidor confirma entrega
   ↓
12. [PedidoEntregado] - Success! ✅
```

## 🔍 Troubleshooting

### Error: "Table already exists"
```bash
# Eliminar tablas existentes
aws dynamodb delete-table --table-name Burger-Usuarios
aws dynamodb delete-table --table-name Burger-Empleados
aws dynamodb delete-table --table-name Burger-Locales
aws dynamodb delete-table --table-name Burger-Productos
aws dynamodb delete-table --table-name Burger-Pedidos
aws dynamodb delete-table --table-name Burger-Historial-Estados
aws dynamodb delete-table --table-name Burger-Tokens-Usuarios

# Volver a ejecutar
bash setup_taller.sh
```

### Error: "Serverless command not found"
```bash
npm install -g serverless
```

### Ver logs de una Lambda
```bash
aws logs tail /aws/lambda/burger-workflow-dev-validateStock --follow
```

### Regenerar datos
```bash
cd data-setup
rm -rf example-data/
python3 DataGenerator.py
python3 DataPoblator.py
```

## ✅ Validaciones Finales

### Archivos .md
```bash
find . -name "*.md" -type f
# Debe mostrar solo:
# ./README.md
# ./data-setup/README.md
```
✅ Correcto - Solo 2 archivos

### Estados del Step Function
```bash
cat workflow-service/step-function.json | jq '.States | keys | length'
# Debe mostrar: 18
```
✅ Correcto - 18 estados (sin Empaquetado)

### Datos Generados
```bash
ls data-setup/example-data/
# Debe mostrar solo:
# empleados.json  locales.json  productos.json  usuarios.json
```
✅ Correcto - Sin pedidos ni historial

### Imports Corregidos
```bash
grep "from common import" workflow-service/*.py
# Debe mostrar imports correctos (no src.common)
```
✅ Correcto - Todos los imports funcionan

## 🎉 ¡Proyecto Listo!

Tu proyecto **Burger Cloud** está completamente configurado y listo para desplegar con:

✅ Base de datos sin pedidos iniciales  
✅ Step Function simplificado (sin despachador)  
✅ Documentación consolidada  
✅ Imports corregidos  
✅ Estructura organizada  

**Siguiente paso:**
```bash
bash setup_taller.sh
```

¡Buena suerte con el despliegue! 🍔
