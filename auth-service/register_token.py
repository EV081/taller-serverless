import time
from common import get_table, TABLE_ORDERS

def register_token(event, context):
    try:
        order_id = event['order_id']
        token = event['taskToken']
        stage = event['stage']
        
        table = get_table(TABLE_ORDERS)
        table.update_item(
            Key={'order_id': order_id},
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


