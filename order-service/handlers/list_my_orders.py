import json
import os
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    """
    Lista los pedidos del usuario autenticado.
    Requiere Authorizer que inyecte el user_id o claims.
    """
    table_name = os.environ.get('TABLE_ORDERS')
    table = dynamodb.Table(table_name)
    
    # Intenta obtener user_id del authorizer context
    user_id = event.get('requestContext', {}).get('authorizer', {}).get('lambda', {}).get('principalId')
    
    if not user_id:
        # Fallback para pruebas si no hay authorizer completo
        print("⚠️ No user_id found in authorizer context")
        return {'statusCode': 401, 'body': json.dumps({'error': 'No autorizado'})}
        
    try:
        # Obtener parámetros de paginación
        limit = int(event.get('queryStringParameters', {}).get('limit', 10))
        last_key = event.get('queryStringParameters', {}).get('lastKey')
        
        # Consultar usando GSI 'by_usuario_v2' o Scan con filtro (menos eficiente)
        # Asumiendo que existe un GSI por user_id. Si no, usamos Scan filtrado.
        # En el setup_taller.sh no vi GSI específico, pero el usuario mencionó "uno q el propio usuario ve sus pedidos"
        # Usaremos Scan con FilterExpression por ahora (simple para taller)
        
        scan_kwargs = {
            'FilterExpression': Key('correo').eq(user_id) | Key('user_id').eq(user_id), # Cubrimos ambos casos
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
        print(f"Error listing user orders: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
