import json
import uuid
import time
import os
import boto3
from common import response, get_table, TABLE_ORDERS, STATE_MACHINE_ARN, stepfunctions

# Env vars
TABLE_PRODUCTS = os.environ.get('TABLE_PRODUCTS')
TABLE_HISTORIAL_ESTADOS = os.environ.get('TABLE_HISTORIAL_ESTADOS')

def create_order(event, context):
    try:
        user_context = event.get('requestContext', {}).get('authorizer', {})
        # Note: 'username' might come from principalId or context depending on Authorizer
        # Our authorizer returns context with username.
        username = user_context.get('username') or event.get('requestContext', {}).get('authorizer', {}).get('principalId')
        
        body = json.loads(event.get('body', '{}'))
        items = body.get('items', []) 

        if not items:
            return response(400, {"error": "El pedido debe tener items"})
        
        # 1. Validate Stock and Calculate Total
        table_products = get_table(TABLE_PRODUCTS)
        total_price = 0
        
        # Logic: We need to decrement stock. Because this is distributed, ideally we use transactions.
        # For simplicity in this workshop, we iterate and update.
        # If any product has insufficient stock, we abort.
        # CAUTION: Race conditions are possible here without transactions (TransactWriteItems).
        # We will assume happy path or simple check-then-act for workshop scope, 
        # OR implement simple decrement.
        
        # Verification pass
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            
            p_res = table_products.get_item(Key={'product_id': product_id})
            if 'Item' not in p_res:
                 return response(400, {"error": f"Producto {product_id} no existe"})
            
            product = p_res['Item']
            stock = int(product.get('stock', 0))
            if stock < quantity:
                return response(400, {"error": f"Stock insuficiente para {product.get('name')}"})
            
            total_price += float(product.get('price', 0)) * quantity

        # Update Stock pass (Decrement)
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            
            table_products.update_item(
                Key={'product_id': product_id},
                UpdateExpression="set stock = stock - :val",
                ExpressionAttributeValues={':val': quantity},
                ReturnValues="UPDATED_NEW"
            )

        # 2. Create Order
        order_id = str(uuid.uuid4())
        timestamp = int(time.time())
        iso_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp))
        
        # FIXED: Use consistent LOCAL_ID matching DataGenerator
        local_id = "BURGER-LOCAL-001"

        table_orders = get_table(TABLE_ORDERS)
        item_order = {
            'local_id': local_id,      # PK
            'pedido_id': order_id,     # SK
            'correo': username,        # GSI Key (Important for list_my_orders)
            'user_id': username,       # Legacy/Backup
            'status': 'CREADO',
            'items': items,
            'total_price': str(total_price), 
            'created_at': iso_time,
            'updated_at': iso_time
        }
        table_orders.put_item(Item=item_order)

        # 3. Log History
        table_history = get_table(TABLE_HISTORIAL_ESTADOS)
        history_id = str(uuid.uuid4())
        table_history.put_item(Item={
            'history_id': history_id,
            'order_id': order_id, # This table uses order_id as PK, so this is fine if schema matches
            'status': 'CREADO',
            'timestamp': iso_time
        })

        # 4. Start Workflow
        sf_input = json.dumps({
            "order_id": order_id,
            "local_id": local_id, # Pass to SF for callbacks
            "items": items
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
