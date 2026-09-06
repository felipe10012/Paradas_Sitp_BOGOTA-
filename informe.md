# Informe - Consumo de API REST publica desde PHP

**Proyecto Paradas SITP**

## Endpoint utilizado

Se consumio el servicio REST tipo **ArcGIS** llamado **"Paraderos Zonales SITP"**, publicado por Catastro Bogota (capa 8 del mapa `Mapa_Referencia`):

```
https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services/Mapa_Referencia/Mapa_Referencia/MapServer/8/query
```

La consulta se construye con parametros:

| Parametro | Valor usado | Que hace |
|---|---|---|
| `where` | `UPPER(LOCALIDAD)='KENNEDY'` | Filtra los paraderos por localidad. El valor se envia en **mayusculas** porque asi lo exige la API. |
| `outFields` | `NOMBRE,LOCALIDAD,DIRECCION_,LATITUD,LONGITUD,CENEFA` | Campos que se desean recibir por cada paradero. |
| `f` | `geojson` | Formato de respuesta GeoJSON. |

## Datos obtenidos

La API responde en **formato GeoJSON**: un objeto `FeatureCollection` cuyo arreglo `features` contiene un elemento por paradero, con sus coordenadas (punto) y sus atributos. De cada paradero se obtuvo:

- **CENEFA**: codigo identificador del paradero.
- **NOMBRE**: nombre del paradero (ej.: "Pq. Alto de los Lagartos").
- **DIRECCION_**: direccion o cruce aproximado (ej.: "AV. Boyaca - AC 127").
- **LATITUD** y **LONGITUD**: coordenadas geograficas.
- **LOCALIDAD**: localidad a la que pertenece.

Por ejemplo, la consulta para la localidad **Kennedy** devolvio alrededor de **896 paraderos**, y para **Suba** unos **829**. La pagina los presenta en una tabla HTML con codigo, nombre, direccion y coordenadas, e incluye manejo de errores:

- si la API no responde,
- si no hay resultados,
- si la localidad no existe o esta mal escrita.

## Nota

El servicio de paraderos puede volverse lento o responder vacio en momentos de carga alta (es una consideracion indicada en el propio enunciado de la actividad). En esos casos basta con reintentar la consulta, y la pagina muestra un mensaje amigable en lugar de un error de PHP.