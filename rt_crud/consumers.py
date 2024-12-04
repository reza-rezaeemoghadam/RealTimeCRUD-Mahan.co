# Importing django modules
from django.shortcuts import get_object_or_404

# Importing channel modules
from channels.generic.websocket import AsyncWebsocketConsumer

# Importing extra modules
import json
import logging
from asgiref.sync import sync_to_async

# Importing custom models
from rt_crud.models import Product

# Importing custom serializers
from rt_crud.api.v1.serializers import ProductSerializer

# Logging module and stuff
import logging
logger = logging.getLogger('rt_crud')
logger_log_consumer = logging.getLogger('consumers')

# Implementing consumers
class ProductConsumer(AsyncWebsocketConsumer):
    serializer_class = ProductSerializer

    async def connect(self):
        self.product_id = self.scope['url_route']['kwargs']['product_id']
        self.product_group_name = f"product_group"
        logger.info(f"Websocket connected: {self.product_group_name}-{self.channel_name}")
        
        user = self.scope['user']
        if not user.is_anonymous:
            logger.info(f"User {user.username} joined the session")
            await self.channel_layer.group_add(
                self.product_group_name,
                self.channel_name
            )
            await self.channel_layer.group_send(
                self.product_group_name,
                {
                    'type': 'send_message',
                    'message': "",
                    'action' : "join",
                    'user' : user.username
                }
            )
            await self.accept()
        else:
            logger.info(f"Unauthenticated user")
            await self.close()
    
    async def receive(self, text_data=None):
        user = self.scope['user']
        logger.info(f"Recieved message: {text_data}")
        data = json.loads(text_data)
        action = data['action']
        payload = data['payload']
        product_id = payload['id']

        logger.info(f"user {user.username} with action {action}")
        match action:
            case "create":
                await self.create_product(data)
            case "read":
                await self.read_product(product_id)
            case "update":
                await self.edit_product(data, product_id)
            case "delete":
                await self.delete_product(product_id)
            case _:
                logger.info(f"Invalid action: {action}")
                self.send(text_data=json.dumps({"message": "Invalid action", "action": action}))

    async def disconnect(self, code):
        logger.info(f"Webssocket disconnected: {self.product_group_name}")
        await self.channel_layer.group_discard(
            self.product_group_name,
            self.channel_name
        )

    async def send_group_message(self, message, action, user):
        print(message)
        await self.channel_layer.group_send(
            self.product_group_name,
            {
                "type": 'send_message',
                'message' : message,
                'action' : action,
                'user' : user.username
            }
        )

    async def send_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'action' : event['action'],
            'user': event['user'],
            'payload' : event.get('payload',None)
        }))

    async def notify_handover(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message' : message,
            'handover_request': True
        }))

    async def create_product(self, data):
        serializer = self.serializer_class(data=data['payload'])
        if serializer.is_valid():
            product = await sync_to_async(serializer.save)()
            logger.info(f"Product created: {serializer.data}")
            await self.send(text_data=json.dumps({'message': "Product created", 'payload': serializer.data, 'user': self.scope['user'].username, 'action': 'create'}))
        else:
            logger.info(f"Product creation failed: {serializer.errors}")
            await self.send(text_data=json.dumps({"message": "Invalid data", "errors": serializer.errors}))

    async def read_product(self, product_id):
        product = await sync_to_async(get_object_or_404)(Product, id=product_id)
        serializer = self.serializer_class(product)
        logger.info(f"Product retrieved: {serializer.data}")
        await self.send(text_data=json.dumps({'message': "Product retrieved", 'payload': serializer.data, 'user': self.scope['user'].username, 'action': 'read'}))

    async def edit_product(self, data, id):
        product = await sync_to_async(get_object_or_404)(Product, id=id)
        serializer = self.serializer_class(product, data=data['payload'], partial=True)
        if serializer.is_valid():
            product = await sync_to_async(serializer.save)()
            logger.info(f"Product updated successfully : {serializer.data}")
            await self.send(text_data=json.dumps({'message': "Product updated", 'paylaod': serializer.data, 'user':self.scope['user'].username, 'action': 'edit'}))
        else:
            logger.info(f"Product update failed: {serializer.error}")
            await self.send(text_data=json.dumps({"message": "Invalid data", "errors": serializer.errors}))

    async def delete_product(self, id):
        product = await sync_to_async(get_object_or_404)(Product, id=id)
        await sync_to_async(product.delete)()
        logger
        await self.send(text_data=json.dumps({'message': 'Product deleted'}))

class LogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger_log_consumer.info("LogConsumer connected.")
        await self.channel_layer.group_add("log_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        logger_log_consumer.info("LogConsumer disconnected.")
        await self.channel_layer.group_discard("log_group", self.channel_name)


    async def send_message(self, event):
        message = event['message']
        logger_log_consumer.info(f"Received log message: {message}")
        await self.send(text_data=json.dumps({"message": message}))