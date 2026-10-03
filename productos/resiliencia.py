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

            if respuesta.status_code >= 500:
                errores.append(f"{base_url}: código {respuesta.status_code}")
                continue

            # Verificamos que el cuerpo sea JSON válido antes de aceptar
            # esta respuesta como buena (evita cuerpos vacíos o páginas
            # intermedias de "despertando" que no son JSON real).
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