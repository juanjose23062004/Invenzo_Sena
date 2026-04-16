from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F, Q, Case, When, IntegerField
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib import messages
from .models import Usuario, Producto, Categoria, Almacen, Inventario, NotificacionConfig, StockAlmacen
from .forms import FormularioRegistro, ProductoForm, CategoriaForm, UsuarioCreateForm, UsuarioEditForm
from datetime import datetime
import csv
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password

# ================================
# DECORADOR PARA PROTEGER RUTAS
# ================================
def require_login(view):
    def wrapper(request, *args, **kwargs):
        if "usuario_id" not in request.session:
            return redirect("invenzo:iniciar_sesion")
        return view(request, *args, **kwargs)
    return wrapper
#================================
#ACCESOS PARA EL ADMINISTRADOR
#================================
def require_admin(view):
    def wrapper(request, *args, **kwargs):
        if "usuario_id" not in request.session:
            return redirect('invenzo:iniciar_sesion')
        if request.session.get('usuario_rol') != 'administrador':
            return redirect('invenzo:dashboard')
        return view(request, *args, **kwargs)
    return wrapper


# ================================
# HOME
# ================================
def inicio(request):
    return render(request, 'usuario/home.html')


# ================================
# REGISTRO
# ================================
def registrar_usuario(request):
    if request.method == 'POST':
        form = FormularioRegistro(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']

            if Usuario.objects.filter(email=email).exists():
                form.add_error("email", "Este correo ya está registrado.")
                return render(request, 'usuario/registro.html', {'form': form})

            # Guardar rol según lo que el usuario seleccionó en el formulario
            Usuario.objects.create(
                nombre=form.cleaned_data['nombre'],
                email=email,
                password=make_password(form.cleaned_data['contraseña']),
                rol="auxiliar",  # ✅ FORZADO
                estado="activo"
            )

            return redirect('invenzo:iniciar_sesion')

    else:
        form = FormularioRegistro()

    return render(request, 'usuario/registro.html', {'form': form})


# ================================
# LOGIN
# ================================

def iniciar_sesion(request):
    error = ''

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('contraseña')

        try:
            usuario = Usuario.objects.get(email=email)

            if not check_password(password, usuario.password):
                raise Usuario.DoesNotExist

            if usuario.estado != "activo":
                error = "Tu cuenta está desactivada."
                return render(request, 'usuario/login.html', {'error': error})

            request.session['usuario_id'] = usuario.id
            request.session['usuario_nombre'] = usuario.nombre
            request.session['usuario_rol'] = usuario.rol
            request.session['usuario_foto'] = usuario.foto.url if usuario.foto else None

            return redirect('invenzo:dashboard')

        except Usuario.DoesNotExist:
            error = "Correo o contraseña incorrectos"

    return render(request, 'usuario/login.html', {'error': error})


# ================================
# LOGOUT
# ================================
def cerrar_sesion(request):
    request.session.flush()
    return redirect('invenzo:iniciar_sesion')


# ================================
# RECUPERAR CONTRASEÑA (BASE)
# ================================
def recuperar_contraseña(request):
    enviado = False
    email = ""

    if request.method == "POST":
        email = request.POST.get("email")
        enviado = True

    return render(request, "usuario/recuperar.html", {
        "enviado": enviado,
        "email": email
    })


# ================================
# DASHBOARD
# ================================
@require_login
def dashboard(request):

    productos = Producto.objects.filter(estado="activo")

    total_productos = productos.count()

    productos_bajos = productos.filter(
        cantidad__lte=F("stock_minimo")
    ).count()

    movimientos_hoy = Inventario.objects.filter(
        fecha_movimiento__date=timezone.now().date()
    ).count()

    valor_total = productos.aggregate(
        total=Sum(F("cantidad") * F("precio"))
    )["total"] or 0

    productos_recientes = productos.order_by("-fecha_ingreso")[:5]

    form = ProductoForm()

    return render(request, "inventario/dashboard.html", {
        "productos": productos,
        "productos_recientes": productos_recientes,
        "total_productos": total_productos,
        "stock_bajo": productos_bajos,
        "movimientos_hoy": movimientos_hoy,
        "valor_total": valor_total,
        "page_title": "Dashboard",
        "form": form,
    })


# ================================
# LISTA DE PRODUCTOS
# ================================
@require_login
def productos_disponibles(request):
    productos = Producto.objects.filter(estado="activo")

    # LÓGICA DE CLASIFICACIÓN DE STOCK
    en_stock = productos.filter(cantidad__gt=F('stock_minimo')).count()
    bajo_stock = productos.filter(cantidad__gt=0, cantidad__lte=F('stock_minimo')).count()
    sin_stock = productos.filter(cantidad=0).count()

    return render(request, 'inventario/gestor_productos.html', {
        'productos': productos,
        'en_stock': en_stock,
        'bajo_stock': bajo_stock,
        'sin_stock': sin_stock
    })

# ================================
# AGREGAR PRODUCTO
# ================================
@require_login
def agregar_producto(request):
    if request.method == "POST":
        form = ProductoForm(request.POST)
        
        if form.is_valid():
            producto = form.save(commit=False)
            almacen = producto.almacen

            capacidad_ocupada = Producto.objects.filter(
                almacen=almacen
            ).aggregate(total=Sum('cantidad'))['total'] or 0

            disponible = almacen.Capacidad - capacidad_ocupada

            if producto.cantidad > disponible:
                messages.error(
                    request,
                    f"El almacén '{almacen.Nombre}' no tiene suficiente espacio. Disponible: {disponible}."
                )
                return redirect("invenzo:dashboard")

            # ✅ Guardar producto
            producto.save()

            # ✅ GUARDAR EN STOCK POR ALMACÉN (ESTO TE FALTABA)
            StockAlmacen.objects.create(
                producto=producto,
                almacen=almacen,
                cantidad=producto.cantidad
            )

            messages.success(request, "Producto agregado correctamente.")
            return redirect("invenzo:dashboard")

    return redirect("invenzo:dashboard")

# ================================
# EDITAR PRODUCTO
# ================================
@require_login
def editar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)

        if form.is_valid():
            form.save()
            return redirect('invenzo:productos_disponibles')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'inventario/editar_producto.html', {'form': form, 'producto': producto})


