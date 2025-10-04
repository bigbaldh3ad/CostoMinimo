import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import numpy as np


def resolver_problema(datos):
    """
    datos: lista de diccionarios, por ejemplo:
    [
        {'x': 1, 'y': 2},
        {'x': 2, 'y': 4},
        ...
    ]
    """
    df = pd.DataFrame(datos)
    
    tabla_html = df.to_html(index=False)
    
    plt.figure()
    plt.plot(df['x'], df['y'], marker='o')
    plt.title("Gráfica de ejemplo")
    plt.xlabel("X")
    plt.ylabel("Y")
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()
    
    return tabla_html, img_base64


def balance_problem(oferta, demanda):
    total_oferta = sum(oferta)
    total_demanda = sum(demanda)

    if total_oferta > total_demanda:
        demanda.append(total_oferta - total_demanda)
        return oferta, demanda, "Se añadió columna ficticia (demanda)."
    elif total_demanda > total_oferta:
        oferta.append(total_demanda - total_oferta)
        return oferta, demanda, "Se añadió fila ficticia (oferta)."
    else:
        return oferta, demanda, "Problema ya balanceado."


def metodo_costo_minimo(costos, oferta, demanda):
    costos = np.array(costos, dtype=float)
    oferta = list(oferta)
    demanda = list(demanda)
    filas, columnas = costos.shape

    asignacion = np.zeros_like(costos)
    oferta_restante = oferta.copy()
    demanda_restante = demanda.copy()

    while sum(oferta_restante) > 0 and sum(demanda_restante) > 0:
        # Encontrar el costo mínimo disponible
        idx = np.unravel_index(np.argmin(costos + (costos == -1) * 1e10), costos.shape)
        i, j = idx

        cantidad = min(oferta_restante[i], demanda_restante[j])
        asignacion[i][j] = cantidad

        oferta_restante[i] -= cantidad
        demanda_restante[j] -= cantidad

        if oferta_restante[i] == 0:
            costos[i, :] = -1  # Ignorar fila
        if demanda_restante[j] == 0:
            costos[:, j] = -1  # Ignorar columna

    costo_total = np.sum(asignacion * (costos.clip(min=0)))

    return asignacion, costo_total, oferta_restante, demanda_restante


def resolver_transporte(costos, oferta, demanda, nombres_origen=None, nombres_destino=None):
    oferta, demanda, balance_msg = balance_problem(oferta, demanda)

    asignacion, costo_total, oferta_restante, demanda_restante = metodo_costo_minimo(costos, oferta, demanda)

    tabla_datos = []
    for i in range(len(oferta)):
        fila = {"nombre": nombres_origen[i] if nombres_origen else f"Planta {i+1}",
                "valores": asignacion[i].tolist(),
                "oferta": oferta[i]}
        tabla_datos.append(fila)

    desglose_costos = []
    for i in range(len(oferta)):
        for j in range(len(demanda)):
            if asignacion[i][j] > 0:
                desglose_costos.append({
                    "origen": nombres_origen[i] if nombres_origen else f"Planta {i+1}",
                    "destino": nombres_destino[j] if nombres_destino else f"Ministíper {j+1}",
                    "cantidad": asignacion[i][j],
                    "costo_unitario": costos[i][j],
                    "contribucion": asignacion[i][j] * costos[i][j]
                })

    return {
        "resultado": "Costo mínimo resuelto",
        "tabla_datos": tabla_datos,
        "balance_msg": balance_msg,
        "desglose_costos": desglose_costos,
        "costo_total": costo_total,
        "total_oferta": sum(oferta),
        "total_demanda": sum(demanda),
        "oferta": oferta,
        "demanda": demanda
    }
