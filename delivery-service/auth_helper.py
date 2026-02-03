import os
import json
import boto3
from typing import Tuple

lambda_client = boto3.client('lambda')

def get_bearer_token(event: dict) -> str:
    auth_header = event.get('headers', {}).get('Authorization') or event.get('headers', {}).get('authorization')
    
    if not auth_header:
        return ""

    if auth_header.lower().startswith('bearer '):
        return auth_header[7:].strip()
    
    return auth_header.strip()


def validate_token_via_lambda(token: str) -> Tuple[bool, str, str]:
    if not token:
        return (False, "Token no proporcionado", "")
    
    lambda_name = os.environ.get('VALIDAR_TOKEN_LAMBDA_NAME')
    
    if not lambda_name:
        print("VALIDAR_TOKEN_LAMBDA_NAME not configured")
        return (False, "Configuración de validación no disponible", "")
    
    try:
        response = lambda_client.invoke(
            FunctionName=lambda_name,
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'authorizationToken': f'Bearer {token}',
                'methodArn': 'arn:aws:execute-api:*:*:*'
            })
        )
        
        payload = json.loads(response['Payload'].read())
        
        policy_document = payload.get('policyDocument', {})
        statements = policy_document.get('Statement', [])
        
        is_valid = any(stmt.get('Effect') == 'Allow' for stmt in statements)
        
        if not is_valid:
            return (False, "Token inválido o expirado", "")
        
        context = payload.get('context', {})
        role = context.get('role', '')
        
        return (True, "", role)
        
    except Exception as e:
        print(f"Error validating token: {e}")
        return (False, f"Error al validar token: {str(e)}", "")
