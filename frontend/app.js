/* SimplexOpt: estado, vistas y acciones de la interfaz. */
const REL_SIGUIENTE = { '<=': '>=', '>=': '=', '=': '<=' };
const REL_TEXTO = { '<=': '≤', '>=': '≥', '=': '=' };
const METODOS = { gran_m: 'Gran M', revisado: 'Revisado' };

const IC = {
  subir: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M12 17v-6"/><path d="m9.5 13 2.5-2.5 2.5 2.5"/></svg>',
  editar: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>',
  info: '<svg class="icono-aviso" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>',
  alerta: '<svg class="icono-aviso" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 2 20h20z"/><path d="M12 10v5M12 18h.01"/></svg>',
  ok: '<svg class="icono-aviso" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="m8 12.5 3 3 5-6"/></svg>',
};

const filaVacia = () => ({ coef: ['', '', ''], rel: '<=', rhs: '' });
const ej = (nombre, sentido, fo, filas) => ({ nombre, sentido, fo, restricciones: filas.map(([coef, rel, rhs]) => ({ coef, rel, rhs })) });
const EJEMPLOS = [
  ej('Enunciado 1 · restricción redundante', 'max', ['50', '80', ''], [[['2', '1', ''], '<=', '100'], [['1', '3', ''], '<=', '90'], [['0', '1', ''], '<=', '40']]),
  ej('Enunciado 2 · mínimo con =, ≥ y lado derecho negativo', 'min', ['4', '1', ''], [[['3', '1', ''], '=', '3'], [['4', '3', ''], '>=', '6'], [['-1', '-2', ''], '>=', '-4']]),
  ej('Enunciado 3 · tres variables', 'max', ['3', '2', '5'], [[['1', '2', '1'], '<=', '430'], [['3', '0', '2'], '<=', '460'], [['1', '4', '0'], '<=', '420']]),
  ej('Enunciado 4 · infactible', 'max', ['1', '1', ''], [[['1', '1', ''], '<=', '2'], [['1', '1', ''], '>=', '5']]),
  ej('Enunciado 5 · no acotado', 'max', ['1', '1', ''], [[['1', '-1', ''], '<=', '1'], [['-1', '1', ''], '<=', '2']]),
  ej('Enunciado 6 · óptimos múltiples', 'max', ['2', '4', ''], [[['1', '2', ''], '<=', '5'], [['1', '1', ''], '<=', '4']]),
  ej('Enunciado 7 · degeneración', 'max', ['3', '9', ''], [[['1', '4', ''], '<=', '8'], [['1', '2', ''], '<=', '4']]),
  ej('Clase · Wyndor Glass', 'max', ['3', '5', ''], [[['1', '0', ''], '<=', '4'], [['0', '2', ''], '<=', '12'], [['3', '2', ''], '<=', '18']]),
];

const estado = {
  vista: 'acceso',          // acceso | formulacion | resultados
  sentido: 'max',
  fo: ['', '', ''],
  restricciones: [filaVacia(), filaVacia()],
  metodo: null,
  errores: [],
  mensaje: '',
  cargando: null,           // null | 'inmediata' | 'paso_a_paso'
  modal: null,              // respuesta inmediata
  resultado: null,          // respuesta paso a paso
  problemaEnviado: null,
  pestana: 'resumen',
  enfocar: null,
};

/* ======================= conversión problema <-> API ======================= */
function aProblemaApi() {
  return {
    sentido: estado.sentido,
    funcion_objetivo: estado.fo.map((v) => v.trim()),
    restricciones: estado.restricciones.map((r) => ({ coeficientes: r.coef.map((v) => v.trim()), relacion: r.rel, rhs: r.rhs.trim() })),
  };
}

function leerProblemaCargado(datos) {
  const p = datos && datos.problema ? datos.problema : datos;
  if (!p || typeof p !== 'object' || !Array.isArray(p.funcion_objetivo) || !Array.isArray(p.restricciones)) {
    throw new Error('El archivo no tiene el formato esperado. Debe incluir "sentido", "funcion_objetivo" y "restricciones".');
  }
  const sentido = String(p.sentido || '').toLowerCase();
  if (!['max', 'min'].includes(sentido)) throw new Error('El campo "sentido" debe ser "max" o "min".');
  if (p.funcion_objetivo.length > 3) throw new Error('La aplicación admite hasta 3 variables (x1, x2 y x3).');
  const celda = (v) => (v === null || v === undefined ? '' : String(v));
  const tres = (a) => [0, 1, 2].map((i) => celda(a[i]));
  const restricciones = p.restricciones.map((r, i) => {
    if (!r || !Array.isArray(r.coeficientes)) throw new Error(`La restricción ${i + 1} no tiene "coeficientes".`);
    if (r.coeficientes.length > 3) throw new Error(`La restricción ${i + 1} tiene más de 3 coeficientes.`);
    const rel = { '<=': '<=', '≤': '<=', '>=': '>=', '≥': '>=', '=': '=' }[String(r.relacion || '').trim()];
    if (!rel) throw new Error(`La restricción ${i + 1} debe tener relación "<=", ">=" o "=".`);
    return { coef: tres(r.coeficientes), rel, rhs: celda(r.rhs) };
  });
  return { sentido, fo: tres(p.funcion_objetivo), restricciones: restricciones.length ? restricciones : [filaVacia()], metodo: METODOS[datos.metodo] ? datos.metodo : null };
}

