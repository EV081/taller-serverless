import json
import os
import boto3
from common import response, get_table

TABLE_ORDERS = os.environ.get('TABLE_ORDERS')

def handler(event, context):
    try:
        # Expect query parameters
        qs = event.get('queryStringParameters', {})
        local_id = qs.get('local_id')
        pedido_id = qs.get('pedido_id')
        
        if not local_id or not pedido_id:
             return response(400, {"error": "Faltan parametros (local_id, pedido_id)"})

        table = get_table(TABLE_ORDERS)
        res = table.get_item(Key={'local_id': local_id, 'pedido_id': pedido_id})
        
        item = res.get('Item')
        if not item:
            return response(404, {"error": "Pedido no encontrado"})
            
        return response(200, {
            "pedido_id": pedido_id,
            "status": item.get('status'),
            "updated_at": item.get('updated_at')
        })

    except Exception as e:
        print(f"Error get status: {e}")
        return response(500, {"error": str(e)})
