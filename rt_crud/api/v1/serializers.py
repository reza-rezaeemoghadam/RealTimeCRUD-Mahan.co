# Improting rest framework modules
from rest_framework.serializers import ModelSerializer

# Importing custom models
from rt_crud.models import Product, User

# Implementing serializers
class ProductSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'