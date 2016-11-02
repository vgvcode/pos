from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

#endpoint = "https://dynamodb.us-east-1.amazonaws.com"
endpoint = "http://localhost:8000"
tableName = "catalog"

dynamodb = boto3.resource('dynamodb',endpoint_url=endpoint)

table = dynamodb.Table(tableName)

CatalogID = 'Cat123'
ItemID = '12345' 

response = table.put_item(
   Item={
        'CatalogID': CatalogID,
        'ItemID': ItemID,
        'Info': {
            'Created Time': '05Oct2016',
            'Updated Time': '06Oct2016',
            'Name': 'IDLI',
            'Price': decimal.Decimal(25)
        }
    }
)

print("PutItem succeeded:")
print(json.dumps(response, indent=4, cls=DecimalEncoder))
