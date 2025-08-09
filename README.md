# 🏢 Sistema de Gestión de Marcas - Estudio Contable

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/GiacosaM/Automation_marcas/releases)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/license-Private-orange.svg)]()

## 📋 Descripción

Sistema web profesional desarrollado en Streamlit para la gestión automatizada de boletines de marcas y patentes. Diseñado específicamente para estudios contables que manejan la administración de marcas comerciales.

## ✨ Características Principales

### 🔐 **Autenticación Segura**
- Sistema de login con encriptación bcrypt
- Gestión de sesiones de usuario
- Credenciales de administrador por defecto

### 📊 **Dashboard Interactivo**
- Métricas en tiempo real
- Gráficos profesionales con Plotly
- Alertas de vencimientos automáticas
- Monitoreo de cumplimiento legal

### 📄 **Gestión de Boletines**
- Carga masiva desde archivos Excel
- Procesamiento automático de datos
- Clasificación por importancia
- Historial completo de registros

### 👥 **Administración de Clientes**
- Base de datos de titulares
- Información de contacto
- Gestión de correspondencia

### 📧 **Sistema de Emails**
- Envío automático de reportes
- Validación de direcciones
- Logs de envíos
- Plantillas profesionales

### 📈 **Generación de Reportes**
- PDFs automáticos con marca de agua
- Informes por titular
- Clasificación por importancia
- Exportación de datos

## 🚀 Instalación

### Requisitos Previos
- Python 3.8 o superior
- pip package manager

### 1. Clonar el Repositorio
```bash
git clone https://github.com/GiacosaM/Automation_marcas.git
cd Automation_marcas
```

### 2. Crear Entorno Virtual
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configuración Inicial
```bash
# Crear directorio de imagenes si no existe
mkdir -p imagenes

# Configurar credenciales de email (opcional)
cp config.json.example config.json
```

## 🎯 Uso

### Iniciar la Aplicación
```bash
streamlit run app.py
```

La aplicación estará disponible en: `http://localhost:8501`

### Credenciales por Defecto
- **Usuario:** `admin`
- **Contraseña:** `admin123`

### Flujo de Trabajo Típico

1. **Autenticación** → Ingresar credenciales
2. **Cargar Datos** → Subir archivo Excel con boletines
3. **Revisar Dashboard** → Verificar métricas y alertas
4. **Gestionar Clientes** → Actualizar información de contacto
5. **Generar Informes** → Crear PDFs automáticamente
6. **Enviar Emails** → Distribuir reportes a clientes

## 📁 Estructura del Proyecto

```
Automation_marcas/
├── app.py                          # Aplicación principal
├── auth_manager_simple.py          # Sistema de autenticación
├── config.py                       # Configuración del sistema
├── database.py                     # Gestión de base de datos
├── email_sender.py                 # Sistema de emails
├── extractor.py                    # Procesamiento de Excel
├── report_generator.py             # Generación de PDFs
├── professional_theme.py           # Tema y estilos
├── dashboard_charts.py             # Gráficos interactivos
├── notifications.py                # Sistema de notificaciones
├── requirements.txt                # Dependencias Python
├── config.json                     # Configuración de email
├── boletines.db                    # Base de datos SQLite
├── imagenes/                       # Recursos visuales
│   ├── Logo.png
│   └── marca_agua.jpg
├── informes/                       # PDFs generados
├── temp/                           # Archivos temporales
└── test_*.py                       # Suite de testing
```

## 🛠️ Configuración

### Configuración de Email
Editar `config.json`:
```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "from_email": "tu-email@gmail.com",
    "password": "tu-password-app"
  },
  "reports": {
    "watermark_path": "imagenes/marca_agua.jpg"
  }
}
```

### Variables de Entorno (Opcional)
```bash
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

## 🧪 Testing

Ejecutar la suite de pruebas:
```bash
# Tests individuales
python test_email_validation.py
python test_credentials.py
python test_vencimientos.py

# Test completo del sistema
python -m pytest test_*.py -v
```

## 📚 Documentación Adicional

- [`CORRECCION_ERROR_GRID.md`](CORRECCION_ERROR_GRID.md) - Corrección de errores de grid
- [`MEJORAS_UI_PROFESIONALES.md`](MEJORAS_UI_PROFESIONALES.md) - Mejoras de interfaz
- [`RESUMEN_INTEGRACION_EMAILS.md`](RESUMEN_INTEGRACION_EMAILS.md) - Integración de emails

## 🐛 Solución de Problemas

### Error de Dependencias
```bash
pip install --upgrade streamlit
pip install -r requirements_professional.txt
```

### Error de Base de Datos
```bash
# Eliminar base de datos corrupta
rm boletines.db
# La aplicación recreará automáticamente
```

### Error de Permisos
```bash
chmod +x venv/bin/activate
chmod 755 imagenes/
```

## 🔄 Workflow de Desarrollo

### Branches
- `main` - Código estable en producción
- `develop` - Desarrollo activo
- `feature/*` - Nuevas características
- `hotfix/*` - Correcciones urgentes

### Commits Semánticos
```bash
feat: nueva funcionalidad
fix: corrección de bug
docs: documentación
test: pruebas
refactor: refactorización
chore: tareas de mantenimiento
```

## 📈 Versiones

### v2.1.0 (Actual)
- ✅ Sistema de autenticación completo
- ✅ Dashboard profesional con gráficos
- ✅ Corrección de errores de sintaxis
- ✅ Suite de testing completa

### Roadmap v2.2.0
- 🔄 Exportación a Excel
- 🔄 API REST
- 🔄 Notificaciones push
- 🔄 Multi-tenant

## 👥 Contribución

1. Fork el proyecto
2. Crear branch de feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto es de uso privado. Todos los derechos reservados.

## 📞 Contacto

**Desarrollador:** Martín Giacosa  
**Email:** [contacto@empresa.com]  
**Proyecto:** [https://github.com/GiacosaM/Automation_marcas](https://github.com/GiacosaM/Automation_marcas)

---

⭐ **¡Dale una estrella si te fue útil!**
