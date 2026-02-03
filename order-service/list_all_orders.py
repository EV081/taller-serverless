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

def handler(event, context):
    table_name = os.environ.get('TABLE_ORDERS')
    table = dynamodb.Table(table_name)
    
    # Verificar Rol - Fix authorizer context path
    authorizer_context = event.get('requestContext', {}).get('authorizer', {})
    role = authorizer_context.get('role', '').lower()
    
    # Only Cocinero and Repartidor can see all orders
    allowed_roles = ['cocinero', 'repartidor']
    
    if role not in allowed_roles:
         return _resp(403, {'error': f'Acceso denegado: se requiere rol Cocinero o Repartidor'})
    
    try:
        # Handle None queryStringParameters
        query_params = event.get('queryStringParameters') or {}
        limit = int(query_params.get('limit', 20))
        last_key = query_params.get('lastKey')
        
        scan_kwargs = {
            'Limit': limit
        }
        
        if last_key:
            scan_kwargs['ExclusiveStartKey'] = json.loads(last_key)
            
        response = table.scan(**scan_kwargs)
        
        items = response.get('Items', [])
        last_evaluated_key = response.get('LastEvaluatedKey')
        
        return _resp(200, {
            'items': items,
            'lastKey': json.dumps(last_evaluated_key) if last_evaluated_key else None
        })
    except Exception as e:
        print(f"Error listing all orders: {e}")
        return _resp(500, {'error': str(e)})
