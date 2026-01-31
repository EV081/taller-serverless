# 🍔 Burger Cloud - Taller Serverless

Sistema completo de delivery de hamburguesas usando arquitectura serverless en AWS. Este proyecto demuestra el uso de Step Functions, DynamoDB, Lambda en un escenario real de negocio.

## ✨ Características

- 🔄 **Step Functions** con wait for task token para intervención humana
- 🗄️ **DynamoDB** con 7 tablas y claves compuestas
- 🔐 **Autenticación** con tokens JWT
- 📊 **Generador de datos** automatizado para pruebas
- ⚡ **Arquitectura serverless** 100% escalable
- 🚀 **Despliegue automático** con un solo comando

## 🏗️ Arquitectura

```
┌─────────────────┐
│   Cliente API   │
└────────┬────────┘
         │
    ┌────▼────┐
    │  Auth   │
    └────┬────┘
         │
    ┌────▼────────────────┐
    │  Order Service      │
    │  - Crear pedido     │
    │  - Iniciar SF       │
    └────┬────────────────┘
         │
    ┌────▼──────────────────────────┐
    │  Step Function (BurgerFlow)   │
    ├───────────────────────────────┤
    │ 1. ValidarStock               │
    │ 2. EsperarConfirmacionCocina  │
    │ 3. EnPreparacion              │
    │ 4. EsperarDelivery            │
    │ 5. EnCamino                   │
    │ 6. PedidoEntregado ✅         │
    └───────────────────────────────┘
         │
    ┌────▼─────────────────┐
    │   DynamoDB Tables    │
    ├──────────────────────┤
    │ - Usuarios           │
    │ - Empleados          │
    │ - Locales            │
    │ - Productos          │
    │ - Pedidos (vacía)    │
    │ - Historial (vacía)  │
    │ - Tokens             │
    └──────────────────────┘
```

## 🚀 Inicio Rápido

### 1. Requisitos
- AWS CLI configurado
- Node.js 18+
- Python 3.10+
- Credenciales de AWS Academy

### 2. Configuración

```bash
# Editar .env con tu configuración
nano .env

# Actualiza:
# AWS_ACCOUNT_ID=tu-account-id
# AWS_REGION=us-east-1
# ORG_NAME=tu-nombre
```

### 3. Despliegue

```bash
# Ejecutar setup (toma 5-8 minutos)
bash setup_taller.sh
```

Esto automáticamente:
- ✅ Genera datos de prueba
- ✅ Crea tablas DynamoDB
- ✅ Puebla con datos iniciales (sin pedidos)
- ✅ Despliega todos los servicios
- ✅ Configura Step Function

## 🗂️ Estructura del Proyecto

```
taller-serverless/
├── data-setup/              # Generación y población de datos
│   ├── DataGenerator.py    # Genera datos JSON de prueba
│   ├── DataPoblator.py      # Crea y puebla tablas DynamoDB
│   ├── schemas-validation/  # Schemas JSON de validación
│   ├── example-data/        # Datos generados (creado al ejecutar)
│   └── README.md            # Documentación de data-setup
├── workflow-service/        # Step Functions + Tablas DynamoDB
│   ├── serverless.yml       # Definición de infraestructura
│   ├── step-function.json   # Flujo del Step Function
│   ├── validate_stock.py    # Lambda: validar stock
│   ├── register_token.py    # Lambda: registrar task tokens
│   └── common.py            # Utilidades comunes
├── auth-service/            # Autenticación
├── order-service/           # Gestión de pedidos
├── kitchen-service/         # Gestión de cocina
├── delivery-service/        # Gestión de delivery
├── setup_taller.sh          # Script de despliegue
├── .env                     # Variables de entorno
└── README.md                # Este archivo
```

## 📊 Datos de Prueba

Después del setup tendrás:

- **1 Local**: Burger Cloud en San Isidro
- **~15 Usuarios**: Gerente y clientes
- **~10 Empleados**: Cocineros y repartidores (con correo/contraseña)
- **~11 Productos**: Hamburguesas y bebidas
- **0 Pedidos**: Base de datos vacía (los pedidos se crean via API)

## 🔄 Flujo del Step Function (Simplificado)

```
Cliente crea pedido
    ↓
[ValidarStock] ← Verifica disponibilidad
    ↓
[EsperarConfirmacionCocina] ← waitForTaskToken (cocina acepta/rechaza)
    ↓
¿Cocina acepta? 
    ├─ NO → [ReintentarCocina] → Max 3 intentos → [CocinaFallida]
    └─ SÍ → [EnPreparacion] ← waitForTaskToken (cocina prepara)
           ↓
       [ListoParaEntrega] ← Pass state
           ↓
       [EsperarDelivery] ← waitForTaskToken (delivery acepta/rechaza)
           ↓
       ¿Delivery acepta?
           ├─ NO → [ReintentarDelivery] → Max 3 intentos → [DeliveryFallido]
           └─ SÍ → [EnCamino] ← waitForTaskToken (delivery entrega)
                  ↓
              [PedidoEntregado] ✅
```

**Nota:** Se eliminó el paso de "Empaquetado" - la cocina prepara y deja listo directamente para delivery.

### Timeouts
- **Confirmación Cocina**: 15 minutos (900s)
- **Preparación**: 15 minutos (900s)
- **Asignación Delivery**: 30 minutos (1800s)
- **En Camino**: 30 minutos (1800s)

## 📋 Tablas DynamoDB

