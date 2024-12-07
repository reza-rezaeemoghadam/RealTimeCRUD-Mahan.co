# Importing django modules
from encodings import normalize_encoding

from django.shortcuts import get_object_or_404
from django.core.cache import cache

# Importing channel modules
from channels.generic.websocket import AsyncWebsocketConsumer

# Importing extra modules
import json
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
        self.room_group_name = f"product_group"
        # Retrieve path and user-agent from scope
        self.page_url = self.scope.get('path', 'unknown')
        user_agent = 'unknown'
        for header in self.scope['headers']:
            if header[0] == b'user-agent':
                user_agent = header[1].decode()
                break

        logger.info(f"Websocket connected: {self.room_group_name}-{self.channel_name}")

        user = self.scope['user']
        if not user.is_anonymous:
            logger.info(f"User {user.username} joined the session at {self.page_url}")
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            # Add user to the connected users in cache system
            await self.add_user(self.scope['user'], "join")
            await self.send_group_message("New user joined")
            # Storing the user channel for permission granting system
            await sync_to_async(cache.set)(f"user_channel_{self.scope['user'].username}", self.channel_name)
            await self.accept()
        else:
            logger.info(f"Unauthenticated user")
            await self.close()

    async def receive(self, text_data=None):
        user = self.scope['user']
        logger.info(f"Received message: {text_data}")
        data = json.loads(text_data)
        logger.info(f"messageeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee {data}")
        action = data['action']
        payload = data['payload']
        product_id = payload['id']

        logger.info(f"user {user.username} with action {action}")
        match action:
            case "create":
                await self.update_user_action(username=user.username, action="create")
                await self.create_product(data)
            case "read":
                await self.update_user_action(username=user.username, action="read")
                await self.read_product(product_id)
            case 'update_req':
                await self.hand_over_request(user=user, product_id=product_id, action='update')
            case 'delete_req':
                pass
            case "update":
                await self.update_user_action(username=user.username, action="update")
                await self.edit_product(data, product_id)
            case "delete":
                await self.update_user_action(username=user.username, action="delete")
                await self.delete_product(product_id)
            case ("permission_granted"|"permission_denied"):
                await self.handle_permission_response(user=user, product_id=product_id, action=action)
            case _:
                logger.info(f"Invalid action: {action}")
                await self.send(text_data=json.dumps({"message": "Invalid action", "action": action}))

    async def disconnect(self, code):
        logger.info(f"Websocket disconnected: {self.room_group_name}")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    # CRUD Part starts here
    async def create_product(self, data):
        serializer = self.serializer_class(data=data['payload'])
        if serializer.is_valid():
            product = await sync_to_async(serializer.save)()
            logger.info(f"Product created: {serializer.data} by {self.scope['user'].username} at {self.page_url}")
            await self.send_group_message(message="Product created")
        else:
            logger.info(f"Product creation failed: {serializer.errors}")
            await self.send(text_data=json.dumps({"message": "Invalid data", "errors": serializer.errors}))

    async def read_product(self, product_id):
        product = await sync_to_async(get_object_or_404)(Product, id=product_id)
        serializer = self.serializer_class(product)
        logger.info(f"Product retrieved: {serializer.data} by {self.scope['user'].username}")
        await self.send_group_message(message="Product retrieved", payload=serializer.data)

    async def edit_product(self, data, product_id):
        product = await sync_to_async(get_object_or_404)(Product, id=product_id)
        serializer = self.serializer_class(product, data=data['payload'], partial=True)
        if serializer.is_valid():
            product = await sync_to_async(serializer.save)()
            logger.info(f"Product updated successfully : {serializer.data} by {self.scope['user'].username} at {self.page_url}")
            await self.send_group_message("Product updated")
        else:
            logger.info(f"Product update failed: {serializer.error}")
            await self.send(text_data=json.dumps({"message": "Invalid data", "errors": serializer.errors}))

    async def delete_product(self, product_id):
        product = await sync_to_async(get_object_or_404)(Product, id=product_id)
        await sync_to_async(product.delete)()
        logger.info(f"Product deleted by {self.scope['user'].username} at {self.page_url}")
        await self.send_group_message("Product deleted")

    # Caching part starts here
    async def add_user(self, user, action):
        users_actions = await sync_to_async(cache.get)(self.room_group_name, {})
        users_actions[user.username] = action
        logger.info(f"'{user}' added to cache system with action '{action}'")
        await sync_to_async(cache.set)(self.room_group_name, users_actions)

    async def update_user_action(self, username, action):
        # Store the user's last action in the cache
        user_actions = await sync_to_async(cache.get)(self.room_group_name, {})
        user_actions[username] = action
        await sync_to_async(cache.set)(self.room_group_name, user_actions)
        logger.info(f"'{username}' action's updated to {action} in cache system")

    async def get_users(self):
        return await sync_to_async(cache.get)(self.room_group_name, {})

    async def remove_user(self, user):
        user_actions = await sync_to_async(cache.get)(self.room_group_name, {})
        user_actions.discard(user.username)
        await sync_to_async(cache.set)(self.room_group_name, user_actions)
        logger.info(f"'{user.username}' removed from cache system")

    async def send_group_message(self, message, payload=None):
        users = await self.get_users()
        logger.info(f"Websocket connected: {users}")
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": 'send_message',
                'message' : message,
                'payload' : payload,
                'users' : users
            }
        )

    async def send_message(self, event):
        logger.info(json.dumps(event))
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'users': event['users'],
            'payload' : event.get('payload',None)
        }))

    # Hand over system
    async def hand_over_request(self, user, product_id, action):
        current_editor = await sync_to_async(cache.get)(f"editor_{product_id}")
        if current_editor and current_editor != user.username:
            await self.send(text_data=json.dumps({
                'message':f"Product {product_id} is being edited by {current_editor}. Requesting permission...",
                'users': "",
                'payload' : ""
            }))
            await self.update_user_action(username=user.username, action=f"permission_request")
            await sync_to_async(cache.set)(f"requesting_user_{product_id}", user.username)
            await self.send_group_message(message=f"{user.username} is requesting to edit product {product_id}.")
            logger.info(f"User {user.username} requested to edit product {product_id}, but it is currently being edited by {current_editor}")
        else:
            await self.update_user_action(username=user.username, action="update")
            await sync_to_async(cache.set)(f"editor_{product_id}", user.username)
            await self.send_group_message(message=f"User {user.username} granted permission to {action} product {product_id}")
            logger.info(f"User {user.username} granted permission to edit product {product_id}")

    async def handle_permission_response(self, user, product_id, action):
        requesting_user = await sync_to_async(cache.get)(f"requesting_user_{product_id}")
        current_editor = await sync_to_async(cache.get)(f"editor_{product_id}")
        if action == "permission_granted":
            logger.info(f"User {current_editor} granted permission to {requesting_user} to edit product {product_id}")
            await self.update_user_action(username=requesting_user, action="update")
            await self.update_user_action(username=current_editor, action="read")
            await sync_to_async(cache.set)(f"editor_{product_id}", requesting_user)
            await self.send_private_message(requesting_user, {'message': f"Permission granted to edit product {product_id}.",'action': 'permission_granted'})
            await self.send_group_message(message="")
        elif action == "permission_denied":
            logger.info(f"User {current_editor} denied permission to {requesting_user} to edit product {product_id}")
            await self.send_private_message(requesting_user, {'message': f"Permission denied to edit product {product_id}.",'action': 'permission_denied'})

    async def send_private_message(self, username, message, payload=None):
        users = await self.get_users()
        user_channel = await sync_to_async(cache.get)(f"user_channel_{username}")
        if user_channel:
            await self.channel_layer.send(user_channel, { 'type': 'send_message', 'message': message , 'users': users, 'payload': payload})

# Implementing Log consumer
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