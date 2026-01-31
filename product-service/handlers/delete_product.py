import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    table_name = os.environ.get('TABLE_PRODUCTS')
    table = dynamodb.Table(table_name)
    
    product_id = event.get('pathParameters', {}).get('id')
    local_id = event.get('queryStringParameters', {}).get('local_id', 'local_001')
    
    try:
        table.delete_item(Key={'local_id': local_id, 'producto_id': product_id})
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Producto eliminado'})
        }
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
