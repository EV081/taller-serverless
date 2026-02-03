import json
import uuid
import os
import re
import boto3
from datetime import datetime, timedelta
from common import response, get_table, hash_password, TABLE_USERS

TOKENS_TABLE_USERS = os.environ.get("TOKENS_TABLE_USERS")

ALLOWED_ROLES = {"Cliente", "Gerente", "Admin", "Cocinero", "Driver"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def register_user(event, context):
    try:
        body = json.loads(event.get("body") or "{}")

        nombre = (body.get("nombre") or "").strip()
        correo_raw = (body.get("correo") or "").strip()
        contrasena = (body.get("contrasena") or "")
        username = (body.get("username") or "").strip()
        role = (body.get("role") or "Cliente").strip()

        correo = correo_raw.lower()
        
        target_username = username if username else correo
        
        if not (target_username and contrasena and role):
            return response(400, {"error": "Faltan datos requeridos"})

        if role not in ALLOWED_ROLES:
            return response(400, {"error": f"Rol inválido. Permitidos: {list(ALLOWED_ROLES)}"})

        table_users = get_table(TABLE_USERS)
        
        res = table_users.get_item(Key={'correo': correo})
        if 'Item' in res:
            return response(400, {"error": "El usuario ya existe"})

        hashed = hash_password(contrasena)
        
        new_user = {
            'correo': correo, 
            'username': target_username or correo,
            'password': hashed, 
            'role': role,
            'nombre': nombre,
            'created_at': datetime.utcnow().isoformat()
        }
        
        table_users.put_item(Item=new_user)

        # Generate Token
        token = str(uuid.uuid4())
        expires = datetime.now() + timedelta(minutes=60)
        expires_str = expires.strftime('%Y-%m-%d %H:%M:%S')
        
        token_record = {
            'token': token,
            'user_id': target_username,
            'rol': role,
            'expires': expires_str
        }
        
        # Store token
        table_tokens = get_table(TOKENS_TABLE_USERS)
        table_tokens.put_item(Item=token_record)

        return response(201, {
            "message": "Usuario registrado",
            "username": target_username,
            "token": token,
            "expires": expires_str,
            "role": role
        })

    except Exception as e:
        print(e)
        return response(500, {"error": str(e)})
