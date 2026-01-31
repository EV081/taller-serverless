"""
Lambda handler para cambiar el estado del pedido
Triggereado por EventBridge cuando cocina/delivery cambian estados
"""
import json
import os
import boto3
from datetime import datetime
import uuid

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    """
    Registra cambios de estado en la tabla Burger-Historial-Estados
    
    Event format (EventBridge):
    {
        "source": "burger.cocina" | "burger.delivery" | "burger.cliente",
        "detail-type": "EnPreparacion" | "CocinaCompleta" | "Empaquetado" | "EnCamino" | "Entregado" | "ConfirmarPedido",
        "detail": {
            "pedido_id": "UUID",
            "local_id": "local_001",
            "estado_nuevo": "COCINANDO",
            "empleado_correo": "cocinero@burger.com",
            "notas": "..."
        }
    }
    """
    print(f"Evento recibido: {json.dumps(event)}")
    
    try:
        # Tabla de historial
        table_name = os.environ['TABLE_ORDER_HISTORY']
        table = dynamodb.Table(table_name)
        
        # Extraer datos del evento
        source = event.get('source', '')
        detail_type = event.get('detail-type', '')
        detail = event.get('detail', {})
        
        pedido_id = detail.get('pedido_id')
        estado_nuevo = detail.get('estado_nuevo', detail_type)
        
        if not pedido_id:
            raise ValueError("Falta campo requerido: pedido_id")
        
        # Crear registro de historial
        estado_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        item = {
            'pedido_id': pedido_id,
            'estado_id': estado_id,
            'estado': estado_nuevo,
            'timestamp': timestamp,
            'source': source,
            'detail_type': detail_type,
            'empleado_correo': detail.get('empleado_correo', 'SYSTEM'),
            'notas': detail.get('notas', ''),
            'metadata': json.dumps(detail)
        }
        
        # Insertar en DynamoDB
        table.put_item(Item=item)
        
        print(f"✅ Estado registrado: {pedido_id} -> {estado_nuevo}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Estado registrado exitosamente',
                'pedido_id': pedido_id,
                'estado_id': estado_id,
                'estado': estado_nuevo
            })
        }
        
    except Exception as e:
        print(f"❌ Error al registrar estado: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
