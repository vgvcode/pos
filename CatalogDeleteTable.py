#!/usr/bin/python
from __future__ import print_function # Python 2/3 compatibility
import boto3
import sys

if len(sys.argv) != 3:
    print("Usage: python3 {} local|remote tablename".format(sys.argv[0]))
    sys.exit(1)

if sys.argv[1] == "remote":
    endpoint = "https://dynamodb.us-east-1.amazonaws.com"
else:
    endpoint = "http://localhost:8000"

tableName = sys.argv[2]

dynamodb = boto3.resource('dynamodb',endpoint_url=endpoint)

table = dynamodb.Table(tableName)

table.delete()
