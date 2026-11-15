# Entrenamiento del detector v4

## Qué cambia

El detector v3 marca daño donde no hay. Medido sobre fotos sanas:

| Fotos sanas | Marcadas con daño |
|---|---|
| 200 fotos reales de interiores (Open Images) | 54,5 % |
| 2.000 capturas del simulador | 70 % |

La causa es que casi no vio ambientes interiores sanos. La v4 suma fotos reales de interiores como `undamaged`. No se usan datos sintéticos. El modelo, el label smoothing y la calibración son los mismos de la v3.

## Qué hay que tener

1. Los datos de la v3 en `notebooks/data/` y `notebooks/data_clasificacion/`. Si no están, correr antes `parte3/descargar_datos_deteccion3.ipynb`.
2. El archivo `paquete_interiores.zip`, que está en `notebooks/data_interiores/`.

## Pasos

1. Descomprimir `paquete_interiores.zip`. Trae dos carpetas y una lista:
   - `interiores/`: fotos completas de ambientes.
   - `interiores_cerca/`: recortes de cerca de esas mismas fotos.
   - `fotos_interiores.csv`: autor y licencia de cada foto.
2. Copiar las dos carpetas dentro de `notebooks/data/undamaged_superficies/`. Tiene que quedar así:

   ```
   notebooks/data/undamaged_superficies/interiores/
   notebooks/data/undamaged_superficies/interiores_cerca/
   notebooks/data/undamaged_superficies/ozgenel_negative/
   notebooks/data/undamaged_superficies/sdnet_uw/
   ```

3. Opcional, para que queden guardadas junto al resto: subir las dos carpetas al bucket, en `processed/damage_detection/undamaged_superficies/`.
4. Abrir `parte4/cnn_damage_detection_training4.ipynb` y correr todas las celdas, en orden.

## Qué revisar al terminar

- **Celda 4:** en la tabla tienen que aparecer filas de `undamaged` con origen `superficies` más grandes que en la v3.
- **Celda 5:** la columna `deteccion_disponibles` tiene que ser mayor o igual que `damaged_deteccion`. Si no alcanza, subir `PROP_CLASIF` en la celda 1 (por ejemplo a 0.55) y volver a correr.
- **Celda 15:** en "% de aciertos por grupo" aparecen `interiores` e `interiores_cerca`. La meta es 90 % o más en esos dos grupos, sin que bajen los grupos de daño (hoy rondan el 91 %).

## Qué devolver

Estos dos archivos, que quedan en `models/`:

- `modelo_detection4.keras`
- `modelo_detection4_calibracion.json`

Y una captura o copia del resultado de la celda 15.

No se pisa ningún modelo anterior.

## Licencia de las fotos nuevas

Las fotos son de Open Images, con licencia Creative Commons Attribution (CC BY). El autor, la página original y la licencia de cada una están en `fotos_interiores.csv`. Ese archivo se tiene que conservar junto con las fotos.
