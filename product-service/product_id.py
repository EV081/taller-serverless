import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')

CORS_HEADERS = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}

def _resp(code, body):
    return {
        "statusCode": code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, ensure_ascii=False, default=str)
    }

def lambda_handler(event, context):
    # Public endpoint - no authentication required
    table_name = os.environ.get('PRODUCTS_TABLE')
    table = dynamodb.Table(table_name)
    
    # Try Body (method is POST per user template)
    body = {}
    if event.get('body'):
        try:
            body = json.loads(event.get('body'))
        except:
            pass
            
    product_id = body.get('producto_id')
    local_id = body.get('local_id') or 'BURGER-LOCAL-001'
    
    if not product_id:
        return _resp(400, {'error': 'Falta producto_id en el body'})

    try:
        response = table.get_item(Key={'local_id': local_id, 'producto_id': product_id})
        item = response.get('Item')
        
        if not item:
            return _resp(404, {'error': 'Producto no encontrado'})
            
        return _resp(200, item)
    except Exception as e:
        print(f"Error getting product: {e}")
        return _resp(500, {'error': str(e)})

