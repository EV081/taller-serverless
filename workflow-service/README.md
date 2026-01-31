# Workflow Service - Orquestación con Step Functions

## ⚠️ Importante

Este servicio **orquesta el flujo de pedidos** usando:
- ✅ **Lambda functions** para control y callbacks
- ✅ **EventBridge** para eventos de cocina/delivery/cliente
- ✅ **HTTP endpoints** para testing y callbacks
- ❌ **NO** crea tablas DynamoDB (las crea `data-setup/DataPoblator.py`)
- ❌ **NO** despliega el Step Function automáticamente (se crea manualmente)

---

## 📋 Lambda Functions

### 1. `startExecution`
**Trigger:** EventBridge (`burger.pedidos` → `CrearPedido`)

Inicia la ejecución del Step Function cuando se crea un nuevo pedido.

**Evento esperado:**
```json
{
  "source": "burger.pedidos",
  "detail-type": "CrearPedido",
  "detail": {
    "order_id": "uuid-123",
    "local_id": "local_001",
    "correo": "cliente@example.com",
    "productos": [...]
  }
}
```

### 2. `cambiarEstado`
**Trigger:** EventBridge (múltiples fuentes y tipos)

Registra cambios de estado en `Burger-Historial-Estados`.

**Fuentes soportadas:**
- `burger.cocina` → `EnPreparacion`, `CocinaCompleta`, `Empaquetado`
- `burger.delivery` → `EnCamino`, `Entregado`
- `burger.cliente` → `ConfirmarPedido`

### 3. `responderCallback` 
**Trigger:** HTTP API (`POST /callback/responder`)

Resume la ejecución del Step Function enviando el resultado del callback.

**Request:**
```bash
curl -X POST https://{api-id}.execute-api.us-east-1.amazonaws.com/callback/responder \
  -H "Content-Type: application/json" \
  -d '{
    "taskToken": "AQCEAAAAKgAAAAMAAA...",
    "decision": "ACEPTAR",
    "empleado_correo": "cocinero@burger.com",
    "notas": "Pedido listo"
  }'
```

**Response:**
```json
{
  "message": "Callback procesado exitosamente",
  "decision": "ACEPTAR"
}
```

### 4. `triggerEvent`
**Trigger:** HTTP API (`POST /eventos/trigger`)

Publica eventos a EventBridge para testing.

**Request:**
```bash
curl -X POST https://{api-id}.execute-api.us-east-1.amazonaws.com/eventos/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "source": "burger.pedidos",
    "detailType": "CrearPedido",
    "detail": {
      "order_id": "test-123",
      "local_id": "local_001"
    }
  }'
```

---

## 🔧 Deployment

```bash
cd workflow-service
serverless deploy
```

**Nota:** Esto despliega solo las Lambdas y EventBridge rules. El Step Function debe crearse manualmente.

---

## 📝 Crear el Step Function manualmente

### 1. Ve a AWS Console → Step Functions

### 2. Create state machine
- Click en **"Create state machine"**
- Selecciona **"Write your workflow in code"**
- Selecciona **"Standard"** type

### 3. Copia el JSON
- Abre el archivo `step-function.json` en este directorio
- **Copia TODO el contenido**
- Pega en el editor de AWS Console

### 4. Configuración
- **Name:** `BurgerFlow-dev` (o el stage que uses)
- **Execution role:** Selecciona `LabRole`
- **Logging:** Opcional (recomendado: ALL para debugging)

### 5. Create

¡Listo! El Step Function quedará configurado con las Lambdas:
- ✅ `burger-kitchen-dev-validateStock` (de kitchen-service)
- ✅ `burger-auth-dev-registerToken` (de auth-service)

---

## 🧪 Testing del Workflow

### 1. Publicar evento de CrearPedido

```bash
# Obtén el API endpoint después del deploy
API_URL=$(serverless info --verbose | grep "POST - " | grep "trigger" | awk '{print $3}')

# Dispara un evento CrearPedido
curl -X POST $API_URL \
  -H "Content-Type: application/json" \
  -d '{
    "source": "burger.pedidos",
    "detailType": "CrearPedido",
    "detail": {
      "order_id": "test-001",
      "local_id": "local_001",
      "correo": "test@burger.com",
      "productos": [{"producto_id": "prod_001", "cantidad": 2}]
    }
  }'
```

### 2. Ver la ejecución en AWS Console

Ve a **Step Functions → State machines → BurgerFlow-dev → Executions**

### 3. Responder al callback (cuando esté en espera)

```bash
# El Step Function estará esperando en "EsperarConfirmacionCocina"
# Obtén el taskToken de la tabla Burger-Tokens-Usuarios

CALLBACK_URL=$(serverless info --verbose | grep "POST - " | grep "callback" | awk '{print $3}')

curl -X POST $CALLBACK_URL \
  -H "Content-Type: application/json" \
  -d '{
    "taskToken": "AQCEAAAAKgAAAAMAAA...",
    "decision": "ACEPTAR",
    "empleado_correo": "cocinero@burger.com"
  }'
```

---

## 📊 Arquitectura

```
EventBridge (default bus)
    │
    ├─ burger.pedidos → CrearPedido
    │        ↓
    │   startExecution → Step Function
    │
    ├─ burger.cocina → EnPreparacion, CocinaCompleta
    ├─ burger.delivery → EnCamino, Entregado
    └─ burger.cliente → ConfirmarPedido
             ↓
        cambiarEstado → DynamoDB Historial

Step Function (BurgerFlow-dev)
    │
    ├─ Espera callbacks con taskToken
    └─ Resume con /callback/responder
```
