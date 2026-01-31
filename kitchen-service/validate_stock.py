from common import get_table, TABLE_PRODUCTS

def validate_stock(event, context):
    items = event.get('items', [])
    products_table = get_table(TABLE_PRODUCTS)
    
    for item in items:
        pid = item.get('product_id')
        qty = item.get('quantity', 1)
        
        res = products_table.get_item(Key={'product_id': pid})
        if 'Item' not in res:
            raise Exception("ProductNotFound")
        
        stock = res['Item'].get('stock', 0)
        if stock < qty:
            raise Exception("StockError")
        
    return event


