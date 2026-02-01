import json
import uuid
import time
import os
import boto3
from common import response, get_table, TABLE_ORDERS, STATE_MACHINE_ARN, stepfunctions
from auth_helper import get_bearer_token, validate_token_via_lambda

# Env vars
TABLE_PRODUCTS = os.environ.get('TABLE_PRODUCTS')

def create_order(event, context):
    try:
        # Validate token and role - require Cliente role
        token = get_bearer_token(event)
        valido, error, rol = validate_token_via_lambda(token)
        
        if not valido:
            return response(403, {"message": error or "Token inválido"})
        
        # Require Cliente role for creating orders
        if rol not in ("Cliente", "Admin"):
            return response(403, {"message": "Permiso denegado: solo clientes pueden crear pedidos"})
        
        user_context = event.get('requestContext', {}).get('authorizer', {})
        # Note: 'username' might come from principalId or context depending on Authorizer
        # Our authorizer returns context with username.
        username = user_context.get('username') or event.get('requestContext', {}).get('authorizer', {}).get('principalId')
        
        body = json.loads(event.get('body', '{}'))
        
        # New Schema Extraction
        local_id = body.get('local_id')
        productos = body.get('productos', [])
        costo_user = body.get('costo')
        direccion = body.get('direccion')
        estado_inicial = body.get('estado', 'procesando')

        if not local_id or not productos:
             return response(400, {"error": "Faltan datos requeridos (local_id, productos)"})

        # 1. Validate Stock and Calculate Total
        table_products = get_table(TABLE_PRODUCTS)
        total_price = 0.0
        
        items_internal = [] # Standardize for internal use
        for p in productos:
            pid = p.get('producto_id')
            qty = int(p.get('cantidad', 1))
            items_internal.append({'product_id': pid, 'quantity': qty})
        
        # Verification pass
        for item in items_internal:
            product_id = item['product_id']
            quantity = item['quantity']
            
            p_res = table_products.get_item(Key={'local_id': local_id, 'producto_id': product_id})
            if 'Item' not in p_res:
                 return response(400, {"error": f"Producto {product_id} no existe en {local_id}"})
            
            product = p_res['Item']
            stock = int(product.get('stock', 0))
            if stock < quantity:
                return response(400, {"error": f"Stock insuficiente para {product.get('nombre')}"})
            
            total_price += float(product.get('precio', 0)) * quantity

        # Update Stock pass (Decrement)
        for item in items_internal:
            product_id = item['product_id']
            quantity = item['quantity']
            
            table_products.update_item(
                Key={'local_id': local_id, 'producto_id': product_id},
                UpdateExpression="set stock = stock - :val",
                ExpressionAttributeValues={':val': quantity},
                ReturnValues="UPDATED_NEW"
            )

        # 2. Create Order
        order_id = str(uuid.uuid4())
        timestamp = int(time.time())
        iso_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp))
        
        table_orders = get_table(TABLE_ORDERS)
        item_order = {
            'local_id': local_id,      # PK
            'pedido_id': order_id,     # SK
            'correo': username,        # GSI Key
            'user_id': username,       # Legacy
            'status': estado_inicial,
            'items': items_internal,
            'productos': productos,    # Store original format too
            'total_price': str(costo_user if costo_user else total_price), 
            'direccion': direccion,
            'created_at': iso_time,
            'updated_at': iso_time
        }
        table_orders.put_item(Item=item_order)

        # 3. Start Workflow
        sf_input = json.dumps({
            "order_id": order_id,
            "local_id": local_id, # Pass to SF for callbacks
            "items": items_internal
        })
        
        stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=order_id,
            input=sf_input
        )

        return response(201, {"message": "Pedido creado", "order_id": order_id})

    except Exception as e:
        print(f"Error creating order: {e}")
        return response(500, {"error": "Error creando pedido"})
