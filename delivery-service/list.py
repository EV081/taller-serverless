from boto3.dynamodb.conditions import Attr
from common import response, get_table, TABLE_ORDERS
from auth_helper import get_bearer_token, validate_token_via_lambda

def _scan_by_status(status, limit=20, start_key=None):
    table = get_table(TABLE_ORDERS)
    scan_kwargs = {'FilterExpression': Attr('status').eq(status), 'Limit': limit}
    if start_key: scan_kwargs['ExclusiveStartKey'] = start_key
    response_dynamo = table.scan(**scan_kwargs)
    return response_dynamo.get('Items', []), response_dynamo.get('LastEvaluatedKey')

def list_ready(event, context):
    """Lista pedidos listos para recoger."""
    # Validate token and role - require Repartidor role
    token = get_bearer_token(event)
    valido, error, rol = validate_token_via_lambda(token)
    
    if not valido:
        return response(403, {"message": error or "Token inválido"})
    
    # Require Repartidor role
    if rol not in ("Repartidor", "Admin"):
        return response(403, {"message": "Permiso denegado: se requiere rol Repartidor"})
    
    items, last_key = _scan_by_status('LISTO_PARA_RECOJO')
    return response(200, {"orders": items, "next_key": last_key})

def list_my_orders(event, context):
    """Lista pedidos asignados al repartidor."""
    # Validate token and role - require Repartidor role
    token = get_bearer_token(event)
    valido, error, rol = validate_token_via_lambda(token)
    
    if not valido:
        return response(403, {"message": error or "Token inválido"})
    
    # Require Repartidor role
    if rol not in ("Repartidor", "Admin"):
        return response(403, {"message": "Permiso denegado: se requiere rol Repartidor"})
    
    items, last_key = _scan_by_status('EN_CAMINO')
    return response(200, {"orders": items, "next_key": last_key})
