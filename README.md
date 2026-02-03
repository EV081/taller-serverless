# Burger Cloud - Sistema de Delivery Serverless

Sistema completo de gestión de pedidos de hamburguesas construido con arquitectura serverless en AWS. El proyecto implementa un flujo de trabajo orquestado con Step Functions, incluyendo validación de stock, confirmación de cocina y asignación de delivery.

## Descripción del Proyecto

**Burger Cloud** es un sistema de delivery que coordina automáticamente el flujo completo de un pedido: desde la creación del pedido por el cliente, validación de stock, aceptación y preparación por la cocina, hasta la asignación de repartidor y entrega final. El sistema utiliza AWS Step Functions para orquestar el flujo de trabajo con puntos de intervención humana (wait for task token).

### Características Principales

- **Orquestación con Step Functions**: Flujo de trabajo con estados de espera para intervención humana
- **Base de datos DynamoDB**: 7 tablas relacionadas con claves compuestas
- **Autenticación JWT**: Sistema de autenticación basado en tokens con roles (Cliente, Cocinero, Repartidor, Gerente)
- **Arquitectura de microservicios**: 6 servicios independientes desplegados con Serverless Framework
- **Manejo de errores**: Reintentos automáticos y timeouts en cada etapa del flujo
- **Datos de prueba**: Generación automática de datos de demostración

## Arquitectura del Sistema

### Servicios

El proyecto está dividido en los siguientes microservicios:

- **auth-service**: Autenticación y gestión de tokens JWT
- **product-service**: CRUD de productos (hamburguesas y bebidas)
- **order-service**: Creación y consulta de pedidos
- **kitchen-service**: Validación de stock, confirmación y preparación de pedidos
- **delivery-service**: Asignación de repartidores y gestión de entregas
- **workflow-service**: Orquestación del flujo con Step Functions y EventBridge

### Flujo del Pedido

```
1. Cliente crea pedido → Order Service
   ↓
2. Validar Stock → Kitchen Service
   ↓
3. Esperar Confirmación Cocina [wait for task token]
   ↓
4. ¿Cocina acepta?
   ├─ NO → Pedido Fallido
   └─ SÍ → Continuar
       ↓
5. En Preparación [wait for task token]
   ↓
6. Listo para Entrega
   ↓
7. Esperar Delivery [wait for task token]
   ↓
8. ¿Delivery acepta?
   ├─ NO → Pedido Fallido
   └─ SÍ → Continuar
       ↓
9. En Camino [wait for task token]
   ↓
10. Pedido Entregado ✓
```

### Tablas DynamoDB

| Tabla | Partition Key | Sort Key | Descripción |
|-------|---------------|----------|-------------|
| Burger-Usuarios | correo | - | Clientes y gerentes |
| Burger-Empleados | local_id | correo | Cocineros y repartidores |
| Burger-Locales | local_id | - | Información de locales |
| Burger-Productos | local_id | producto_id | Catálogo de productos |
| Burger-Pedidos | local_id | pedido_id | Pedidos del sistema |
| Burger-Historial-Estados | pedido_id | estado_id | Historial de cambios de estado |
| Burger-Tokens-Usuarios | token | - | Tokens JWT activos (con TTL) |

## Requisitos Previos

- **AWS CLI**: Configurado con credenciales de AWS Academy
- **Node.js**: Versión 18 o superior
- **Python**: Versión 3.10 o superior
- **Serverless Framework**: `npm install -g serverless`
- **Cuenta de AWS**: Con permisos de AWS Academy Lab

## Configuración Inicial

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd taller-serverless
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
nano .env
```

Actualiza las siguientes variables en el archivo `.env`:

```bash
# AWS Configuration
AWS_ACCOUNT_ID=tu-account-id
AWS_REGION=us-east-1
ORG_NAME=tu-nombre-organizacion

# DynamoDB Tables
TABLE_USUARIOS=Burger-Usuarios
TABLE_EMPLEADOS=Burger-Empleados
TABLE_LOCALES=Burger-Locales
TABLE_PRODUCTOS=Burger-Productos
TABLE_PEDIDOS=Burger-Pedidos
TABLE_HISTORIAL_ESTADOS=Burger-Historial-Estados
TABLE_TOKENS_USUARIOS=Burger-Tokens-Usuarios

