# Importing django modules
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=150, verbose_name="name")
    quantity = models.IntegerField(verbose_name="quantity")

    locked_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    locked_at = models.DateField(null=True, blank=True, verbose_name="date")