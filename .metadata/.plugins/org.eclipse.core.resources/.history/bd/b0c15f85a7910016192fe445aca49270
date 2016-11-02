from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal

#endpoint = "https://dynamodb.us-east-1.amazonaws.com"
endpoint = "http://localhost:8000"
tableName = "orders"
dynamodb = boto3.resource('dynamodb',endpoint_url=endpoint)
table = dynamodb.Table(tableName)

with open("ordersdata.json") as json_file:
    orders = json.load(json_file, parse_float = decimal.Decimal)
    for order in orders:
        PosID = order['PosID']
        OrderID = order['OrderID']
        Info = order['Info']

        print("Adding order:", PosID, OrderID, Info)

        table.put_item(
           Item={
               'PosID': PosID,
               'OrderID': OrderID,
               'Info': Info
            }
        )
