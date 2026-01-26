import boto3
import os
import decimal

def seed():
    stage = os.environ.get('STAGE', 'dev')
    table_users_name = f"Burger-Users-{stage}"
    table_products_name = f"Burger-Products-{stage}"
    
    dynamodb = boto3.resource('dynamodb')
    table_users = dynamodb.Table(table_users_name)
    table_products = dynamodb.Table(table_products_name)
    
    print(f"Seed data into {table_users_name} and {table_products_name}...")

    users = [
        {'username': 'cliente1', 'password': 'password123', 'role': 'USER'},
        {'username': 'cocinero1', 'password': 'password123', 'role': 'COOK'},
        {'username': 'driver1', 'password': 'password123', 'role': 'DRIVER'},
         {'username': 'admin1', 'password': 'password123', 'role': 'ADMIN'},
    ]

    for u in users:
        try:
            table_users.put_item(Item=u)
            print(f"User added: {u['username']}")
        except Exception as e:
            print(f"Error adding user {u['username']}: {e}")

    products = [
        {'product_id': 'hamb-clasica', 'name': 'Hamburguesa Clásica', 'price': 15.00, 'stock': 100},
        {'product_id': 'hamb-queso', 'name': 'Hamburguesa con Queso', 'price': 18.00, 'stock': 50},
        {'product_id': 'papas-fritas', 'name': 'Papas Fritas', 'price': 8.00, 'stock': 200},
        {'product_id': 'gaseosa', 'name': 'Gaseosa 500ml', 'price': 5.00, 'stock': 0},
    ]

    for p in products:
        p['price'] = str(p['price'])
        try:
           table_products.put_item(Item=p)
           print(f"Product added: {p['name']}")
        except Exception as e:
            print(f"Error adding product {p['name']}: {e}")

    print("Seed completed!")

if __name__ == "__main__":
    seed()
