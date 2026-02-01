from common import get_table, TABLE_PRODUCTS

def validate_stock(event, context):
    products_table = get_table(TABLE_PRODUCTS)
    
    # Extract local_id and items from event
    local_id = event.get('local_id', 'BURGER-LOCAL-001')
    items = event.get('items', [])
    
    for item in items:
        pid = item.get('product_id')
        qty = item.get('quantity', 1)
        
        # Use composite key: local_id (PK) and producto_id (SK)
        res = products_table.get_item(Key={'local_id': local_id, 'producto_id': pid})
        product = res.get('Item')
        
        if not product:
            raise Exception(f"Product {pid} not found")
        
        stock = int(product.get('stock', 0))
        if stock < qty:
            raise Exception(f"Insufficient stock for {product.get('nombre', pid)}")
    
    return {"status": "OK", "message": "Stock validated"}
