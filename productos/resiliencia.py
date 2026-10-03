import time
import requests
from django.conf import settings


def llamar_con_resiliencia(metodo, ruta, json=None, timeout=10):
    """
    Intenta la petición HTTP contra cada microservicio de la lista, en orden,
    hasta que uno responda con un cuerpo JSON realmente válido.
    Si todos fallan (timeout, caído, error 5xx, o respuesta no-JSON), lanza
    una excepción con el detalle de qué pasó en cada uno.

    Devuelve una tupla: (respuesta, nombre_del_microservicio_usado)
    """
    errores = []

    for base_url in settings.MICROSERVICIOS:
        url = f"{base_url}{ruta}"
        try:
            respuesta = requests.request(metodo, url, json=json, timeout=timeout)

            # Un 404 solo es válido cuando se pide UN producto puntual
            # (ej. /productos/5/), nunca cuando se pide la lista completa.
            es_detalle = ruta.rstrip("/").split("/")[-1].isdigit()
            if respuesta.status_code == 404 and not es_detalle:
                errores.append(f"{base_url}: ruta no encontrada (404) en listado")
                continue

            if respuesta.status_code >= 500:
                errores.append(f"{base_url}: código {respuesta.status_code}")
                continue

            if respuesta.content:
                try:
                    respuesta.json()
                except ValueError:
                    errores.append(f"{base_url}: respuesta sin JSON válido")
                    continue

            return respuesta, base_url

        except requests.exceptions.RequestException as e:
            errores.append(f"{base_url}: {e.__class__.__name__}")

    raise ConnectionError(
        "Todos los microservicios fallaron:\n" + "\n".join(errores)
    )


def verificar_estado_microservicios():
    """
    Revisa, uno por uno, si cada microservicio de la lista responde.
    No usa resiliencia aquí a propósito: queremos el estado de TODOS,
    no detenernos en el primero que funcione.
    """
    resultados = []

    for base_url in settings.MICROSERVICIOS:
        estado = {"url": base_url, "activo": False, "tiempo_ms": None, "detalle": ""}
        try:
            inicio = time.time()
            respuesta = requests.get(f"{base_url}/productos/", timeout=6)
            tiempo = round((time.time() - inicio) * 1000)

            if respuesta.status_code < 500 and respuesta.content:
                respuesta.json()
                estado["activo"] = True
                estado["tiempo_ms"] = tiempo
                estado["detalle"] = f"OK ({respuesta.status_code})"
            else:
                estado["detalle"] = f"Código {respuesta.status_code}"
        except requests.exceptions.RequestException as e:
            estado["detalle"] = e.__class__.__name__
        except ValueError:
            estado["detalle"] = "Respuesta sin JSON válido"

        resultados.append(estado)

    return resultados