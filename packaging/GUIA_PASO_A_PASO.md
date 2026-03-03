# 📋 GUÍA PASO A PASO - MiAppMarcas

## 🎯 Proceso Completo de Compilación y Distribución

---

## 📝 PASO 1: Desarrollo y Pruebas Locales

### 1.1 Modificar tu código
```bash
cd /Users/martingiacosa/Desktop/Proyectos/Python/Automation
# Edita tus archivos Python, modifica la UI, etc.
```

### 1.2 Probar localmente
```bash
# Activar entorno virtual (si lo usas)
source venv/bin/activate

 C:\Users\Iara\Desktop\Automation\Automation_marcas\packaging\build_release\MiAppMarcas\app> 
 .\venv\Scripts\Activate.ps1


# Ejecutar la aplicación
streamlit run app_refactored.py
```

### 1.3 Verificar que todo funciona
- ✅ La aplicación abre correctamente
- ✅ Todas las páginas funcionan
- ✅ No hay errores en consola
- ✅ La base de datos funciona correctamente

---

## 🔨 PASO 2: Compilar la Aplicación

### 2.1 Usar el script automatizado (RECOMENDADO)

```bash
cd /Users/martingiacosa/Desktop/Proyectos/Python/Automation/packaging
./quick_build.sh
```

**El script hace todo automáticamente:**
- ✅ Limpia builds anteriores
- ✅ Compila el launcher
- ✅ Prepara Python embebido
- ✅ Copia todos los archivos necesarios
- ✅ Verifica que todo esté correcto

**Tiempo estimado:** 30-60 segundos

### 2.2 Revisar el resultado

El script te mostrará:
```
✓ BUILD COMPLETADO EXITOSAMENTE
📦 Ubicación: build_release/MiAppMarcas
📊 Tamaño: ~150MB
```

---

## 🧪 PASO 3: Probar el Ejecutable

### 3.1 Navegar a la carpeta

```bash
cd /Users/martingiacosa/Desktop/Proyectos/Python/Automation/packaging/build_release/MiAppMarcas
```

### 3.2 Limpiar instalación anterior (si existe)

**⚠️ IMPORTANTE:** Si vas a probar desde cero, debes eliminar `.venv` **completamente**:

```bash
# Verificar que se eliminó todo
rm -rf .venv launcher.log
ls -la | grep venv  # No debería mostrar nada
```

### 3.3 Ejecutar la aplicación

**Opción A - Usar ruta absoluta (más confiable):**
```bash
/Users/martingiacosa/Desktop/Proyectos/Python/Automation/packaging/build_release/MiAppMarcas/MiAppMarcas
```

**Opción B - Desde el directorio:**
```bash
cd /Users/martingiacosa/Desktop/Proyectos/Python/Automation/packaging/build_release/MiAppMarcas
./MiAppMarcas
```

**⚠️ Si al ejecutar dice "zsh: no such file or directory":**
- Estás en el directorio equivocado → Usa la ruta absoluta (Opción A)
- O navega correctamente al directorio (Opción B)

### 3.4 Verificar funcionamiento

La primera vez verás:
```
============================================================
         PRIMERA EJECUCIÓN - CONFIGURACIÓN INICIAL          
============================================================

  MiAppMarcas necesita configurar el entorno
  Esto tomará 1-2 minutos (solo esta vez)

[Instalando dependencias...]
✅ Configuración completada exitosamente!
🌐 Abriendo navegador en http://localhost:8501...
```

**Checklist de pruebas:**
- [ ] El servidor inicia correctamente
- [ ] El navegador se abre automáticamente
- [ ] Puedes hacer login
- [ ] Todas las páginas cargan sin errores
- [ ] Puedes generar informes
- [ ] Puedes enviar emails (si aplica)

---

## 📦 PASO 4: Empaquetar para Distribución

### 4.1 Comprimir la aplicación

```bash
cd /Users/martingiacosa/Desktop/Proyectos/Python/Automation/packaging/build_release
tar --exclude='.venv' --exclude='*.log' --exclude='__pycache__' -czf MiAppMarcas-v1.0.0-macos.tar.gz MiAppMarcas/
```

### 4.2 Verificar el tamaño

```bash
ls -lh MiAppMarcas-v1.0.0-macos.tar.gz
```

**Tamaño esperado:** 80-150 MB

---

## 📧 PASO 5: Entregar al Cliente

### 5.1 Subir el archivo

Opciones:
- **Google Drive**: Compartir el archivo .tar.gz
- **WeTransfer**: Para archivos grandes
- **Dropbox**: Compartir enlace
- **Email**: Si es menor a 25MB (poco probable)

### 5.2 Enviar instrucciones al cliente

```
Hola [Nombre del Cliente],

Te envío la aplicación MiAppMarcas v1.0.0 para macOS.

INSTRUCCIONES DE INSTALACIÓN:

1. Descarga el archivo MiAppMarcas-v1.0.0-macos.tar.gz
2. Descomprime el archivo (doble clic)
3. Abre la carpeta MiAppMarcas
4. Haz doble clic en "MiAppMarcas"
5. La primera vez tomará 1-2 minutos configurando
6. ¡Listo! La aplicación se abrirá automáticamente

NOTAS IMPORTANTES:
- La primera ejecución toma más tiempo (instalando dependencias)
- Las siguientes ejecuciones serán mucho más rápidas (3-5 segundos)
- NO muevas la carpeta MiAppMarcas después de la primera ejecución
- Todos los datos se guardan dentro de la carpeta

Cualquier duda, no dudes en contactarme.

Saludos!
```

