#!/usr/bin/python
import boto3

def make_queue(qn):
    result = True
    try:
        sqs=boto3.resource('sqs')
        queue = sqs.create_queue(QueueName=qn)
        print('Queue {} created'.format(qn))
    except Exception as e:
        print(e)
    finally:
        return result

def send_message(qn, body, dly, att):
    try:
        sqs=boto3.resource('sqs')
        queue = sqs.get_queue_by_name(QueueName=qn)
        response = queue.send_message(MessageBody=body, DelaySeconds=dly, MessageAttributes=att)
        return response
    except Exception as e:
        print(e)
        return None

def send_messages(qn, lst):
    try:
        sqs=boto3.resource('sqs')
        queue = sqs.get_queue_by_name(QueueName=qn)
        response = queue.send_messages(Entries=lst)
        return response
    except Exception as e:
        print(e)
        return None

def receive_messages(qn):
    try:
        sqs=boto3.resource('sqs')
        queue = sqs.get_queue_by_name(QueueName=qn)
        response = queue.receive_messages(WaitTimeSeconds=20)
        return response
    except Exception as e:
        print(e)
        return None

def receive_messages_with_attributes(qn, att):
    try:
        sqs=boto3.resource('sqs')
        queue = sqs.get_queue_by_name(QueueName=qn)
        response = queue.receive_messages(MessageAttributeNames=att, WaitTimeSeconds=20)
        return response
    except Exception as e:
        print(e)
        return None
