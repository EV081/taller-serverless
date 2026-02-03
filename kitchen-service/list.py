from boto3.dynamodb.conditions import Attr
from common import response, get_table, TABLE_ORDERS
from auth_helper import get_bearer_token, validate_token_via_lambda

def _scan_by_status(status, limit=20, start_key=None):
    table = get_table(TABLE_ORDERS)
    
    scan_kwargs = {
        'FilterExpression': Attr('status').eq(status),
        'Limit': limit
    }
    if start_key:
        scan_kwargs['ExclusiveStartKey'] = start_key
        
    response_dynamo = table.scan(**scan_kwargs)
    
    items = response_dynamo.get('Items', [])
    last_key = response_dynamo.get('LastEvaluatedKey')
    
    return items, last_key

def list_pending(event, context):
    # Validate token and role - require Cocinero role
    token = get_bearer_token(event)
    valido, error, rol = validate_token_via_lambda(token)
    
    if not valido:
        return response(403, {"message": error or "Token inválido"})
    
    # Require Cocinero role
    if rol not in ("Cocinero", "Admin"):
        return response(403, {"message": "Permiso denegado: se requiere rol Cocinero"})
    
    items, last_key = _scan_by_status('PENDIENTE_COCINA')
    return response(200, {"orders": items, "next_key": last_key})

def list_cooking(event, context):
    # Validate token and role - require Cocinero role
    token = get_bearer_token(event)
    valido, error, rol = validate_token_via_lambda(token)
    
    if not valido:
        return response(403, {"message": error or "Token inválido"})
    
    # Require Cocinero role
    if rol not in ("Cocinero", "Admin"):
        return response(403, {"message": "Permiso denegado: se requiere rol Cocinero"})
    
    items, last_key = _scan_by_status('COCINANDO')
    return response(200, {"orders": items, "next_key": last_key})
