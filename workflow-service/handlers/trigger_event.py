import json
import boto3
from datetime import datetime

eventbridge = boto3.client('events')

def handler(event, context):
    print(f"Request recibido: {json.dumps(event)}")
    
    try:
        # Parsear body
        body = json.loads(event.get('body', '{}'))
        
        source = body.get('source', 'burger.testing')
        detail_type = body.get('detailType', 'TestEvent')
        detail = body.get('detail', {})
        
        # Construir entrada del evento
        event_entry = {
            'Source': source,
            'DetailType': detail_type,
            'Detail': json.dumps(detail),
            'EventBusName': 'default'
        }
        
        # Publicar evento
        response = eventbridge.put_events(
            Entries=[event_entry]
        )
        
        # Verificar si fue exitoso
        if response['FailedEntryCount'] > 0:
            raise Exception(f"Error al publicar evento: {response['Entries']}")
        
        print(f"Evento publicado: {source} -> {detail_type}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Evento publicado exitosamente',
                'source': source,
                'detailType': detail_type,
                'eventId': response['Entries'][0].get('EventId', '')
            })
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Body inválido, debe ser JSON'
            })
        }
        
    except Exception as e:
        print(f"Error al publicar evento: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