function aplicarProblema(p) {
  estado.sentido = p.sentido;
  estado.fo = p.fo;
  estado.restricciones = p.restricciones;
  if (p.metodo) estado.metodo = p.metodo;
  estado.errores = [];
  estado.mensaje = '';
}

/* ================================ acciones ================================= */
async function resolver(modo) {
  if (!estado.metodo || estado.cargando) return;
  estado.errores = [];
  estado.mensaje = '';
  estado.cargando = modo;
  render();
  const problema = aProblemaApi();
  try {
    const resp = await fetch('/api/resolver', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ metodo: estado.metodo, modo, problema }),
    });
    const datos = await resp.json();
    if (!resp.ok || !datos.ok) {
      estado.errores = datos.errores || ['No se pudo resolver el problema.'];
    } else if (modo === 'inmediata') {
      estado.modal = datos;
    } else {
      estado.resultado = datos;
      estado.problemaEnviado = problema;
      estado.vista = 'resultados';
      estado.pestana = 'resumen';
    }
  } catch (error) {
    estado.errores = ['No se pudo conectar con el servidor. Verifique que la aplicación esté en ejecución.'];
  }
  estado.cargando = null;
  render();
  window.scrollTo(0, 0);
}

function exportarSolucion() {
  const r = estado.resultado;
  if (!r) return;
  const s = r.solucion;
  const contenido = {
    problema: estado.problemaEnviado,
    metodo: r.metodo,
    solucion: {
      estado: r.estado,
      mensaje: r.mensaje,
      ...(s ? { z: s.z, variables: s.variables, restricciones: s.restricciones, base_final: s.base_final, optimos_alternativos: s.optimos_alternativos } : {}),
      casos_especiales: r.casos_especiales,
    },
  };
  descargarTexto('solucion_simplexopt.txt', JSON.stringify(contenido, null, 2));
}

function manejarAccion(accion, arg) {
  switch (accion) {
    case 'ir':
      if (arg === 'resultados' && !estado.resultado) return;
      estado.vista = arg; estado.errores = []; estado.mensaje = ''; break;
    case 'nuevo':
      estado.sentido = 'max'; estado.fo = ['', '', '']; estado.restricciones = [filaVacia(), filaVacia()];
      estado.metodo = null; estado.errores = []; estado.mensaje = ''; estado.vista = 'formulacion'; break;
    case 'cargar-archivo': document.getElementById('archivo').click(); return;
    case 'sentido': estado.sentido = estado.sentido === 'max' ? 'min' : 'max'; break;
    case 'relacion': { const r = estado.restricciones[+arg]; r.rel = REL_SIGUIENTE[r.rel]; break; }
    case 'agregar': estado.restricciones.push(filaVacia()); estado.enfocar = `c:${estado.restricciones.length - 1}:0`; break;
    case 'quitar': if (estado.restricciones.length > 1) estado.restricciones.splice(+arg, 1); break;
    case 'metodo': estado.metodo = arg; break;
    case 'resolver': resolver(arg); return;
    case 'cerrar-modal': estado.modal = null; break;
    case 'pestana': estado.pestana = arg; break;
    case 'exportar': exportarSolucion(); return;
    default: return;
  }
  render();
}

document.addEventListener('click', (e) => {
  const el = e.target.closest('[data-accion]');
  if (el && !el.disabled) manejarAccion(el.dataset.accion, el.dataset.arg);
  else if (e.target.classList && e.target.classList.contains('fondo-modal')) manejarAccion('cerrar-modal');
});
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && estado.modal) manejarAccion('cerrar-modal'); });
document.addEventListener('input', (e) => {
  const c = e.target.dataset && e.target.dataset.campo;
  if (!c) return;
  const p = c.split(':');
  if (p[0] === 'fo') estado.fo[+p[1]] = e.target.value;
  else if (p[0] === 'c') estado.restricciones[+p[1]].coef[+p[2]] = e.target.value;
  else if (p[0] === 'rhs') estado.restricciones[+p[1]].rhs = e.target.value;
});
document.addEventListener('change', (e) => {
  if (e.target.dataset && e.target.dataset.cambio === 'ejemplo' && e.target.value !== '') {
    const x = EJEMPLOS[+e.target.value];
    aplicarProblema({ sentido: x.sentido, fo: [...x.fo], restricciones: x.restricciones.map((r) => ({ coef: [...r.coef], rel: r.rel, rhs: r.rhs })) });
    estado.mensaje = `Ejemplo cargado: ${x.nombre}.`;
    render();
  }
});
document.getElementById('archivo').addEventListener('change', async (e) => {
  const archivo = e.target.files[0];
  e.target.value = '';
  if (!archivo) return;
  try {
    const datos = JSON.parse(await archivo.text());
    aplicarProblema(leerProblemaCargado(datos));
    estado.mensaje = `Problema cargado desde «${archivo.name}».`;
    estado.vista = 'formulacion';
  } catch (error) {
    estado.errores = [error instanceof SyntaxError ? `«${archivo.name}» no es un JSON válido.` : error.message];
  }
  render();
});

