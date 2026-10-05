    # ===================================================================
# PROYECTO PARADAS SITP - API REST de paraderos del SITP en Python
# ===================================================================
# QUE HACE ESTE ARCHIVO:
# Consulta los paraderos del SITP y los expone como API REST.
#
# IMPORTANTE: TODO el codigo esta en este unico archivo .py
# No hay ningun .html, ni .css, ni .javascript suelto por ahi.
# El formulario y la tabla los arma ESTE PROGRAMA en Python, con
# una sola cadena de texto.
#
# RUTAS (endpoints):
#   GET  /                 La pagina web (el HTML lo construye Python)
#   GET  /api/paraderos     Los paraderos de una localidad (el dato)
#   GET  /api/localidades   Las localidades que existen de verdad
#   GET  /api/salud         Estado de la API y del servicio de Catastro
#   GET  /docs              Documentacion interactiva que da FastAPI solo
#
# COMO EJECUTARLO:
#   1) Activar el entorno virtual:   .\.venv\Scripts\Activate.ps1
#   2) Instalar lo necesario:       pip install -r requirements.txt
#   3) Levantar el servidor:        python -m uvicorn main:app --reload
#   4) Abrir en el navegador:       http://localhost:8001/
# ===================================================================

# -------------------------------------------------------------------------
# SECCION 1: LAS HERRAMIENTAS QUE SE USAN
# -------------------------------------------------------------------------
# En Python NO se programan todas las cosas desde cero. Se usan
# librerias: archivos de codigo que ya escribio otra persona y que uno
# simplemente llama con una linea.
#
#   httpx   -> la libreria que se encarga de hablar por HTTP.
#   fastapi -> el "motor" que recibe las peticiones web y devuelve
#              respuestas, ademas de generar la documentacion.
#
# Estas librerias se instalan aparte con "pip install". Por eso al
# final esta el archivo requirements.txt, que las lista todas.
# -------------------------------------------------------------------------

import re

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse

# -------------------------------------------------------------------------
# SECCION 2: CONFIGURACION
# -------------------------------------------------------------------------

# El endpoint ArcGIS: la capa 8 de Mapa_Referencia = "Paraderos Zonales SITP".
URL = (
    "https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services/"
    "Mapa_Referencia/Mapa_Referencia/MapServer/8/query"
)

# Segundos maximos de espera antes de cancelar la peticion.
TIMEOUT = 20

# -------------------------------------------------------------------------
# SECCION 3: LA FUNCION QUE CONSUME LA API
# -------------------------------------------------------------------------
# Aqui esta el corazon del proyecto: la funcion que le pide los
# paraderos al servicio de Catastro y los devuelve como una lista
# de diccionarios de Python. El recorrido se documenta paso a paso:
# -------------------------------------------------------------------------


async def consultar(localidad):
    # 1) Construir la URL con el filtro 'where'.
    #   La diferencia es que aqui NO se arma la URL a mano: se le dan los
    #   parametros sueltos en "params" y httpx los junta y los escapa.
    #   Eso evita el problema de los espacios y las tildes.
    #
    #   El f"..." permite meter el valor de la localidad dentro del texto
    #   {localidad.strip().upper()}, sin tener que pegarlo a mano.
    #
    #   OJO: .upper() SI convierte las vocales acentuadas
    #   (engativa -> ENGATIVA). El filtro exige exactamente ese formato.
    params = {
        "where": f"UPPER(LOCALIDAD)='{localidad.strip().upper()}'",
        "outFields": "NOMBRE,LOCALIDAD,DIRECCION_,LATITUD,LONGITUD,CENEFA",
        "f": "geojson",
    }

    # 2) La conexion y la llamada.
    #   "async with" abre el cliente, lo usa y lo cierra solo.
    #   "await" significa "espera aqui". Como el servidor puede atender
    #   otras peticiones mientras espera, no se bloquea.
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as cliente:
            respuesta = await cliente.get(URL, params=params)
            respuesta.raise_for_status()
            # 3) Convertir el JSON a una estructura de datos de Python.
            #   .json() devuelve directamente el diccionario de la respuesta.
            datos = respuesta.json()
    except httpx.TimeoutException:
        # El caso de "no se pudo conectar con la API".
        raise HTTPException(
            status_code=503,
            detail="El servicio de Catastro Bogota tardo demasiado en responder.",
        )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=503,
            detail="No se pudo conectar con el servicio de Catastro Bogota.",
        )

    # 4) Extraer la lista de paraderos.
    #   Aqui se usa una "list comprehension": una forma corta de armar
    #   una lista con lo que hay entre corchetes.
    #   .get("NOMBRE") es seguro: si el campo no existe en la respuesta
    #   devuelve None en vez de romper el programa.
    return [
        {
            "CENEFA": f["properties"].get("CENEFA"),
            "NOMBRE": f["properties"].get("NOMBRE"),
            "DIRECCION_": f["properties"].get("DIRECCION_"),
            "LOCALIDAD": f["properties"].get("LOCALIDAD"),
            "LATITUD": f["properties"].get("LATITUD"),
            "LONGITUD": f["properties"].get("LONGITUD"),
        }
        for f in datos.get("features", [])
    ]


