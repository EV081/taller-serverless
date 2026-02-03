import json
import os
import boto3
from datetime import datetime

stepfunctions = boto3.client('stepfunctions')

def handler(event, context):
    print(f"Evento recibido: {json.dumps(event)}")
    
    try:
        # Extraer datos del evento de EventBridge
        detail = event.get('detail', {})
        order_id = detail.get('order_id')
        local_id = detail.get('local_id')
        
        if not order_id or not local_id:
            raise ValueError("Faltan campos requeridos: order_id o local_id")
        
        # ARN del Step Function
        state_machine_arn = os.environ['STATE_MACHINE_ARN']
        
        # Nombre único para la ejecución
        execution_name = f"order-{order_id}-{int(datetime.now().timestamp())}"
        
        # Iniciar la ejecución del Step Function
        response = stepfunctions.start_execution(
            stateMachineArn=state_machine_arn,
            name=execution_name,
            input=json.dumps(detail)
        )
        
        print(f"Step Function iniciado: {response['executionArn']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Step Function iniciado exitosamente',
                'executionArn': response['executionArn'],
                'startDate': response['startDate'].isoformat()
            })
        }
        
    except Exception as e:
        print(f"Error al iniciar Step Function: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
