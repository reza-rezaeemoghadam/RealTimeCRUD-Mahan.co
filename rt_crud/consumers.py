# Importing channel modules
from channels.generic.websocket import AsyncWebsocketConsumer

# Importing extra modules
import json
import logging
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async

# Importing custom models
from rt_crud.models import Product

# Logging module and stuff
import logging
logger = logging.getLogger('rt_crud')
logger_log_consumer = logging.getLogger('consumers')

# Implementing consumers
class ProductConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.product_id = self.scope['url_route']['kwargs']['product_id']
        self.product_group_name = f"product_{self.product_id}"
        logger.info(f"Websocket connected: {self.product_group_name}-{self.channel_name}")
        
        self.user = self.scope['user']
        logger.info(f"User {self.user} joined the session")

        product = await database_sync_to_async(Product.objects.get)(id=self.product_id)
        logger.info(f"Product retrieved : {self.product_id}-{product.name}")
        await self.channel_layer.group_add(
            self.product_group_name,
            self.channel_name
        )
        await self.channel_layer.group_send(
            self.product_group_name,
            {
                'type': 'send_message',
                'message': f"{self.user.username} joined",
                'action' : "read"
            }
        )
        await self.accept()
    
    async def receive(self, text_data=None):
        logger.info(f"Recieved message: {text_data}")


    async def disconnect(self, code):
        logger.info(f"Webssocket disconnected: {self.product_group_name}-{self.channel_name}")
        await self.channel_layer.group_discard(
            self.product_group_name,
            self.channel_name
        )

    async def send_group_message(self, message, action):
        await self.channel_layer.group_send(
            self.product_group_name,
            {
                "type": 'send_message',
                'message' : message,
            }
        )

    async def send_message(self, event):
        message = event['message']
        action = event['action']
        await self.send(text_data=json.dumps({
            'message': message,
            'action' : action
        }))

    async def notify_handover(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message' : message,
            'handover_request': True
        }))


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