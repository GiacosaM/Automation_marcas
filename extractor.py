# extractor.py
from collections import defaultdict

def extraer_datos_agrupados(df):
    """Extrae y agrupa los datos del DataFrame por titular."""
    agrupados = defaultdict(list)

    for i in range(len(df)):
        if str(df.iloc[i, 1]).strip() == "Titular":
            nombre_titular = str(df.iloc[i, 2]).split(". Acta:")[0].strip()

            # Buscar hacia arriba la fila del boletín
            fila_boletin = -1
            for j in range(i, -1, -1):
                if isinstance(df.iloc[j, 2], str) and "BOLETIN NRO." in df.iloc[j, 2]:
                    fila_boletin = j
                    break

            if fila_boletin == -1:
                continue

            boletin_texto = str(df.iloc[fila_boletin, 2]).strip()
            partes = boletin_texto.split()
            numero_boletin = partes[2]
            fecha_boletin = partes[4]

            numero_orden = df.iloc[i - 4, 1] if i >= 4 else ""
            solicitante_raw = str(df.iloc[i - 3, 4]) if i >= 3 else ""
            solicitante = solicitante_raw.split("(País:")[0].strip() if "(País:" in solicitante_raw else solicitante_raw
            agente = df.iloc[i - 3, 5] if i >= 3 else ""
            numero_expediente = df.iloc[i - 1, 0] if i >= 1 else ""
            clase = df.iloc[i - 1, 1] if i >= 1 else ""
            marca_custodia = df.iloc[i - 1, 2] if i >= 1 else ""
            marca_publicada = df.iloc[i - 1, 4] if i >= 1 else ""
            clases_acta = df.iloc[i - 1, 5] if i >= 1 else ""

            agrupados[nombre_titular].append({
                "Número de Boletín": numero_boletin,
                "Fecha de Boletín": fecha_boletin,
                "Número de Orden": numero_orden,
                "Solicitante": solicitante,
                "Agente": agente,
                "Expediente": numero_expediente,
                "Clase": clase,
                "Marca en Custodia": marca_custodia,
                "Marca Publicada": marca_publicada,
                "Clases/Acta": clases_acta
            })

    return agrupados