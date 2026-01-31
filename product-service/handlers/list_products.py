import json
import os
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    table_name = os.environ.get('TABLE_PRODUCTS')
    table = dynamodb.Table(table_name)
    
    try:
        # Paginación básica (scan)
        # Nota: Scan no es eficiente para grandes volúmenes, pero ok para taller
        # Para producción usar Query con GSI si es necesario
        
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
        print(f"Error listing products: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
