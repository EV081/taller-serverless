import json
import os
import decimal
import boto3
from typing import Any, Dict

# Inicializar recursos AWS
dynamodb = boto3.resource('dynamodb')
stepfunctions = boto3.client('stepfunctions')

TABLE_USERS = os.environ.get('TABLE_USERS')
TABLE_ORDERS = os.environ.get('TABLE_ORDERS')
TABLE_PRODUCTS = os.environ.get('TABLE_PRODUCTS')
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

def response(status_code: int, body: Any) -> Dict:
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

import hashlib
from datetime import datetime

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
