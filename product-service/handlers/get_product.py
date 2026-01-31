import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    table_name = os.environ.get('TABLE_PRODUCTS')
    table = dynamodb.Table(table_name)
    
    product_id = event.get('pathParameters', {}).get('id')
    # Necesitamos local_id, asumimos un default o lo pedimos en query param
    # La key schema es (local_id, producto_id)
    local_id = event.get('queryStringParameters', {}).get('local_id', 'local_001') 
    
    try:
        response = table.get_item(Key={'local_id': local_id, 'producto_id': product_id})
        item = response.get('Item')
        
        if not item:
            return {'statusCode': 404, 'body': json.dumps({'error': 'Producto no encontrado'})}
            
        return {
            'statusCode': 200,
            'body': json.dumps(item, default=str)
        }
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
