# 🍔 Guía del Taller: Burger Cloud (Step Functions)

Este taller demuestra cómo construir un sistema de delivery resiliente y orquestado por eventos usando AWS Step Functions, Lambda y DynamoDB.

## 1. Prerrequisitos
- Tener una cuenta AWS (AWS Academy/Student funciona bien).
- Tener configuradas las credenciales en tu terminal (`aws configure`).
- Node.js y Python 3 instalados.

## 2. Instalación y Despliegue

Ejecuta el script automatizado desde la carpeta `taller-burger-cloud`:

```bash
cd taller-burger-cloud
bash setup_taller.sh
```

Esto instalará dependencias, desplegará la infraestructura y creará usuarios de prueba.

**Toma nota de la URL base que devuelve el despliegue (Service Endpoint).**
Ejemplo: `https://xyz.execute-api.us-east-1.amazonaws.com/dev`

## 3. Usuarios de Prueba
| Rol | Usuario | Password | Permisos |
|-----|---------|----------|----------|
| Cliente | `cliente1` | `password123` | Crear pedidos |
| Cocina | `cocinero1` | `password123` | Ver pendientes, Confirmar, Cocinar |
| Driver | `driver1` | `password123` | Ver disponibles, Tomar envio, Entregar |

## 4. Probando el Flujo (Paso a Paso)

Reemplaza `API_URL` con tu URL real.

### Paso A: Login (Obtener Token)
Necesitas un token de **Cliente** para pedir, y luego tokens de **Cocinero** y **Driver** para procesar.

```bash
# Login Cliente
curl -X POST https://API_URL/login \
  -d '{"username": "cliente1", "password": "password123"}'

# Login Cocinero
curl -X POST https://API_URL/login \
  -d '{"username": "cocinero1", "password": "password123"}'
```

*(Guarda los tokens devueltos)*

### Paso B: Crear Pedido (Cliente)
```bash
curl -X POST https://API_URL/pedido \
  -H "Authorization: Bearer <TOKEN_CLIENTE>" \
  -d '{
    "items": [{"product_id": "hamb-clasica", "quantity": 2}]
  }'
```
Retorna un `order_id`. El estado en DB será `PENDIENTE_COCINA`.

### Paso C: Cocina Acepta (Cocinero)
1. Listar pendientes:
```bash
curl -X GET https://API_URL/cocina/pendientes \
  -H "Authorization: Bearer <TOKEN_COCINERO>"
```

2. Aceptar el pedido (Esto avanza la Step Function):
```bash
curl -X POST https://API_URL/cocina/confirmar \
  -H "Authorization: Bearer <TOKEN_COCINERO>" \
  -d '{"order_id": "<ORDER_ID>", "decision": "ACEPTAR"}'
```
El estado cambia a `COCINANDO`.

### Paso D: Cocina Termina (Cocinero)
```bash
curl -X POST https://API_URL/cocina/terminar \
  -H "Authorization: Bearer <TOKEN_COCINERO>" \
  -d '{"order_id": "<ORDER_ID>"}'
```
El estado cambia a `LISTO_PARA_RECOJO`.

### Paso E: Delivery Toma Pedido (Driver)
1. Listar disponibles:
```bash
curl -X GET https://API_URL/delivery/disponibles \
  -H "Authorization: Bearer <TOKEN_DRIVER>"
```

2. Asignarse:
```bash
curl -X POST https://API_URL/delivery/tomar \
  -H "Authorization: Bearer <TOKEN_DRIVER>" \
  -d '{"order_id": "<ORDER_ID>"}'
```
El estado cambia a `EN_CAMINO`.

### Paso F: Entrega Final (Driver)
```bash
curl -X POST https://API_URL/delivery/entregar \
  -H "Authorization: Bearer <TOKEN_DRIVER>" \
  -d '{"order_id": "<ORDER_ID>"}'
```
El estado final es `DELIVERED` (Success).

## 5. Visualización
Ve a la consola de AWS -> Step Functions -> `BurgerFlow-dev`.
Verás la traza visual de cada paso y cómo se detuvo esperando los tokens humanos.
