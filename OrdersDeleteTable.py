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

tableName = "orders"

dynamodb = boto3.resource('dynamodb',endpoint_url=endpoint)

table = dynamodb.Table(tableName)

table.delete()
