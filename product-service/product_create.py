import json
import os
import boto3
import uuid
from auth_helper import get_bearer_token, validate_token_via_lambda

dynamodb = boto3.resource('dynamodb')

CORS_HEADERS = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}

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
    
    try:
        body = json.loads(event.get('body', '{}'))
        
        local_id = body.get('local_id', 'BURGER-LOCAL-001')
        nombre = body.get('nombre')
        descripcion = body.get('descripcion')
        categoria = body.get('categoria')
        precio = body.get('precio')
        stock = body.get('stock', 0)
        
        if not nombre or not precio:
            return _resp(400, {'error': 'Nombre y precio son requeridos'})
            
        product_id = f"prod-{str(uuid.uuid4())[:8]}"
        
        item = {
            'local_id': local_id,
            'producto_id': product_id,
            'nombre': nombre,
            'descripcion': descripcion,
            'categoria': categoria,
            'precio': str(precio),
            'stock': int(stock),
            'imagen': body.get('imagen', '')
        }
        
        table.put_item(Item=item)
        
        return _resp(201, {'message': 'Producto creado', 'product': item})
    except Exception as e:
        return _resp(500, {'error': str(e)})