async def contar(localidad):
    """Cuenta cuantos paraderos hay sin descargarlos.

    returnCountOnly=true le pregunta al servicio "¿cuantos hay?" y el
    responde solo {"count": 829}. Es una consulta muy barata, por eso
    sirve para mostrar el total real y no inventar un numero.
    """
    params = {
        "where": f"UPPER(LOCALIDAD)='{localidad.strip().upper()}'",
        "returnCountOnly": "true",
        "f": "json",
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as cliente:
            respuesta = await cliente.get(URL, params=params)
            datos = respuesta.json()
    except httpx.HTTPError:
        return None
    return datos.get("count")


async def listar_localidades():
    """Las localidades que existen de verdad en la base de datos.

    Se le preguntan al servicio con returnDistinctValues, en vez de
    escribir una lista a mano en el codigo. Si Catastro renombra o
    agrega una localidad, esta lista se actualiza sola.
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as cliente:
            respuesta = await cliente.get(
                URL,
                params={
                    "where": "1=1",
                    "outFields": "LOCALIDAD",
                    "returnDistinctValues": "true",
                    "returnGeometry": "false",
                    "f": "json",
                },
            )
            datos = respuesta.json()
    except httpx.HTTPError:
        return []

    # Con f=json los valores vienen en "attributes" (no en "properties"
    # como en geojson, que es una diferencia molesta de ArcGIS).
    nombres = {
        f.get("attributes", {}).get("LOCALIDAD")
        for f in datos.get("features", [])
    }
    nombres.discard(None)
    return sorted(nombres)


# -------------------------------------------------------------------------
# SECCION 4: VALIDACION DE LO QUE ENTRA
# -------------------------------------------------------------------------
# La validacion se hace ANTES de armar el filtro, y se hace con una
# expresion regular: solo deja pasar letras (con o sin tilde), espacios
# y numeros. Asi una comilla o un parentesis del usuario nunca llega a
# la consulta del ArcGIS. Es la barrera de seguridad contra inyeccion
# de codigo SQL.
# -------------------------------------------------------------------------

PERMITIDO = re.compile(r"^[A-Za-zÁÉÍÓÚÑÜáéíóúñü0-9 ]+$")


def validar(localidad):
    """Revisa la localidad. Devuelve HTTP 400 si no es aceptable."""
    if not localidad.strip():
        raise HTTPException(
            status_code=400,
            detail="Escribe el nombre de una localidad para consultar.",
        )
    if not PERMITIDO.match(localidad):
        raise HTTPException(
            status_code=400,
            detail=(
                "La localidad solo puede llevar letras, espacios y numeros. "
                "Ojo: la API compara con tildes, escribe por ejemplo Engativá."
            ),
        )
    return localidad.strip()


# -------------------------------------------------------------------------
# SECCION 5: LA PAGINA WEB, ARMADA EN PYTHON
# -------------------------------------------------------------------------
# Esta es la parte que reemplaza al index.html. En vez de tener un archivo
# HTML aparte, el programa guarda el HTML en una cadena de texto y la
# entrega completa, con la tabla ya rellena.
#
# El HTML se devuelve completo, ya con la tabla rellena.
#
# Ojo con las tres comillas: permiten escribir texto de varias lineas sin
# tener que poner comillas en cada renglon.
#
# Los {llaves} que se ven en el texto NO son codigo Python: son los
# huecos que despues se rellenan con .format(). Para que Python no los
# interprete como llaves de codigo, se le antepone un { a cada uno.
# -------------------------------------------------------------------------

CSS = """
        /* Todo el ancho y alto, para que el padding no suma de mas */
        * { box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
            margin: 0;
            padding: 0 0 40px 0;
            background: linear-gradient(180deg, #eef4f8 0%, #e3ebf2 100%);
            color: #1f2933;
            -webkit-font-smoothing: antialiased;
        }

        /* Encabezado: degradado turquesa y sombra suave */
        header {
            background: linear-gradient(135deg, #0e7490 0%, #1193b5 100%);
            color: #ffffff;
            padding: 30px 20px 34px 20px;
            text-align: center;
            box-shadow: 0 4px 18px rgba(14, 116, 144, 0.28);
        }
        header h1 {
            margin: 0;
            font-size: 27px;
            font-weight: 600;
            letter-spacing: -0.3px;
        }

        /* La tarjeta blanca que contiene todo */
        main {
            max-width: 1120px;
            margin: -18px auto 0 auto;
            padding: 0 18px;
        }
        .tarjeta {
            background: #ffffff;
            border-radius: 14px;
            box-shadow: 0 10px 32px rgba(15, 40, 60, 0.12);
            padding: 28px;
        }

        /* Formulario */
        form {
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
            padding-bottom: 24px;
            margin-bottom: 24px;
            border-bottom: 1px solid #e6edf3;
        }
        form label {
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.7px;
            text-transform: uppercase;
            color: #52606d;
            width: 100%;
            margin-bottom: -4px;
        }
        form input[type="text"] {
            flex: 1;
            min-width: 240px;
            padding: 12px 14px;
            border: 1px solid #cbd7e2;
            border-radius: 8px;
            font-size: 15px;
            color: #1f2933;
            transition: border-color 0.15s, box-shadow 0.15s;
        }
        form input[type="text"]:focus {
            outline: none;
            border-color: #0e7490;
            box-shadow: 0 0 0 3px rgba(14, 116, 144, 0.18);
        }
        form button {
            padding: 12px 30px;
            background: linear-gradient(135deg, #0e7490 0%, #1193b5 100%);
            color: #ffffff;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(14, 116, 144, 0.32);
            transition: transform 0.12s, box-shadow 0.12s;
        }
        form button:hover {
            transform: translateY(-1px);
            box-shadow: 0 7px 18px rgba(14, 116, 144, 0.42);
        }

        /* Mensajes: fondo claro y una franja de color a la izquierda */
        .aviso {
            padding: 14px 18px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 15px;
            border-left: 5px solid;
            background: #f8fafc;
        }
        .ok     { border-color: #16a34a; background: #f0fdf4; color: #14532d; }
        .info   { border-color: #ea580c; background: #fff7ed; color: #7c2d12; }
        .error  { border-color: #dc2626; background: #fef2f2; color: #7f1d1d; }
        .conteo {
            display: inline-block;
            background: #0e7490;
            color: #ffffff;
            font-size: 13px;
            font-weight: 700;
            padding: 2px 10px;
            border-radius: 999px;
            margin-right: 6px;
            vertical-align: 1px;
        }

        /* Tabla: contenedor con scroll propio */
        .tabla-caja {
            max-height: 520px;
            overflow: auto;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
            background: #ffffff;
            box-shadow: 0 2px 10px rgba(15, 40, 60, 0.07);
        }
        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        table thead th {
            background: #0e7490;
            color: #ffffff;
            padding: 13px 14px;
            text-align: left;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.6px;
            text-transform: uppercase;
            position: sticky;
            top: 0;
            box-shadow: inset 0 -1px 0 rgba(255, 255, 255, 0.18);
        }
        table tbody td {
            padding: 11px 14px;
            border-bottom: 1px solid #eef2f6;
            color: #33414f;
        }
        table tbody tr:nth-child(even) { background: #f8fafc; }
        table tbody tr:hover { background: #e6f4fa; }
        table tbody tr:last-child td { border-bottom: none; }
"""

# La "plantilla" de la pagina. Los {llaves} son huecos que se rellenan
# despues con .format(...).
PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Paraderos SITP</title>
    <style>{css}</style>
</head>
<body>
    <header>
        <h1>Paraderos del SITP en Bogota</h1>
    </header>

    <main>
        <div class="tarjeta">
            <form method="get" action="/">
                <label for="localidad">Localidad de Bogota</label>
                <input type="text" id="localidad" name="localidad" list="localidades"
                       placeholder="Ej: Suba, Kennedy, Chapinero"
                       value="{localidad}" autofocus>
                <datalist id="localidades">{opciones}</datalist>
                <button type="submit">Consultar</button>
            </form>

            {mensaje}
            {tabla}
        </div>
    </main>
</body>
</html>
"""


def escapar(texto):
    """Escapa los caracteres especiales del HTML.

    El dato del ArcGIS se mete dentro del HTML que este programa
    construye. Sin esta proteccion, un paradero llamado "<b>x"
    deformaria la pagina. Por eso se cambian los caracteres por sus
    equivalentes &lt; &gt; &amp; antes de mostrarlos.
    """
    return (
        str(texto)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def construir_tabla(paraderos):
    """Arma el <table> con una fila por paradero.

    Se usa un for de Python y las filas se acumulan en una lista,
    que al final se unen en una sola cadena.
    """
    if not paraderos:
        return ""

    filas = []
    for p in paraderos:
        # escapar() en cada campo: por si el nombre trae algo raro.
        filas.append(
            "<tr>"
            f"<td>{escapar(p.get('CENEFA'))}</td>"
            f"<td>{escapar(p.get('NOMBRE'))}</td>"
            f"<td>{escapar(p.get('DIRECCION_'))}</td>"
            f"<td>{escapar(p.get('LATITUD'))}</td>"
            f"<td>{escapar(p.get('LONGITUD'))}</td>"
            "</tr>"
        )

    return (
        '<div class="tabla-caja"><table>'
        "<thead><tr>"
        "<th>Codigo</th>"
        "<th>Nombre del paradero</th>"
        "<th>Direccion / ubicacion</th>"
        "<th>Latitud</th>"
        "<th>Longitud</th>"
        "</tr></thead>"
        f"<tbody>{''.join(filas)}</tbody>"
        "</table></div>"
    )


def construir_pagina(localidad, mensaje, tabla, localidades):
    """Junta el CSS, el mensaje y la tabla en una sola pagina."""
    opciones = "".join(
        f"<option value=\"{escapar(nombre)}\"></option>"
        for nombre in localidades
    )
    return PLANTILLA.format(
        css=CSS,
        localidad=escapar(localidad or ""),
        opciones=opciones,
        mensaje=mensaje,
        tabla=tabla,
    )


# -------------------------------------------------------------------------
# SECCION 6: LA API
# -------------------------------------------------------------------------
# FastAPI es el "motor". El decorador @app.get(...) le dice:
# "cuando alguien pida esta direccion, ejecuta la funcion de abajo".
# Asi el programa sabe que funcion ejecutar segun la direccion pida.
# -------------------------------------------------------------------------

app = FastAPI(
    title="API Paraderos SITP Bogota",
    description=(
        "Consulta los paraderos del SITP de Bogota (servicio ArcGIS de "
        "Catastro Bogota) filtrando por localidad."
    ),
    version="1.0.0",
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def pagina(localidad: str = Query(None, description="Localidad a consultar")):
    """La pagina web. Construye el HTML en Python.

    - Si no llega "localidad", solo muestra el formulario vacio.
    - Si llega, busca los paraderos y muestra el resultado o el error.
    """
    localidades = await listar_localidades()
    mensaje = ""
    tabla = ""

    if localidad is None or not localidad.strip():
        #Todavia no se ha consultado nada.
        return construir_pagina("", "", "", localidades)

    # Validar() puede lanzar HTTPException, que se muestra como error.
    localidad = validar(localidad)

    try:
        total = await contar(localidad)
        paraderos = await consultar(localidad)
    except HTTPException as error:
        # El servicio de Catastro fallo: se avisa sin breaking nada.
        mensaje = f'<p class="aviso error">{escapar(error.detail)}</p>'
        return construir_pagina(localidad, mensaje, "", localidades)

    if not paraderos:
        # La localidad esta bien escrita pero no tiene paraderos.
        mensaje = (
            f'<p class="aviso info">No se encontraron paraderos del SITP en '
            f'"{escapar(localidad)}". Revisa el nombre o elige una de las '
            f"localidades de la lista.</p>"
        )
    else:
        mensaje = (
            f'<p class="aviso ok"><span class="conteo">{total}</span>'
            f'paraderos del SITP encontrados en la localidad '
            f'"{escapar(localidad)}".</p>'
        )
        tabla = construir_tabla(paraderos)

    return construir_pagina(localidad, mensaje, tabla, localidades)


@app.get("/api/paraderos", tags=["consulta"])
async def api_paraderos(
    # Asi se declara un parametro de la URL. FastAPI lo lee solo, lo
    # convierte al tipo que dice y si viene algo mal responde 422 sin
    # escribir una linea de validacion.
    localidad: str = Query(..., description="Localidad. Ejemplo: Suba, Kennedy"),
    limite: int = Query(
        100, ge=1, le=1000,
        description="Cuantos paraderos devolver (maximo 1000)",
    ),
    offset: int = Query(0, ge=0, description="Desde cual paradero empezar"),
):
    """Devuelve los paraderos de una localidad, en formato JSON."""
    localidad = validar(localidad)

    # Primero el total (consulta rapida) y despues los paraderos.
    total = await contar(localidad)
    paraderos = await consultar(localidad)

    # El caso de "no se encontraron paraderos". No es un error, es una
    # localidad mal escrita, asi que se responde 200 con la lista vacia
    # y un mensaje util.
    if not paraderos:
        return {
            "localidad": localidad,
            "total": total,
            "devueltos": 0,
            "paraderos": [],
            "mensaje": (
                f"No se encontraron paraderos del SITP en \"{localidad}\". "
                f"Revisa el nombre o consulta /api/localidades."
            ),
        }

    # Se aplica el limite y el offset (la paginacion).
    # OJO: primero se recorta el arreglo y DESPUES se cuenta, porque si
    # se contara antes "devueltos" diria siempre el total de la localidad.
    paraderos = paraderos[offset : offset + limite]

    return {
        "localidad": localidad,
        "total": total,
        "devueltos": len(paraderos),
        "paraderos": paraderos,
    }


@app.get("/api/localidades", tags=["consulta"])
async def api_localidades():
    """Las localidades que existen de verdad en la base de datos."""
    return await listar_localidades()


@app.get("/api/salud", tags=["sistema"])
async def api_salud():
    """Comprueba que la API responde Y que el servicio de Catastro
    tambien. Hace una consulta real de 2 paraderos, para no mentir."""
    try:
        paraderos = await consultar("Suba")
    except HTTPException as error:
        return JSONResponse(
            status_code=503,
            content={
                "estado": "degradado",
                "detalle": error.detail,
            },
        )

    return {
        "estado": "ok",
        "servicio": "Catastro Bogota (capa 8 de Mapa_Referencia)",
        "detalle": f"API y servicio funcionando. Prueba con Suba: {len(paraderos)} paraderos.",
    }
