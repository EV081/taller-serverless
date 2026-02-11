import json
import uuid
import os
import boto3
from datetime import datetime, timedelta
from common import response, get_table, hash_password
from boto3.dynamodb.conditions import Key

TOKENS_TABLE_USERS = os.environ.get("TOKENS_TABLE_USERS")
TABLE_EMPLEADOS = os.environ.get("TABLE_EMPLEADOS")

def login_empleado(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('correo') 
        password = body.get('contrasena')

        if not email or not password:
            return response(400, {"error": "Faltan credenciales (correo y contrasena)"})

        
        table = get_table(TABLE_EMPLEADOS)
        
        scan_res = table.scan(
            FilterExpression=Key('correo').eq(email)
        )
        items = scan_res.get('Items', [])
        
        if not items:
            return response(401, {"error": "Credenciales inválidas (Empleado no encontrado)"})
            
        user = items[0]

        # Validate password (check hash or fallback)
        stored_password = user.get('password') or user.get('contrasena')
        input_hash = hash_password(password)
        
        if stored_password != input_hash:
             # Fallback for plain text
            if stored_password != password:
                return response(401, {"error": "Credenciales inválidas (Password incorrecto)"})

        # Generate Token
        token = str(uuid.uuid4())
        role = user.get('role', 'Empleado')
        expires = datetime.now() + timedelta(minutes=60)
        expires_str = expires.strftime('%Y-%m-%d %H:%M:%S')

        # Store Token in DynamoDB
        token_record = {
            'token': token,
            'user_id': email,
            'rol': role,
            'type': 'empleado',
            'expires': expires_str
        }
        
        table_tokens = get_table(TOKENS_TABLE_USERS)
        table_tokens.put_item(Item=token_record)

        return response(200, {
            "token": token,
            "role": role,
            "expires": expires_str,
            "message": "Login empleado exitoso"
        })

    except Exception as e:
        print(f"Error login_empleado: {e}")
        return response(500, {"error": "Error interno login empleado"})
