#!/usr/bin/python
from __future__ import print_function # Python 2/3 compatibility
import json
from decimal import *
import time
import uuid
import boto3
from copy import deepcopy
from boto3.dynamodb.conditions import Key, Attr
import ordersmodule
import catalogmodule
import sqsmodule
     
def money(num):
    return Decimal(num).quantize(Decimal('.01'), rounding=ROUND_UP) 

def copyRemoteCatalogToLocal(catalogId, remoteEndpoint):
    'copy remote catalog to local and return local catalog'
    try:
        'fetch the remote catalog'
        remoteCat = catalogmodule.Catalog(catalogId, endpoint=remoteEndpoint)
        if remoteCat.fetchFromDB() == False: raise RuntimeError("Error: Could not fetch remote catalog:" + catalogId)  
        print("Fetched remote catalog")
        
        'copy the remote catalog to a dictionary'
        copyCatDict = remoteCat.get()
        
        'exit here if remote catalog is empty'
        if len(copyCatDict['items']) == 0: 
            print("Remote catalogmodule.Catalog empty")
            return
    
        print(copyCatDict)
        
        'create local catalog - this will fetch from local db if items are present'
        localCat = catalogmodule.Catalog(catalogId, endpoint="http://localhost:8000")
        
        'delete local table'
        if localCat.deleteTable() == False:
            print("No local table found for:" + catalogId)
        else:
            print("Deleted local table")
              
        'recreate local table'
        if localCat.createTable() == False: raise RuntimeError("Error")
        print("Re-create local table")
    
        'load local table'
        for i in copyCatDict['items']:
            #print('{}, {}, {}'.format(i, copyCatDict['items'][i]['Name'], copyCatDict['items'][i]['Price']))
            if localCat.addItem(i, copyCatDict['items'][i]['Name'], copyCatDict['items'][i]['Price']) == False: raise RuntimeError("Error")
            print("Added item to catalog")
        print('Added all items to catalog')
        return localCat
    except RuntimeError as e:
        print(e)
        return None

def getOrdersMadeInXSeconds(posId, numSeconds, ep="http://localhost:8000"):
    ticks = time.time() - numSeconds
    ot = ordersmodule.OrderTable(endpoint = ep)
    orderTable = ot.getTable()
    response = orderTable.query(
                    KeyConditionExpression=Key('PosID').eq(posId),
                    FilterExpression=Attr('Info.CreatedTicks').gt(Decimal(ticks))
                    )
    print(response)
    return response

def replace_decimals(obj):
    if isinstance(obj, ordersmodule.Order):
        for att in obj.__dict__:
            val = getattr(obj, att)
            setattr(obj, att, replace_decimals(val))
        return obj
    elif isinstance(obj, list):
        for i in range(0, len(obj)):
            obj[i] = replace_decimals(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = replace_decimals(obj[k])
        return obj
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj 

def replace_floats(obj):
    if isinstance(obj, ordersmodule.Order):
        for att in obj.__dict__:
            val = getattr(obj, att)
            setattr(obj, att, replace_floats(val))
        return obj
    elif isinstance(obj, list):
        for i in range(0, len(obj)):
            obj[i] = replace_floats(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = replace_floats(obj[k])
        return obj
    elif isinstance(obj, float):
        if obj % 1 == 0:
            return int(obj)
        else:
            return Decimal(obj)
    else:
        return obj 


"""
def copyRemoteToLocalCatalog(catalogId):
    try:
        'fetch the remote catalog'
        remoteCat = Catalog(catalogId, endpoint="https://dynamodb.us-east-1.amazonaws.com")
        if remoteCat.fetchFromDB() == False: raise RuntimeError("Error")  
        print("Fetched remote catalog")
        
        'copy the remote catalog to a dictionary'
        copyCatDict = remoteCat.get()
        
        'exit here if remote catalog is empty'
        if len(copyCatDict['items']) == 0: 
            print("Remote catalog empty")
            return
    
        print(copyCatDict)
        
        localCat = Catalog(catalogId, endpoint="http://localhost:8000")
        
        'delete local table'
        if localCat.deleteTable() == False: raise RuntimeError("Error")
        print("Fetched local table")
              
        'recreate local table'
        if localCat.createTable() == False: raise RuntimeError("Error")
        print("Re-create local table")
    
        'load local table'
        for i in copyCatDict['items']:
            #print('{}, {}, {}'.format(i, copyCatDict['items'][i]['Name'], copyCatDict['items'][i]['Price']))
            if localCat.addItem(i, copyCatDict['items'][i]['Name'], copyCatDict['items'][i]['Price']) == False: raise RuntimeError("Error")
            print("Added item to catalog")
        print('Added all items to catalog')
    except RuntimeError as e:
        print(e.response['Error']['Message'])
    else:
        print("Table created")
"""        
def createOrderQueues():
    for q in ["NewOrdersQueue", "UpdatedOrdersQueue", "DeletedOrdersQueue"]:
        sqsmodule.make_queue(q)

        