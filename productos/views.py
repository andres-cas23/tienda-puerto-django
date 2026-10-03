from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .resiliencia import llamar_con_resiliencia


def index(request):
    """Consulta TODOS los productos, con resiliencia entre los 4 microservicios."""
    try:
        respuesta, usado = llamar_con_resiliencia("GET", "/productos/")
    except ConnectionError as e:
        return HttpResponse(f"No se pudo consultar el inventario en ningún microservicio.<br><pre>{e}</pre>")

    productos = respuesta.json()
    context = {"productos": productos, "microservicio_usado": usado}
    return render(request, "productos/index.html", context)


def detalle(request, producto_id):
    """Ruta dinámica: consulta UN producto, con resiliencia."""
    try:
        respuesta, usado = llamar_con_resiliencia("GET", f"/productos/{producto_id}/")
    except ConnectionError as e:
        return HttpResponse(f"No se pudo consultar el producto en ningún microservicio.<br><pre>{e}</pre>")

    if respuesta.status_code == 404:
        return HttpResponse(f"No existe un producto con el id {producto_id}.")

    producto = respuesta.json()
    context = {"producto": producto, "microservicio_usado": usado}
    return render(request, "productos/detalle.html", context)


def por_categoria(request, categoria):
    """Filtra productos por categoría, con resiliencia."""
    try:
        respuesta, usado = llamar_con_resiliencia("GET", "/productos/")
    except ConnectionError as e:
        return HttpResponse(f"No se pudo consultar el inventario.<br><pre>{e}</pre>")

    productos = respuesta.json()
    filtrados = [p for p in productos if p["categoria"].lower() == categoria.lower()]
    context = {"productos": filtrados, "categoria": categoria, "microservicio_usado": usado}
    return render(request, "productos/index.html", context)


def crear(request):
    """Crea un producto. Con resiliencia: si el microservicio principal
    de escritura falla, también puede usar cualquiera de los otros 3,
    ya que los 4 saben hacer CRUD completo."""
    if request.method == "POST":
        datos = {
            "nombre": request.POST.get("nombre"),
            "categoria": request.POST.get("categoria"),
            "precio": float(request.POST.get("precio")),
            "stock": int(request.POST.get("stock")),
            "descripcion": request.POST.get("descripcion", ""),
        }
        try:
            respuesta, usado = llamar_con_resiliencia("POST", "/productos/", json=datos)
        except ConnectionError as e:
            return HttpResponse(f"No se pudo crear el producto en ningún microservicio.<br><pre>{e}</pre>")

        if respuesta.status_code in (200, 201):
            return redirect("productos:index")
        return HttpResponse(f"Error al crear el producto: {respuesta.text}")

    return render(request, "productos/form.html", {"accion": "Crear"})


def editar(request, producto_id):
    """Actualiza un producto, con resiliencia."""
    if request.method == "POST":
        datos = {
            "nombre": request.POST.get("nombre"),
            "categoria": request.POST.get("categoria"),
            "precio": float(request.POST.get("precio")),
            "stock": int(request.POST.get("stock")),
            "descripcion": request.POST.get("descripcion", ""),
        }
        try:
            respuesta, usado = llamar_con_resiliencia("PUT", f"/productos/{producto_id}/", json=datos)
        except ConnectionError as e:
            return HttpResponse(f"No se pudo actualizar el producto.<br><pre>{e}</pre>")

        if respuesta.status_code == 200:
            return redirect("productos:detalle", producto_id=producto_id)
        return HttpResponse(f"Error al actualizar el producto: {respuesta.text}")

    try:
        respuesta, usado = llamar_con_resiliencia("GET", f"/productos/{producto_id}/")
    except ConnectionError as e:
        return HttpResponse(f"No se pudo consultar el producto.<br><pre>{e}</pre>")

    if respuesta.status_code == 404:
        return HttpResponse(f"No existe un producto con el id {producto_id}.")

    producto = respuesta.json()
    context = {"accion": "Editar", "producto": producto}
    return render(request, "productos/form.html", context)


def eliminar(request, producto_id):
    """Elimina un producto, con resiliencia."""
    if request.method == "POST":
        try:
            llamar_con_resiliencia("DELETE", f"/productos/{producto_id}/")
        except ConnectionError as e:
            return HttpResponse(f"No se pudo eliminar el producto.<br><pre>{e}</pre>")
        return redirect("productos:index")

    try:
        respuesta, usado = llamar_con_resiliencia("GET", f"/productos/{producto_id}/")
    except ConnectionError as e:
        return HttpResponse(f"No se pudo consultar el producto.<br><pre>{e}</pre>")

    if respuesta.status_code == 404:
        return HttpResponse(f"No existe un producto con el id {producto_id}.")

    producto = respuesta.json()
    return render(request, "productos/eliminar.html", {"producto": producto})


def preguntar_ia(request):
    """Vista que consulta una IA externa (Google Gemini), dándole como
    contexto el inventario real (consultado con resiliencia)."""
    pregunta = request.GET.get("pregunta", "").strip()
    respuesta_ia = None

    if pregunta:
        try:
            resp_productos, _ = llamar_con_resiliencia("GET", "/productos/")
            productos = resp_productos.json()
        except ConnectionError:
            productos = []

        if productos:
            productos_ordenados = sorted(productos, key=lambda p: p["id"])
            inventario_texto = "\n".join(
                f"- id: {p['id']} | {p['nombre']} | categoría: {p['categoria']} | "
                f"precio: ${p['precio']} | stock: {p['stock']} unidades"
                for p in productos_ordenados
            )
        else:
            inventario_texto = "No hay datos de inventario disponibles en este momento."

        prompt = (
            "Eres un asistente experto en gestión de inventario para una tienda "
            "de barrio. Aquí está el inventario ACTUAL y REAL de la tienda, "
            "ordenado por id de menor a mayor. El id es autoincremental, por lo "
            "tanto el producto con el id MÁS ALTO es el que se registró más "
            "recientemente:\n\n"
            f"{inventario_texto}\n\n"
            "Usa estos datos reales para responder la siguiente pregunta del "
            "dueño de la tienda, de forma breve y concreta (máximo 4 líneas). "
            f"Pregunta: {pregunta}"
        )

        import requests as req
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-3.8-flash:generateContent?key={settings.GEMINI_API_KEY}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            resp = req.post(url, json=payload, timeout=15)
            datos = resp.json()
            if resp.status_code == 200:
                respuesta_ia = datos["candidates"][0]["content"]["parts"][0]["text"]
            else:
                mensaje = datos.get("error", {}).get("message", "desconocido")
                respuesta_ia = f"Error al consultar la IA: {mensaje}"
        except req.exceptions.RequestException:
            respuesta_ia = "No se pudo conectar con el servicio de IA. Intenta de nuevo."

    context = {"pregunta": pregunta, "respuesta_ia": respuesta_ia}
    return render(request, "productos/preguntar_ia.html", context)