import json
import uuid
import time
import os
from common import response, get_table, TABLE_ORDERS, stepfunctions
from auth_helper import get_bearer_token, validate_token_via_lambda

TABLE_HISTORIAL_ESTADOS = os.environ.get('TABLE_HISTORIAL_ESTADOS')

def take(event, context):
    try:
        # Validate token and role - require Repartidor role
        token = get_bearer_token(event)
        valido, error, rol = validate_token_via_lambda(token)
        
        if not valido:
            return response(403, {"message": error or "Token inválido"})
        
        # Require Repartidor role
        if rol not in ("Repartidor", "Admin"):
            return response(403, {"message": "Permiso denegado: se requiere rol Repartidor"})
        
        body = json.loads(event.get('body', '{}'))
        order_id = body.get('order_id')
        local_id = body.get('local_id', 'BURGER-LOCAL-001')
        
        table = get_table(TABLE_ORDERS)
        # Use composite key: local_id (PK) and pedido_id (SK)
        item_resp = table.get_item(Key={'local_id': local_id, 'pedido_id': order_id})
        item = item_resp.get('Item')
        
        if not item or item.get('status') != "LISTO_PARA_RECOJO":
            return response(400, {"error": "Pedido no disponible"})
            
        token = item.get('task_token')
        if not token:
            return response(400, {"error": "No hay token activo"})

        # Log History
        table_history = get_table(TABLE_HISTORIAL_ESTADOS)
        iso_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
        estado_id = str(uuid.uuid4())
        table_history.put_item(Item={
            'pedido_id': order_id,
            'estado_id': estado_id,
            'estado': 'EN_CAMINO',
            'timestamp': iso_time
        })

        stepfunctions.send_task_success(taskToken=token, output=json.dumps({"decision": "ACEPTAR", "status": "PICKED_UP"}))
        return response(200, {"message": "Pedido tomado"})
    except Exception as e:
        return response(500, {"error": str(e)})
