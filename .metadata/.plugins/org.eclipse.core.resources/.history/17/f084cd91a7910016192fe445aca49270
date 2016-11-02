from sqsmodule import make_queue, send_messages

msg_list = [
    {
        'Id': '1',
        'MessageBody': 'pointer to file 1',
        'MessageAttributes': {
            'ftp': {
                'StringValue': 'connection-string1',
                'DataType': 'String'
            },
            'retry': {
                'StringValue': '5',
                'DataType': 'String'
            },
            'schedule': {
                'StringValue': '01:00',
                'DataType': 'String'
            }
        }
    },
    {
        'Id': '2',
        'MessageBody': 'pointer to file 2',
        'MessageAttributes': {
            'ftp': {
                'StringValue': 'connection-string2',
                'DataType': 'String'
            }
        }
    }
]

q = make_queue('vgvtest')
print('Sending messages...')
r = send_messages('vgvtest', msg_list) 
print(r)
