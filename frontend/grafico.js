/* Método gráfico: dibuja la región factible, las restricciones, los vértices con su Z y la recta de Z en el óptimo. */
const PALETA_RESTRICCIONES = ['#60A5FA', '#34D399', '#FBBF24', '#F472B6', '#FB923C', '#22D3EE', '#A3E635'];
const colorRestriccion = (i) => PALETA_RESTRICCIONES[i % PALETA_RESTRICCIONES.length];

function marcasEje(maximo) {
  const bruto = maximo / 7;
  const potencia = Math.pow(10, Math.floor(Math.log10(bruto)));
  const paso = [1, 2, 5, 10].map((k) => k * potencia).find((p) => p >= bruto);
  const marcas = [];
  for (let v = 0; v <= maximo + paso * 1e-9; v += paso) marcas.push(Number(v.toFixed(10)));
  return marcas;
}

const etiquetaMarca = (v) => String(Number(v.toFixed(6)));

function dibujarGrafico(g) {
  const ancho = 760, alto = 560, ml = 58, mr = 28, mt = 28, mb = 52;
  const W = ancho - ml - mr, H = alto - mt - mb;
  const X = g.caja.x_max, Y = g.caja.y_max;
  const px = (x) => ml + (x / X) * W;
  const py = (y) => mt + H - (y / Y) * H;
  const partes = [];

  partes.push(`<defs><clipPath id="recorte"><rect x="${ml}" y="${mt}" width="${W}" height="${H}"/></clipPath></defs>`);

  // cuadrícula y ejes
  for (const v of marcasEje(X)) {
    partes.push(`<line class="g-rejilla" x1="${px(v)}" y1="${mt}" x2="${px(v)}" y2="${mt + H}"/>`);
    partes.push(`<text class="g-marca" x="${px(v)}" y="${mt + H + 18}" text-anchor="middle">${etiquetaMarca(v)}</text>`);
  }
  for (const v of marcasEje(Y)) {
    partes.push(`<line class="g-rejilla" x1="${ml}" y1="${py(v)}" x2="${ml + W}" y2="${py(v)}"/>`);
    partes.push(`<text class="g-marca" x="${ml - 8}" y="${py(v) + 4}" text-anchor="end">${etiquetaMarca(v)}</text>`);
  }
  partes.push(`<line class="g-eje" x1="${ml}" y1="${mt + H}" x2="${ml + W}" y2="${mt + H}"/>`);
  partes.push(`<line class="g-eje" x1="${ml}" y1="${mt}" x2="${ml}" y2="${mt + H}"/>`);
  partes.push(`<text class="g-eje-nombre" x="${ml + W}" y="${mt + H + 40}" text-anchor="end">x<tspan baseline-shift="sub" font-size="11">1</tspan></text>`);
  partes.push(`<text class="g-eje-nombre" x="${ml - 40}" y="${mt + 8}" text-anchor="middle">x<tspan baseline-shift="sub" font-size="11">2</tspan></text>`);

  partes.push('<g clip-path="url(#recorte)">');
  // región factible
  const poli = g.region.poligono;
  if (poli.length >= 3) {
    const puntos = poli.map((p) => `${px(p[0]).toFixed(2)},${py(p[1]).toFixed(2)}`).join(' ');
    partes.push(`<polygon class="g-region" points="${puntos}"><title>Región factible</title></polygon>`);
  } else if (poli.length === 2) {
    partes.push(`<line class="g-region-linea" x1="${px(poli[0][0])}" y1="${py(poli[0][1])}" x2="${px(poli[1][0])}" y2="${py(poli[1][1])}"/>`);
  }
  // restricciones
  g.restricciones.forEach((r, i) => {
    if (!r.segmento) return;
    const [a, b] = r.segmento;
    partes.push(`<line class="g-restriccion" stroke="${colorRestriccion(i)}" x1="${px(a[0])}" y1="${py(a[1])}" x2="${px(b[0])}" y2="${py(b[1])}"><title>${esc(r.etiqueta)}: ${esc(r.expresion)}</title></line>`);
  });
  // recta de Z en el óptimo
  if (g.optimo && g.optimo.recta) {
    const [a, b] = g.optimo.recta;
    partes.push(`<line class="g-isoutilidad" x1="${px(a[0])}" y1="${py(a[1])}" x2="${px(b[0])}" y2="${py(b[1])}"><title>Recta de Z en el óptimo: ${esc(g.optimo.expresion)}</title></line>`);
  }
  // vértices no factibles (tenues) y factibles
  g.vertices.filter((v) => !v.factible).forEach((v) => {
    partes.push(`<circle class="g-vertice-no" cx="${px(v.x.decimal)}" cy="${py(v.y.decimal)}" r="3.5"><title>Intersección no factible (${esc(v.x.fraccion)}, ${esc(v.y.fraccion)})</title></circle>`);
  });
  g.vertices.filter((v) => v.factible).forEach((v) => {
    const cx = px(v.x.decimal), cy = py(v.y.decimal);
    partes.push(`<circle class="${v.es_optimo ? 'g-vertice-opt' : 'g-vertice'}" cx="${cx}" cy="${cy}" r="${v.es_optimo ? 7 : 5}"><title>(${esc(v.x.fraccion)}, ${esc(v.y.fraccion)})  Z = ${esc(v.z.fraccion)}</title></circle>`);
  });
  partes.push('</g>');

  // rótulos de restricciones y de vértices (fuera del recorte para que no se corten)
  g.restricciones.forEach((r, i) => {
    if (!r.segmento) return;
    const [a, b] = r.segmento;
    const punto = a[1] > b[1] ? a : b;  // el extremo más alto
    const x = Math.min(Math.max(px(punto[0]) + 6, ml + 4), ml + W - 26);
    const y = Math.min(Math.max(py(punto[1]) + 14, mt + 12), mt + H - 6);
    partes.push(`<text class="g-rotulo" fill="${colorRestriccion(i)}" x="${x}" y="${y}">${esc(r.etiqueta)}</text>`);
  });
  g.vertices.filter((v) => v.factible).forEach((v) => {
    const x = Math.min(px(v.x.decimal) + 9, ml + W - 135);
    const y = Math.max(py(v.y.decimal) - 9, mt + 12);
    const clase = v.es_optimo ? 'g-etiqueta g-etiqueta-opt' : 'g-etiqueta';
    partes.push(`<text class="${clase}" x="${x}" y="${y}">(${numCorto(v.x)}, ${numCorto(v.y)}) Z=${numCorto(v.z)}</text>`);
  });

  return `<svg class="grafico" viewBox="0 0 ${ancho} ${alto}" role="img" aria-label="Método gráfico: región factible, restricciones y vértices">${partes.join('')}</svg>`;
}

function leyendaGrafico(g) {
  const items = g.restricciones.map((r, i) => `<li><span class="leyenda-linea" style="background:${colorRestriccion(i)}"></span><b>${esc(r.etiqueta)}</b> ${menos(esc(r.expresion))}</li>`);
  items.push('<li><span class="leyenda-region"></span>Región factible</li>');
  if (g.optimo && g.optimo.recta) items.push(`<li><span class="leyenda-iso"></span>Recta de Z en el óptimo: ${menos(esc(g.optimo.expresion))}</li>`);
  items.push('<li><span class="leyenda-punto-opt"></span>Vértice óptimo</li>');
  items.push('<li><span class="leyenda-punto"></span>Vértice factible</li>');
  items.push('<li><span class="leyenda-punto-no"></span>Intersección no factible</li>');
  return `<ul class="leyenda">${items.join('')}</ul>`;
}