# JWT Configuration
JWT_SECRET=tu-secret-key
JWT_EXPIRATION=3600

# Step Functions (se configura después del despliegue)
STATE_MACHINE_ARN=arn:aws:states:us-east-1:<account-id>:stateMachine:BurgerFlow-dev
```

### 3. Instalar dependencias

```bash
# Instalar dependencias de Python
pip3 install -r requirements.txt

# Instalar Serverless Framework (si no está instalado)
npm install -g serverless
```

## Despliegue

El proyecto incluye un script de despliegue automatizado que ofrece varias opciones:

```bash
bash setup_taller.sh
```

### Opciones del script

1. **Desplegar todo**: Crea infraestructura, genera datos de prueba y despliega todos los microservicios
2. **Eliminar todo**: Elimina microservicios y tablas DynamoDB
3. **Solo infraestructura**: Genera datos y crea tablas DynamoDB
4. **Solo microservicios**: Despliega únicamente los servicios Lambda

### Pasos del despliegue completo

El script ejecuta automáticamente:

1. Instalación de dependencias Python (`boto3`, `python-dotenv`)
2. Generación de datos de prueba con `data-setup/DataGenerator.py`
3. Creación y población de tablas DynamoDB con `data-setup/DataPoblator.py`
4. Despliegue de todos los microservicios usando Serverless Compose

**Tiempo estimado**: 5-8 minutos

### Crear Step Function manualmente

Después del despliegue, debes crear la Step Function en AWS Console:

1. Ve a **AWS Console** → **Step Functions**
2. Click en **Create state machine**
3. Selecciona **Standard** type
4. En la sección de definición, copia el contenido de `workflow-service/step-function.json`
5. Configura:
   - **Name**: `BurgerFlow-dev`
   - **Role**: Selecciona `LabRole`
6. Click en **Create state machine**
7. Copia el ARN de la Step Function y actualiza `STATE_MACHINE_ARN` en tu archivo `.env`
8. Redespliega `workflow-service` y `order-service`:
   ```bash
   cd workflow-service && serverless deploy && cd ..
   cd order-service && serverless deploy && cd ..
   ```

## Estructura del Proyecto

```
taller-serverless/
├── auth-service/              # Autenticación y tokens JWT
│   ├── login.py               # Lambda: login de usuarios
│   ├── auth.py                # Lambda: validador de tokens
│   ├── common.py              # Utilidades compartidas
│   └── serverless.yml         # Configuración del servicio
│
├── product-service/           # Gestión de productos
│   ├── product_create.py      # Lambda: crear producto
│   ├── product_update.py      # Lambda: actualizar producto
│   ├── product_delete.py      # Lambda: eliminar producto
│   ├── product_list.py        # Lambda: listar productos
│   └── serverless.yml
│
├── order-service/             # Gestión de pedidos
│   ├── create.py              # Lambda: crear pedido
│   ├── list_my_orders.py      # Lambda: pedidos del usuario
│   ├── list_all_orders.py     # Lambda: todos los pedidos
│   ├── get_status.py          # Lambda: estado del pedido
│   └── serverless.yml
│
├── kitchen-service/           # Operaciones de cocina
│   ├── validate_stock.py      # Lambda: validar stock
│   ├── register_token.py      # Lambda: registrar task tokens
│   ├── confirm.py             # Lambda: confirmar pedido
│   ├── complete.py            # Lambda: completar preparación
│   └── serverless.yml
│
├── delivery-service/          # Operaciones de delivery
│   ├── accept.py              # Lambda: aceptar pedido
│   ├── complete.py            # Lambda: completar entrega
│   └── serverless.yml
│
├── workflow-service/          # Orquestación
│   ├── handlers/
│   │   ├── start_execution.py      # Lambda: iniciar Step Function
│   │   ├── cambiar_estado.py       # Lambda: cambiar estado
│   │   ├── responder_callback.py   # Lambda: callback HTTP
│   │   └── trigger_event.py        # Lambda: eventos de prueba
│   ├── step-function.json          # Definición de la Step Function
│   ├── step-function-definition.yml # Definición en YAML
│   └── serverless.yml
│
├── data-setup/                # Generación de datos
│   ├── DataGenerator.py       # Genera datos JSON de prueba
│   ├── DataPoblator.py        # Crea y puebla tablas DynamoDB
│   ├── schemas-validation/    # Esquemas de validación JSON
│   └── example-data/          # Datos generados (creado al ejecutar)
│
├── setup_taller.sh            # Script de despliegue
├── serverless-compose.yml     # Composición de servicios
├── requirements.txt           # Dependencias Python
├── .env                       # Variables de entorno
└── README.md                  # Este archivo
```

## Datos de Prueba

El script `DataGenerator.py` crea automáticamente:

- **1 Local**: Burger Cloud en San Isidro, Lima
- **~15 Usuarios**: 1 gerente y múltiples clientes con correos únicos
- **~10 Empleados**: Cocineros y repartidores (todos con credenciales de acceso)
- **~11 Productos**: Hamburguesas (clásicas, especiales) y bebidas
- **0 Pedidos**: La tabla de pedidos comienza vacía

**Nota**: Todos los empleados tienen correo y contraseña para poder autenticarse.

## Uso del Sistema

### 1. Obtener URLs de API

Después del despliegue, anota las URLs de API Gateway:

```bash
aws apigatewayv2 get-apis --query 'Items[].{Name:Name,Endpoint:ApiEndpoint}' --output table
```

### 2. Autenticación

**Login como cliente**:
```bash
curl -X POST https://<api-url>/login \
  -H "Content-Type: application/json" \
  -d '{
    "correo": "cliente@example.com",
    "contrasena": "password123"
  }'
