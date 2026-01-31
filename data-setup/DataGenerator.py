import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import random
import os

# Configuración
OUTPUT_DIR = Path(__file__).parent / "example-data"
SCHEMAS_DIR = Path(__file__).parent / "schemas-validation"

# Un solo local de burgers
LOCAL_ID = "BURGER-LOCAL-001"
LOCAL_NAME = "Burger Cloud"

NOMBRES = ["Juan", "María", "Carlos", "Ana", "Luis", "Carmen", "José", "Laura", "Miguel", "Isabel", "Pedro", "Sofía", "Diego", "Valentina", "Andrés", "Camila"]
APELLIDOS = ["Pérez", "García", "López", "Martínez", "Rodríguez", "Fernández", "González", "Sánchez", "Torres", "Ramírez", "Flores", "Castro", "Morales", "Ortiz", "Silva", "Rojas"]
CORREOS_DOMINIOS = ["gmail.com", "outlook.com", "hotmail.com"]

# Categorías de productos según schema
CATEGORIAS_PRODUCTO = ["Hamburguesas", "Bebidas"]

# Productos de burgers
PRODUCTOS_BURGER = {
    "Hamburguesas": [
        ("Hamburguesa Clásica", 15.00, "Carne de res, lechuga, tomate, cebolla", 50),
        ("Cheeseburger", 18.00, "Hamburguesa clásica con queso cheddar", 45),
        ("Hamburguesa BBQ", 20.00, "Carne, queso, cebolla caramelizada, salsa BBQ", 40),
        ("Burger Deluxe", 25.00, "Doble carne, queso, bacon, huevo", 30),
        ("Mushroom Swiss Burger", 23.00, "Carne, champiñones, queso suizo", 35),
        ("Spicy Jalapeño Burger", 22.00, "Carne, jalapeños, queso pepper jack", 38),
    ],
    "Bebidas": [
        ("Coca Cola 500ml", 5.00, "Bebida gasificada", 100),
        ("Limonada Natural", 6.00, "Limonada fresca", 80),
        ("Agua Mineral", 3.00, "Agua embotellada 500ml", 120),
        ("Fanta Naranja 500ml", 5.00, "Bebida gasificada sabor naranja", 90),
        ("Sprite 500ml", 5.00, "Bebida gasificada sabor lima-limón", 95),
    ]
}

# Roles según schemas
ROLES_EMPLEADOS = ["Cocinero", "Repartidor"]  # Solo estos 2 según schema
ROLES_USUARIOS = ["Cliente", "Gerente"]  # Sin Admin según schema
ESTADOS_PEDIDO = ["procesando", "cocinando", "enviando", "recibido"]  # Según schema

USUARIOS_TOTAL = int(os.getenv("USUARIOS_TOTAL", "15"))
EMPLEADOS_TOTAL = int(os.getenv("EMPLEADOS_TOTAL", "10"))
PEDIDOS_TOTAL = int(os.getenv("PEDIDOS_TOTAL", "20"))


def generar_correo(nombre, apellido):
    base = (f"{nombre}.{apellido}".lower()
            .replace("á", "a").replace("é", "e").replace("í", "i")
            .replace("ó", "o").replace("ú", "u"))
    dominio = random.choice(CORREOS_DOMINIOS)
    return f"{base}@{dominio}"


def generar_telefono():
    return f"+51 9{random.randint(10000000, 99999999)}"


def generar_slug(texto: str) -> str:
    s = texto.lower()
    for k, v in {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n"}.items():
        s = s.replace(k, v)
    s = s.replace(" ", "-")
    return "".join(c for c in s if c.isalnum() or c in "-_")


def generar_local():
    """Genera un solo local de burgers."""
    nombre_gerente = f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)}"
    correo_gerente = generar_correo(*nombre_gerente.split())
    gerente = {
        "nombre": nombre_gerente,
        "correo": correo_gerente,
        "contrasena": f"ger_{uuid.uuid4().hex[:8]}"
    }
    
    return {
        "local_id": LOCAL_ID,
        "direccion": "Av. Javier Prado 2050, San Isidro, Lima",
        "telefono": generar_telefono(),
        "hora_apertura": "10:00",
        "hora_finalizacion": "23:00",
        "gerente": gerente
    }