| Tabla | PK | SK | GSI | Descripción |
|-------|----|----|-----|-------------|
| `Burger-Usuarios` | correo | - | - | Clientes y gerentes |
| `Burger-Empleados` | local_id | correo | - | Empleados (Cocinero, Repartidor) |
| `Burger-Locales` | local_id | - | - | Información del local |
| `Burger-Productos` | local_id | producto_id | - | Hamburguesas y Bebidas |
| `Burger-Pedidos` | local_id | pedido_id | by_usuario | Pedidos (vacía inicialmente) |
| `Burger-Historial-Estados` | pedido_id | estado_id | - | Historial de cambios (vacía) |
| `Burger-Tokens-Usuarios` | token | - | - | Tokens de autenticación (con TTL) |

## 🧪 Probando el Sistema

### Paso 1: Obtener las URLs de la API

Después del despliegue, anota las URLs que se muestran:
```
Service Endpoint: https://XXXXXXXXXX.execute-api.us-east-1.amazonaws.com/dev
```

### Paso 2: Login

```bash
# Reemplaza API_URL con tu URL real
API_URL="https://XXXXXXXXXX.execute-api.us-east-1.amazonaws.com/dev"

# Login como gerente (ver data-setup/example-data/locales.json para credenciales)
curl -X POST $API_URL/login \
  -H "Content-Type: application/json" \
  -d '{
    "correo": "CORREO_GERENTE",
    "contrasena": "CONTRASENA_GERENTE"
  }'

# Guarda el token
TOKEN="<tu_token_aqui>"
```

### Paso 3: Crear un Pedido

```bash
# Obtén IDs de productos desde data-setup/example-data/productos.json
curl -X POST $API_URL/pedido \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "local_id": "BURGER-LOCAL-001",
    "productos": [
      {
        "producto_id": "<UUID_PRODUCTO>",
        "cantidad": 2
      }
    ],
    "direccion": "Calle Los Tulipanes 123, Miraflores",
    "costo": 30.00
  }'
```

### Paso 4: Ver el Step Function en AWS Console

1. Ve a AWS Console → Step Functions
2. Busca la state machine `BurgerFlow-dev`
3. Verás la ejecución en curso, esperando confirmación de cocina

### Paso 5: Cocina Acepta y Prepara

```bash
# Cocina acepta pedido
curl -X POST $API_URL/cocina/confirmar \
  -H "Authorization: Bearer $TOKEN_COCINERO" \
  -d '{"order_id": "...", "local_id": "BURGER-LOCAL-001", "decision": "ACEPTAR"}'

# Cocina termina preparación
curl -X POST $API_URL/cocina/terminar \
  -H "Authorization: Bearer $TOKEN_COCINERO" \
  -d '{"order_id": "...", "local_id": "BURGER-LOCAL-001"}'
```

### Paso 6: Delivery Toma y Entrega

```bash
# Delivery acepta pedido
curl -X POST $API_URL/delivery/tomar \
  -H "Authorization: Bearer $TOKEN_DELIVERY" \
  -d '{"order_id": "...", "local_id": "BURGER-LOCAL-001", "decision": "ACEPTAR"}'

# Delivery entrega
curl -X POST $API_URL/delivery/entregar \
  -H "Authorization: Bearer $TOKEN_DELIVERY" \
  -d '{"order_id": "...", "local_id": "BURGER-LOCAL-001"}'
```

## 🛠️ Comandos Útiles

### Ver logs de una lambda
```bash
aws logs tail /aws/lambda/burger-workflow-dev-validateStock --follow
```

### Ver estado de un pedido en DynamoDB
```bash
aws dynamodb get-item \
  --table-name Burger-Pedidos \
  --key '{"local_id":{"S":"BURGER-LOCAL-001"},"pedido_id":{"S":"<PEDIDO_ID>"}}'
```

### Ver datos generados
```bash
cd data-setup
cat example-data/usuarios.json | jq
cat example-data/empleados.json | jq
cat example-data/productos.json | jq
```

### Regenerar datos
```bash
cd data-setup
python3 DataGenerator.py
python3 DataPoblator.py
```

## 🎯 Conceptos Clave del Taller

1. **Wait For Task Token**: Las lambdas pausan el Step Function hasta recibir confirmación humana
2. **Retry Logic**: Manejo de rechazos con reintentos limitados
3. **Timeouts**: Cada estado tiene timeout para evitar pedidos eternos
4. **Error Handling**: Estados Fail para casos de error (stock, rechazo, timeout)
5. **DynamoDB Patterns**: Uso de claves compuestas (PK + SK) y GSIs
6. **Serverless Framework**: Organización de servicios y despliegue
7. **Flujo Simplificado**: Cocina → Delivery (sin paso intermedio de empaquetado)

## 📝 Notas Importantes

- ⚠️ **Sin pedidos iniciales**: La base de datos de pedidos e historial está vacía
- ⚠️ **Empleados con credenciales**: Todos los empleados tienen correo y contraseña
- ⚠️ **Solo 2 categorías**: Productos limitados a Hamburguesas y Bebidas
- ⚠️ **Solo 2 roles de empleado**: Cocinero y Repartidor (sin Despachador)
- ⚠️ **Flujo simplificado**: No hay paso de empaquetado, cocina entrega directo a delivery

## 📚 Recursos

- [Step Functions Documentation](https://docs.aws.amazon.com/step-functions/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Serverless Framework Docs](https://www.serverless.com/framework/docs)

---

**Proyecto**: Burger Cloud - Taller Serverless  
**Curso**: Cloud Computing  
**Institución**: UTEC  
**Año**: 2025