# Importing rest framework modules
from rest_framework.generics import RetrieveAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.permissions import AllowAny

# Importing custom models
from rt_crud.models import Product

# Importing custom serializers
from rt_crud.api.v1.serializers import ProductSerializer

# Implementing custom views
class ProductRetrieveAPIView(RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]