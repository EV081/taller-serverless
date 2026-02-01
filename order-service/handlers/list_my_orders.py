import json
import os
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')

CORS_HEADERS = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}

def _resp(code, body):
    return {
        "statusCode": code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, ensure_ascii=False, default=str)
    }

def handler(event, context):
    """
    Lista los pedidos del usuario autenticado.
    Requiere Authorizer que inyecte el user_id o claims.
    """
    table_name = os.environ.get('TABLE_ORDERS')
    table = dynamodb.Table(table_name)
    
    # Intenta obtener user_id del authorizer context
    user_id = event.get('requestContext', {}).get('authorizer', {}).get('principalId')
    
    if not user_id:
        # Fallback para pruebas si no hay authorizer completo
        print("⚠️ No user_id found in authorizer context")
        return _resp(401, {'error': 'No autorizado'})
        
    try:
        # Obtener parámetros de paginación
        limit = int(event.get('queryStringParameters', {}).get('limit', 10))
        last_key = event.get('queryStringParameters', {}).get('lastKey')
        
        # Scan with filter by user_id
        scan_kwargs = {
            'FilterExpression': Key('correo').eq(user_id) | Key('user_id').eq(user_id),
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
        print(f"Error listing user orders: {e}")
        return _resp(500, {'error': str(e)})

