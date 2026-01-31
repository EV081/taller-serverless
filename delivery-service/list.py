from boto3.dynamodb.conditions import Attr
from common import response, get_table, TABLE_ORDERS

def _scan_by_status(status, limit=20, start_key=None):
    table = get_table(TABLE_ORDERS)
    scan_kwargs = {'FilterExpression': Attr('status').eq(status), 'Limit': limit}
    if start_key: scan_kwargs['ExclusiveStartKey'] = start_key
    response_dynamo = table.scan(**scan_kwargs)
    return response_dynamo.get('Items', []), response_dynamo.get('LastEvaluatedKey')

def list_ready(event, context):
    items, last_key = _scan_by_status('LISTO_PARA_RECOJO')
    return response(200, {"orders": items, "next_key": last_key})

def list_my_orders(event, context):
    items, last_key = _scan_by_status('EN_CAMINO')
    return response(200, {"orders": items, "next_key": last_key})
