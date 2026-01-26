import json
import os
import decimal
import boto3
from typing import Any, Dict

# Inicializar recursos AWS fuera de los handlers para reutilizar conexiones
dynamodb = boto3.resource('dynamodb')
stepfunctions = boto3.client('stepfunctions')

TABLE_USERS = os.environ.get('TABLE_USERS')
TABLE_ORDERS = os.environ.get('TABLE_ORDERS')
TABLE_PRODUCTS = os.environ.get('TABLE_PRODUCTS')
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN')

class DecimalEncoder(json.JSONEncoder):
    """Ayuda a serializar tipos Decimal de DynamoDB a JSON."""
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

def response(status_code: int, body: Any) -> Dict:
    """Genera una respuesta estándar para API Gateway."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
        },
        "body": json.dumps(body, cls=DecimalEncoder)
    }

def get_table(table_name):
    return dynamodb.Table(table_name)
