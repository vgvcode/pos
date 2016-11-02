from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal
import time
from boto3.dynamodb.conditions import Key, Attr

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")

table = dynamodb.Table('catalog')
print("Items with price higher than 25")
response = table.query(
    KeyConditionExpression=Key('CatalogID').eq('SRC_CAT100'),
    FilterExpression=Attr('Info.Price').gt(decimal.Decimal(25))
)
for i in response['Items']:
    print(i['CatalogID'], ":", i['ItemID'], i['Info'])