---

## 🔄 PASO 6: Actualizar la Aplicación (Futuro)

### 6.1 Para cambios menores (recomendado)

```bash
# 1. Hacer cambios en el código
# 2. Compilar solo la carpeta app/
cd /Users/martingiacosa/Desktop/Proyectos/Python/Automation/packaging
./quick_build.sh

# 3. Comprimir solo la carpeta app/
cd build_release/MiAppMarcas
tar -czf MiAppMarcas-update-v1.0.1.tar.gz app/

# 4. Enviar al cliente con instrucciones:
#    - Cerrar la aplicación
#    - Reemplazar la carpeta app/ antigua con la nueva
#    - Ejecutar normalmente
```

**Ventaja:** Archivo mucho más pequeño (~20-30MB)

### 6.2 Para cambios mayores

Repetir todo el PASO 2-5 completo

---

## ⚠️ SOLUCIÓN DE PROBLEMAS COMUNES

### Problema 1: "requirements.txt no encontrado"
**Solución:**
```bash
cp /Users/martingiacosa/Desktop/Proyectos/Python/Automation/requirements.txt \
   /Users/martingiacosa/Desktop/Proyectos/Python/Automation/packaging/build_release/MiAppMarcas/
```

### Problema 2: "ModuleNotFoundError: No module named 'src'"
**Solución:**
```bash
cp -R /Users/martingiacosa/Desktop/Proyectos/Python/Automation/src \
      /Users/martingiacosa/Desktop/Proyectos/Python/Automation/packaging/build_release/MiAppMarcas/app/
```

### Problema 3: "Port 8501 already in use"
**Solución:**
```bash
# Matar el proceso que está usando el puerto
pkill -f streamlit
# O reiniciar la aplicación
```

### Problema 4: El script quick_build.sh falla
**Solución:**
```bash
# Ver el error completo
cd /Users/martingiacosa/Desktop/Proyectos/Python/Automation/packaging
./quick_build.sh 2>&1 | tee build_error.log
# Revisar build_error.log para ver el problema
```

### Problema 5: La aplicación no encuentra la base de datos
**Solución:**
Verificar que `boletines.db` esté en:
- `/Users/martingiacosa/Desktop/MiAppMarcas/boletines.db` (producción)
- O en la carpeta `app/` de la compilación

### Problema 6: "No such file or directory: .venv/bin/python"
**Causa:** El `.venv` se eliminó parcialmente o está corrupto

**Solución:**
```bash
# 1. Ir al directorio de la app
cd /Users/martingiacosa/Desktop/Proyectos/Python/Automation/packaging/build_release/MiAppMarcas

# 2. Eliminar COMPLETAMENTE .venv
rm -rf .venv launcher.log

# 3. Verificar que se eliminó (no debe mostrar nada)
ls -la | grep venv

# 4. Ejecutar con ruta absoluta
/Users/martingiacosa/Desktop/Proyectos/Python/Automation/packaging/build_release/MiAppMarcas/MiAppMarcas
```

**Explicación:** Si `rm -rf` se interrumpe, puede quedar un `.venv/` incompleto que confunde al launcher

---

## 📊 CHECKLIST PRE-DISTRIBUCIÓN

Antes de enviar al cliente, verificar:

**Código:**
- [ ] Sin prints de debug
- [ ] Sin credenciales hardcodeadas
- [ ] Versión actualizada en VERSION.txt

**Compilación:**
- [ ] `./quick_build.sh` ejecutado sin errores
- [ ] Todos los archivos copiados (verificar output)
- [ ] Tamaño razonable (~150-200MB sin .venv)

**Pruebas:**
- [ ] Ejecutable probado desde cero (sin .venv)
- [ ] Primera ejecución completa exitosa
- [ ] Login funciona
- [ ] Todas las páginas cargan
- [ ] Generación de informes OK
- [ ] Base de datos funciona correctamente

**Distribución:**
- [ ] Archivo comprimido creado
- [ ] Nombre versionado (v1.0.0, v1.0.1, etc.)
- [ ] Instrucciones de instalación preparadas

---

## 🎓 COMANDOS ÚTILES RÁPIDOS

### Compilar rápido
```bash
cd ~/Desktop/Proyectos/Python/Automation/packaging && ./quick_build.sh
```

### Probar rápido
```bash
cd ~/Desktop/Proyectos/Python/Automation/packaging/build_release/MiAppMarcas && \
rm -rf .venv launcher.log && ./MiAppMarcas
```

### Comprimir rápido
```bash
cd ~/Desktop/Proyectos/Python/Automation/packaging/build_release && \
tar --exclude='.venv' --exclude='*.log' -czf MiAppMarcas-v$(date +%Y%m%d).tar.gz MiAppMarcas/
```

### Ver logs si hay problemas
```bash
tail -f ~/Desktop/Proyectos/Python/Automation/packaging/build_release/MiAppMarcas/launcher.log
```

---

## 📞 SOPORTE

Si algo no funciona:
1. Revisar este documento
2. Verificar los logs en `launcher.log`
3. Ejecutar `./quick_build.sh` nuevamente
4. Si persiste, contactar soporte técnico

---

**¡Listo!** 🚀 Ahora tienes un proceso completo y automatizado para compilar y distribuir MiAppMarcas.
