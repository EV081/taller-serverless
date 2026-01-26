import json
import uuid
import time
import os
from src.common import response, get_table, TABLE_ORDERS, stepfunctions

TABLE_HISTORIAL_ESTADOS = os.environ.get('TABLE_HISTORIAL_ESTADOS')

def complete(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        order_id = body.get('order_id')
        
        table = get_table(TABLE_ORDERS)
        item_resp = table.get_item(Key={'order_id': order_id})
        item = item_resp.get('Item')
        
        if not item:
            return response(404, {"error": "Pedido no encontrado"})
            
        if item.get('status') != "COCINANDO":
            return response(400, {"error": "El pedido no está en cocción"})
            
        token = item.get('task_token')
        if not token:
            return response(400, {"error": "No hay token activo"})
        
        # Log History
        table_history = get_table(TABLE_HISTORIAL_ESTADOS)
        iso_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
        table_history.put_item(Item={
            'history_id': str(uuid.uuid4()),
            'order_id': order_id,
            'status': 'LISTO_PARA_ENTREGA',
            'timestamp': iso_time
        })

        stepfunctions.send_task_success(
            taskToken=token,
            output=json.dumps({"status": "COOKED"})
        )
        return response(200, {"message": "Cocción finalizada"})

    except Exception as e:
        print(f"SF Error: {e}")
        return response(500, {"error": "Error interno"})
