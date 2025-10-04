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
