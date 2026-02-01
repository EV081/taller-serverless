import json
import uuid
import time
import os
from common import response, get_table, TABLE_ORDERS, stepfunctions
from auth_helper import get_bearer_token, validate_token_via_lambda

TABLE_HISTORIAL_ESTADOS = os.environ.get('TABLE_HISTORIAL_ESTADOS')

def confirm(event, context):
    try:
        # Validate token and role - require Cocinero role
        token = get_bearer_token(event)
        valido, error, rol = validate_token_via_lambda(token)
        
        if not valido:
            return response(403, {"message": error or "Token inválido"})
        
        # Require Cocinero role
        if rol not in ("Cocinero", "Admin"):
            return response(403, {"message": "Permiso denegado: se requiere rol Cocinero"})
        
        body = json.loads(event.get('body', '{}'))
        order_id = body.get('order_id')
        local_id = body.get('local_id', 'BURGER-LOCAL-001')
        decision = body.get('decision')
        
        if decision not in ['ACEPTAR', 'RECHAZAR']:
            return response(400, {"error": "Decisión inválida"})

        table = get_table(TABLE_ORDERS)
        # Use composite key: local_id (PK) and pedido_id (SK)
        item_resp = table.get_item(Key={'local_id': local_id, 'pedido_id': order_id})
        item = item_resp.get('Item')
        
        if not item:
            return response(404, {"error": "Pedido no encontrado"})
            
        if item.get('status') != "PENDIENTE_COCINA":
            return response(400, {"error": "El pedido no está pendiente de cocina"})
            
        token = item.get('task_token')
        if not token:
            return response(400, {"error": "No hay token activo"})
            
        # Log History
        status = 'EN_COCINA' if decision == 'ACEPTAR' else 'RECHAZADO_COCINA'
        
        table_history = get_table(TABLE_HISTORIAL_ESTADOS)
        iso_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
        history_timestamp = int(time.time() * 1000)
        
        table_history.put_item(Item={
            'pedido_id': order_id,
            'timestamp': history_timestamp,
            'status': status,
            'fecha': iso_time
        })

        stepfunctions.send_task_success(
            taskToken=token,
            output=json.dumps({"decision": decision})
        )
        return response(200, {"message": "Decisión procesada"})

    except Exception as e:
        print(f"SF Error: {e}")
        return response(500, {"error": "Error interno"})
