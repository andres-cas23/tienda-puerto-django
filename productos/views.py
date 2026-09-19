import requests
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    """Consulta TODOS los productos llamando al microservicio,
    y envía la lista al template a través del context."""
    respuesta = requests.get(f"{settings.MICROSERVICIO_URL}/productos/")
    productos = respuesta.json()

    context = {"productos": productos}
    return render(request, "productos/index.html", context)


def detalle(request, producto_id):
    """Ruta dinámica: consulta UN producto llamando al microservicio."""
    respuesta = requests.get(f"{settings.MICROSERVICIO_URL}/productos/{producto_id}/")

    if respuesta.status_code == 404:
        return HttpResponse(f"No existe un producto con el id {producto_id}.")

    producto = respuesta.json()
    context = {"producto": producto}
    return render(request, "productos/detalle.html", context)


def por_categoria(request, categoria):
    """Filtra productos por categoría, pidiendo TODOS al microservicio
    y filtrando en Django."""
    respuesta = requests.get(f"{settings.MICROSERVICIO_URL}/productos/")
    productos = respuesta.json()

    filtrados = [p for p in productos if p["categoria"].lower() == categoria.lower()]
    context = {"productos": filtrados, "categoria": categoria}
    return render(request, "productos/index.html", context)