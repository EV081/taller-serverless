import json
import uuid
import os
import boto3
from datetime import datetime, timedelta
from common import response, get_table, hash_password, TABLE_USERS

TOKENS_TABLE_USERS = os.environ.get("TOKENS_TABLE_USERS")

def login(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        # Accept email or username, treat as email/PK
        email = body.get('correo') 
        password = body.get('contrasena')

        if not email or not password:
            return response(400, {"error": "Faltan credenciales (email y password)"})

        table = get_table(TABLE_USERS)
        # Schema uses 'correo' as PK
        result = table.get_item(Key={'correo': email})
        
        user = result.get('Item')
        
        if not user:
            return response(401, {"error": "Credenciales inválidas (Usuario no encontrado)"})

        # Validate password (check hash)
        # Check 'password' (new standard) or 'contrasena' (legacy/datagen)
        stored_password = user.get('password') or user.get('contrasena')
        input_hash = hash_password(password)
        
        if stored_password != input_hash:
             # Fallback for plain text passwords (like from DataGenerator without hashing)
            if stored_password != password:
                return response(401, {"error": "Credenciales inválidas (Password incorrecto)"})

        # Generate Token
        token = str(uuid.uuid4())
        role = user.get('role', 'Cliente')
        expires = datetime.now() + timedelta(minutes=60)
        expires_str = expires.strftime('%Y-%m-%d %H:%M:%S')

        # Store Token in DynamoDB
        token_record = {
            'token': token,
            'user_id': email, # FIXED: using email from input
            'rol': role,
            'expires': expires_str
        }
        
        table_tokens = get_table(TOKENS_TABLE_USERS)
        table_tokens.put_item(Item=token_record)

        return response(200, {
            "token": token,
            "role": role,
            "expires": expires_str
        })

    except Exception as e:
        print(e)
        return response(500, {"error": "Error interno"})
