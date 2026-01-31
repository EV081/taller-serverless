"""
Lambda handler para responder al Step Function con taskToken
Endpoint HTTP para que cocina/delivery respondan con ACEPTAR o RECHAZADO
"""
import json
import os
import boto3

stepfunctions = boto3.client('stepfunctions')

def handler(event, context):
    """
    Resume la ejecución del Step Function enviando el resultado del callback
    
    HTTP Request (POST /callback/responder):
    {
        "taskToken": "AQCEAAAAKgAAAAMAAA...",
        "decision": "ACEPTAR" | "RECHAZADO",
        "empleado_correo": "cocinero@burger.com",
        "notas": "Todo listo, pedido preparado"
    }
    """
    print(f"Request recibido: {json.dumps(event)}")
    
    try:
        # Parsear body del request
        body = json.loads(event.get('body', '{}'))
        
        task_token = body.get('taskToken')
        decision = body.get('decision', 'RECHAZADO')
        
        if not task_token:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Falta campo requerido: taskToken'
                })
            }
        
        if decision not in ['ACEPTAR', 'RECHAZADO']:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'decision debe ser ACEPTAR o RECHAZADO'
                })
            }
        
        # Preparar output para el Step Function
        output = {
            'decision': decision,
            'empleado_correo': body.get('empleado_correo', 'UNKNOWN'),
            'notas': body.get('notas', ''),
            'timestamp': body.get('timestamp', '')
        }
        
        # Enviar success al Step Function
        stepfunctions.send_task_success(
            taskToken=task_token,
            output=json.dumps(output)
        )
        
        print(f"✅ Callback enviado: decision={decision}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Callback procesado exitosamente',
                'decision': decision
            })
        }
        
    except stepfunctions.exceptions.TaskTimedOut:
        print("⚠️ El taskToken expiró (timeout)")
        return {
            'statusCode': 410,
            'body': json.dumps({
                'error': 'El token de tarea expiró'
            })
        }
        
    except stepfunctions.exceptions.InvalidToken:
        print("❌ Token inválido")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Token de tarea inválido'
            })
        }
        
    except Exception as e:
        print(f"❌ Error al procesar callback: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