/* ================================== vistas ================================= */
const cabecera = () => `
  <header class="cabecera">
    <div class="marca"><span class="logo">fx</span><span class="marca-nombre">SimplexOpt</span></div>
    <div class="estado-sistema"><span class="punto-activo"></span>Sistema activo</div>
  </header>`;

const avisoErrores = (lista, titulo = 'Revise el problema antes de resolver') => lista.length ? `
  <div class="aviso aviso-error" role="alert">${IC.alerta}<div><b>${esc(titulo)}</b><ul>${lista.map((m) => `<li>${esc(m)}</li>`).join('')}</ul></div></div>` : '';

function vistaAcceso() {
  return `${cabecera()}
  <main class="acceso">
    <div>
      <h1>SimplexOpt</h1>
      <p class="sub">Plataforma de optimización lineal</p>
      <div class="opciones">
        <button class="opcion" data-accion="cargar-archivo"><span class="icono">${IC.subir}</span>Cargar problema<small>Archivo JSON</small></button>
        <button class="opcion" data-accion="nuevo"><span class="icono">${IC.editar}</span>Registro manual del problema<small>Ir a Formulación</small></button>
      </div>
      <div style="max-width:560px;margin:24px auto 0;text-align:left">${avisoErrores(estado.errores, 'No se pudo cargar el archivo')}</div>
    </div>
  </main>
  <footer class="pie"><span>SimplexOpt · Gran M y simplex revisado</span><span>Formulación y resolución lineal</span></footer>`;
}

function nav() {
  const item = (clave, n, texto, off) => `<button class="nav-item ${estado.vista === clave ? 'activo' : ''}" data-accion="ir" data-arg="${clave}" ${off ? 'disabled' : ''}><span class="nav-num">${n}</span>${texto}</button>`;
  return `<aside class="lateral"><div class="lateral-titulo">NAVEGACIÓN DEL MODELO</div>
    ${item('acceso', 1, 'Acceso', false)}${item('formulacion', 2, 'Formulación del problema', false)}${item('resultados', 3, 'Resultados', !estado.resultado)}</aside>`;
}

const carcasa = (contenido) => `${cabecera()}<div class="carcasa">${nav()}<main class="principal"><div class="contenedor">${contenido}</div></main></div>`;

function vistaFormulacion() {
  const x = (j) => `<span class="var">x<sub>${j + 1}</sub></span>`;
  const fo = `<div class="fila-modelo">
      <button class="sentido" data-accion="sentido" aria-label="Cambiar entre maximizar y minimizar" title="Clic para cambiar entre Max y Min">${estado.sentido === 'max' ? 'Max' : 'Min'}</button>
      <span class="z-igual">Z =</span>
      ${[0, 1, 2].map((j) => `${j ? '<span class="op">+</span>' : ''}<input class="campo" inputmode="decimal" autocomplete="off" aria-label="Coeficiente de x${j + 1} en la función objetivo" data-campo="fo:${j}" value="${esc(estado.fo[j])}">${x(j)}`).join('')}
    </div>`;
  const filas = estado.restricciones.map((r, i) => `<div class="fila-modelo">
      <span class="rotulo-restriccion">R${i + 1}</span>
      ${[0, 1, 2].map((j) => `${j ? '<span class="op">+</span>' : ''}<input class="campo" inputmode="decimal" autocomplete="off" aria-label="Coeficiente de x${j + 1} en la restricción ${i + 1}" data-campo="c:${i}:${j}" value="${esc(r.coef[j])}">${x(j)}`).join('')}
      <button class="relacion" data-accion="relacion" data-arg="${i}" aria-label="Cambiar tipo de restricción" title="Clic para cambiar entre ≤, ≥ y =">${REL_TEXTO[r.rel]}</button>
      <input class="campo campo-ancho" inputmode="decimal" autocomplete="off" aria-label="Lado derecho de la restricción ${i + 1}" data-campo="rhs:${i}" value="${esc(r.rhs)}">
      <button class="quitar" data-accion="quitar" data-arg="${i}" aria-label="Eliminar restricción ${i + 1}" title="Eliminar restricción" ${estado.restricciones.length === 1 ? 'disabled' : ''}>×</button>
    </div>`).join('');
  const sinMetodo = !estado.metodo || estado.cargando;
  const boton = (modo, texto, clase) => `<button class="btn ${clase}" data-accion="resolver" data-arg="${modo}" ${sinMetodo ? 'disabled' : ''}>${estado.cargando === modo ? 'Resolviendo…' : texto}</button>`;
  const contenido = `
    <div class="titulo-vista">
      <div><h1>Formulación del problema</h1><p>Ingrese la función objetivo y las restricciones. Todas las variables son no negativas (x ≥ 0).</p></div>
      <select class="ejemplos" data-cambio="ejemplo" aria-label="Cargar un ejemplo">
        <option value="">Cargar un ejemplo…</option>${EJEMPLOS.map((e, i) => `<option value="${i}">${esc(e.nombre)}</option>`).join('')}
      </select>
    </div>
    <div class="tarjeta ${estado.cargando ? 'cargando' : ''}">
      <section class="seccion-form"><p class="etiqueta">FUNCIÓN OBJETIVO</p>${fo}</section>
      <section class="seccion-form"><p class="etiqueta">RESTRICCIONES (S.A.)</p>${filas}
        <button class="btn btn-chico" data-accion="agregar">+ Agregar restricción</button>
        <p class="nota">Se aceptan enteros, decimales y fracciones (por ejemplo 1/3). Deje x<sub>3</sub> vacía en la función objetivo y en todas las restricciones para resolver con 2 variables.</p>
      </section>
      <section class="seccion-form"><p class="etiqueta">MÉTODO DE SOLUCIÓN</p>
        <div class="barra-metodo">
          ${Object.entries(METODOS).map(([k, n]) => `<button class="btn btn-selector" data-accion="metodo" data-arg="${k}" aria-pressed="${estado.metodo === k}">${n}</button>`).join('')}
          ${estado.metodo ? '' : '<span class="ayuda-metodo">Elija un método para habilitar las respuestas.</span>'}
        </div>
        <div class="barra-acciones">${boton('inmediata', 'Respuesta inmediata', 'btn-primario')}${boton('paso_a_paso', 'Respuesta paso a paso', '')}</div>
      </section>
      ${estado.mensaje ? `<div class="aviso aviso-info">${IC.info}<div>${esc(estado.mensaje)}</div></div>` : ''}
      ${avisoErrores(estado.errores)}
    </div>`;
  return carcasa(contenido);
}