# ================================
# ELIMINAR PRODUCTO
# ================================
@require_login
def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.estado = "inactivo"
    producto.save()
    return redirect('invenzo:productos_disponibles')


# ================================
# MOVIMIENTOS DE INVENTARIO
# ================================
@require_login
def registrar_movimiento(request, id):

    producto = get_object_or_404(Producto, id=id)

    if request.method == "POST":
        tipo = request.POST.get("tipo")
        cantidad = int(request.POST.get("cantidad"))
        observacion = request.POST.get("observacion", "")

        if tipo == "entrada":
            producto.cantidad += cantidad
        else:
            producto.cantidad -= cantidad

        producto.save()

        Inventario.objects.create(
            producto=producto,
            usuario_id=request.session["usuario_id"],
            tipo_movimiento=tipo,
            cantidad=cantidad,
            observacion=observacion
        )

        return redirect("invenzo:productos_disponibles")

    return render(request, "inventario/movimiento.html", {
        "producto": producto
    })


# ================================
# CATEGORIAS
# ================================

@require_admin
def categorias(request):
    search = request.GET.get("search", "")

    categorias = Categoria.objects.all()

    if search:
        categorias = categorias.filter(nombre__icontains=search)

    return render(request, "inventario/categorias.html", {
        "categorias": categorias,
    })


@require_admin
def crear_categoria(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")

        Categoria.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            estado="activo"
        )

    return redirect("invenzo:categorias")


@require_admin
def editar_categoria(request, id):
    categoria = get_object_or_404(Categoria, id=id)

    if request.method == "POST":
        categoria.nombre = request.POST.get("nombre")
        categoria.descripcion = request.POST.get("descripcion")
        categoria.estado = request.POST.get("estado")
        categoria.save()

    return redirect("invenzo:categorias")


