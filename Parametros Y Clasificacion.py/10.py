#!/usr/bin/env python3
# detectar_tranitos_curva.py
# Descarga LC (Kepler), procesa, ejecuta TLS, guarda resultados y plot.

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import light_curve as lc

# Intenta importar las librerías necesarias y dar mensajes útiles si faltan
try:
    from light_curve import search_lightcurvefile
except Exception as e:
    raise ImportError("Error al importar lightkurve. Instala con 'pip install lightkurve'") from e
   
try:
    from transitleastsquares import transitleastsquares
except Exception as e:
    raise ImportError("Error al importar transitleastsquares. Instala con 'pip install transitleastsquares'") from e
# ---------- CONFIG ----------
# KepID seleccionado (usé el primer candidato de tu tabla)
kepid = 10797460

# límites de búsqueda de periodo para TLS (ajusta según lo que busques)
min_period = 0.3   # días
max_period = 100.0 # días

# carpeta de salida
out_dir = "output_transitos"
os.makedirs(out_dir, exist_ok=True)

# ---------- 1) Descargar curva de luz (Kepler) ----------
print(f"Buscando lightcurve para KIC {kepid} (Kepler)...")
search = search_lightcurvefile(f'KIC {kepid}', mission='Kepler')
if len(search) == 0:
    raise RuntimeError(f"No se encontró lightcurve para KIC {kepid} con lightkurve (Kepler).")

# descargar todos los archivos disponibles y unir
print(f"Se encontraron {len(search)} archivos. Descargando y ensamblando...")
lc_collection = search.download_all()
# Preferimos PDCSAP_FLUX (corrige sistema instrumental). Si no existe, probar SAP_FLUX.
lcs = []
for lcfile in lc_collection:
    if hasattr(lcfile, "PDCSAP_FLUX") and lcfile.PDCSAP_FLUX is not None:
        lcs.append(lcfile.PDCSAP_FLUX)
    elif hasattr(lcfile, "SAP_FLUX") and lcfile.SAP_FLUX is not None:
        lcs.append(lcfile.SAP_FLUX)

if len(lcs) == 0:
    raise RuntimeError("No se encontraron columnas PDCSAP_FLUX ni SAP_FLUX en los archivos descargados.")

# stitch() une los segmentos (quarters)
lc = lcs[0]
if len(lcs) > 1:
    lc = lc.stitch()

# limpiar NaNs y outliers básicos
lc = lc.remove_nans()
# Normalizar y quitar tendencias largas (flatten) para preservar tránsitos (ajusta window_length si es necesario)
lc_flat = lc.flatten(window_length=401)  # si es muy ruidoso, reduce; si muy largo, aumenta

# Obtener arrays para TLS
# Nota: lightkurve time para Kepler está en BKJD (barycentric - 2454833). TLS funciona con cualquier escala consistente.
t_bkjd = lc_flat.time.value           # BKJD (días)
# Opcional: convertir a BJD añadiendo offset: 2454833.0  (si necesitas BJD absoluto)
# t = t_bkjd + 2454833.0
t = t_bkjd.copy()
y = lc_flat.flux.value / np.nanmedian(lc_flat.flux.value)  # normalizar por mediana
dy = lc_flat.flux_err.value if lc_flat.flux_err is not None else None

print("Puntos válidos:", len(t))
print(f"Rango tiempo: {t.min():.4f} - {t.max():.4f} (BKJD)")
print("Preparando TLS...")

# ---------- 2) Ejecutar TLS ----------
model = transitleastsquares(t, y)

print(f"Corriendo TLS (min_period={min_period} d, max_period={max_period} d). Esto puede tardar un poco...")
# Si dy es None, TLS lo acepta, pero mejor si existe.
results = model.power(min_period=min_period, max_period=max_period)

# Extraer parámetros clave
periodo = float(results.period)
epoch_t0 = float(results.T0)          # en la misma escala temporal que t (BKJD)
duracion_dias = float(results.duration)
duracion_horas = duracion_dias * 24.0
profundidad = float(results.depth)    # fracción de flujo (ej. 0.001 = 0.1%)
sde = float(results.SDE) if hasattr(results, "SDE") else None
snr_tls = float(results.snr) if hasattr(results, "snr") else None

print("\n--- RESULTADOS TLS ---")
print(f"Periodo (d): {periodo:.6f}")
print(f"Epoch T0 (BKJD): {epoch_t0:.6f}")
print(f"Duración (h): {duracion_horas:.3f}")
print(f"Profundidad (fracción): {profundidad:.6e}")
print(f"SDE: {sde}, SNR (si disponible): {snr_tls}")

# Guardar parámetros en JSON/CSV simples
import json
params = {
    "kepid": int(kepid),
    "periodo_dias": periodo,
    "epoch_t0_bkjd": epoch_t0,
    "duracion_dias": duracion_dias,
    "duracion_horas": duracion_horas,
    "profundidad": profundidad,
    "sde": sde,
    "snr_tls": snr_tls,
    "puntos_validos": int(len(t))
}
with open(os.path.join(out_dir, "tls_params.json"), "w") as f:
    json.dump(params, f, indent=2)
