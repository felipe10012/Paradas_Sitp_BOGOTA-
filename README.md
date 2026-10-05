# Proyecto Paradas SITP

Consumo de una **API REST pública** desde **Python**. Una API que consulta los
**paraderos del SITP de Bogotá** (servicio ArcGIS/GeoJSON de Catastro Bogotá), los
filtra por localidad y los devuelve en JSON, además de un formulario web que el propio
servidor construye en Python.

Actividad de aprendizaje: **Consumo de una API REST pública desde Python** (ADSO).

## Contenido

```
Proyecto-Paradas-SITP-Bogota/
|-- main.py             # API completa (FastAPI): consulta, validación, HTML y endpoints
|-- iniciar.py          # Levanta el servidor y abre el navegador
|-- requirements.txt    # Las librerías necesarias
`-- informe.md          # Informe breve del endpoint y los datos obtenidos
```

Todo el proyecto está escrito en Python. No hay archivos HTML, CSS ni JavaScript
sueltos: el HTML y el CSS se guardan como cadenas de texto dentro de `main.py`.

## Cómo ejecutarlo

1. Crear el entorno virtual (solo la primera vez):
   ```
   python -m venv .venv
   ```
2. Activarlo:
   ```
   .\.venv\Scripts\Activate.ps1
   ```
3. Instalar lo necesario (solo la primera vez):
   ```
   pip install -r requirements.txt
   ```
4. Levantar el servidor de dos maneras:
   ```
   python iniciar.py
   ```
   o directamente:
   ```
   python -m uvicorn main:app --reload --port 8001
   ```
5. Se abre solo en el navegador, o/entra a mano en:
   ```
   http://localhost:8001/
   ```
6. Escribir una localidad (ej: `Suba`, `Kennedy`, `Chapinero`) y pulsar **Consultar**.

## Cómo funciona (flujo)

1. El formulario envía la **localidad** por GET a la ruta `/`.
2. FastAPI **recibe** el dato y llama a `validar()`, que lo revisa con una expresión
   regular (solo letras, espacios y números).
3. `consultar()` **arma la URL** del servicio con el filtro `where` usando el
   diccionario `params`, y `httpx` la escapa por ella.
4. Se **llama a la API** de forma asíncrona, con un tiempo máximo de espera.
5. La respuesta se **convierte a diccionario** con `.json()`.
6. Se **recorre** el resultado con una *list comprehension* y se queda solo con los
   campos pedidos.
7. `construir_tabla()` **arma el HTML** y el servidor lo entrega completo, ya con la
   tabla rellena. El navegador no ejecuta JavaScript.

## Endpoints

| Método | Ruta | Qué devuelve |
|---|---|---|
| GET | `/` | La página web con el formulario y los resultados. |
| GET | `/api/paraderos?localidad=Suba` | Los paraderos de una localidad, en JSON. Admite `limite` y `offset`. |
| GET | `/api/localidades` | Las localidades que existen de verdad en el servicio. |
| GET | `/api/salud` | Estado de la API y del servicio de Catastro. |
| GET | `/docs` | Documentación interactiva que genera FastAPI. |

## Endpoint que se consume

| Elemento | Valor |
|---|---|
| Servicio | Paraderos Zonales SITP (capa 8 de `Mapa_Referencia`) |
| URL | `https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services/Mapa_Referencia/Mapa_Referencia/MapServer/8/query` |
| Filtro | `where=UPPER(LOCALIDAD)='SUBA'` (en mayúsculas y con tildes) |
| Campos | `outFields=NOMBRE,LOCALIDAD,DIRECCION_,LATITUD,LONGITUD,CENEFA` |
| Formato | `f=geojson` |

Cada paradero devuelve: **CENEFA** (código), **NOMBRE**, **DIRECCION_**, **LOCALIDAD**,
**LATITUD** y **LONGITUD**.

## Datos de ejemplo

| Código | Nombre | Dirección | Latitud | Longitud |
|---|---|---|---|---|
| 003A03 | Pq. Alto de los Lagartos | AV. Boyaca - AC 127 | 4.709208 | -74.080583 |
| 013A02 | Gimnasio Iragua | AV. Boyaca - AC 170 | 4.759866 | -74.066350 |

La localidad **Kennedy** devolvió, por ejemplo, **896 paraderos**; **Suba**, **829**.

## Manejo de errores implementado

- **El servicio no responde** → mensaje amigable, código `503`.
- **El servicio tarda demasiado** → mensaje amigable, código `503`.
- **Formulario vacío** → `400`, pide escribir una localidad.
- **Caracteres peligrosos** (comillas, paréntesis, operadores) → `400`. Es la barrera
  contra inyección de código.
- **`limite` fuera de 1 a 1000 u `offset` negativo** → `422`, lo detecta FastAPI solo.
- **Sin resultados o localidad mal escrita** → `200` con lista vacía y un mensaje que
  sugiere revisar el nombre.
- **Seguridad en las dos direcciones**: la entrada se valida con `validar()` y la salida
  se escapa con `escapar()`.

## En qué otros casos sirve este código

Es una plantilla reutilizable para consumir **cualquier API REST pública**:

- APIs JSON de clima (**Open-Meteo**), países (**REST Countries**), transporte, datos
  abiertos.
- Servicios **ArcGIS/GeoJSON** (consulta de capas, filtros `where`).
- Búsquedas con formulario donde se pasa un parámetro y se muestran resultados en tabla.

Solo cambian la URL, el filtro y las columnas; la lógica del consumo
(`params` + `httpx` + `.json()` + list comprehension) se mantiene igual.