from __future__ import print_function # Python 2/3 compatibility
import boto3

#endpoint="https://dynamodb.us-east-1.amazonaws.com")
endpoint="http://localhost:8000"
dynamodb = boto3.resource('dynamodb',endpoint_url=endpoint)
tableName ='catalog'


table = dynamodb.create_table(
    TableName=tableName,
    KeySchema=[
        {
            'AttributeName': 'CatalogID',
            'KeyType': 'HASH'  #Partition key
        },
        {
            'AttributeName': 'ItemID',
            'KeyType': 'RANGE'  #Sort key
        }
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'CatalogID',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'ItemID',
            'AttributeType': 'S'
        },

    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 10,
        'WriteCapacityUnits': 10
    }
)

print("Table status:", table.table_status)
