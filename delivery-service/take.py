import json
import uuid
import time
import os
from common import response, get_table, TABLE_ORDERS, stepfunctions

TABLE_HISTORIAL_ESTADOS = os.environ.get('TABLE_HISTORIAL_ESTADOS')

def take(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        order_id = body.get('order_id')
        
        table = get_table(TABLE_ORDERS)
        item_resp = table.get_item(Key={'order_id': order_id})
        item = item_resp.get('Item')
        
        if not item or item.get('status') != "LISTO_PARA_RECOJO":
            return response(400, {"error": "Pedido no disponible"})
            
        token = item.get('task_token')
        if not token:
            return response(400, {"error": "No hay token activo"})

        # Log History
        table_history = get_table(TABLE_HISTORIAL_ESTADOS)
        iso_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
        table_history.put_item(Item={
            'history_id': str(uuid.uuid4()),
            'order_id': order_id,
            'status': 'EN_CAMINO',
            'timestamp': iso_time
        })

        stepfunctions.send_task_success(taskToken=token, output=json.dumps({"status": "PICKED_UP"}))
        return response(200, {"message": "Pedido tomado"})
    except Exception as e:
        return response(500, {"error": str(e)})
