# Logos de la portada

`scripts/crear_deck.py` pone los logos sobre la escalera de la portada **solo si están los cinco**.
Si falta alguno, usa el nombre de cada marca en texto (para que la portada sea coherente).

| Marca | Fichero esperado | Estado |
|---|---|---|
| Primark | `primark.png` | ✅ (enviado por Javi) |
| Lefties | `lefties.png` | falta |
| H&M | `hm.png` | ✅ (Simple Icons, CC0) |
| Zara | `zara.png` | ✅ (Simple Icons, CC0) |
| Massimo Dutti | `massimo_dutti.png` | falta |

- Vale cualquier PNG (mejor con fondo transparente; si tiene fondo blanco también funciona).
- El script los convierte a un solo color gris oscuro, para que ningún color de marca
  choque con el azul que identifica a Inditex en todo el deck.
- Los logos son marcas registradas de sus dueños; aquí se usan solo para identificar
  a las cadenas analizadas.
