from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

endpoint="http://localhost:8000"
#endpoint="https://dynamodb.us-east-1.amazonaws.com"
dynamodb = boto3.resource("dynamodb", endpoint_url=endpoint)

table = dynamodb.Table('catalog')

CatalogID = 'Cat123'
ItemID = '12345'

try:
    response = table.get_item(
        Key={
            'CatalogID': CatalogID,
            'ItemID': ItemID
        }
    )
except ClientError as e:
    print(e.response['Error']['Message'])
else:
    item = response['Item']
    print("GetItem succeeded:")
    print(json.dumps(item, indent=4, cls=DecimalEncoder))