def generar_usuarios(local, cantidad=None):
    """
    Genera usuarios: Gerente y Clientes.
    Schema: correo (PK), nombre, contrasena, role (Cliente|Gerente)
    """
    cantidad = max(1, cantidad or USUARIOS_TOTAL)
    usuarios = []
    correos_usados = set()

    # 1. Gerente del local (Generado dinámicamente)
    g = local["gerente"]
    usuarios.append({
        "correo": g["correo"],
        "nombre": g["nombre"],
        "contrasena": g["contrasena"],
        "role": "Gerente"
    })
    correos_usados.add(g["correo"])

    # 2. Usuarios de Prueba (Hardcoded)
    usuarios_prueba = [
        {"correo": "cliente@test.com", "nombre": "Cliente Test", "role": "Cliente", "contrasena": "123456"},
        {"correo": "gerente@burger.com", "nombre": "Gerente Test", "role": "Gerente", "contrasena": "123456"}
    ]
    
    for u in usuarios_prueba:
        if u["correo"] not in correos_usados:
            usuarios.append({
                "correo": u["correo"],
                "nombre": u["nombre"],
                "contrasena": u["contrasena"], # hash real debería hacerse en auth-service al registrar
                "role": u["role"]
            })
            correos_usados.add(u["correo"])

    # 3. Clientes Aleatorios
    while len(usuarios) < cantidad:
        nombre = random.choice(NOMBRES)
        apellido = random.choice(APELLIDOS)
        correo = generar_correo(nombre, apellido)
        if correo in correos_usados:
            continue
        usuario = {
            "correo": correo,
            "nombre": f"{nombre} {apellido}",
            "contrasena": f"cli_{uuid.uuid4().hex[:10]}",
            "role": "Cliente"
        }
        usuarios.append(usuario)
        correos_usados.add(correo)

    return usuarios


def generar_empleados(local, cantidad=None):
    """
    Genera empleados del local de burgers.
    Schema: local_id (PK), correo (SK), contrasena, nombre, apellido, role (Cocinero|Repartidor)
    """
    cantidad = max(1, cantidad or EMPLEADOS_TOTAL)
    empleados = []
    correos_usados = set()
    
    # 1. Empleados de Prueba (Hardcoded)
    empleados_prueba = [
        {"correo": "cocina@burger.com", "nombre": "Chef", "apellido": "Ramsay", "role": "Cocinero"},
        {"correo": "delivery@burger.com", "nombre": "Flash", "apellido": "Gordon", "role": "Repartidor"}
    ]
    
    for emp in empleados_prueba:
        empleados.append({
            "local_id": local["local_id"],
            "correo": emp["correo"],
            "contrasena": "123456",
            "nombre": emp["nombre"],
            "apellido": emp["apellido"],
            "role": emp["role"]
        })
        correos_usados.add(emp["correo"])

    # 2. Empleados Aleatorios
    for _ in range(cantidad):
        nombre = random.choice(NOMBRES)
        apellido = random.choice(APELLIDOS)
        correo = generar_correo(nombre, apellido)
        
        # Evitar duplicados de correo
        if correo in correos_usados:
            correo = f"{nombre.lower()}.{apellido.lower()}.{random.randint(1,99)}@{random.choice(CORREOS_DOMINIOS)}"
        
        empleados.append({
            "local_id": local["local_id"],
            "correo": correo,
            "contrasena": f"emp_{uuid.uuid4().hex[:8]}",
            "nombre": nombre,
            "apellido": apellido,
            "role": random.choice(ROLES_EMPLEADOS)
        })
        correos_usados.add(correo)
    
    return empleados


def generar_productos(local):
    """
    Genera catálogo de productos de burgers.
    Schema: local_id (PK), producto_id (SK), nombre, precio, descripcion, categoria, stock, imagen_url
    """
    productos = []
    for categoria, items in PRODUCTOS_BURGER.items():
        for nombre, precio, descripcion, stock in items:
            producto_id = str(uuid.uuid4())
            slug = generar_slug(nombre)
            productos.append({
                "local_id": local["local_id"],
                "producto_id": producto_id,
                "nombre": nombre,
                "precio": precio,
                "descripcion": descripcion,
                "categoria": categoria,
                "stock": stock,
                "imagen_url": f"https://burgercloud.s3.amazonaws.com/productos/{slug}.jpg"
            })
    return productos


