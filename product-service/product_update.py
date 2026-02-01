import json
import os
import boto3
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
        product_id = body.get('producto_id')
        
        if not product_id:
            # Fallback to path param if mixed usage
            product_id = event.get('pathParameters', {}).get('id')
            
        if not product_id:
             return _resp(400, {'error': 'producto_id requerido'})

        update_expr = "set "
        expr_attr_values = {}
        
        if 'nombre' in body:
            update_expr += "nombre = :n, "
            expr_attr_values[':n'] = body['nombre']
        if 'precio' in body:
            update_expr += "precio = :p, "
            expr_attr_values[':p'] = str(body['precio'])
        if 'stock' in body:
            update_expr += "stock = :s, "
            expr_attr_values[':s'] = int(body['stock'])
            
        update_expr = update_expr.rstrip(", ")
        
        if not expr_attr_values:
            return _resp(400, {'error': 'Nada que actualizar'})
            
        response = table.update_item(
            Key={'local_id': local_id, 'producto_id': product_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_attr_values,
            ReturnValues="ALL_NEW"
        )
        
        return _resp(200, {'message': 'Producto actualizado', 'product': response.get('Attributes')})
    except Exception as e:
        return _resp(500, {'error': str(e)})

