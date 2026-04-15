from django.db import models
from django.db.models import Sum


# ============================
# USUARIOS
# ============================

class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)

    rol = models.CharField(
        max_length=20,
        choices=[
            ('administrador', 'Administrador'),
            ('auxiliar', 'Auxiliar')
        ],
        default='auxiliar'
    )

    foto = models.ImageField(upload_to='usuarios/', null=True, blank=True)

    estado = models.CharField(
        max_length=10,
        choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')],
        default='activo'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    estado = models.CharField(
        max_length=10,
        choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')],
        default='activo'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

# =============================
#   MODELO ALMACÉN
# =============================

class Almacen(models.Model):
    Nombre = models.CharField(max_length=50)
    Capacidad = models.PositiveIntegerField(default=0)
    Tipo = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    # Nivel_seguridad = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return self.Nombre

# ============================
# PRODUCTOS
# ============================
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, unique=True)

    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    almacen = models.ForeignKey(Almacen, on_delete=models.CASCADE)

    cantidad = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5)
    stock_maximo = models.PositiveIntegerField(default=100)

    precio = models.DecimalField(max_digits=10, decimal_places=2)

    descripcion = models.TextField(blank=True, null=True)

    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)   # NUEVO

    estado = models.CharField(
        max_length=10,
        choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')],
        default='activo'
    )

    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

# ============================
# MODELO INVENTARIO (MOVIMIENTOS)
# ============================
class Inventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    almacen = models.ForeignKey(Almacen, on_delete=models.CASCADE)

    tipo_movimiento = models.CharField(
        max_length=10,
        choices=[('entrada', 'Entrada'), ('salida', 'Salida')],
        default='entrada'
    )

    cantidad = models.PositiveIntegerField(default=0)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)

    # Opcionales según tu diagrama
    stock_minimo = models.PositiveIntegerField(default=0)
    stock_maximo = models.PositiveIntegerField(default=0)

    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.producto.nombre} - {self.tipo_movimiento} ({self.cantidad})"


class NotificacionConfig(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)

    alertas_stock = models.BooleanField(default=True)
    movimientos = models.BooleanField(default=True)
    productos_nuevos = models.BooleanField(default=True)

    correo_alertas = models.BooleanField(default=True)
    correo_movimientos = models.BooleanField(default=True)

    def __str__(self):
        return f"Notificaciones de {self.usuario.nombre}"

class ConfigSistema(models.Model):
    nombre_sistema = models.CharField(max_length=100, default="Invenzo")
    stock_min_global = models.PositiveIntegerField(default=5)
    stock_max_global = models.PositiveIntegerField(default=100)


class StockAlmacen(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    almacen = models.ForeignKey(Almacen, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('producto', 'almacen')