@require_admin
def eliminar_categoria(request, id):
    categoria = get_object_or_404(Categoria, id=id)
    categoria.delete()
    return redirect("invenzo:categorias")



@require_login
def exportar_productos(request):
    productos = Producto.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="productos.csv"'

    writer = csv.writer(response)
    writer.writerow(['Nombre', 'Código', 'Categoría', 'Cantidad', 'Precio'])

    for p in productos:
        writer.writerow([p.nombre, p.codigo, p.categoria.nombre, p.cantidad, p.precio])

    return response




def control_inventario(request):
    if "usuario_id" not in request.session:
        return redirect("invenzo:iniciar_sesion")

    productos = Producto.objects.all().order_by("nombre")
    movimientos = Inventario.objects.select_related("producto", "usuario").order_by("-fecha_movimiento")[:5]

    mensaje = ""
    error = ""

    if request.method == "POST":
        producto_id = request.POST.get("producto")
        tipo = request.POST.get("tipo_movimiento")
        cantidad = int(request.POST.get("cantidad"))
        observacion = request.POST.get("observacion")

        producto = get_object_or_404(Producto, id=producto_id)

        # Validación de salida
        if tipo == "salida" and cantidad > producto.cantidad:
            error = "No puedes retirar más del stock disponible."
        else:
            # Crear movimiento
            movimiento = Inventario.objects.create(
                producto=producto,
                usuario=Usuario.objects.get(id=request.session["usuario_id"]),
                tipo_movimiento=tipo,
                cantidad=cantidad,
                observacion=observacion,
            )

            # Actualizar stock
            if tipo == "entrada":
                producto.cantidad += cantidad
            else:
                producto.cantidad -= cantidad

            producto.save()

            mensaje = "Movimiento registrado exitosamente."

    contexto = {
        "productos": productos,
        "movimientos": movimientos,
        "mensaje": mensaje,
        "error": error,
    }

    return render(request, "inventario/control_inventario.html", contexto)



# ================================
# MOVIMIENTOS DE INVENTARIO
# ================================


@require_login
def historial(request):
    movimientos = Inventario.objects.select_related("producto", "usuario", "producto__categoria").order_by("-fecha_movimiento")

    # -------- FILTROS --------
    search = request.GET.get("search", "")
    tipo = request.GET.get("tipo", "")
    categoria = request.GET.get("categoria", "")
    fecha = request.GET.get("fecha", "")

    if search:
        movimientos = movimientos.filter(
            Q(producto__nombre__icontains=search) |
            Q(producto__codigo__icontains=search) |
            Q(observacion__icontains=search)
        )

    if tipo in ["entrada", "salida"]:
        movimientos = movimientos.filter(tipo_movimiento=tipo)

    if categoria:
        movimientos = movimientos.filter(producto__categoria__nombre__icontains=categoria)

    if fecha:
        movimientos = movimientos.filter(fecha_movimiento__date=fecha)

    # -------- PAGINACIÓN --------
    paginator = Paginator(movimientos, 8)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)

    context = {
        "movimientos": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "tipos": ["Entrada", "Salida"],
        "categorias": Categoria.objects.all(),
        "query": request.GET,
    }

    return render(request, "inventario/historial.html", context)


@require_login
def alerta_stock(request):

    productos = Producto.objects.select_related("categoria").all()

    # -------- CATEGORÍAS --------
    criticos = productos.filter(cantidad=0) | productos.filter(cantidad__lt=F("stock_minimo") / 2)
    bajos = productos.filter(cantidad__gt=0, cantidad__lte=F("stock_minimo"))

    # -------- FILTROS --------
    search = request.GET.get("search", "")
    nivel = request.GET.get("nivel", "")

    queryset = productos

    if search:
        queryset = queryset.filter(
            Q(nombre__icontains=search) |
            Q(codigo__icontains=search) |
            Q(categoria__nombre__icontains=search)
        )

    if nivel == "critico":
        queryset = criticos
    elif nivel == "bajo":
        queryset = bajos

    # -------- PAGINACIÓN --------
    paginator = Paginator(queryset, 8)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)

    # -------- ESTADÍSTICAS --------
    total_criticos = criticos.count()
    total_bajos = bajos.count()

    valor_estimado = sum(
        p.precio * (p.stock_minimo - p.cantidad)
        for p in productos if p.cantidad < p.stock_minimo
    )

    context = {
        "productos": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "total_criticos": total_criticos,
        "total_bajos": total_bajos,
        "valor_estimado": valor_estimado,
        "query": request.GET
    }

    return render(request, "inventario/alerta_stock.html", context)


