import json
import os
import boto3
import uuid

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    table_name = os.environ.get('TABLE_PRODUCTS')
    table = dynamodb.Table(table_name)
    
    try:
        body = json.loads(event.get('body', '{}'))
        
        local_id = body.get('local_id', 'local_001')
        nombre = body.get('nombre')
        descripcion = body.get('descripcion')
        categoria = body.get('categoria')
        precio = body.get('precio')
        stock = body.get('stock', 0)
        
        if not nombre or not precio:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Nombre y precio son requeridos'})}
            
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
        
        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Producto creado', 'product': item})
        }
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
