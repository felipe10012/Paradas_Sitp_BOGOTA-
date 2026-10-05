# Informe - Consumo de API REST pública desde Python

**Proyecto Paradas SITP**

## Endpoint utilizado

Se consumió el servicio REST tipo **ArcGIS** llamado **"Paraderos Zonales SITP"**,
publicado por Catastro Bogotá (capa 8 del mapa `Mapa_Referencia`):

```
https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services/Mapa_Referencia/Mapa_Referencia/MapServer/8/query
```

La consulta se construye con parámetros:

| Parámetro | Valor usado | Qué hace |
|---|---|---|
| `where` | `UPPER(LOCALIDAD)='KENNEDY'` | Filtra los paraderos por localidad. El valor se envía en **mayúsculas** y con **tildes exactas** porque así lo exige la API. |
| `outFields` | `NOMBRE,LOCALIDAD,DIRECCION_,LATITUD,LONGITUD,CENEFA` | Campos que se desean recibir por cada paradero. |
| `returnCountOnly` | `true` | No devuelve datos, solo cuántos hay. Se usa para mostrar el total real. |
| `returnDistinctValues` | `true` | Se usa para listar las localidades sin repetirlas. |
| `f` | `geojson` | Formato de respuesta. |

## Datos obtenidos

La API responde en **formato GeoJSON**: un objeto `FeatureCollection` cuyo arreglo
`features` contiene un elemento por paradero, con sus coordenadas (punto) y sus
atributos. De cada paradero se obtuvo:

- **CENEFA**: código identificador del paradero.
- **NOMBRE**: nombre del paradero (ej.: "Pq. Alto de los Lagartos").
- **DIRECCION_**: dirección o cruce aproximado (ej.: "AV. Boyaca - AC 127").
- **LATITUD** y **LONGITUD**: coordenadas geográficas.
- **LOCALIDAD**: localidad a la que pertenece.

Por ejemplo, la consulta para la localidad **Kennedy** devolvió **896 paraderos**, y para
**Suba**, **829**.

## Endpoints expuestos

| Método | Ruta | Qué devuelve |
|---|---|---|
| GET | `/` | La página web con el formulario y los resultados. |
| GET | `/api/paraderos` | Los paraderos de una localidad, en JSON. Admite `limite` y `offset`. |
| GET | `/api/localidades` | Las localidades que existen de verdad en el servicio. |
| GET | `/api/salud` | Estado de la API y del servicio de Catastro. |
| GET | `/docs` | Documentación interactiva que genera FastAPI. |

## Manejo de errores

- Si la API no responde o tarda demasiado: `503` con mensaje amigable.
- Si el formulario viene vacío: `400`.
- Si el dato trae caracteres peligrosos: `400`. Es la barrera contra inyección de código.
- Si `limite` está fuera de rango o `offset` es negativo: `422`.
- Si la localidad no existe o está mal escrita: `200` con lista vacía y un mensaje útil.
- Seguridad en las dos direcciones: la entrada se valida con `validar()` y la salida se
  escapa con `escapar()`.

## Nota

El servicio de paraderos puede volverse lento o responder vacío en momentos de carga
alta. En esos casos basta con reintentar la consulta, y la API muestra un mensaje
amigable en lugar de un error técnico.

## Totales por localidad

| Localidad | Paraderos | Localidad | Paraderos |
|---|---|---|---|
| Kennedy | 896 | Rafael Uribe | 299 |
| Suba | 829 | Teusaquillo | 255 |
| Engativá | 781 | Santa Fe | 212 |
| Usaquén | 705 | Barrios Unidos | 208 |
| Ciudad Bolívar | 590 | Tunjuelito | 195 |
| Bosa | 485 | Los Mártires | 156 |
| Fontibón | 425 | Antonio Nariño | 105 |
| San Cristóbal | 424 | Candelaria | 29 |
| Puente Aranda | 366 | | |
| Usme | 345 | | |
| Chapinero | 318 | **TOTAL** | **7623** |

19 localidades en total.