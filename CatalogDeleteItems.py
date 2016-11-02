from __future__ import print_function # Python 2/3 compatibility
import boto3
from botocore.exceptions import ClientError
import json
import decimal
import sys
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

def deleteItem(catId, itemId):
    try:
        response = table.delete_item(
            Key={
	        'CatalogID': catId,
                'ItemID': itemId
            },
        )
    except ClientError as e:
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print(e.response['Error']['Message'])
        else:
            raise
    else:
        print("DeleteItem succeeded:")
        print(json.dumps(response, indent=4, cls=DecimalEncoder))

if len(sys.argv) != 3:
    print("Usage: python3 {} catalogId local|remote".format(sys.argv[0]))
    sys.exit(1)

catalogId = sys.argv[1]

if sys.argv[2] == "remote":
    endpoint = "https://dynamodb.us-east-1.amazonaws.com"
else:
    endpoint = "http://localhost:8000"

#endpoint="https://dynamodb.us-east-1.amazonaws.com"
#endpoint="http://localhost:8000"

inp = input('Enter the name of the table, to confirm:')
if inp != 'catalog':
    print('Table name is not correct')
    sys.exit(1)

dynamodb = boto3.resource('dynamodb',endpoint_url=endpoint)
table = dynamodb.Table('catalog')

response = table.query(
    KeyConditionExpression=Key('CatalogID').eq(catalogId),
    FilterExpression=Attr('Info.CreatedTicks').gt(0)
)

print("Number of items:{}".format(len(response['Items'])))
listOfItems = response['Items']
listOfItemsByTime = sorted(listOfItems, key=lambda item: item['Info']['CreatedTicks'])
count = 0
for o in listOfItemsByTime:
    count = count + 1
    print("Item: {}".format(count))
    itemId = o['ItemID']
    print('CatalogID:{} ItemID:{}'.format(catalogId, itemId))
    deleteItem(catalogId, itemId)
