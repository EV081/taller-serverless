import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    """
    Lista todos los pedidos (para staff: cocinero, repartidor, gerente).
    RBAC: Verifica rol en authorizer context.
    """
    table_name = os.environ.get('TABLE_ORDERS')
    table = dynamodb.Table(table_name)
    
    # Verificar Rol
    authorizer_context = event.get('requestContext', {}).get('authorizer', {}).get('lambda', {})
    role = authorizer_context.get('role', '').lower()
    
    allowed_roles = ['cocina', 'cocinero', 'repartidor', 'delivery', 'gerente']
    
    if role not in allowed_roles:
         return {
            'statusCode': 403, 
            'body': json.dumps({'error': f'Acceso denegado: Rol {role} no autorizado para ver todos los pedidos'})
        }
    
    try:
        limit = int(event.get('queryStringParameters', {}).get('limit', 20))
        last_key = event.get('queryStringParameters', {}).get('lastKey')
        
        scan_kwargs = {
            'Limit': limit
        }
        
        if last_key:
            scan_kwargs['ExclusiveStartKey'] = json.loads(last_key)
            
        response = table.scan(**scan_kwargs)
        
        items = response.get('Items', [])
        last_evaluated_key = response.get('LastEvaluatedKey')
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'items': items,
                'lastKey': json.dumps(last_evaluated_key) if last_evaluated_key else None
            }, default=str)
        }
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