/* ---------------------------- ventana de respuesta inmediata ---------------------------- */
function vistaModal() {
  const r = estado.modal;
  const s = r.solucion;
  const ok = r.estado === 'optimo';
  let cuerpo = `<div class="aviso ${ok ? 'aviso-ok' : 'aviso-error'}" style="margin-top:0">${ok ? IC.ok : IC.alerta}<div><b>${esc(r.mensaje)}</b></div></div>`;
  if (ok) {
    cuerpo += `<div class="kpis"><div class="kpi kpi-z"><p class="etiqueta">VALOR ÓPTIMO Z*</p><div class="valor">${num(s.z)}</div></div></div>
      <p class="subtitulo">Variables</p>
      <div class="tabla-envoltorio"><table><tbody>${s.variables.map((v) => `<tr><td class="izq">${subind(v.nombre)}</td><td>${num(v.valor)}</td></tr>`).join('')}</tbody></table></div>
      <p class="subtitulo">Holgura o exceso de cada restricción</p>
      <div class="tabla-envoltorio"><table><thead><tr><th class="izq">Restricción</th><th>Valor</th><th class="izq">Tipo</th></tr></thead><tbody>
        ${s.restricciones.map((c) => `<tr><td class="izq">R${c.numero}</td><td>${num(c.valor)}</td><td class="izq">${c.tipo}${c.activa ? ' · activa' : ''}</td></tr>`).join('')}
      </tbody></table></div>`;
    if (r.casos_especiales.mensajes.length) cuerpo += `<div class="aviso aviso-alerta">${IC.alerta}<div>${r.casos_especiales.mensajes.map((m) => `<div>${tx(m)}</div>`).join('')}</div></div>`;
  }
  return `<div class="fondo-modal"><div class="modal" role="dialog" aria-modal="true" aria-label="Respuesta inmediata">
    <div class="modal-cab"><h2>Respuesta inmediata <span class="chip chip-azul">${METODOS[r.metodo]}</span></h2>
      <button class="cerrar" data-accion="cerrar-modal" aria-label="Cerrar">✕</button></div>${cuerpo}</div></div>`;
}

/* ================================ resultados ================================ */
function vistaResultados() {
  const r = estado.resultado;
  const pestanas = [['resumen', 'Resumen'], ['paso', 'Paso a paso'], ['grafico', 'Método gráfico'], ['sensibilidad', 'Sensibilidad']];
  const cuerpo = { resumen: tabResumen, paso: tabPasoAPaso, grafico: tabGrafico, sensibilidad: tabSensibilidad }[estado.pestana](r);
  return carcasa(`
    <div class="titulo-vista">
      <div><h1>Dashboard de resultados</h1><p>${menos(esc(r.modelo.objetivo))}</p></div>
      <div class="barra-acciones">
        <button class="btn" data-accion="ir" data-arg="formulacion">← Volver a la formulación</button>
        <button class="btn btn-primario" data-accion="exportar">Exportar solución</button>
      </div>
    </div>
    <div class="pestanas" role="tablist">${pestanas.map(([k, t]) => `<button class="pestana" role="tab" aria-selected="${estado.pestana === k}" data-accion="pestana" data-arg="${k}">${t}</button>`).join('')}</div>
    ${cuerpo}`);
}

