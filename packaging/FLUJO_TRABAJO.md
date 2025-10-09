# 🔄 Flujo de Trabajo: Resumen Visual

## 📋 Cuando modificas tu código

```
┌─────────────────────────────────────────────────────────────────┐
│  1. DESARROLLO                                                   │
│  ─────────────                                                   │
│                                                                  │
│  📝 Editas tu código Python                                      │
│  📝 Modificas la UI de Streamlit                                 │
│  📝 Actualizas la base de datos                                  │
│  📝 Cambias configuraciones                                      │
│                                                                  │
│  Ubicación: /Automation/                                         │
└─────────────────────────────────────────────────────────────────┘
                            ⬇️
┌─────────────────────────────────────────────────────────────────┐
│  2. PROBAR LOCALMENTE                                            │
│  ─────────────────────                                           │
│                                                                  │
│  🧪 streamlit run app_refactored.py                             │
│  ✅ Verificar que todo funciona                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            ⬇️
┌─────────────────────────────────────────────────────────────────┐
│  3. COMPILAR                                                     │
│  ────────────                                                    │
│                                                                  │
│  macOS:                                                          │
│  $ cd packaging                                                  │
│  $ ./build_release.sh                                            │
│                                                                  │
│  Windows:                                                        │
│  > cd packaging                                                  │
│  > build_release.bat                                             │
│                                                                  │
│  ⏱️  Tiempo: 30-60 segundos                                      │
│  📦 Resultado: build_release/MiAppMarcas/                        │
└─────────────────────────────────────────────────────────────────┘
                            ⬇️
┌─────────────────────────────────────────────────────────────────┐
│  4. PROBAR EJECUTABLE                                            │
│  ─────────────────────                                           │
│                                                                  │
│  $ cd build_release/MiAppMarcas                                  │
│  $ rm -rf .venv launcher.log                                     │
│  $ ./MiAppMarcas  (macOS)                                        │
│  $ MiAppMarcas.exe  (Windows)                                    │
│                                                                  │
│  ✅ Verificar funcionamiento completo                            │
└─────────────────────────────────────────────────────────────────┘
                            ⬇️
┌─────────────────────────────────────────────────────────────────┐
│  5. EMPAQUETAR PARA DISTRIBUCIÓN                                 │
│  ────────────────────────────                                    │
│                                                                  │
│  macOS:                                                          │
│  $ tar -czf MiAppMarcas-v1.0.0-macos.tar.gz MiAppMarcas/        │
│                                                                  │
│  Windows:                                                        │
│  > 7z a MiAppMarcas-v1.0.0-windows.zip MiAppMarcas\             │
│                                                                  │
│  📦 Archivo comprimido: ~80-150 MB                               │
└─────────────────────────────────────────────────────────────────┘
                            ⬇️
┌─────────────────────────────────────────────────────────────────┐
│  6. ENTREGAR AL CLIENTE                                          │
│  ───────────────────────                                         │
│                                                                  │
│  📧 Enviar por email / Drive / WeTransfer                        │
│  📄 Incluir INSTRUCCIONES_CLIENTE.txt                            │
│  ✨ Cliente descomprime y ejecuta                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Comandos Rápidos (Copy-Paste)

### En macOS (tu máquina de desarrollo)

```bash
# 1. Compilar después de cambios
cd /Users/martingiacosa/Desktop/Proyectos/Python/Automation/packaging
./build_release.sh

# 2. Probar
cd build_release/MiAppMarcas
rm -rf .venv launcher.log
./MiAppMarcas

# 3. Comprimir para macOS
cd /Users/martingiacosa/Desktop/Proyectos/Python/Automation/packaging/build_release
tar --exclude='.venv' --exclude='*.log' --exclude='__pycache__' -czf MiAppMarcas-v1.0.0-macos.tar.gz MiAppMarcas/

# 4. Ver tamaño
ls -lh MiAppMarcas-v1.0.0-macos.tar.gz
```

### En Windows (para compilar versión Windows)

```batch
REM 1. Clonar/actualizar código
git pull origin main

REM 2. Compilar
cd packaging
build_release.bat

REM 3. Probar
cd build_release\MiAppMarcas
MiAppMarcas.exe

REM 4. Comprimir
cd ..
"C:\Program Files\7-Zip\7z.exe" a -tzip MiAppMarcas-v1.0.0-windows.zip MiAppMarcas\
```

---

## 📦 Qué contiene el paquete final

```
MiAppMarcas/
├── 🚀 MiAppMarcas.exe              (7-10 MB) - Launcher
├── 📄 LEEME.txt                     (Instrucciones)
├── 📄 VERSION.txt                   (Info de versión)
├── 📋 requirements.txt              (Lista de dependencias)
│
├── 🐍 python/                       (Python portable ~100MB)
│   ├── python.exe
│   ├── Scripts/
│   └── Lib/
│
└── 📦 app/                          (Tu aplicación ~50MB)
    ├── app_refactored.py           (Código principal)
    ├── boletines.db                (Base de datos)
    ├── config.json                 (Configuración)
    │
    ├── 📂 src/                      (Código modular)
    │   ├── config/
    │   ├── models/
    │   ├── services/
    │   ├── ui/
    │   └── utils/
    │
    ├── 📂 imagenes/                 (Assets visuales)
    │   ├── logo.png
    │   └── ...
    │
    ├── 📂 informes/                 (Se crea automáticamente)
    ├── 📂 logs/                     (Se crea automáticamente)
    │
    └── 📄 [módulos .py]             (database.py, email_sender.py, etc.)
