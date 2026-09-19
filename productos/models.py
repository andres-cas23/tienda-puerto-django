from django.db import models

# El catálogo de productos ya no vive aquí.
# Ahora se consulta a través del microservicio desplegado en Render,
# que a su vez accede a la base de datos en Supabase.