function chipsEstado(r) {
  const c = r.comparacion;
  const chips = [`<span class="chip chip-azul">Método: ${METODOS[r.metodo]}</span>`, `<span class="chip">Iteraciones: ${r.iteraciones}</span>`, `<span class="chip">Variables: ${r.modelo.num_variables}</span>`];
  if (r.casos_especiales.degenerado) chips.push('<span class="chip chip-aviso">Degenerado</span>');
  if (r.casos_especiales.optimos_multiples) chips.push('<span class="chip chip-aviso">Óptimos múltiples</span>');
  if (c && c.disponible) {
    const coincide = c.mismo_estado && c.mismo_z !== false && c.misma_base_final;
    chips.push(coincide
      ? `<span class="chip chip-ok" title="${METODOS[c.metodo_alterno]}: ${c.iteraciones[c.metodo_alterno]} iteraciones${c.misma_secuencia_de_bases ? ', misma secuencia de bases' : ''}">Verificado con ${METODOS[c.metodo_alterno]}</span>`
      : `<span class="chip chip-aviso">Difiere de ${METODOS[c.metodo_alterno]}</span>`);
  }
  return chips.join('');
}

function tabResumen(r) {
  const s = r.solucion;
  const ok = r.estado === 'optimo';
  const sens = r.sensibilidad;
  let html = `<div class="aviso ${ok ? 'aviso-ok' : 'aviso-error'}" style="margin-top:0">${ok ? IC.ok : IC.alerta}
    <div><b>${esc(r.mensaje)}</b><div class="chips">${chipsEstado(r)}</div></div></div>`;
  if (r.casos_especiales.mensajes.length) html += `<div class="aviso aviso-alerta">${IC.alerta}<div>${r.casos_especiales.mensajes.map((m) => `<div>${tx(m)}</div>`).join('')}</div></div>`;
  if (r.advertencias.length) html += `<div class="aviso aviso-alerta">${IC.alerta}<div>${r.advertencias.map((m) => `<div>${esc(m)}</div>`).join('')}</div></div>`;
  if (ok) {
    html += `<div class="kpis">
      <div class="kpi kpi-z"><p class="etiqueta">VALOR ÓPTIMO Z*</p><div class="valor">${num(s.z)}</div></div>
      ${s.variables.map((v) => `<div class="kpi"><p class="etiqueta">VARIABLE ${esc(v.nombre.toUpperCase())}*</p><div class="valor">${num(v.valor)}</div></div>`).join('')}
      <div class="kpi"><p class="etiqueta">BASE ÓPTIMA</p><div class="valor" style="font-size:18px">{ ${s.base_final.map(subind).join(', ')} }</div></div>
    </div>
    <div class="tarjeta"><p class="etiqueta">ESTADO DE LAS RESTRICCIONES</p>
      <div class="tabla-envoltorio"><table><thead><tr><th class="izq">Restricción</th><th>Uso (lado izq.)</th><th>Lado derecho</th><th>Holgura / exceso</th><th>Precio sombra</th><th class="izq">Estado</th></tr></thead><tbody>
        ${s.restricciones.map((c, i) => `<tr><td class="izq">R${c.numero}: ${menos(esc(r.modelo.restricciones[i]))}</td><td>${num(c.lhs)}</td><td>${num(c.rhs)}</td><td>${num(c.valor)} <span class="dec">(${c.tipo})</span></td><td>${sens ? num(sens.precios_sombra[i].valor) : '—'}</td><td class="izq">${c.activa ? '<span class="chip chip-azul">Activa</span>' : '<span class="chip">Con holgura</span>'}</td></tr>`).join('')}
      </tbody></table></div></div>`;
  }
  html += `<div class="tarjeta"><p class="etiqueta">MODELO INGRESADO</p><div class="mono" style="font-family:var(--mono);font-size:14px">${menos(esc(r.modelo.objetivo))}<br>${r.modelo.restricciones.map((x, i) => `R${i + 1}: ${menos(esc(x))}`).join('<br>')}<br>x ≥ 0</div></div>`;
  return html;
}

/* ------------------------------ paso a paso ------------------------------ */
function motivoEntrante(e) {
  if (e.criterio === 'bland') return 'se aplicó la regla de Bland (menor índice con costo reducido negativo) para evitar ciclos.';
  let t = `tiene el costo reducido más negativo del renglón (0): ${tx(e.costo)}.`;
  if (e.candidatos.length > 1) t += ` Candidatos: ${e.candidatos.map((c) => `${subind(c.nombre)} (${tx(c.costo)})`).join(', ')}.`;
  if (e.empate) t += ' Hay empate: se elige la de menor índice.';
  return t;
}