print(f"Parámetros guardados en {os.path.join(out_dir, 'tls_params.json')}")

# ---------- 3) Generar y guardar plot plegado (phase-folded) ----------
# Crear fase centrada en T0: fase en [-0.5, +0.5]
phi = ((t - epoch_t0 + 0.5*periodo) % periodo) / periodo - 0.5
order = np.argsort(phi)
phi_sorted = phi[order]
y_sorted = y[order]

# Para mostrar modelo TLS: construir modelo con mismo periodo/T0/duration
model_fold = results.model_lightcurve(t)  # modelo en tiempo original
mf_sorted = model_fold[order]

plt.figure(figsize=(8,5))
plt.scatter(phi_sorted, y_sorted, s=6, alpha=0.6, label='Datos (plegados)')
plt.plot(phi_sorted, mf_sorted, color='red', linewidth=1.5, label='Modelo TLS')
plt.xlim(-0.2, 0.2)  # zoom alrededor del tránsito (ajusta si la duración es más grande)
plt.xlabel("Fase (periodo normalizado)")
plt.ylabel("Flujo normalizado")
plt.title(f"KIC {kepid} - Periodo = {periodo:.6f} d - Profundidad = {profundidad:.3e}")
plt.legend()
out_png = os.path.join(out_dir, f"kep{kepid}_phasefold.png")
plt.savefig(out_png, dpi=200, bbox_inches="tight")
plt.close()
plt.show()
print(f"Plot plegado guardado en: {out_png}")

# También guardar la curva plegada (CSV) para inspección
df_fold = pd.DataFrame({"phase": phi_sorted, "flux": y_sorted, "model": mf_sorted})
csv_fold = os.path.join(out_dir, f"kep{kepid}_phasefold.csv")
df_fold.to_csv(csv_fold, index=False)
print(f"CSV de fase guardado en: {csv_fold}")

print("\nProceso completo. Revisa la carpeta:", out_dir)
#PROBABILIDADES
import numpy as np
import pandas as pd
import os


from sklearn.model_selection import train_test_split
if 'X_test' not in globals() or 'Y_test' not in globals():
    X_train_tmp, X_test_tmp, Y_train_tmp, Y_test_tmp = train_test_split(X, Y, test_size=0.2, random_state=42)
   
    if 'X_train' in globals() and 'Y_train' in globals():
        X_train_for_calib = X_train
        Y_train_for_calib = Y_train
        X_test_use = X_test
        Y_test_use = Y_test
    else:
        X_train_for_calib = X_train_tmp
        Y_train_for_calib = Y_train_tmp
        X_test_use = X_test_tmp
        Y_test_use = Y_test_tmp
else:
    X_test_use = X_test
    Y_test_use = Y_test
    X_train_for_calib = X_train
    Y_train_for_calib = Y_train

# Obtener un clasificador con predict_proba calibrado
clf_proba = None
if hasattr(clf, "predict_proba"):
    clf_proba = clf
else:
    # Si el clasificador no tiene predict_proba, calibramos con CalibratedClassifierCV
    from sklearn.calibration import CalibratedClassifierCV
    print("Calibrando clasificador para obtener probabilidades (esto re-entrena el clasificador internamente)...")
    calibrador = CalibratedClassifierCV(clf, cv=5)  # usa cv=5 por defecto
    calibrador.fit(X_train_for_calib, Y_train_for_calib)
    clf_proba = calibrador

# --- Probabilidades sobre el conjunto de test 
probs_test = clf_proba.predict_proba(X_test_use)[:, 1]  # prob de clase 1 = Exoplaneta
preds_test = clf_proba.predict(X_test_use)

# DataFrame con resultados de test
df_test_probs = pd.DataFrame(X_test_use, columns=['periodo','profundidad','duracion'])
df_test_probs['y_true'] = Y_test_use
df_test_probs['p_exoplaneta'] = probs_test
df_test_probs['pred'] = preds_test
df_test_probs = df_test_probs.sort_values('p_exoplaneta', ascending=False).reset_index(drop=True)

# Guardar y mostrar top
csv_test_out = "test_probabilities_sorted.csv"
df_test_probs.to_csv(csv_test_out, index=False)
print(f"\nResultados (test) guardados en: {csv_test_out}")
print("\nTop 10 candidatos en test por probabilidad de ser exoplaneta:")
print(df_test_probs.head(10).to_string(index=False))

# --- Métrica de calibración simple (Brier score) ---
try:
    from sklearn.metrics import brier_score_loss
    brier = brier_score_loss(Y_test_use, probs_test)
    print(f"\nBrier score (test): {brier:.4f}  (más bajo = mejores probabilidades calibradas)")
except Exception as e:
    print("No se pudo calcular Brier score:", e)

