import json
import uuid
import os
import re
import boto3
from datetime import datetime, timedelta
from src.common import response, get_table, hash_password, TABLE_USERS

# Environment variable for tokens table
TOKENS_TABLE_USERS = os.environ.get("TOKENS_TABLE_USERS")

ALLOWED_ROLES = {"Cliente", "Gerente", "Admin", "Cocinero", "Driver"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def register_user(event, context):
    try:
        body = json.loads(event.get("body") or "{}")

        nombre = (body.get("nombre") or "").strip()
        correo_raw = (body.get("correo") or "").strip()
        contrasena = (body.get("contrasena") or "")
        username = (body.get("username") or "").strip() # Support username if needed, but email is primary PK usually
        role = (body.get("role") or "Cliente").strip()

        # Normalizar correo
        correo = correo_raw.lower()
        
        # Fallback if username is used as PK in legacy code, but user requested email based register.
        # Based on user snippet, they used 'correo' as PK for existence check.
        # However, serverless.yml defines 'username' as PK for TABLE_USERS (Burger-Users-dev).
        # We need to adapt. The user snippet implies 'correo' PK, but existing dynamo has 'username'.
        # Let's check TABLE_USERS definition in serverless.yml again or assume we might need to query by index or change PK.
        # Actually, let's look at the existing login.py: it uses 'username'.
        # The user REQUESTED valid logic with 'correo'. 
        # I will use 'username' as the Partition Key to match existing infrastructure, 
        # but I will also store 'correo'. If they want 'correo' as login, they should probably map it.
        # For this implementation, I will assume 'username' is required OR use correo as username.
        
        target_username = username if username else correo
        
        if not (target_username and contrasena and role):
            return response(400, {"error": "Faltan datos requeridos"})

        if role not in ALLOWED_ROLES:
            return response(400, {"error": f"Rol inválido. Permitidos: {list(ALLOWED_ROLES)}"})

        table_users = get_table(TABLE_USERS)
        
        # Check if user exists
        # If PK is username
        res = table_users.get_item(Key={'username': target_username})
        if 'Item' in res:
            return response(400, {"error": "El usuario ya existe"})

        # Register User
        hashed = hash_password(contrasena)
        
        new_user = {
            'username': target_username,
            'correo': correo,
            'password': hashed, # Storing as 'password' to match login.py legacy or 'contrasena'
            # Note: login.py checked 'password' field. User snippet uses 'contrasena'. 
            # I will store BOTH or stick to one. login.py uses 'password'. I will update login.py later.
            # I will store 'password' (for legacy compat) AND 'contrasena' (for user preference) or just standardize.
            # The plan said "Update login.py". So I can standardize on 'password' (hashed).
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