function decisiones(paso) {
  const e = paso.entrante;
  let html = `<li><b>Entra ${subind(e.nombre)}:</b> ${motivoEntrante(e)}</li>`;
  if (paso.saliente) {
    const rz = paso.razones[paso.saliente.fila];
    html += `<li><b>Sale ${subind(paso.saliente.nombre)}:</b> tiene la razón mínima, ${tx(rz.xb)} ÷ ${tx(rz.columna)} = ${tx(rz.razon)}. Solo se consideran coeficientes positivos de la columna de ${subind(e.nombre)}.${paso.empate_razon ? ' Hay empate en la razón mínima: se elige la de menor índice y la solución será degenerada.' : ''}</li>
      <li><b>Pivote:</b> ${tx(paso.pivote)} (fila de ${subind(paso.saliente.nombre)}, columna de ${subind(e.nombre)}).</li>`;
  } else {
    html += `<li><b>No sale ninguna variable:</b> ningún coeficiente de la columna de ${subind(e.nombre)} es positivo, no existe razón mínima y Z puede crecer sin límite (solución no acotada).</li>`;
  }
  return `<ol class="decisiones">${html}</ol>`;
}

function tablaTablero(inst, paso) {
  const nV = inst.columnas.length - 1;
  const ent = paso ? paso.entrante.indice : -1;
  const sale = paso && paso.saliente ? paso.saliente.fila : -1;
  const ce = (j) => (j === ent ? 'c-ent' : '');
  const cab = `<tr><th class="centro">Ec</th><th class="vb">VB</th><th>Z</th>${inst.columnas.slice(0, nV).map((c, j) => `<th class="${ce(j)}">${subind(c)}</th>`).join('')}<th>LD</th>${paso ? '<th>Razón</th>' : ''}</tr>`;
  const fz = `<tr class="fila-z"><td class="centro">0</td><td class="vb">${tx(inst.etiqueta_z)}</td><td>1</td>${inst.fila_z.slice(0, nV).map((v, j) => `<td class="${ce(j)} ${String(v).startsWith('-') ? 'celda-neg' : ''}">${tx(v)}</td>`).join('')}<td>${tx(inst.fila_z[nV])}</td>${paso ? '<td></td>' : ''}</tr>`;
  const filas = inst.filas.map((f, i) => {
    const rz = paso ? paso.razones[i].razon : null;
    return `<tr class="${i === sale ? 'f-sale' : ''}"><td class="centro">${i + 1}</td><td class="vb">${subind(f.variable_basica)}</td><td>0</td>
      ${f.valores.slice(0, nV).map((v, j) => `<td class="${ce(j)} ${i === sale && j === ent ? 'pivote' : ''}">${tx(v)}</td>`).join('')}<td>${tx(f.valores[nV])}</td>
      ${paso ? `<td class="${i === sale ? 'razon-min' : ''}">${rz === null ? '—' : tx(rz)}</td>` : ''}</tr>`;
  }).join('');
  return `<div class="tabla-envoltorio"><table class="tablero"><thead>${cab}</thead><tbody>${fz}${filas}</tbody></table></div>`;
}

function bloqueRevisado(inst, paso) {
  const m = inst.base.length;
  const R = Array.from({ length: m }, (_, i) => `<th>R${i + 1}</th>`).join('');
  const sale = paso && paso.saliente ? paso.saliente.fila : -1;
  const tabla = (cab, filas) => `<div class="tabla-envoltorio"><table class="tablero"><thead><tr>${cab}</tr></thead><tbody>${filas}</tbody></table></div>`;
  const binv = tabla(`<th class="vb">B⁻¹</th>${R}`, inst.B_inv.map((fila, i) => `<tr class="${i === sale ? 'f-sale' : ''}"><td class="vb">${subind(inst.base[i])}</td>${fila.map((v) => `<td>${tx(v)}</td>`).join('')}</tr>`).join(''));
  const xb = tabla('<th class="vb">VB</th><th>X<sub>B</sub></th>', inst.base.map((b, i) => `<tr class="${i === sale ? 'f-sale' : ''}"><td class="vb">${subind(b)}</td><td>${tx(inst.xb[i])}</td></tr>`).join(''));
  const y = tabla(R, `<tr>${inst.y.map((v) => `<td>${tx(v)}</td>`).join('')}</tr>`);
  const entNombre = paso ? paso.entrante.nombre : null;
  const costos = tabla(inst.costos_reducidos.map((c) => `<th class="${c.variable === entNombre ? 'c-ent' : ''}">${subind(c.variable)}</th>`).join(''),
    `<tr>${inst.costos_reducidos.map((c) => `<td class="${c.variable === entNombre ? 'c-ent' : ''} ${String(c.valor).startsWith('-') ? 'celda-neg' : ''}">${c.basica ? '0' : tx(c.valor)}</td>`).join('')}</tr>`);
  let razones = '';
  if (paso) {
    razones = `<div><p class="subtitulo">Columna entrante ${subind(paso.entrante.nombre)} (B⁻¹·P) y prueba de la razón mínima</p>${tabla('<th class="vb">VB</th><th>Columna</th><th>X<sub>B</sub></th><th>Razón</th>',
      paso.razones.map((q, i) => `<tr class="${i === sale ? 'f-sale' : ''}"><td class="vb">${subind(q.variable_basica)}</td><td class="${i === sale ? 'pivote' : ''}">${tx(q.columna)}</td><td>${tx(q.xb)}</td><td class="${i === sale ? 'razon-min' : ''}">${q.razon === null ? '—' : tx(q.razon)}</td></tr>`).join(''))}</div>`;
  }
  return `<div class="bloque-revisado">
      <div><p class="subtitulo">Matriz B⁻¹ (filas: variables básicas)</p>${binv}</div>
      <div><p class="subtitulo">Variables básicas y valores</p>${xb}</div>
      <div><p class="subtitulo">Multiplicadores y = C<sub>B</sub>·B⁻¹</p>${y}</div>
    </div>
    <p class="subtitulo">Costos reducidos (d<sub>j</sub> = C<sub>B</sub>·B⁻¹·P<sub>j</sub> − C<sub>j</sub>)</p>${costos}
    <p class="subtitulo">Valor actual: ${tx(inst.etiqueta_z)} = ${tx(inst.z)}</p>${razones}`;
}

