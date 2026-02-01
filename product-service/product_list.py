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

def lambda_handler(event, context):
    # Public endpoint - no authentication required
    table_name = os.environ.get('PRODUCTS_TABLE')
    table = dynamodb.Table(table_name)
    
    try:
        # Method is POST per user request, so limit/lastKey might come in Body
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event.get('body'))
            except:
                pass

        limit = int(body.get('limit', event.get('queryStringParameters', {}).get('limit', 20)))
        last_key = body.get('lastKey')
        
        scan_kwargs = {
            'Limit': limit
        }
        
        if last_key:
            scan_kwargs['ExclusiveStartKey'] = last_key
            
        response = table.scan(**scan_kwargs)
        
        items = response.get('Items', [])
        last_evaluated_key = response.get('LastEvaluatedKey')
        
        return _resp(200, {
            'items': items,
            'lastKey': last_evaluated_key
        })
        
    except Exception as e:
        print(f"Error listing products: {e}")
        return _resp(500, {'error': str(e)})

