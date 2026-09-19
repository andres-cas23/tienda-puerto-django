from django.urls import path

from . import views

app_name = "ventas"
urlpatterns = [
    path("", views.index, name="index"),
    path("producto/<int:producto_id>/", views.por_producto, name="por_producto"),
    path("registrar/<int:producto_id>/", views.registrar, name="registrar"),
    path("<int:venta_id>/", views.detalle, name="detalle"),
]
