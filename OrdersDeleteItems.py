from __future__ import print_function # Python 2/3 compatibility
import boto3
from botocore.exceptions import ClientError
import json
import decimal
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

def deleteOrder(posId, orderId):
    try:
        response = table.delete_item(
            Key={
                'PosID': posId,
	        'OrderID': orderId
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
    print("Usage: python3 {} posId local|remote".format(sys.argv[0]))
    sys.exit(1)

posId = sys.argv[1]

if sys.argv[2] == "remote":
    endpoint = "https://dynamodb.us-east-1.amazonaws.com"
else:
    endpoint = "http://localhost:8000"

#endpoint="https://dynamodb.us-east-1.amazonaws.com"
#endpoint="http://localhost:8000"

dynamodb = boto3.resource('dynamodb',endpoint_url=endpoint)

table = dynamodb.Table('orders')

response = table.query(
    KeyConditionExpression=Key('PosID').eq('PosGNChettyRoadCafe'),
    FilterExpression=Attr('Info.CreatedTicks').gt(0)
)

print("Number of orders:{}".format(len(response['Items'])))
listOfOrders = response['Items']
listOfOrdersByTime = sorted(listOfOrders, key=lambda order: order['Info']['CreatedTicks'])
count = 0
for o in listOfOrdersByTime:
    count = count + 1
    print("Order: {}".format(count))
    orderId = o['OrderID']
    print('PosID:{} OrderID:{}'.format(posId, orderId))
    deleteOrder(posId, orderId)