function tarjetaIteracion(titulo, etiqueta, inst, paso) {
  const cuerpo = inst.tipo === 'tablero' ? tablaTablero(inst, paso) : bloqueRevisado(inst, paso);
  return `<section class="iteracion"><div class="iteracion-cab"><h3>${titulo}</h3>${etiqueta ? `<span class="chip">${etiqueta}</span>` : ''}</div>${cuerpo}${paso ? decisiones(paso) : ''}</section>`;
}

function tabPasoAPaso(r) {
  const fe = r.forma_estandar;
  const tipos = { original: 'original', holgura: 'holgura', exceso: 'exceso', artificial: 'artificial' };
  let html = `<section class="tarjeta"><h3>Forma estándar</h3>
    <p class="subtitulo">Transformaciones aplicadas</p>
    <ul class="lista-simple">${fe.transformaciones.length ? fe.transformaciones.map((t) => `<li>${menos(esc(t))}</li>`).join('') : '<li>Todas las restricciones son ≤ con lado derecho no negativo: solo se agregan holguras.</li>'}</ul>
    <p class="subtitulo">Función objetivo aumentada</p><div class="tabla-envoltorio"><ul class="lista-ecuaciones"><li>${menos(esc(fe.objetivo))}</li></ul></div>
    <p class="subtitulo">Restricciones con variables de holgura, exceso y artificiales</p>
    <div class="tabla-envoltorio"><ul class="lista-ecuaciones">${fe.ecuaciones.map((q, i) => `<li>R${i + 1}: ${menos(esc(q))}</li>`).join('')}</ul></div>
    <div class="chips">${fe.variables.map((v) => `<span class="chip">${subind(v.nombre)} · ${tipos[v.tipo]}</span>`).join('')}</div>
    <p class="subtitulo">Base inicial: { ${fe.base_inicial.map(subind).join(', ')} }${r.metodo === 'gran_m' && fe.variables.some((v) => v.tipo === 'artificial') ? ' · M es un valor positivo muy grande' : ''}</p>
  </section>`;
  html += r.pasos.map((p) => tarjetaIteracion(`Iteración ${p.numero}`, p.numero === 0 ? 'Tablero inicial' : '', p.instantanea, p)).join('');
  if (r.estado !== 'no_acotado') {
    const titulos = {
      optimo: ['Solución final', 'Todos los costos reducidos son ≥ 0: la solución es óptima.'],
      infactible: ['Tablero final', 'Una variable artificial sigue en la base con valor positivo: no hay solución factible.'],
    };
    const [t, nota] = titulos[r.estado];
    html += tarjetaIteracion(`Iteración ${r.iteraciones} · ${t}`, '', r.instantanea_final, null).replace('</section>', `<div class="aviso ${r.estado === 'optimo' ? 'aviso-ok' : 'aviso-error'}">${r.estado === 'optimo' ? IC.ok : IC.alerta}<div>${nota}</div></div></section>`);
  }
  return html;
}

/* ------------------------------ gráfico ------------------------------ */
function tabGrafico(r) {
  const g = r.grafico;
  if (!g.aplica) return `<div class="aviso aviso-info" style="margin-top:0">${IC.info}<div><b>${esc(g.mensaje)}</b><br>Use las pestañas Paso a paso y Sensibilidad para analizar este problema.</div></div>`;
  const factibles = g.vertices.filter((v) => v.factible);
  const vert = factibles.length ? `<div class="tabla-envoltorio"><table><thead><tr><th class="izq">Vértice</th><th>x<sub>1</sub></th><th>x<sub>2</sub></th><th>Z</th></tr></thead><tbody>
    ${factibles.map((v, i) => `<tr><td class="izq">V${i + 1} ${v.es_optimo ? '<span class="chip chip-azul">óptimo</span>' : ''}</td><td>${num(v.x)}</td><td>${num(v.y)}</td><td>${num(v.z)}</td></tr>`).join('')}</tbody></table></div>` : '';
  const extra = r.casos_especiales.optimos_multiples ? `<div class="aviso aviso-alerta">${IC.alerta}<div>${r.casos_especiales.mensajes.filter((m) => m.includes('óptimas')).map(tx).join('<br>')}</div></div>` : '';
  return `<div class="grafico-caja"><div>${dibujarGrafico(g)}</div>
    <div><p class="etiqueta">LEYENDA</p>${leyendaGrafico(g)}<p class="nota" style="margin:0">${esc(g.mensaje)}</p></div></div>${extra}
    ${vert ? `<section class="tarjeta"><p class="etiqueta">VÉRTICES FACTIBLES Y SU VALOR DE Z</p>${vert}</section>` : ''}`;
}

