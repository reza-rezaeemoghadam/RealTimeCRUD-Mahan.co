# Importing rest framework modules
from rest_framework.urls import path

# Imorting custom views
from rt_crud.api.v1.views import ProductRetrieveAPIView

# Implementing urlpatterns
urlpatterns = [
    path("product/<int:pk>/", ProductRetrieveAPIView.as_view(), name=""),
    path("product/<int:pk>/", ProductRetrieveAPIView.as_view(), name=""),
    path("product/<int:pk>/edit/", ProductRetrieveAPIView.as_view(), name=""),
    path("product/<int:pk>/delete/", ProductRetrieveAPIView.as_view(), name=""),
]