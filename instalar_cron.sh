#!/bin/bash
# instalar_cron.sh
# Script para instalar automáticamente la tarea cron

# Obtener la ruta absoluta del directorio actual
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Crear una entrada temporal para cron
TEMP_CRON=$(mktemp)

# Extraer cron actual y añadir nueva entrada
crontab -l > "$TEMP_CRON" 2>/dev/null || echo "" > "$TEMP_CRON"

# Comprobar si la entrada ya existe para evitar duplicados
if ! grep -q "ejecucion_programada.py" "$TEMP_CRON"; then
    # Añadir nueva entrada de cron - ejecutar el primer día de cada mes a las 8:00 AM
    echo "0 8 1 * * cd $DIR && /usr/bin/python3 $DIR/ejecucion_programada.py >> $DIR/verificacion_log.txt 2>&1" >> "$TEMP_CRON"
    
    # Instalar nuevo crontab
    crontab "$TEMP_CRON"
    echo "Tarea cron instalada exitosamente."
    echo "Se ejecutará automáticamente el primer día de cada mes a las 8:00 AM."
else
    echo "La tarea cron ya está instalada."
fi

# Limpiar archivo temporal
rm "$TEMP_CRON"

# Mostrar crontab actual para verificar
echo ""
echo "Crontab actual:"
crontab -l