```

**Login como cocinero** (ver credenciales en `data-setup/example-data/empleados.json`):
```bash
curl -X POST https://<api-url>/login \
  -H "Content-Type: application/json" \
  -d '{
    "correo": "cocinero1@burgercloud.com",
    "contrasena": "password_cocina123"
  }'
```

Guarda el token recibido para futuras peticiones.

### 3. Crear un Pedido

```bash
export TOKEN="<tu-token-jwt>"

curl -X POST https://<api-url>/pedido \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "local_id": "BURGER-LOCAL-001",
    "productos": [
      {
        "producto_id": "<uuid-del-producto>",
        "cantidad": 2
      }
    ],
    "direccion": "Av. Principal 123, Miraflores",
    "costo": 30.00
  }'
```

Los IDs de productos se encuentran en `data-setup/example-data/productos.json`.

### 4. Monitorear el Flujo

Ve a **AWS Console** → **Step Functions** → **BurgerFlow-dev** para ver:
- Ejecuciones activas
- Estado actual del pedido
- Tiempo de espera en cada etapa

### 5. Confirmación de Cocina

**Aceptar pedido**:
```bash
curl -X POST https://<api-url>/cocina/confirmar \
  -H "Authorization: Bearer $TOKEN_COCINERO" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "<order-id>",
    "local_id": "BURGER-LOCAL-001",
    "decision": "ACEPTAR"
  }'
```

**Completar preparación**:
```bash
curl -X POST https://<api-url>/cocina/terminar \
  -H "Authorization: Bearer $TOKEN_COCINERO" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "<order-id>",
    "local_id": "BURGER-LOCAL-001"
  }'
```

### 6. Asignación de Delivery

**Aceptar pedido**:
```bash
curl -X POST https://<api-url>/delivery/tomar \
  -H "Authorization: Bearer $TOKEN_DELIVERY" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "<order-id>",
    "local_id": "BURGER-LOCAL-001",
    "decision": "ACEPTAR"
  }'
```

**Completar entrega**:
```bash
curl -X POST https://<api-url>/delivery/entregar \
  -H "Authorization: Bearer $TOKEN_DELIVERY" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "<order-id>",
    "local_id": "BURGER-LOCAL-001"
  }'
