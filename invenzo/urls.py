from django.urls import path
from . import views

app_name = 'invenzo'

urlpatterns = [

    # ============================
    # USUARIO / AUTENTICACIÓN
    # ============================
    path('', views.inicio, name='home'),
    path('registro/', views.registrar_usuario, name='registrar_usuario'),
    path('login/', views.iniciar_sesion, name='iniciar_sesion'),
    path('logout/', views.cerrar_sesion, name='cerrar_sesion'),
    path('recuperar/', views.recuperar_contraseña, name='recuperar'),

    # ============================
    # DASHBOARD
    # ============================
    path('dashboard/', views.dashboard, name='dashboard'),

    # ============================
    # PRODUCTOS
    # ============================
    path('productos/', views.productos_disponibles, name='productos_disponibles'),
    path('productos/agregar/', views.agregar_producto, name='agregar_producto'),
    path('productos/editar/<int:id>/', views.editar_producto, name='editar_producto'),
    path('productos/eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),
    path('productos/exportar/', views.exportar_productos, name='exportar_productos'),


    # ============================
    # INVENTARIO (MOVIMIENTOS)
    # ============================
    path('productos/<int:id>/movimiento/', views.registrar_movimiento, name='registrar_movimiento'),

    # ============================
    # CATEGORÍAS
    # ============================
    path('categorias/', views.categorias, name='categorias'),
    path('categorias/crear/', views.crear_categoria, name='crear_categoria'),
    path('categorias/editar/<int:id>/', views.editar_categoria, name='editar_categoria'),
    path('categorias/eliminar/<int:id>/', views.eliminar_categoria, name='eliminar_categoria'),

#almacen 
    path('almacenes/', views.lista_almacenes, name='lista_almacenes'),
    path('almacenes/crear/', views.crear_almacen, name='crear_almacen'),
    path('almacenes/editar/<int:id>/', views.editar_almacen, name='editar_almacen'),
    path('almacenes/eliminar/<int:id>/', views.eliminar_almacen, name='eliminar_almacen'),
    path("almacenes/<int:id>/inventario/", views.inventario_por_almacen, name="inventario_por_almacen"),
    
# ============================
# INVENTSARIO
# ============================
    path('inventario/', views.control_inventario, name='control_inventario'),
    path("historial/", views.historial, name="historial"),

    path("alertas/", views.alerta_stock, name="alerta_stock"),
    path("alertas/reponer/<int:id>/", views.reponer_stock, name="reponer_stock"),



    path('usuarios/', views.usuarios, name='usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/editar/<int:id>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/desactivar/<int:id>/', views.desactivar_usuario, name='desactivar_usuario'),
    path('usuarios/activar/<int:id>/', views.activar_usuario, name='activar_usuario'),
    path('usuarios/reset-password/<int:id>/', views.reset_password, name='reset_password'),




    path("configuracion/", views.configuracion, name="configuracion"),
    path("configuracion/perfil/", views.configuracion_perfil, name="configuracion_perfil"),
    path('configuracion/eliminar_foto/<int:usuario_id>/', views.eliminar_foto, name='eliminar_foto'),
    path("configuracion/sistema/", views.configuracion_sistema, name="configuracion_sistema"),
    path("configuracion/notificaciones/", views.configuracion_notificaciones, name="configuracion_notificaciones"),



]