```

### Tamaños aproximados:

| Componente | Tamaño |
|------------|--------|
| Launcher (MiAppMarcas.exe) | 7-10 MB |
| Python portable | ~100 MB |
| Tu aplicación (app/) | ~50 MB |
| **Total sin .venv** | **~150-200 MB** |
| .venv (se crea en primera ejecución) | ~800 MB - 1 GB |
| **Total con .venv** | **~1-1.2 GB** |
| **Comprimido (.zip/.tar.gz)** | **~80-150 MB** |

---

## 🔄 Actualización Completa vs Ligera

### Actualización COMPLETA (recomendada cada X meses)
```
MiAppMarcas-v1.1.0-windows.zip (150 MB)
└── Contiene TODO: launcher + python + app
```

**Cliente debe**:
1. Hacer backup de datos
2. Eliminar carpeta vieja
3. Descomprimir nueva versión
4. Restaurar datos

### Actualización LIGERA (para cambios menores)
```
MiAppMarcas-update-v1.0.1.zip (20 MB)
└── Solo carpeta app/
```

**Cliente debe**:
1. Cerrar aplicación
2. Reemplazar carpeta app/
3. Ejecutar normalmente (mantiene .venv)

---

## ⚠️ Problemas Comunes y Soluciones

| Problema | Causa | Solución |
|----------|-------|----------|
| "ModuleNotFoundError" | Falta módulo en build_release.sh | Agregarlo a la lista de módulos |
| "FileNotFoundError: boletines.db" | DB no copiada | Verificar ruta en paths.py |
| Imágenes no se ven | Carpeta imagenes/ no copiada | Verificar en build script |
| "Port 8501 already in use" | Otra instancia corriendo | Cerrar procesos Streamlit/MiAppMarcas |
| Antivirus bloquea .exe | Firma digital ausente | Agregar excepción o firmar ejecutable |
| .venv no se crea | Sin conexión a internet | Conectar y reintentar |
| Launcher muy lento | Muchas dependencias | Normal en primera ejecución |

---

## 📝 Checklist Pre-Release

Antes de enviar al cliente:

**Código**:
- [ ] Todos los cambios committeados
- [ ] Sin console.log() o prints de debug
- [ ] Credenciales hardcodeadas removidas
- [ ] Versión actualizada en VERSION.txt

**Build**:
- [ ] `./build_release.sh` ejecutado sin errores
- [ ] Todos los módulos Python copiados
- [ ] Base de datos incluida y funcional
- [ ] Imágenes y assets copiados
- [ ] requirements.txt actualizado

**Testing**:
- [ ] Ejecutable probado desde cero (sin .venv)
- [ ] Primera ejecución completa exitosa
- [ ] Todas las páginas/funciones probadas
- [ ] Login funciona correctamente
- [ ] Generación de informes OK
- [ ] Envío de emails OK
- [ ] Base de datos lee/escribe correctamente

**Documentación**:
- [ ] LEEME.txt actualizado
- [ ] VERSION.txt con número correcto
- [ ] INSTRUCCIONES_CLIENTE.txt incluido
- [ ] Cambios documentados

**Distribución**:
- [ ] Paquete comprimido creado
- [ ] Tamaño razonable (<200MB)
- [ ] Nombre de archivo versionado
- [ ] Hash MD5/SHA256 generado (opcional)

---

## 🎓 Tips Pro

1. **Versionado Semántico**:
   ```
   v1.0.0 → v1.0.1 (bug fix)
   v1.0.0 → v1.1.0 (nueva funcionalidad)
   v1.0.0 → v2.0.0 (cambio mayor/incompatible)
   ```

2. **Changelog**: Mantén un archivo con cambios entre versiones
   ```
   ## v1.0.1 (2025-10-15)
   - Fix: Error al generar informes con fechas
   - Add: Nuevo filtro en dashboard
   ```

3. **Tags Git**: Tagea cada release
   ```bash
   git tag -a v1.0.0 -m "Release 1.0.0"
   git push origin v1.0.0
   ```

4. **Backup automático**: Considera script para backup antes de actualizar

5. **Testing en VM**: Prueba en Windows VM antes de enviar al cliente

---

## 🚀 Automatización Avanzada (Futuro)

Puedes crear un script que haga todo:

```bash
#!/bin/bash
# release.sh - Script de release automatizado

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Uso: ./release.sh v1.0.1"
    exit 1
fi

echo "Creating release $VERSION"

# 1. Build
./build_release.sh

# 2. Test
cd build_release/MiAppMarcas
rm -rf .venv
./MiAppMarcas &
sleep 30
curl -f http://localhost:8501 || exit 1
pkill MiAppMarcas

# 3. Package
cd ..
tar -czf MiAppMarcas-$VERSION-macos.tar.gz MiAppMarcas/

# 4. Git tag
git tag -a $VERSION -m "Release $VERSION"
git push origin $VERSION

echo "✅ Release $VERSION created!"
```

Uso:
```bash
./release.sh v1.0.1
```