```

## Colección Postman

El proyecto incluye una colección de Postman con todos los endpoints configurados:

- `taller-serverless-postman-collection.json`: Colección completa con ejemplos
- `postman-collection-updated.json`: Versión actualizada

Importa cualquiera de estos archivos en Postman y actualiza las variables de entorno:
- `api_url`: URL de API Gateway
- `token`: Token JWT después del login

## Comandos Útiles

### Ver logs de una función Lambda

```bash
aws logs tail /aws/lambda/burger-order-dev-createOrder --follow
```

### Consultar un pedido en DynamoDB

```bash
aws dynamodb get-item \
  --table-name Burger-Pedidos \
  --key '{"local_id":{"S":"BURGER-LOCAL-001"},"pedido_id":{"S":"<PEDIDO_ID>"}}'
```

### Listar todos los pedidos

```bash
aws dynamodb scan --table-name Burger-Pedidos
```

### Ver datos generados

```bash
cat data-setup/example-data/usuarios.json | jq
cat data-setup/example-data/empleados.json | jq
cat data-setup/example-data/productos.json | jq
```

### Regenerar datos y repoblar tablas

```bash
cd data-setup
python3 DataGenerator.py
python3 DataPoblator.py
cd ..
```

## Conceptos Técnicos Implementados

### 1. Wait For Task Token
Las Step Functions pausan la ejecución hasta recibir una respuesta externa mediante `SendTaskSuccess` o `SendTaskFailure`. Esto permite intervención humana en puntos críticos del flujo.

### 2. Timeouts
- **Confirmación Cocina**: 15 minutos (900s)
- **Preparación**: 15 minutos (900s)
- **Asignación Delivery**: 30 minutos (1800s)
- **En Camino**: 30 minutos (1800s)

### 3. DynamoDB Patterns
- Uso de claves compuestas (Partition Key + Sort Key)
- Global Secondary Index (GSI) en Burger-Pedidos para consultar por usuario
- TTL en Burger-Tokens-Usuarios para expiración automática de tokens

### 4. EventBridge
Comunicación entre servicios mediante eventos personalizados:
- `burger.pedidos`: Eventos de creación de pedidos
- `burger.cocina`: Eventos de cocina
- `burger.delivery`: Eventos de delivery

### 5. Serverless Compose
Orquestación de despliegue con dependencias entre servicios:
- `auth` debe desplegarse antes que servicios que usan autorización
- `kitchen` debe desplegarse antes que `workflow` (por imports de ARNs)

## Troubleshooting

### Error: "Step Function ARN not found"
Asegúrate de haber creado la Step Function manualmente y actualizado `STATE_MACHINE_ARN` en `.env`.

### Error: "Insufficient stock"
Verifica que los productos tengan stock disponible en `Burger-Productos`. El campo `stock` debe ser mayor que la cantidad solicitada.

### Error: "Token expired"
Los tokens JWT expiran después de 1 hora. Realiza login nuevamente para obtener un nuevo token.

### Error: "Unauthorized"
Verifica que el token se esté enviando correctamente en el header:
```
Authorization: Bearer <tu-token>
```

### Step Function no se ejecuta
Verifica que el EventBridge rule esté conectado correctamente y que el `STATE_MACHINE_ARN` sea correcto en el servicio `order-service`.

## Recursos Adicionales

- [AWS Step Functions - Documentación](https://docs.aws.amazon.com/step-functions/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Serverless Framework](https://www.serverless.com/framework/docs)
- [EventBridge Patterns](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html)

## Notas Importantes

- Las tablas `Burger-Pedidos` y `Burger-Historial-Estados` comienzan vacías
- Todos los empleados tienen credenciales de acceso (correo/contraseña)
- Solo hay 2 categorías de productos: Hamburguesas y Bebidas
- Solo hay 2 roles de empleados: Cocinero y Repartidor
- El flujo NO incluye paso de empaquetado (cocina prepara y entrega directamente a delivery)

---

**Proyecto**: Burger Cloud - Taller Serverless  
**Curso**: Cloud Computing  
**Institución**: UTEC  
**Año**: 2025