#amazon_lib.py
from boto.sqs.connection import SQSConnection
from boto.sqs.jsonmessage import JSONMessage

conn = SQSConnection()
DEBUG = True

def setdebug(debug=True):
    DEBUG=debug

def get_queues():
    return conn.get_all_queues()

def get_requests():
    queue_name = 'dev_portal_requests' if DEBUG else 'portal_requests'
    print 'Getting %s' % queue_name 
    queue = conn.get_queue(queue_name)
    queue.set_message_class(JSONMessage)
    while True:
        rs = queue.get_messages()
        if rs:
            break

    for message in rs:
        print message.get('label')
        print message.get('body')
    return rs

def purge_requests():
    queue_name = 'dev_portal_requests'
    queue = conn.get_queue(queue_name)
    queue.clear()
    return True
    
