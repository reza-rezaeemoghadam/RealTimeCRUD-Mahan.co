# Importing django modules
from django.urls import path

# Importing custom cunsumer
from rt_crud.consumers import ProductConsumer, LogConsumer

# Implementing urlpatterns
ws_urlpatterns = [
    path('ws/product/<int:product_id>/', ProductConsumer.as_asgi(), name="product_consumer"),
    path('ws/logs/', LogConsumer.as_asgi(), name='log_consumer'),
]