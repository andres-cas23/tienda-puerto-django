import requests
from django.conf import settings


def llamar_con_resiliencia(metodo, ruta, json=None, timeout=8):
    """
    Intenta la petición HTTP contra cada microservicio de la lista,
    en orden, hasta que uno responda exitosamente (código 2xx o 404,
    que son respuestas "válidas" del servicio, solo que sin datos).
    Si todos fallan (timeout, caído, error 5xx), lanza una excepción.

    Devuelve una tupla: (respuesta, nombre_del_microservicio_usado)
    """
    errores = []

    for base_url in settings.MICROSERVICIOS:
        url = f"{base_url}{ruta}"
        try:
            respuesta = requests.request(metodo, url, json=json, timeout=timeout)
            if respuesta.status_code < 500:
                return respuesta, base_url
            else:
                errores.append(f"{base_url}: código {respuesta.status_code}")
        except requests.exceptions.RequestException as e:
            errores.append(f"{base_url}: {e.__class__.__name__}")

    raise ConnectionError(
        "Todos los microservicios fallaron:\n" + "\n".join(errores)
    )