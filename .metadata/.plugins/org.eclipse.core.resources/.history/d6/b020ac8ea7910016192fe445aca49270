from sqsmodule import receive_messages

print('Retrieving messages...')
att_list = ['ftp', 'retry', 'schedule']
for msg in receive_messages('vgvtest',att_list):
    if msg.message_attributes is not None:
        att_dict = {}
        for att in att_list:
            a = msg.message_attributes.get(att)
            if a:
                att_dict[att] = msg.message_attributes.get(att).get('StringValue')
        print("Message:")
        print(msg.body)
        print(att_dict)
        msg.delete()
