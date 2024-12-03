# Importing django modules
from django.contrib import admin

# Importing cusotm models
from rt_crud.models import Product

# Register admin models.
admin.site.register(Product)