@require_login
def reponer_stock(request, id):
    producto = get_object_or_404(Producto, id=id)

    producto.cantidad = producto.stock_maximo
    producto.save()

    # Registrar movimiento automático
    Inventario.objects.create(
        producto=producto,
        usuario=Usuario.objects.get(id=request.session["usuario_id"]),
        tipo_movimiento="entrada",
        cantidad=producto.stock_maximo,
        observacion="Reposición automática desde Alertas de Stock"
    )

    return redirect("invenzo:alerta_stock")



# Helper: comprobar rol admin

@require_admin
def usuarios(request):
    q = request.GET.get('search', '')
    rol = request.GET.get('rol', '')
    estado = request.GET.get('estado', '')

    qs = Usuario.objects.all().order_by('-fecha_creacion')

    if q:
        qs = qs.filter(
            Q(nombre__icontains=q) |
            Q(email__icontains=q)
    )


    if rol:
        qs = qs.filter(rol=rol)
    if estado:
        qs = qs.filter(estado=estado)

    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    context = {
        'usuarios': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'query': request.GET,
    }
    return render(request, 'usuario/usuarios.html', context)


@require_admin
def crear_usuario(request):
    if request.method == 'POST':
        form = UsuarioCreateForm(request.POST, request.FILES)
        if form.is_valid():
            u = form.save(commit=False)
            u.password = make_password(u.password)
            u.save()
            # Guardamos password tal cual para mantener compatibilidad con login actual.
            # (Si luego quieres hashing, actualizamos login.)
            u.save()
            return redirect('invenzo:usuarios')
    else:
        form = UsuarioCreateForm()
    return render(request, 'usuario/crear_usuario.html', {'form': form})

@require_admin
def editar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)

    es_admin = request.session.get('usuario_rol') == 'administrador'

    if request.method == 'POST':
        form = UsuarioEditForm(
            request.POST,
            request.FILES,
            instance=usuario,
            es_admin=es_admin   # 🔥 IMPORTANTE
        )
        if form.is_valid():
            form.save()
            return redirect('invenzo:usuarios')
    else:
        form = UsuarioEditForm(
            instance=usuario,
            es_admin=es_admin   # 🔥 IMPORTANTE
        )

    return render(request, 'usuario/editar_usuario.html', {
        'form': form,
        'usuario': usuario
    })


@require_admin
def desactivar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)
    usuario.estado = 'inactivo'
    usuario.save()
    return redirect('invenzo:usuarios')


@require_admin
def activar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)
    usuario.estado = 'activo'
    usuario.save()
    return redirect('invenzo:usuarios')


@require_admin
def reset_password(request, id):
    usuario = get_object_or_404(Usuario, id=id)
    if request.method == 'POST':
        nueva = request.POST.get('password')
        usuario.password = make_password(nueva)
        usuario.save()
        return redirect('invenzo:usuarios')
    return render(request, 'usuario/reset_password.html', {'usuario': usuario})





@require_login
def configuracion(request):
    return render(request, "inventario/configuracion.html")

@require_login
def configuracion_perfil(request):
    usuario = get_object_or_404(Usuario, id=request.session["usuario_id"])

    if request.method == "POST":
        usuario.nombre = request.POST.get("nombre", usuario.nombre)
        usuario.email = request.POST.get("email", usuario.email)

        # FOTO
        if request.FILES.get("foto"):
            usuario.foto = request.FILES["foto"]

        # CONTRASEÑA
        nueva_pass = request.POST.get("password")
        if nueva_pass:
            usuario.password = make_password(nueva_pass)

        usuario.save()

        # Actualizar datos en la sesión
        request.session["usuario_nombre"] = usuario.nombre
        request.session["usuario_foto"] = usuario.foto.url if usuario.foto else None

        return redirect("invenzo:configuracion_perfil")

    return render(request, "usuario/configuracion_perfil.html", {
        "usuario": usuario
    })


