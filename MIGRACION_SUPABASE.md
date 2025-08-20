# 🚀 Migración a Supabase

Esta guía te ayudará a migrar tu proyecto de SQLite a Supabase PostgreSQL.

## 📋 Requisitos Previos

1. **Cuenta en Supabase**: Crea una cuenta gratuita en [supabase.com](https://supabase.com)
2. **Proyecto en Supabase**: Crea un nuevo proyecto
3. **Python 3.8+**: Asegúrate de tener Python instalado

## 🔧 Librerías Instaladas

Las siguientes librerías han sido agregadas al proyecto:

```bash
pip install psycopg2-binary==2.9.10
pip install supabase==2.18.1
pip install python-dotenv==1.1.1
```

### 📦 Descripción de Librerías

- **psycopg2-binary**: Adaptador PostgreSQL para Python
- **supabase**: SDK oficial de Supabase para Python
- **python-dotenv**: Manejo de variables de entorno

## ⚙️ Configuración

### 1. Variables de Entorno

Copia el archivo `.env.example` a `.env` y completa los valores:

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales de Supabase:

```env
# Configuración de Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_anon_key_aqui
SUPABASE_SERVICE_KEY=tu_service_role_key_aqui

# Configuración de PostgreSQL
DB_HOST=db.tu-proyecto.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=tu_password_aqui
```

### 2. Obtener Credenciales de Supabase

1. Ve a tu panel de Supabase
2. Selecciona tu proyecto
3. Ve a **Settings** > **API**
4. Copia los siguientes valores:
   - **Project URL**: Para `SUPABASE_URL`
   - **anon public**: Para `SUPABASE_KEY`
   - **service_role**: Para `SUPABASE_SERVICE_KEY`

5. Ve a **Settings** > **Database**
6. Copia los datos de conexión:
   - **Host**: Para `DB_HOST`
   - **Database password**: Para `DB_PASSWORD`

## 🚀 Proceso de Migración

### Opción 1: Usar la Interfaz Web

1. Ejecuta la aplicación:
   ```bash
   streamlit run app_refactored.py
   ```

2. Ve a la pestaña **"Supabase"** en el menú

3. Configura tus credenciales en la pestaña **"Configurar Supabase"**

4. Prueba la conexión en **"Probar Conexión"**

5. Migra los datos en **"Migrar Datos"**:
   - Crear tablas en Supabase
   - Exportar datos de SQLite
   - Importar datos a Supabase

### Opción 2: Script de Migración

Ejecuta el script de migración directamente:

```bash
python migrate_to_supabase.py
```

## 📊 Estructura de Tablas

El sistema creará las siguientes tablas en Supabase:

### `boletines`
```sql
CREATE TABLE boletines (
    id SERIAL PRIMARY KEY,
    titular VARCHAR(255) NOT NULL,
    numero_boletin VARCHAR(100),
    importancia VARCHAR(50) DEFAULT 'Pendiente',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_envio_reporte TIMESTAMP,
    reporte_enviado BOOLEAN DEFAULT FALSE,
    nombre_archivo_reporte VARCHAR(255),
    ruta_reporte VARCHAR(500),
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `clientes`
```sql
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    titular VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    fecha_ultimo_reporte TIMESTAMP,
    total_reportes INTEGER DEFAULT 0,
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `emails_enviados`
```sql
CREATE TABLE emails_enviados (
    id SERIAL PRIMARY KEY,
    titular VARCHAR(255),
    destinatario VARCHAR(255) NOT NULL,
    asunto VARCHAR(500) NOT NULL,
    mensaje TEXT NOT NULL,
    tipo_email VARCHAR(100) DEFAULT 'general',
    status VARCHAR(50) DEFAULT 'pendiente',
    fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_mensaje TEXT,
    numero_boletin VARCHAR(100),
    ruta_archivo VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔄 Uso del Nuevo Sistema

### Conexión con Supabase SDK

```python
from supabase_connection import crear_conexion_supabase

# Usar el SDK de Supabase
supabase = crear_conexion_supabase()

# Insertar datos
result = supabase.table('boletines').insert({
    'titular': 'Cliente Ejemplo',
    'numero_boletin': '2024-001',
    'importancia': 'Alta'
}).execute()

# Consultar datos
data = supabase.table('boletines').select('*').execute()
```

### Conexión Directa a PostgreSQL

```python
from supabase_connection import crear_conexion_postgres

# Para queries complejas
conn = crear_conexion_postgres()
cursor = conn.cursor()
cursor.execute("SELECT * FROM boletines WHERE importancia = %s", ('Alta',))
results = cursor.fetchall()
```

## 🎯 Ventajas de Supabase

### ✅ Beneficios Técnicos
- **Escalabilidad**: PostgreSQL maneja grandes volúmenes de datos
- **Backups automáticos**: Sin preocupaciones por pérdida de datos
- **Índices**: Mejor rendimiento en consultas
- **ACID compliance**: Transacciones confiables

### ✅ Beneficios Operacionales
- **Acceso remoto**: Base de datos accesible desde cualquier lugar
- **Panel de administración**: Interfaz web para gestionar datos
- **APIs automáticas**: REST y GraphQL generadas automáticamente
- **Tiempo real**: Subscripciones para actualizaciones en vivo

### ✅ Beneficios de Desarrollo
- **Row Level Security**: Seguridad granular
- **Funciones de base de datos**: Lógica personalizada en PostgreSQL
- **Extensiones**: PostGIS, pg_cron, y más
- **Integración**: Webhooks y triggers

## 🔧 Funciones de Compatibilidad

El código existente seguirá funcionando gracias a las funciones de compatibilidad:

```python
# Función original (SQLite)
from database import crear_conexion, crear_tabla

# Función nueva (Supabase) - misma interfaz
from supabase_connection import crear_conexion, crear_tabla
```

## 🚨 Consideraciones Importantes

### 🔒 Seguridad
- Nunca commitees las credenciales al repositorio
- Usa variables de entorno para datos sensibles
- Habilita Row Level Security en producción

### 💾 Backups
- SQLite se respaldará automáticamente antes de la migración
- Supabase maneja backups automáticos
- Considera exports periódicos para redundancia

### 🔄 Rollback
Si necesitas volver a SQLite:

```python
from config import switch_to_sqlite
switch_to_sqlite()
```

## 📚 Recursos Adicionales

- [Documentación de Supabase](https://supabase.com/docs)
- [SDK Python de Supabase](https://github.com/supabase/supabase-py)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [psycopg2 Documentation](https://psycopg.org/docs/)

## 🆘 Solución de Problemas

### Error de Conexión
```bash
# Verifica las credenciales
python -c "from supabase_connection import supabase_manager; print(supabase_manager.supabase)"
```

### Error de Migración
```bash
# Revisa los logs
tail -f logs/migration.log
```

### Problemas de Rendimiento
- Revisa los índices creados
- Optimiza las consultas SQL
- Considera connection pooling

## 📞 Soporte

Si encuentras problemas:

1. Revisa la consola de Supabase
2. Verifica las variables de entorno
3. Consulta los logs de la aplicación
4. Usa la página de "Probar Conexión" en la aplicación
