from django.urls import path

from . import views

app_name = "productos"
urlpatterns = [
    path("", views.index, name="index"),
    path("nuevo/", views.crear, name="crear"),
    path("preguntar-ia/", views.preguntar_ia, name="preguntar_ia"),
    path("<int:producto_id>/", views.detalle, name="detalle"),
    path("<int:producto_id>/editar/", views.editar, name="editar"),
    path("<int:producto_id>/eliminar/", views.eliminar, name="eliminar"),
    path("categoria/<str:categoria>/", views.por_categoria, name="por_categoria"),
]