def eliminar_foto(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    if usuario.foto:
        usuario.foto.delete()  # Borra el archivo del storage
        usuario.foto = None
        usuario.save()
    return redirect('invenzo:configuracion')  # Redirige a la página de perfil



@require_admin
def configuracion_sistema(request):
    # TEMPORAL — si deseas lo conecto a un modelo Config.
    data = {
        "nombre_sistema": "Invenzo",
        "stock_min_global": 5,
        "stock_max_global": 100,
    }

    if request.method == "POST":
        data["nombre_sistema"] = request.POST.get("nombre_sistema")
        data["stock_min_global"] = request.POST.get("stock_min_global")
        data["stock_max_global"] = request.POST.get("stock_max_global")

        # Si quieres guardar esto en BD te creo el modelo Config y lo implemento.

    return render(request, "usuario/configuracion_sistema.html", data)


@require_login
def configuracion_notificaciones(request):
    usuario = get_object_or_404(Usuario, id=request.session["usuario_id"])

    # Crear config si no existe
    config, created = NotificacionConfig.objects.get_or_create(usuario=usuario)

    if request.method == "POST":
        config.alertas_stock = "alertas_stock" in request.POST
        config.movimientos = "movimientos" in request.POST
        config.productos_nuevos = "productos_nuevos" in request.POST

        config.correo_alertas = "correo_alertas" in request.POST
        config.correo_movimientos = "correo_movimientos" in request.POST

        config.save()

        return redirect("invenzo:configuracion_notificaciones")

    return render(request, "usuario/configuracion_notificaciones.html", {
        "config": config
    })


# ================================
# CRUD ALMACENES
# ================================


@require_login
def lista_almacenes(request):

    almacenes = Almacen.objects.annotate(
        ocupado=Sum("stockalmacen__cantidad")
    ).annotate(
        ocupado=Case(
            When(ocupado__isnull=True, then=0),
            default=F("ocupado"),
            output_field=IntegerField()
        ),
        disponible=F("Capacidad") - F("ocupado")
    )

    categorias = Categoria.objects.all()

    return render(request, "inventario/lista_almacen.html", {
        "almacenes": almacenes,
        "categorias": categorias
    })

@require_admin
def crear_almacen(request):
    if request.method == "POST":

        nombre = request.POST.get("Nombre")
        capacidad = request.POST.get("Capacidad")
        tipo_id = request.POST.get("Tipo")  # ahora es categoría
        nivel = request.POST.get("Nivel_seguridad")

        Almacen.objects.create(
            Nombre=nombre,
            Capacidad=capacidad,
            Tipo_id=tipo_id,
            Nivel_seguridad=nivel
        )

        return redirect("invenzo:lista_almacenes")

    categorias = Categoria.objects.filter(estado="activo")

    return render(request, "inventario/almacenes/crear.html", {
        "categorias": categorias
    })


@require_admin
def editar_almacen(request, id):
    almacen = get_object_or_404(Almacen, id=id)

    if request.method == "POST":
        almacen.Nombre = request.POST.get("Nombre")
        almacen.Capacidad = request.POST.get("Capacidad")
        almacen.Tipo_id = request.POST.get("Tipo")   # ← CORRECTO
        almacen.Nivel_seguridad = request.POST.get("Nivel_seguridad")
        almacen.save()

        return redirect("invenzo:lista_almacenes")

    # Necesitas las categorías para el select
    categorias = Categoria.objects.filter(estado="activo")

    return render(request, "inventario/editar_almacen.html", {
        "almacen": almacen,
        "categorias": categorias
    })

@require_admin
def eliminar_almacen(request, id):
    almacen = get_object_or_404(Almacen, id=id)
    almacen.delete()
    return redirect("invenzo:lista_almacenes")


@require_login
def inventario_por_almacen(request, id):
    almacen = get_object_or_404(Almacen, id=id)

    movimientos = (
        Inventario.objects
        .filter(almacen=almacen)
        .select_related("producto")
        .order_by("-fecha_movimiento")
    )

    total_entradas = movimientos.filter(tipo_movimiento="entrada").aggregate(
        total=Sum("cantidad")
    )["total"] or 0

    total_salidas = movimientos.filter(tipo_movimiento="salida").aggregate(
        total=Sum("cantidad")
    )["total"] or 0

    productos_totales = movimientos.values("producto").distinct().count()

    recientes = movimientos[:10]

    return render(request, "inventario/almacenes/dashboard.html", {
        "almacen": almacen,
        "movimientos": movimientos,
        "recientes": recientes,
        "total_entradas": total_entradas,
        "total_salidas": total_salidas,
        "productos_totales": productos_totales,
    })



@require_login
def control_inventario(request):

    if "usuario_id" not in request.session:
        return redirect("invenzo:iniciar_sesion")

    productos = Producto.objects.all().order_by("nombre")
    almacenes = Almacen.objects.all().order_by("Nombre")

    movimientos = Inventario.objects.select_related(
        "producto", "usuario", "almacen"
    ).order_by("-fecha_movimiento")[:5]

    mensaje = ""
    error = ""

    if request.method == "POST":

        producto_id = request.POST.get("producto")
        almacen_id = request.POST.get("almacen")
        tipo = request.POST.get("tipo_movimiento")
        observacion = request.POST.get("observacion")

        # --- VALIDAR CANTIDAD ---
        try:
            cantidad = int(request.POST.get("cantidad"))
            if cantidad <= 0:
                raise ValueError
        except (TypeError, ValueError):
            error = "La cantidad debe ser un número mayor a cero."

        if not error:

            if not almacen_id or not producto_id:
                error = "Debe seleccionar un almacén y un producto."
            else:
                producto = get_object_or_404(Producto, id=producto_id)
                almacen = get_object_or_404(Almacen, id=almacen_id)

                # Validar que el producto pertenezca al almacén
                if producto.almacen_id != almacen.id:
                    error = "El producto no pertenece a este almacén."
                else:
                    # Obtener o crear stock por almacén
                    stock, created = StockAlmacen.objects.get_or_create(
                        producto=producto,
                        almacen=almacen,
                        defaults={'cantidad': 0}
                    )

                    # Capacidad del almacén
                    ocupado = StockAlmacen.objects.filter(
                        almacen=almacen
                    ).aggregate(total=Sum('cantidad'))['total'] or 0

                    disponible = almacen.Capacidad - ocupado

                    # --- VALIDACIONES ---
                    if tipo == "entrada" and cantidad > disponible:
                        error = (
                            f"No hay espacio suficiente en el almacén. "
                            f"Disponible: {disponible}"
                        )

                    elif tipo == "salida" and cantidad > stock.cantidad:
                        error = "No puedes retirar más de lo disponible en este almacén."

                    else:
                        # Registrar movimiento
                        Inventario.objects.create(
                            producto=producto,
                            usuario=Usuario.objects.get(id=request.session["usuario_id"]),
                            almacen=almacen,
                            tipo_movimiento=tipo,
                            cantidad=cantidad,
                            observacion=observacion,
                        )

                        # Actualizar stock por almacén
                        if tipo == "entrada":
                            stock.cantidad += cantidad
                        else:
                            stock.cantidad -= cantidad

                        stock.save()

                        # Recalcular stock global del producto
                        producto.cantidad = StockAlmacen.objects.filter(
                            producto=producto
                        ).aggregate(total=Sum('cantidad'))['total'] or 0

                        producto.save()

                        mensaje = "Movimiento registrado correctamente."

    return render(request, "inventario/control_inventario.html", {
        "productos": productos,
        "almacenes": almacenes,
        "movimientos": movimientos,
        "mensaje": mensaje,
        "error": error,
    })