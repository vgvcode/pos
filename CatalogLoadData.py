from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal

#endpoint = "https://dynamodb.us-east-1.amazonaws.com"
endpoint = "http://localhost:8000"
tableName = "catalog"
dynamodb = boto3.resource('dynamodb',endpoint_url=endpoint)
table = dynamodb.Table(tableName)

with open("catalogdata.json") as json_file:
    orders = json.load(json_file, parse_float = decimal.Decimal)
    for order in orders:
        CatalogID = order['CatalogID']
        ItemID = order['ItemID']
        Info = order['Info']

        print("Adding order:", CatalogID, ItemID, Info)

        table.put_item(
           Item={
               'CatalogID': CatalogID,
               'ItemID': ItemID,
               'Info': Info
            }
        )
