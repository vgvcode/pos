#!/usr/bin/python
from __future__ import print_function # Python 2/3 compatibility
import json
from decimal import *
import time
import uuid
import boto3
import commonmodule
from copy import deepcopy
from boto3.dynamodb.conditions import Key, Attr
import sqsmodule

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    'convert decimal to float representation for serialization'
    def default(self, o):
        if isinstance(o, Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)
    
class OrderTable:
    'base class for DDL operations on orders table'
    __tableName = "orders"
    
    def __init__(self, endpoint = "http://localhost:8000"):
        self.__endpoint = endpoint
        self.__dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint)
        self.__table = self.__dynamodb.Table(OrderTable.__tableName)

    def createTable(self):
        'create a new table to hold orders'
        result = True
        try:
            self.__table = self.__dynamodb.create_table(
                TableName=OrderTable.__tableName,
                KeySchema=[
                    {
                        'AttributeName': 'PosID',
                        'KeyType': 'HASH'  #Partition key
                    },
                    {
                        'AttributeName': 'OrderID',
                        'KeyType': 'RANGE'  #Sort key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'PosID',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'OrderID',
                        'AttributeType': 'S'
                    },
            
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            )
        except Exception as e:
            print(e)
            result = False
        finally:
            return result        

    def deleteTable(self):
        result = True
        try:
            self.__table.delete()
        except Exception as e:
            print(e)
            result = False
        finally:
            return result

    def fetchAllOrdersForPos(self, posId):
        'fetch all orders from db for a given posId'
        response = None
        try:
            response = self.__table.query(KeyConditionExpression=Key('PosID').eq(posId))
        except Exception as e:
            print(e)
        finally:
            return response

    def fetchNumOrdersForPosToday(self, posId):
        'fetch all orders from db for a given posId'
        response = None
        nowTicks = time.time()
        localTime = time.localtime()
        ticksSinceBOD = localTime.tm_hour * 3600 + localTime.tm_min * 60 + localTime.tm_sec
        BODTicks = nowTicks - ticksSinceBOD
        try:
            response = self.__table.query(
                KeyConditionExpression=Key('PosID').eq(posId),
                FilterExpression=Attr('Info.CreatedTicks').gt(Decimal(BODTicks))
            )
            return len(response['Items'])            
        except Exception as e:
            print(e)
            return 0

    def getEndPoint(self):
        return self.__endpoint
    
    def getTableName(self):
        return self.__tableName
    
    def getTable(self):
        return self.__table
    
    def deQueueOrdersToRemote(self, operation, endpoint):
        #Get orders from new order queue and save them in remote db
        try:
            remoteDynamoDb = boto3.resource('dynamodb', endpoint_url = endpoint)
            remoteTable = remoteDynamoDb.Table(OrderTable.__tableName)
    
            oq = OrderQueues()
            if operation == "insert":
                qn = oq.getNewQueue()
            elif operation == "delete":
                qn = oq.getDeletedQueue()
            elif operation == "update":
                qn = oq.getUpdatedQueue()
            else:
                raise NameError('Unknown operation: {}'.format(operation))
    
            loopCondition = True
            while loopCondition == True:    
                recvMsgs = sqsmodule.receive_messages(qn)
                if len(recvMsgs) == 0:
                    print('No orders in queue: {}'.format(qn))
                    loopCondition = False
                else:
                    for msg in recvMsgs:
                        o = json.loads(msg.body)
                        #replace floats with Decimal(...) because DynamoDb cannot handle floats
                        commonmodule.replace_floats(o)
                        updatedTicks = o['Info']['UpdatedTicks']
                        print(updatedTicks)
                        if operation == 'insert':
                            response = remoteTable.put_item(Item = o)
                            print("Inserted message to remote DB")
                        elif operation == 'delete':
                            'delete only if the item to be deleted has same or higher timestamp than item in database'
                            response = remoteTable.delete_item(
                                            Key = {
                                                   'PosID': o['PosID'],
                                                   'OrderID': o['OrderID']
                                                   },
                                            ConditionExpression = "Info.UpdatedTicks <= :ticks",                                          
                                            ExpressionAttributeValues = {
                                                   ':ticks': updatedTicks
                                                    },
                                        )
                            print("Deleted message from remote DB")
                        elif operation == 'update':
                            'update item only if item to be updated has higher timestamp than item in database'
                            response = remoteTable.update_item(
                                            Key = {
                                                   'PosID': o["PosID"],
                                                   'OrderID': o["OrderID"]
                                                   },
                                            UpdateExpression = "set Info = :i",
                                            ConditionExpression = "Info.UpdatedTicks < :ticks",                                          
                                            ExpressionAttributeValues = {
                                                   ':i': o["Info"],
                                                   ':ticks': updatedTicks
                                                    },
                                            ReturnValues="UPDATED_NEW"
                                        )                        
                        print(response)
                        print('PosID: {}, OrderID: {}'.format(o['PosID'], o['OrderID']))
                        msg.delete()
        except Exception as e:
            print(e)


class OrderQueues:
    'base class that holds all order queue details'
    
    __newOrdersQueue = "NewOrdersQueue"
    __updatedOrdersQueue = "UpdatedOrdersQueue"
    __deletedOrdersQueue = "DeletedOrdersQueue"

    def getQueues(self):
        return [OrderQueues.__newOrdersQueue, OrderQueues.__deletedOrdersQueue, OrderQueues.__updatedOrdersQueue]
    
    def getNewQueue(self):
        return OrderQueues.__newOrdersQueue
    
    def getUpdatedQueue(self):
        return OrderQueues.__updatedOrdersQueue
    
    def getDeletedQueue(self):
        return OrderQueues.__deletedOrdersQueue
    
    def makeQueues(self):
        sqsmodule.make_queue(self.__newOrdersQueue)
        sqsmodule.make_queue(self.__updatedOrdersQueue)
        sqsmodule.make_queue(self.__deletedOrdersQueue)
     
                
class Order:
    'common base class for an order'
    
    __taxPct = 10

    def __init__(self, posId, endpoint = "http://localhost:8000"):
        ot = OrderTable(endpoint)
        ticks = time.time()
        self.__tableName = ot.getTableName()
        self.__table = ot.getTable()
        self.__posId = posId
        self.__orderId = str(uuid.uuid1())
        self.__orderNumber = 0
        self.__listOfItems = []
        self.__createdTicks = ticks
        self.__createdTime = time.asctime(time.localtime(ticks))
        self.__updatedTicks = 0
        self.__updatedTime = "0"
        self.__queued = 0
        self.__gross = 0
        self.__tax = 0
        self.__net = 0
 
    def toDictionary(self):
        odict = {'PosID': self.__posId, 'OrderID': self.__orderId}
        odict['Info'] = {
                         'OrderNumber': self.__orderNumber,
                         'CreatedTime': self.__createdTime,
                         'CreatedTicks': self.__createdTicks,
                         'UpdatedTime': self.__updatedTime,
                         'UpdatedTicks': self.__updatedTicks,
                         'Queued': self.__queued,
                         'ListOfItems': self.__listOfItems,
                         'Gross': self.__gross,
                         'TaxPct': Order.__taxPct,
                         'Tax': self.__tax,
                         'Net': self.__net
                         }
                
        #print(odict)
        return odict
    
    def fromDictionary(self, odict):
        self.__posId = odict['PosID']
        self.__orderId = odict['OrderID']
        self.__orderNumber = odict['Info']['OrderNumber']
        self.__createdTicks = odict['Info']['CreatedTicks']
        self.__createdTime = odict['Info']['CreatedTime']
        self.__updatedTicks = odict['Info']['UpdatedTicks']
        self.__updatedTime = odict['Info']['UpdatedTime']
        self.__queued = odict['Info']['Queued']
        self.__listOfItems = odict['Info']['ListOfItems']
        self.__gross = odict['Info']['Gross']
        self.__taxPct = odict['Info']['TaxPct']
        self.__tax = odict['Info']['Tax']
        self.__net = odict['Info']['Net']

    def floatToDecimal(self):
        for att in self.__dict__:
            print(att)
            val = getattr(self, att)
            print('Before:{}'.format(val))
            setattr(self, att, commonmodule.replace_floats(val))
            print('After:{}'.format(val))
        
    def fetchFromDBUsingOrderId(self, orderId):
        'fetch order from db based on orderId'
        self.__orderId = orderId
        result = True
        try:
            response = self.__table.query(KeyConditionExpression=Key('PosID').eq(self.__posId) & Key('OrderID').eq(self.__orderId))
            'convert the first match into an order'
            if len(response['Items']) > 0:
                self.fromDictionary(response['Items'][0])
        except Exception as e:
            print(e)
            result = False
        finally:
            return result
    
    def fetchFromDBUsingOrderNumber(self, orderNumber):
        'fetch order from db based on orderNumber'
        self.__orderNumber = orderNumber
        result = True
        try:
            response = self.__table.query(
                KeyConditionExpression=Key('PosID').eq(self.__posId),
                FilterExpression=Attr('Info.OrderNumber').eq(orderNumber)
            )
            'convert the first match into an order'
            if len(response['Items']) > 0:
                self.fromDictionary(response['Items'][0])
        except Exception as e:
            print(e)
            result = False
        finally:
            return result

    def addOrderItem(self, newOrderItem):
        'add an element of type orderitem to order'
        self.__listOfItems.append(newOrderItem.toDictionary())
        ticks = time.time()
        self.__updatedTicks = ticks
        self.__updatedTime = time.asctime(time.localtime(ticks))       
        self.updateTotal()
        
    def addItem(self, itm, qty):
        'add an item to order by converting it into an orderitem'
        oi = OrderItem(itm['ItemId'], itm['Name'], itm['Price'], qty)
        self.addOrderItem(oi)
        
    def removeItemAt(self, at):
        del self.__listOfItems[at]
        ticks = time.time()
        self.__updatedTicks = ticks
        self.__updatedTime = time.asctime(time.localtime(ticks))       
        self.updateTotal()
        
    def indexOfItem(self, name):
        'returns index of first match or -1'
        itemFound = -1
        idx = 0
        for elt in self.__listOfItems:
            if elt['name'] == name:
                itemFound = idx
                break
            idx+=1
        return itemFound
    
    def updateTotal(self):
        gross = 0
        for elt in self.__listOfItems:
            price = commonmodule.money(elt['_OrderItem__price'])
            qty = commonmodule.money(elt['_OrderItem__quantity'])
            gross += commonmodule.money(price * qty)
        tax = commonmodule.money(Order.__taxPct * gross / 100)
        net = commonmodule.money(gross + tax)
        self.__gross = str(gross)
        self.__tax = str(tax)
        self.__net = str(net)
    
    def saveToDB(self):
        result = True
        #update before saving
        self.updateTotal()
        # assign order number to be the next in the db for today
        ot = OrderTable()
        numOrders = ot.fetchNumOrdersForPosToday(self.__posId)
        self.__orderNumber = numOrders + 1
        try:
            #push to queue
            oq = OrderQueues()
            qn = oq.getNewQueue()
            print('Trying to push to: {}'.format(qn))
            if self.pushToQueue(qn) == True:
                print("Pushed order to " + qn)
            else:
                print('Failed to push order to ' + qn)
            
            commonmodule.replace_floats(self)
            #print(corder)
            response = self.__table.put_item(Item = self.toDictionary())
            print("PutItem succeeded:")
            print(json.dumps(response, indent=4, cls=DecimalEncoder))
        except Exception as e:
            print("put_item failed")
            print(e)
            result = False       
        finally:
            return result
        
    def deleteFromDB(self):
        'push to queue and delete order from DB'
        result = True
        try:
            ticks = time.time()
            self.__updatedTicks = ticks
            self.__updatedTime = time.asctime(time.localtime(ticks))       

            #push to queue
            oq = OrderQueues()
            qn = oq.getDeletedQueue()
            self.pushToQueue(qn)

            #replace all float with Decimal(...) because DynamoDb cannot handle float
            commonmodule.replace_floats(self)
            response = self.__table.delete_item(
                            Key = {
                                   'PosID': self.__posId,
                                   'OrderID': self.__orderId
                                   }
                        )
            print("DeleteItem succeeded:")
            print(json.dumps(response, indent=4, cls=DecimalEncoder))
        except Exception as e:
            print('Delete from DB failed')
            print(e)
            result = False       
        finally:
            return result
    
    def updateToDB(self):
        'push to queue and update order in DB'
        result = True
        try:
            ticks = time.time()
            self.__updatedTicks = ticks
            self.__updatedTime = time.asctime(time.localtime(ticks))       

            #push to queue
            oq = OrderQueues()
            qn = oq.getUpdatedQueue()
            self.pushToQueue(qn)

            #replace all float with Decimal(...) because DynamoDb cannot handle float
            commonmodule.replace_floats(self)
            odict = self.toDictionary()
            print(odict)
            response = self.__table.update_item(
                            Key = {
                                   'PosID': odict["PosID"],
                                   'OrderID': odict["OrderID"]
                                   },
                            UpdateExpression = "set Info = :i",
                            ExpressionAttributeValues = {
                                   ':i': odict["Info"]
                                    },
                            ReturnValues="UPDATED_NEW"
                        )
            print("UpdateItem succeeded:")
            print(json.dumps(response, indent=4, cls=DecimalEncoder))
        except Exception as e:
            print('Update to DB failed')
            print(e)
            result = False       
        finally:
            return result
                
    def pushToQueue(self, qn):
        result = True
        try:
            #replace all Decimal(...) with float because Decimal(...) cannot be serialized
            commonmodule.replace_decimals(self)
            dct = self.toDictionary()
            msg_list = [
                {
                    'Id': str(uuid.uuid1()),
                    'MessageBody': json.dumps(dct, cls=DecimalEncoder),
                    'MessageAttributes': { 
                                     'PosID': {
                                        'StringValue': dct['PosID'],
                                        'DataType': 'String'
                                        },            
                                     'OrderID': {
                                        'StringValue': dct['OrderID'],
                                        'DataType': 'String'
                                        }
                                    }
                 }
                ]
            response = sqsmodule.send_messages(qn, msg_list)
            print(response)
            self.__queued = '1'
        except Exception as e:
            print(e)
            result = False        
        finally:
            return result

    def get(self):
        return self.toDictionary()
    
    def print(self):
        #update before printing
        self.updateTotal()
        print('PosId: {}'.format(self.__posId))
        print('OrderId: {}'.format(self.__orderId))
        print('OrderNumber: {}'.format(self.__orderNumber))
        print('Created: {}'.format(self.__createdTime))
        print('Updated: {}'.format(self.__updatedTime))
        print('Number of items in this order:{}'.format(len(self.__listOfItems)))
        for elt in self.__listOfItems:
            itmObj= OrderItem('1','dummy', '0', '0')
            itmObj.fromDictionary(elt)
            itmObj.print()
            #for k in elt.keys():
            #    newK = k.replace('_OrderItem__', '')
            #    newK = newK[0].upper() + newK[1:]
            #    print('{}: {}'.format(newK, elt[k]), end=", ")
        print('Gross: {}'.format(self.__gross))
        print('Tax: {}'.format(self.__tax))
        print('Net: {}'.format(self.__net))
        
    def writeToFile(self, fn):
        self.updateTotal()
        with open(fn, 'a') as file:
            file.write('New order\n')
            file.write('PosId: {}\n'.format(self.__posId))
            file.write('OrderId: {}\n'.format(self.__orderId))
            file.write('OrderNumber: {}\n'.format(self.__orderNumber))
            file.write('Created: {}\n'.format(self.__createdTime))
            file.write('Number of items in this order:{}\n'.format(len(self.__listOfItems)))
            #for elt in self.__listOfItems:
            #    file.write(str(elt))
            file.write('Gross: {}\n'.format(self.__gross))
            file.write('Tax: {}\n'.format(self.__tax))
            file.write('Net: {}\n'.format(self.__net))
                                                
class OrderItem:
    'common base class for an item'
    
    def __init__(self, idy, name, price, quantity):
        ticks = time.time()
        self.__id = str(idy)
        self.__name = name
        self.__price = str(price)
        self.__quantity = str(quantity)
        self.__amount = str(commonmodule.money(self.__quantity) * commonmodule.money(self.__price))
        self.__createdTicks = str(ticks)
        self.__createdTime = time.asctime(time.localtime(ticks))
    
    def toDictionary(self):
        return deepcopy(self.__dict__)
    
    def fromDictionary(self, idict):
        #print(idict)
        prefix = "_OrderItem__"
        self.__id = idict[prefix + 'id']
        self.__name = idict[prefix + 'name']
        self.__price = idict[prefix + "price"]
        self.__quantity = idict[prefix + "quantity"]
        self.__amount = idict[prefix + "amount"]
        self.__createdTicks = idict[prefix + "createdTicks"]
        self.__createdTime = idict[prefix + "createdTime"]
        
    def print(self):
        print("Item ID:{} Name:{} Price:{} Quantity:{} Amount:{} CreatedTime:{} CreatedTicks:{}".format(self.__id, self.__name, self.__price, self.__quantity, self.__amount, self.__createdTicks, self.__createdTime))
