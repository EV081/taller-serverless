import json
import os
import boto3
from auth_helper import get_bearer_token, validate_token_via_lambda

dynamodb = boto3.resource('dynamodb')

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Content-Type": "application/json"
}

def _resp(code, body):
    return {
        "statusCode": code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, ensure_ascii=False)
    }

def lambda_handler(event, context):
    # Validate token and role
    token = get_bearer_token(event)
    valido, error, rol = validate_token_via_lambda(token)
    
    if not valido:
        return _resp(403, {"message": error or "Token inválido"})
    
    # Require Gerente role
    if rol not in ("Admin", "Gerente"):
        return _resp(403, {"message": "Permiso denegado: se requiere rol Gerente"})
    
    table_name = os.environ.get('PRODUCTS_TABLE')
    table = dynamodb.Table(table_name)
    
    # Try Body first
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
        table.delete_item(Key={'local_id': local_id, 'producto_id': product_id})
        
        return _resp(200, {'message': 'Producto eliminado'})
    except Exception as e:
        return _resp(500, {'error': str(e)})

