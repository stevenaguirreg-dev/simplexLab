/* Utilidades de formato: escape de HTML, números exactos (fracción + decimal) y subíndices. */
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/* Cambia el guion por el signo menos tipográfico: "-3M - 2/5" -> "−3M − 2/5". */
const menos = (s) => String(s).replace(/-(?=[\dMxZ(])/g, '−').replace(/ - /g, ' − ');

/* Texto exacto del servidor (ya viene como "5/2" o "-3M + 2/5") listo para mostrar. */
const tx = (s) => (s === null || s === undefined ? '—' : menos(esc(s)));

/* x1 -> x₁, s2 -> s₂, a1 -> a₁ */
function subind(nombre) {
  const m = /^([a-z])(\d+)$/.exec(nombre);
  return m ? `${m[1]}<sub>${m[2]}</sub>` : esc(nombre);
}

/* Número final {fraccion, decimal, exacto}: fracción con el decimal al lado cuando no es entero. */
function num(n) {
  if (!n) return '—';
  const f = menos(esc(n.fraccion));
  if (!n.fraccion.includes('/')) return f;
  return `${f} <span class="dec">${n.exacto ? '=' : '≈'} ${menos(String(n.decimal))}</span>`;
}

/* Versión corta, solo texto, para etiquetas dentro del gráfico. */
function numCorto(n) {
  if (!n) return '—';
  if (n.fraccion.length <= 7) return menos(n.fraccion);
  return menos(String(n.decimal));
}

/* Límite de un rango: null significa infinito. */
function limite(n, signo) {
  return n === null || n === undefined ? (signo < 0 ? '−∞' : '+∞') : num(n);
}

function descargarTexto(nombre, contenido) {
  const blob = new Blob([contenido], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = nombre;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
