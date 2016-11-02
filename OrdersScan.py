from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal
from boto3.dynamodb.conditions import Key, Attr
import sys

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

if len(sys.argv) != 2:
    print("Usage: python3 {} local|remote".format(sys.argv[0]))
    sys.exit(1)

if sys.argv[1] == "remote":
    endpoint = "https://dynamodb.us-east-1.amazonaws.com"
else:
    endpoint = "http://localhost:8000"

#endpoint="https://dynamodb.us-east-1.amazonaws.com"
#endpoint="http://localhost:8000"

dynamodb = boto3.resource('dynamodb',endpoint_url=endpoint)

table = dynamodb.Table('orders')

response = table.scan(
    FilterExpression=Attr('Info.CreatedTicks').gt(0)
)

for i in response['Items']:
    print(i)

from __future__ import print_function # Python 2/3 compatibility
import boto3

tableName ='orders'

table = dynamodb.create_table(
    TableName=tableName,
    KeySchema=[
        {
            'AttributeName': 'PosID',
            'KeyType': 'HASH'  #Partition key
        },
        {
            'AttributeName': 'OrderID',
            'KeyType': 'RANGE'  #Sort key
        }
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'PosID',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'OrderID',
            'AttributeType': 'S'
        },

    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 10,
        'WriteCapacityUnits': 10
    }
)

print("Table status:", table.table_status)
