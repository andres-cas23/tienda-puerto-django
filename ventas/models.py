from django.db import models


class Venta(models.Model):
    producto_id = models.IntegerField()  # id del producto en Supabase (ya no es FK local)
    cantidad = models.IntegerField(default=1)
    fecha = models.DateTimeField("fecha de venta", auto_now_add=True)

    def __str__(self):
        return f"Venta de {self.cantidad} unidades del producto #{self.producto_id}"