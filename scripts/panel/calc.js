/*
 * Motor de cálculo del panel. Reproduce en JavaScript las mismas operaciones
 * que el SQL del proyecto, para que el panel dé las mismas cifras que el deck:
 *   - clasificar()   = sql/04_clasificar.sql (reglas LIKE de sql/03)
 *   - resumen()      = vista v_resumen_precios (cuartiles con NTILE(4))
 *   - solape()       = vista v_solape_pares (coeficiente de solapamiento por tramos)
 *   - hueco()        = output/tablas/hueco_escalera.csv (precios redondeados al euro)
 * scripts/crear_panel.py comprueba con Node que coincide con la base de datos.
 */
(function (root) {
  'use strict';

  // SQLite: lower() y LIKE solo distinguen mayúsculas en letras ASCII.
  function minusculasAscii(s) {
    return String(s == null ? '' : s).replace(/[A-Z]/g, function (c) { return c.toLowerCase(); });
  }

  // Patrón LIKE -> expresión regular: % = cualquier texto, _ = un carácter.
  function likeARegex(patron) {
    var out = '';
    var p = minusculasAscii(patron);
    for (var i = 0; i < p.length; i++) {
      var ch = p[i];
      if (ch === '%') out += '[\\s\\S]*';
      else if (ch === '_') out += '[\\s\\S]';
      else out += ch.replace(/[.*+?^${}()|[\]\\\/-]/g, '\\$&');
    }
    return new RegExp('^' + out + '$');
  }

  function prepararReglas(reglas) {
    return reglas
      .map(function (r, i) {
        return { categoria: r.categoria, prioridad: r.prioridad, motivo: r.motivo, campo: r.campo,
                 regex: likeARegex(r.patron), orden: i };
      })
      .sort(function (a, b) { return a.prioridad - b.prioridad || a.orden - b.orden; });
  }

  // Devuelve el motivo de exclusión, o '7_basica' si ninguna regla encaja.
  function clasificar(fila, reglasPreparadas) {
    var nombre = minusculasAscii(fila.nombre);
    var clasif = minusculasAscii(fila.clasificacion_web);
    for (var i = 0; i < reglasPreparadas.length; i++) {
      var r = reglasPreparadas[i];
      if (r.categoria !== fila.categoria) continue;
      var texto = r.campo === 'nombre' ? nombre : clasif;
      if (r.regex.test(texto)) return r.motivo;
    }
    return '7_basica';
  }

  // Cuartiles como NTILE(4) de SQLite: los primeros (n mod 4) grupos tienen un
  // elemento más; P25, mediana y P75 son el máximo de los grupos 1, 2 y 3.
  function resumen(precios) {
    var p = precios.slice().sort(function (a, b) { return a - b; });
    var n = p.length;
    if (n === 0) return null;
    var base = Math.floor(n / 4), resto = n % 4, fin = [], acum = 0;
    for (var k = 0; k < 4; k++) { acum += base + (k < resto ? 1 : 0); fin.push(acum); }
    var maxGrupo = function (k) { return fin[k] > 0 && (k === 0 || fin[k] > fin[k - 1]) ? p[fin[k] - 1] : null; };
    var suma = p.reduce(function (s, x) { return s + x; }, 0);
    return {
      n: n, minimo: p[0], p25: maxGrupo(0), mediana: maxGrupo(1), p75: maxGrupo(2), maximo: p[n - 1],
      media: Math.round((suma / n) * 100) / 100,
      muestraPequena: n < 15
    };
  }

  // Coeficiente de solapamiento: se reparte cada marca por tramos de 'ancho' euros
  // y se suma, tramo a tramo, la menor de las dos proporciones.
  function reparto(precios, ancho) {
    var cuenta = {};
    precios.forEach(function (x) {
      var t = Math.trunc(x / ancho);       // CAST(precio / ancho AS INTEGER)
      cuenta[t] = (cuenta[t] || 0) + 1;
    });
    var n = precios.length, out = {};
    Object.keys(cuenta).forEach(function (t) { out[t] = cuenta[t] / n; });
    return out;
  }

  function solape(preciosA, preciosB, ancho) {
    if (!preciosA.length || !preciosB.length) return null;
    var a = reparto(preciosA, ancho), b = reparto(preciosB, ancho), s = 0;
    Object.keys(a).forEach(function (t) { if (b[t] !== undefined) s += Math.min(a[t], b[t]); });
    return Math.round(100 * s);
  }

  // Redondeo al euro "de toda la vida" (0,5 sube): 39,95 y 39,99 -> 40.
  function redondearEuro(x) { return Math.floor(x + 0.5); }

  // % de los modelos de cada marca con precio por encima de 'desde' y por
  // debajo de 'hasta', comparando precios redondeados al euro.
  function enHueco(precios, desde, hasta) {
    var lo = redondearEuro(desde), hi = redondearEuro(hasta), k = 0;
    precios.forEach(function (x) { var r = redondearEuro(x); if (r > lo && r < hi) k++; });
    return { n: precios.length, enHueco: k, pct: precios.length ? Math.round(100 * k / precios.length) : null };
  }

  var Calc = { minusculasAscii: minusculasAscii, likeARegex: likeARegex, prepararReglas: prepararReglas,
               clasificar: clasificar, resumen: resumen, solape: solape, redondearEuro: redondearEuro,
               enHueco: enHueco };
  root.Calc = Calc;
  if (typeof module !== 'undefined' && module.exports) module.exports = Calc;
})(typeof window !== 'undefined' ? window : this);
