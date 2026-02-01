import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    table_name = os.environ.get('TABLE_PRODUCTS')
    table = dynamodb.Table(table_name)
    
    # Try Body first, then Query/Path
    body = {}
    if event.get('body'):
        try:
            body = json.loads(event.get('body'))
        except:
            pass
            
    product_id = body.get('producto_id') or event.get('pathParameters', {}).get('id')
    local_id = body.get('local_id') or event.get('queryStringParameters', {}).get('local_id', 'BURGER-LOCAL-001')
    
    if not product_id:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Falta producto_id'})}

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
