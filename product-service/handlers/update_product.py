import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    table_name = os.environ.get('TABLE_PRODUCTS')
    table = dynamodb.Table(table_name)
    
    product_id = event.get('pathParameters', {}).get('id')
    
    try:
        body = json.loads(event.get('body', '{}'))
        local_id = body.get('local_id', 'local_001')
        
        update_expr = "set "
        expr_attr_values = {}
        original_attr_names = {} # DynamoDB reserved words workaround if needed
        
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
            return {'statusCode': 400, 'body': json.dumps({'error': 'Nada que actualizar'})}
            
        response = table.update_item(
            Key={'local_id': local_id, 'producto_id': product_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_attr_values,
            ReturnValues="ALL_NEW"
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Producto actualizado', 'product': response.get('Attributes')}, default=str)
        }
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
