from django.db import models

# Create your models here
class Cliente(models.Model):
    nombre = models.CharField(max_length=30)
    direccion = models.CharField(max_length=50)
    email = models.EmailField()
    telefono = models.CharField(max_length=9)
    
    def __str__(self):
        return self.nombre

class Articulos(models.Model):
    nombre = models.CharField(max_length=30)
    precio = models.IntegerField()
    seccion = models.CharField(max_length=20)
    
    def __str__(self):
        return self.nombre

class Pedidos(models.Model):
    numero = models.IntegerField()
    fecha = models.DateField()
    entregado = models.BooleanField()

    def __str__(self):
        return f"Pedido {self.numero} - {self.fecha}"