# --- Predicciones en lote (si existe 'nuevos_candidatos.csv') ---
csv_entrada = "nuevos_candidatos.cs"
csv_salida_prob = "predicciones_prob_sorted.csv"

if os.path.exists(csv_entrada):
    print(f"\nArchivo '{csv_entrada}' encontrado. Calculando probabilidades para ese lote...")
    df_nuevos = pd.read_csv(csv_entrada)
    # Aceptar dos formatos: columnas nombradas o primeras 3 columnas
    if not set(['periodo','profundidad','duracion']).issubset(df_nuevos.columns):
        df_nuevos = df_nuevos.iloc[:, :3]
        df_nuevos.columns = ['periodo','profundidad','duracion']
    X_nuevos = df_nuevos[['periodo','profundidad','duracion']].values.astype(float)
    probs_nuevos = clf_proba.predict_proba(X_nuevos)[:, 1]
    preds_nuevos = clf_proba.predict(X_nuevos)
    df_nuevos['p_exoplaneta'] = probs_nuevos
    df_nuevos['pred'] = preds_nuevos
    df_nuevos['label'] = df_nuevos['pred'].apply(lambda v: "Exoplaneta" if int(v)==1 else "Falso positivo")
    df_nuevos = df_nuevos.sort_values('p_exoplaneta', ascending=False).reset_index(drop=True)
    df_nuevos.to_csv(csv_salida_prob, index=False)
    print(f"Predicciones con probabilidades guardadas en: {csv_salida_prob}")
    print("\nTop 10 candidatos en lote por probabilidad de ser exoplaneta:")
    print(df_nuevos.head(10).to_string(index=False))
else:
    print(f"\nNo se encontró '{csv_entrada}'. Si quieres predecir en lote crea ese archivo con columnas: periodo,profundidad,duracion")

# --- Función útil: obtener probabilidad para un solo candidato 
def probabilidad_exoplaneta(periodo, profundidad, duracion):
    x = np.array([[float(periodo), float(profundidad), float(duracion)]])
    p = clf_proba.predict_proba(x)[0,1]
    return float(p)

    #PLOT
    # ----------------------------
# Scatter: Periodo_orbital vs Profundidad_transito (unidades originales), resaltar test set
# ----------------------------
import matplotlib.pyplot as plt
import numpy as np
import os

out_dir = "plots_rf"
os.makedirs(out_dir, exist_ok=True)

# Usar el DataFrame 
try:
    df_all = data.copy()
except NameError:
    df_all = pd.DataFrame(X, columns=['periodo_orbital', 'profundidad_transito', 'duracion_transito'])
    df_all['etiqueta'] = Y

# Intentar obtener X_test (o X_test_use) para resaltar puntos de test
test_mask = np.zeros(len(df_all), dtype=bool)
try:
    Xt = X_test_use if 'X_test_use' in globals() else X_test
    rows_all = df_all[['periodo_orbital', 'profundidad_transito', 'duracion_transito']].values
    # Para cada fila de df_all, marcar True si aparece en Xt (comparación con tolerancia)
    for idx, row in enumerate(rows_all):
        if any(np.allclose(row, r, rtol=1e-6, atol=1e-8) for r in Xt):
            test_mask[idx] = True
except Exception:
    # Si algo falla (p. ej. no existe X_test), simplemente no resaltamos
    test_mask = np.zeros(len(df_all), dtype=bool)

# Crear figura
fig, ax = plt.subplots(figsize=(8,6))

mask0 = df_all['etiqueta'] == 0
mask1 = df_all['etiqueta'] == 1

ax.scatter(df_all.loc[mask0, 'periodo_orbital'], df_all.loc[mask0, 'profundidad_transito'],
           label='Falso positivo (0)', marker='o', s=70, alpha=0.9, edgecolor='k')
ax.scatter(df_all.loc[mask1, 'periodo_orbital'], df_all.loc[mask1, 'profundidad_transito'],
           label='Exoplaneta (1)', marker='s', s=90, alpha=0.9, edgecolor='k')

# Resaltar puntos de test (amarillo, borde grueso)
if test_mask.any():
    ax.scatter(df_all.loc[test_mask, 'periodo_orbital'], df_all.loc[test_mask, 'profundidad_transito'],
               facecolors='none', edgecolors='yellow', s=300, linewidths=2, label='Test set')

ax.set_xlabel('Periodo orbital (días)')
ax.set_ylabel('Profundidad del tránsito (unidades originales)')
ax.set_title('Periodo orbital vs Profundidad — Datos (test resaltado)')
ax.legend(loc='best')
ax.grid(alpha=0.3)
fig.tight_layout()

fname = os.path.join(out_dir, "scatter_periodo_vs_profundidad.png")
fig.savefig(fname, dpi=150)
print("Guardado scatter en:", fname)

# Mostrar la figura en pantalla (si tu entorno lo permite)
plt.show()
plt.close(fig)