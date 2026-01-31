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
        username = body.get('username')
        password = body.get('password')

        if not username or not password:
            return response(400, {"error": "Faltan credenciales"})

        table = get_table(TABLE_USERS)
        result = table.get_item(Key={'username': username})
        
        user = result.get('Item')
        
        if not user:
            return response(401, {"error": "Credenciales inválidas"})

        # Validate password (check hash)
        # Assuming database stores HASHED password in 'password' field as per my register.py
        stored_password = user.get('password')
        input_hash = hash_password(password)
        
        if stored_password != input_hash:
             # Fallback for legacy plain text passwords if any exist (optional but good for transition)
            if stored_password != password:
                return response(401, {"error": "Credenciales inválidas"})

        # Generate Token
        token = str(uuid.uuid4())
        role = user.get('role', 'Cliente')
        expires = datetime.now() + timedelta(minutes=60)
        expires_str = expires.strftime('%Y-%m-%d %H:%M:%S')

        # Store Token in DynamoDB
        token_record = {
            'token': token,
            'user_id': username,
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
