import json
import os
import boto3
from datetime import datetime

stepfunctions = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')

def get_table(table_name):
    return dynamodb.Table(table_name)

def handler(event, context):
    print(f"Request recibido: {json.dumps(event)}")
    
    try:
        # ------- 1. Validación de Token y Rol (RBAC) -------
        token = event.get('headers', {}).get('authorization') or event.get('headers', {}).get('Authorization')
        if not token:
            return {'statusCode': 401, 'body': json.dumps({'error': 'Falta header Authorization'})}
        
        if token.lower().startswith('bearer '):
            token = token[7:]
            
        # Buscar token en DynamoDB
        tokens_table_name = os.environ.get('TABLE_TOKENS_USUARIOS', 'Burger-Tokens-Usuarios')
        tokens_table = get_table(tokens_table_name)
        token_item = tokens_table.get_item(Key={'token': token})
        user_data = token_item.get('Item')
        
        if not user_data:
            return {'statusCode': 401, 'body': json.dumps({'error': 'Token inválido o expirado'})}
            
        user_role = user_data.get('rol', '').lower()
        print(f"Usuario autenticado: {user_data.get('user_id')} - Rol: {user_role}")
        
        # ------- 2. Parsear Body -------
        body = json.loads(event.get('body', '{}'))
        task_token = body.get('taskToken')
        decision = body.get('decision', 'RECHAZADO')
        stage = body.get('stage', 'unknown').lower()
        
        if not task_token:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Falta campo requerido: taskToken'})}
            
        if decision not in ['ACEPTAR', 'RECHAZADO']:
            return {'statusCode': 400, 'body': json.dumps({'error': 'decision debe ser ACEPTAR o RECHAZADO'})}

        
        authorized = False
        
        if stage == 'cocina':
            if user_role in ['cocina', 'cocinero', 'gerente']:
                authorized = True
        elif stage == 'delivery':
            if user_role in ['repartidor', 'delivery', 'gerente']:
                authorized = True
        else:
            print("No se especificó 'stage', validación laxa de roles")
            if user_role in ['cocina', 'cocinero', 'repartidor', 'delivery', 'gerente']:
                authorized = True
        
        if not authorized:
            print(f"Acceso denegado. Rol '{user_role}' no tiene permiso para stage '{stage}'")
            return {
                'statusCode': 403, 
                'body': json.dumps({
                    'error': f'Acceso denegado: El rol {user_role} no puede confirmar acciones de {stage}'
                })
            }

        # ------- 4. Enviar Callback a Step Functions -------
        output = {
            'decision': decision,
            'empleado_id': user_data.get('user_id'),
            'empleado_rol': user_role,
            'stage_confirmed': stage,
            'timestamp': datetime.now().isoformat()
        }
        
        stepfunctions.send_task_success(
            taskToken=task_token,
            output=json.dumps(output)
        )
        
        print(f"Callback enviado: decision={decision} por {user_role}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Callback procesado exitosamente',
                'decision': decision,
                'operator': user_role
            })
        }
        
    except stepfunctions.exceptions.TaskTimedOut:
        return {'statusCode': 410, 'body': json.dumps({'error': 'El token de tarea expiró'})}
    except stepfunctions.exceptions.InvalidToken:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Token de tarea inválido'})}
    except Exception as e:
        print(f"Error al procesar callback: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
