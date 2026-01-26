import os
import boto3
from datetime import datetime
from src.common import get_table

TOKENS_TABLE_USERS = os.environ.get("TOKENS_TABLE_USERS")

def authorize(event, context):
    try:
        token = event.get('authorizationToken') or event.get('headers', {}).get('Authorization')
        
        if not token:
            return generate_policy('user', 'Deny', event['methodArn'])

        # Remove Bearer prefix if present
        if token.lower().startswith('bearer '):
            token = token[7:]

        # Validate against DynamoDB
        table = get_table(TOKENS_TABLE_USERS)
        result = table.get_item(Key={'token': token})
        
        item = result.get('Item')
        
        if not item:
            print("Token not found")
            return generate_policy('user', 'Deny', event['methodArn'])

        # Check expiration
        expires_str = item.get('expires')
        if expires_str:
            try:
                expires_dt = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S")
                if datetime.now() > expires_dt:
                    print("Token expired")
                    return generate_policy('user', 'Deny', event['methodArn'])
            except ValueError:
                # Handle possible format issues or skip if format doesn't match
                pass
        
        # Valid token
        user = item.get('user_id')
        role = item.get('rol')
        
        # Return Allow policy
        return generate_policy(user, 'Allow', event['methodArn'], context={'role': role, 'username': user})

    except Exception as e:
        print(f"Auth failed: {e}")
        return generate_policy('user', 'Deny', event['methodArn'])

def generate_policy(principal_id, effect, resource, context=None):
    auth_response = {
        'principalId': principal_id
    }
    
    if effect and resource:
        auth_response['policyDocument'] = {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': resource
            }]
        }
    
    if context:
        auth_response['context'] = context
        
    return auth_response
