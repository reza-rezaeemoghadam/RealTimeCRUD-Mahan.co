import logging
from channels.layers import get_channel_layer
import asyncio

class WebSocketLogHandler(logging.Handler):
    async def async_emit(self, record):
        """This method is designed to send log messages asynchronously to the WebSocket group"""
        channel_layer = get_channel_layer()
        message = self.format(record)
        await channel_layer.group_send(
            'log_group',
            {
                'type': 'send_message',
                'message': message
            }
        )

    def emit(self, record):
        """This method determines whether the current context is asynchronous or synchronous and calls the async_emit method accordingly."""
        try:
            # Checks if an asynchronous event loop is already running
            if asyncio.get_event_loop().is_running():
                # Schedules the async_emit coroutine to run in the existing event loop, ensuring non-blocking behavio
                asyncio.create_task(self.async_emit(record))
            else:
                # Creates a new event loop if no async event loop is running.
                loop = asyncio.new_event_loop()
                #Runs the async_emit coroutine to completion in the newly created event loop.
                loop.run_until_complete(self.async_emit(record))
        except Exception as e:
            print(f"Logging error: {e}")
