from __future__ import print_function # Python 2/3 compatibility
import boto3
import sys

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
