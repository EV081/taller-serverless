import time
from common import get_table, TABLE_ORDERS

def register_token(event, context):
    try:
        order_id = event.get('order_id')
        local_id = event.get('local_id', 'BURGER-LOCAL-001') # Fallback if missing
        token = event.get('taskToken')
        stage = event.get('stage')
        
        table = get_table(TABLE_ORDERS)
        table.update_item(
            Key={
                'local_id': local_id,
                'pedido_id': order_id
            },
            UpdateExpression="SET task_token = :t, #s = :s, updated_at = :u",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':t': token,
                ':s': stage,
                ':u': int(time.time())
            }
        )
        return {"status": "TokenRegistered"}
    except Exception as e:
        print(f"Error registering token: {e}")
        raise e


