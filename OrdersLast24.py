from __future__ import print_function # Python 2/3 compatibility
import sys
import json
import decimal
import time
import boto3
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

#dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")

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
print("Orders created within 24 hours")
ticks = time.time() - 24*60*60
print("Ticks one day ago:{}".format(ticks))

response = table.query(
    KeyConditionExpression=Key('PosID').eq('PosGNChettyRoadCafe'),
    FilterExpression=Attr('Info.CreatedTicks').gt(decimal.Decimal(ticks))
)

print("Number of orders:{}".format(len(response['Items'])))
listOfOrders = response['Items']
listOfOrdersByTime = sorted(listOfOrders, key=lambda order: order['Info']['CreatedTicks'])
count = 0
for o in listOfOrdersByTime:
    count = count + 1
    print("Order: {}".format(count))
    print('PosID:{} OrderID:{}'.format(o['PosID'], o['OrderID']))
    for k in sorted(o['Info']):
        if k == 'ListOfItems':
            for elt in o['Info']['ListOfItems']:
                print(elt)
        else:
            print('{}:{}'.format(k, o['Info'][k]))
    print()
