"""
Utilidades comunes compartidas entre todos los servicios serverless.
"""
import json
import os
import decimal
import boto3
import hashlib
from typing import Any, Dict
from datetime import datetime

# Inicializar recursos AWS (reutilizables entre invocaciones)
dynamodb = boto3.resource('dynamodb')
stepfunctions = boto3.client('stepfunctions')

# Variables de entorno comunes
TABLE_USERS = os.environ.get('TABLE_USERS')
TABLE_EMPLOYEES = os.environ.get('TABLE_EMPLOYEES')
TABLE_LOCALS = os.environ.get('TABLE_LOCALS')
TABLE_ORDERS = os.environ.get('TABLE_ORDERS')
TABLE_PRODUCTS = os.environ.get('TABLE_PRODUCTS')
TABLE_ORDER_HISTORY = os.environ.get('TABLE_ORDER_HISTORY')
TABLE_TOKENS = os.environ.get('TABLE_TOKENS')
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN')


class DecimalEncoder(json.JSONEncoder):
    """Serializa tipos Decimal de DynamoDB a JSON."""
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
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


def get_table(table_name: str):
    """Obtiene una referencia a una tabla DynamoDB."""
    return dynamodb.Table(table_name)


def hash_password(password: str) -> str:
    """Hashea una contraseña usando SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def now_iso() -> str:
    """Retorna la fecha/hora actual en formato ISO."""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def now_timestamp() -> int:
    """Retorna timestamp Unix actual."""
    return int(datetime.utcnow().timestamp())
