from django.urls import path

from . import views

app_name = "productos"
urlpatterns = [
    path("", views.index, name="index"),
    path("<int:producto_id>/", views.detalle, name="detalle"),
    path("categoria/<str:categoria>/", views.por_categoria, name="por_categoria"),
]