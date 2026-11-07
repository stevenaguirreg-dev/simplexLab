# SimplexOpt — Aplicación de Programación Lineal

Resuelve problemas de programación lineal con **dos métodos implementados por el equipo**: **Gran M** y **simplex revisado**.
Muestra el proceso completo (forma estándar, cada iteración, razón mínima, pivote), el método gráfico (2 variables),
el análisis de sensibilidad y los casos sin solución única. Backend en Python, interfaz web, todo en un solo contenedor (puerto **8080**).

> Los métodos usan solo `fractions.Fraction` de Python: todo el cálculo es exacto. El resultado final se muestra como
> fracción con su decimal al lado (hasta 4 cifras). Las librerías de optimización (scipy, etc.) solo se usan en las pruebas.

## Estructura

```
Dockerfile
README.md
backend/
  main.py                      # revisa/instala librerías y arranca el servidor en el puerto 8080
  requirements.txt
  api/                         # capa HTTP
    rutas.py                   #   POST /api/resolver, GET /api/salud y archivos del frontend
    esquemas.py                #   formato de la solicitud y lectura del JSON
    manejo_errores.py          #   errores -> mensajes claros (nunca trazas)
  services/
    servicio_resolucion.py     # orquesta: validar -> resolver -> casos especiales -> sensibilidad -> gráfico
  domain/                      # matemáticas puras, sin dependencias web
    modelos/
      base.py                  #   ModeloPL y Restriccion
      dos_variables.py         #   ModeloDosVariables  (admite método gráfico)
      tres_variables.py        #   ModeloTresVariables (sin gráfico)
    validacion.py              # valida la entrada y elige el modelo (regla de x3)
    forma_estandar.py          # holguras, excesos, artificiales y -Z para Min
    numeros.py                 # GranM: números a + b·M, y fracción + decimal
    algebra.py                 # inversa de matrices con fracciones
    pivoteo.py                 # variable entrante y prueba de la razón mínima
    resolutores/
      base.py                  #   ciclo común del simplex
      gran_m.py                #   Gran M con tablero completo
      revisado.py              #   simplex revisado con B^-1
    calculos_base.py           # B^-1, X_B, costos reducidos de una base dada
    casos_especiales.py        # degeneración y óptimos múltiples
    sensibilidad.py            # precios sombra, costos reducidos, rangos de c y de b
    grafico.py                 # región factible, vértices, recta de Z
    presentacion.py            # números -> texto para el front
  tests/                       # pruebas (unittest)
frontend/
  index.html  estilos.css  app.js  formato.js  grafico.js
```

### Regla de las variables
La pantalla siempre tiene tres columnas (x₁, x₂, x₃). Si **x₃ está vacía en la función objetivo y en todas las restricciones**,
el problema se resuelve como `ModeloDosVariables` (con método gráfico). Si x₃ tiene datos en algún lugar,
se usa `ModeloTresVariables` y todas sus celdas deben completarse (use 0 donde no participe); el método gráfico indica que no aplica.
Todas las variables son no negativas (x ≥ 0).

## Ejecución sin Docker

Requisitos: Python 3.9 o superior.

```bash
python backend/main.py
```

Abra http://localhost:8080. Al arrancar, `main.py` revisa si `numpy` y `sympy` están instaladas y, si no, ejecuta `pip install`
(si no hay internet, continúa sin ellas: el núcleo no las necesita). Para cambiar el puerto: `PUERTO=9000 python backend/main.py`.

## Docker

Desde la carpeta que contiene el `Dockerfile`:

```bash
# 1. construir la imagen
docker build -t simplexopt .

# 2. ejecutar el contenedor (la app queda en http://localhost:8080)
docker run --rm -p 8080:8080 --name simplexopt simplexopt

# 3. detenerlo (si se ejecutó en segundo plano con -d)
docker stop simplexopt
```

## Uso de la interfaz

1. **Acceso:** *Cargar problema* (sube un archivo JSON desde su equipo) o *Registro manual*.
2. **Formulación:** clic en **Max/Min** para alternar; clic en **≤** para ciclar entre ≤, ≥ y =; *Agregar restricción* y **×** para añadir o quitar filas.
   Elija el método (**Gran M** o **Revisado**) y luego *Respuesta inmediata* (ventana con los valores numéricos) o *Respuesta paso a paso* (dashboard).
3. **Dashboard:** pestañas *Resumen*, *Paso a paso*, *Método gráfico* y *Sensibilidad*. El botón **Exportar solución** descarga un `.txt` que contiene un JSON con el problema y la solución.

## Ejemplo de JSON que recibe el frontend (archivo para «Cargar problema»)

