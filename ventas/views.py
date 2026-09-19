import requests
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Venta


def index(request):
    """Lista las últimas ventas registradas localmente (SQLite),
    enviadas al template a través del context."""
    ventas = Venta.objects.order_by("-fecha")[:10]
    context = {"ventas": ventas}
    return render(request, "ventas/index.html", context)


def detalle(request, venta_id):
    """Shortcut get_object_or_404: busca una Venta guardada en SQLite.
    Si no existe, Django devuelve automáticamente un error 404."""
    venta = get_object_or_404(Venta, pk=venta_id)
    context = {"venta": venta}
    return render(request, "ventas/detalle.html", context)


def por_producto(request, producto_id):
    """Consulta el producto en el microservicio, y filtra
    las ventas locales de ese producto."""
    respuesta = requests.get(f"{settings.MICROSERVICIO_URL}/productos/{producto_id}/")
    if respuesta.status_code == 404:
        return HttpResponse(f"No existe un producto con el id {producto_id}.")

    producto = respuesta.json()
    ventas = Venta.objects.filter(producto_id=producto_id)

    context = {"producto": producto, "ventas": ventas}
    return render(request, "ventas/index.html", context)


def registrar(request, producto_id):
    """Registra una venta: llama al microservicio para descontar stock
    en Supabase, y guarda una copia local en SQLite."""
    cantidad_str = request.GET.get("cantidad", "1")
    if not cantidad_str.isdigit():
        return HttpResponse("El parámetro 'cantidad' debe ser un número entero positivo.")
    cantidad = int(cantidad_str)

    respuesta = requests.post(
        f"{settings.MICROSERVICIO_URL}/productos/{producto_id}/vender/",
        json={"cantidad": cantidad},
    )

    if respuesta.status_code == 404:
        return HttpResponse(f"No existe un producto con el id {producto_id}.")
    if respuesta.status_code == 400:
        return HttpResponse("Stock insuficiente para completar la venta.")

    venta = Venta.objects.create(producto_id=producto_id, cantidad=cantidad)

    context = {"venta": venta, "datos_microservicio": respuesta.json()}
    return render(request, "ventas/detalle.html", context)