def generar_pedidos_y_historial(local, usuarios, productos, cantidad=None):
    """
    Genera pedidos y su historial de estados.
    Pedido Schema: local_id (PK), pedido_id (SK), correo, productos[], costo, direccion, estado, created_at
    Historial Schema: pedido_id (PK), estado_id (SK), estado, hora_inicio, hora_fin
    """
    cantidad = max(1, cantidad or PEDIDOS_TOTAL)
    pedidos, historial_estados = [], []

    clientes = [u for u in usuarios if u["role"] == "Cliente"]
    productos_disponibles = productos

    for _ in range(cantidad):
        cliente = random.choice(clientes)
        
        # Seleccionar productos aleatorios
        num_items = random.randint(1, 3)
        items = random.sample(productos_disponibles, k=min(num_items, len(productos_disponibles)))
        productos_pedido, costo = [], 0.0
        
        for prod in items:
            cant = random.randint(1, 2)
            # Solo producto_id y cantidad según schema
            productos_pedido.append({
                "producto_id": prod["producto_id"],
                "cantidad": cant
            })
            costo += prod["precio"] * cant

        # Crear pedido
        ahora = datetime.now()
        inicio = ahora - timedelta(minutes=random.randint(5, 120))
        created_at = inicio.isoformat()

        # Estados posibles
        estados_posibles = ESTADOS_PEDIDO.copy()
        ultimo_estado = random.choice(estados_posibles)
        idx_final = estados_posibles.index(ultimo_estado)
        secuencia = estados_posibles[: idx_final + 1]

        pedido_id = str(uuid.uuid4())
        t_actual = inicio
        
        # Generar historial de estados
        for estado in secuencia:
            dur = random.randint(3, 15)
            t_fin = t_actual + timedelta(minutes=dur)
            historial_estados.append({
                "pedido_id": pedido_id,
                "estado_id": str(uuid.uuid4()),
                "estado": estado,
                "hora_inicio": t_actual.isoformat(),
                "hora_fin": t_fin.isoformat()
            })
            t_actual = t_fin

        # Crear pedido
        pedido = {
            "local_id": local["local_id"],
            "pedido_id": pedido_id,
            "correo": cliente["correo"],
            "productos": productos_pedido,
            "costo": round(costo, 2),
            "direccion": f"Calle {random.randint(1, 50)} #{random.randint(100, 999)}, {random.choice(['Miraflores', 'San Isidro', 'Surco', 'La Molina'])}",
            "estado": ultimo_estado,
            "created_at": created_at
        }

        pedidos.append(pedido)

    return pedidos, historial_estados


def validar_con_esquema(datos, nombre_esquema):
    """Validación básica de campos requeridos."""
    try:
        schema_path = SCHEMAS_DIR / f"{nombre_esquema}.json"
        if not schema_path.exists():
            print(f"   ⚠️  Schema no encontrado: {schema_path}")
            return True
        
        with open(schema_path, "r", encoding="utf-8") as f:
            esquema = json.load(f)
        required = esquema.get("required", [])
        for item in datos:
            for campo in required:
                if campo not in item:
                    print(f"⚠️ Falta campo requerido '{campo}' en {nombre_esquema}")
                    return False
        print(f"✅ Datos de {nombre_esquema} pasan validación básica (required)")
        return True
    except Exception as e:
        print(f"❌ Error al validar {nombre_esquema}: {e}")
        return False


def guardar_json(datos, nombre_archivo):
    """Guarda datos en archivo JSON."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    ruta = OUTPUT_DIR / nombre_archivo
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    print(f"📝 Generado: {ruta} ({len(datos)} registros)")


def main():
    print("=" * 60)
    print("🍔 GENERADOR DE DATOS - BURGER CLOUD")
    print("=" * 60)
    print()

    print("📊 Generando local...")
    local = generar_local()
    guardar_json([local], "locales.json")
    print()

    print("📊 Generando usuarios...")
    usuarios = generar_usuarios(local)
    validar_con_esquema(usuarios, "usuarios")
    guardar_json(usuarios, "usuarios.json")
    print()

    print("📊 Generando empleados...")
    empleados = generar_empleados(local)
    validar_con_esquema(empleados, "empleados")
    guardar_json(empleados, "empleados.json")
    print()

    print("📊 Generando productos...")
    productos = generar_productos(local)
    validar_con_esquema(productos, "productos")
    guardar_json(productos, "productos.json")
    print()

    # DESHABILITADO: No generar pedidos ni historial en la base de datos inicial
    # print("📊 Generando pedidos e historial de estados...")
    # pedidos, historial_estados = generar_pedidos_y_historial(local, usuarios, productos)
    # validar_con_esquema(pedidos, "pedidos")
    # guardar_json(pedidos, "pedidos.json")
    # print()
    # 
    # validar_con_esquema(historial_estados, "historial_estados")
    # guardar_json(historial_estados, "historial_estados.json")
    # print()

    print("=" * 60)
    print("✨ Generación completada exitosamente")
    print(f"📂 Archivos guardados en: {OUTPUT_DIR}")
    print("⚠️  NOTA: Pedidos e historial NO generados (base de datos vacía)")
    print("=" * 60)


if __name__ == "__main__":
    main()