Los números se escriben como texto para conservar la exactitud (`"0.1"`, `"-3"`, `"1/3"`). Una celda vacía se escribe `""`.
Problema 3 del enunciado (3 variables):

```json
{
  "sentido": "max",
  "funcion_objetivo": ["3", "2", "5"],
  "restricciones": [
    { "coeficientes": ["1", "2", "1"], "relacion": "<=", "rhs": "430" },
    { "coeficientes": ["3", "0", "2"], "relacion": "<=", "rhs": "460" },
    { "coeficientes": ["1", "4", "0"], "relacion": "<=", "rhs": "420" }
  ]
}
```

Problema de 2 variables (x₃ vacía): el segundo problema del enunciado, con `=`, `≥` y lado derecho negativo:

```json
{
  "sentido": "min",
  "funcion_objetivo": ["4", "1", ""],
  "restricciones": [
    { "coeficientes": ["3", "1", ""],  "relacion": "=",  "rhs": "3" },
    { "coeficientes": ["4", "3", ""],  "relacion": ">=", "rhs": "6" },
    { "coeficientes": ["-1", "-2", ""], "relacion": ">=", "rhs": "-4" }
  ]
}
```

El archivo que genera **Exportar solución** también se puede volver a cargar (el problema va dentro de la clave `"problema"`).

## API

`POST /api/resolver`

```json
{
  "metodo": "gran_m",
  "modo": "paso_a_paso",
  "problema": { "sentido": "max", "funcion_objetivo": ["50", "80", ""], "restricciones": [ { "coeficientes": ["2", "1", ""], "relacion": "<=", "rhs": "100" } ] }
}
```

- `metodo`: `gran_m` o `revisado`. `modo`: `inmediata` (solo resultado) o `paso_a_paso` (forma estándar, iteraciones, gráfico, sensibilidad).
- Respuesta correcta (resumen): `{"ok": true, "estado": "optimo" | "infactible" | "no_acotado", "mensaje": "...", "solucion": {"z": {"fraccion": "3380", "decimal": 3380, "exacto": true}, "variables": [...], "restricciones": [...]}, ...}`
- Entrada inválida: HTTP 400 con `{"ok": false, "errores": ["Restricción 2, coeficiente de x1: está vacío.", ...]}`.

## Pruebas

```bash
cd backend
python -m unittest discover -s tests -t .          # sin dependencias
pip install scipy && python -m unittest discover -s tests -t .   # además compara con scipy (150 problemas aleatorios)
```

Incluyen los 7 problemas del enunciado con ambos métodos, la validación de entrada, la sensibilidad (Wyndor de la clase 12 y comprobación por re-resolución),
el método gráfico y la comparación de Z/estado contra scipy.

| # | Problema | Resultado verificado |
|---|---|---|
| 1 | Redundante + gráfico | x₁ = 42, x₂ = 16, Z = 3380 |
| 2 | Min con =, ≥, b < 0 | x₁ = 2/5, x₂ = 9/5, Z = 17/5 |
| 3 | Tres variables | x = (0, 100, 230), Z = 1350 |
| 4 | Infactible | «El problema no tiene solución factible.» |
| 5 | No acotado | «La solución es no acotada…» |
| 6 | Óptimos múltiples | Z = 10 en el segmento (0, 5/2) – (3, 1) |
| 7 | Degeneración | x = (0, 2), Z = 18, variable básica s₁ = 0 |

## Notas de diseño

- **Mismo ciclo, dos estados:** `ResolutorSimplex` (plantilla) contiene el ciclo; `ResolutorGranM` guarda el tablero y `ResolutorRevisado` guarda B⁻¹.
  Con las mismas reglas de entrada y salida ambos recorren las mismas bases; la app lo comprueba y lo muestra como «Verificado con …».
- **Reglas de pivoteo:** entra la variable con el costo reducido más negativo (empate: menor índice); sale la de menor razón entre coeficientes positivos (empate: menor índice).
  Si hay muchas iteraciones sin mejorar Z, se activa la regla de Bland para evitar ciclos.
- **Infactible vs. no acotado:** si queda una artificial positiva en la base, es infactible. Si aparece una columna sin razón válida mientras hay una artificial positiva,
  se prueba la factibilidad con un problema auxiliar antes de declarar «no acotado».
- **Sensibilidad:** se calcula desde la base final con las fórmulas de las clases 11 y 12 (C_B B⁻¹), independiente del método usado.
- **Mínimo:** se resuelve como Max(−Z); los tableros muestran la fila de −Z y los resultados finales siempre se reportan con el Z original.
- **Capa HTTP:** usa el servidor de la biblioteca estándar de Python (sin dependencias). Como solo `api/` conoce HTTP, se puede reemplazar por FastAPI sin tocar `services/` ni `domain/`.