/* ------------------------------ sensibilidad ------------------------------ */
function tabSensibilidad(r) {
  const s = r.sensibilidad;
  if (!s) return `<div class="aviso aviso-info" style="margin-top:0">${IC.info}<div>El análisis de sensibilidad solo está disponible cuando el problema tiene solución óptima.</div></div>`;
  const rango = (a, b) => `entre ${a === null ? '−∞' : num(a)} y ${b === null ? '+∞' : num(b)}`;
  const tabla = (cab, filas) => `<div class="tabla-envoltorio"><table class="tabla-texto"><thead><tr>${cab}</tr></thead><tbody>${filas}</tbody></table></div>`;
  const precios = tabla('<th class="izq">Restricción</th><th>Precio sombra</th><th class="izq">Interpretación</th>', s.precios_sombra.map((p, i) => {
    const nulo = p.valor.fraccion === '0';
    const rb = s.rangos_lado_derecho[i];
    return `<tr><td class="izq">R${p.restriccion}: ${menos(esc(r.modelo.restricciones[i]))}</td><td class="num">${num(p.valor)}</td><td class="izq">${nulo
      ? `R${p.restriccion} no limita la solución: aumentar su lado derecho no cambia Z.`
      : `Cada unidad adicional en el lado derecho de R${p.restriccion} cambia Z en ${num(p.valor)}, mientras b<sub>${p.restriccion}</sub> esté ${rango(rb.minimo, rb.maximo)}.`}</td></tr>`;
  }).join(''));
  const costos = tabla('<th class="izq">Variable</th><th>Costo reducido</th><th class="izq">Interpretación</th>', s.costos_reducidos.map((c) => `<tr><td class="izq">${subind(c.variable)}</td><td class="num">${num(c.valor)}</td><td class="izq">${c.basica
    ? 'Es variable básica: su costo reducido es 0.'
    : (c.valor.fraccion === '0' ? 'Costo reducido 0 fuera de la base: indica un óptimo alternativo.' : `Cada unidad que se obligue a entrar de ${subind(c.variable)} empeora Z en ${num(c.valor)}.`)}</td></tr>`).join(''));
  const coefs = tabla('<th class="izq">Variable</th><th>Coeficiente actual</th><th>Mínimo</th><th>Máximo</th><th class="izq">Interpretación</th>', s.rangos_coeficientes.map((c) => `<tr><td class="izq">${subind(c.variable)}</td><td class="num">${num(c.actual)}</td><td class="num">${limite(c.minimo, -1)}</td><td class="num">${limite(c.maximo, 1)}</td><td class="izq">La solución óptima no cambia mientras el coeficiente de ${subind(c.variable)} esté ${rango(c.minimo, c.maximo)}.</td></tr>`).join(''));
  const rhs = tabla('<th class="izq">Restricción</th><th>Lado derecho actual</th><th>Mínimo</th><th>Máximo</th><th class="izq">Interpretación</th>', s.rangos_lado_derecho.map((c) => `<tr><td class="izq">R${c.restriccion}</td><td class="num">${num(c.actual)}</td><td class="num">${limite(c.minimo, -1)}</td><td class="num">${limite(c.maximo, 1)}</td><td class="izq">La base óptima sigue siendo factible, y el precio sombra válido, mientras b<sub>${c.restriccion}</sub> esté ${rango(c.minimo, c.maximo)}.</td></tr>`).join(''));
  return `${s.advertencias.map((a) => `<div class="aviso aviso-alerta" style="margin-top:0">${IC.alerta}<div>${esc(a)}</div></div>`).join('')}
    <section class="tarjeta"><p class="etiqueta">PRECIOS SOMBRA</p>${precios}</section>
    <section class="tarjeta"><p class="etiqueta">COSTOS REDUCIDOS</p>${costos}</section>
    <section class="tarjeta"><p class="etiqueta">RANGO DE CADA COEFICIENTE DE LA FUNCIÓN OBJETIVO</p>${coefs}</section>
    <section class="tarjeta"><p class="etiqueta">RANGO DE CADA LADO DERECHO</p>${rhs}</section>`;
}

/* ================================== render ================================== */
function render() {
  const app = document.getElementById('app');
  app.innerHTML = { acceso: vistaAcceso, formulacion: vistaFormulacion, resultados: vistaResultados }[estado.vista]();
  document.getElementById('modal').innerHTML = estado.modal ? vistaModal() : '';
  if (estado.modal) { const b = document.querySelector('.cerrar'); if (b) b.focus(); }
  if (estado.enfocar) {
    const campo = document.querySelector(`[data-campo="${estado.enfocar}"]`);
    if (campo) campo.focus();
    estado.enfocar = null;
  }
}

render();
