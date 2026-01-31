# 📊 Data Setup - Burger Cloud

Esta carpeta contiene todo lo necesario para generar y poblar datos de prueba en DynamoDB.

## 📁 Contenido

### Scripts Principales

- **DataGenerator.py** - Genera datos de prueba JSON
- **DataPoblator.py** - Crea tablas DynamoDB y las puebla con datos

### Carpetas

- **schemas-validation/** - Esquemas JSON para validación de datos
- **example-data/** - JSONs generados (se crea al ejecutar DataGenerator.py)

## 🚀 Uso

### 1. Generar Datos

```bash
cd data-setup
python3 DataGenerator.py
```

Esto creará la carpeta `example-data/` con:
- `usuarios.json` - Usuarios (Cliente, Gerente)
- `empleados.json` - Empleados (Cocinero, Repartidor) con correo y contraseña
- `locales.json` - Un local de burgers
- `productos.json` - Hamburguesas y Bebidas
- `pedidos.json` - Pedidos de ejemplo
- `historial_estados.json` - Historial de estados de pedidos

### 2. Crear y Poblar Tablas

```bash
python3 DataPoblator.py
```

Esto:
1. Verifica credenciales AWS
2. Crea 7 tablas DynamoDB
3. Puebla las tablas con los datos generados

## 📋 Schemas Actualizados

### Usuarios
- **PK**: correo
- Campos: nombre, correo, contrasena, role (Cliente|Gerente)

### Empleados (Actualizado)
- **PK**: local_id
- **SK**: correo (antes era dni)
- Campos: local_id, correo, contrasena, nombre, apellido, role (Cocinero|Repartidor)

### Productos
- **PK**: local_id
- **SK**: producto_id
- Categorías: Hamburguesas | Bebidas (solo 2 categorías)
- Campos: nombre, precio, descripcion, categoria, stock, imagen_url

### Pedidos
- **PK**: local_id
- **SK**: pedido_id
- **GSI**: by_usuario (correo + created_at)
- productos[] solo tiene: producto_id y cantidad
- Estados: procesando | cocinando | enviando | recibido

## ⚠️ Notas Importantes

1. **Correo en Empleados**: Ahora los empleados usan `correo` como Sort Key en vez de `dni`
2. **Correo y Contraseña**: Todos los empleados tienen correo y contraseña para autenticación
3. **Categorías Limitadas**: Solo Hamburguesas y Bebidas (según schema actualizado)
4. **Roles de Usuario**: Solo Cliente y Gerente (sin Admin)
5. **Roles de Empleado**: Solo Cocinero y Repartidor (sin Despachador)

## 🔄 Regenerar Datos

Si necesitas datos frescos:

```bash
# Eliminar datos anteriores
rm -rf example-data/

# Generar nuevos datos
python3 DataGenerator.py

# Volver a poblar (esto limpia las tablas primero)
python3 DataPoblator.py
```
