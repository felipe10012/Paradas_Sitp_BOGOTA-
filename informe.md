# Informe ÔÇö Consumo de API REST p├║blica desde PHP

**Proyecto Paradas SITP**

## Endpoint utilizado

Se consumi├│ el servicio REST tipo **ArcGIS** llamado **"Paraderos Zonales SITP"**, publicado por Catastro Bogot├í (capa 8 del mapa `Mapa_Referencia`):

```
https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services/Mapa_Referencia/Mapa_Referencia/MapServer/8/query
```

La consulta se construye con par├ímetros:

| Par├ímetro | Valor usado | Qu├® hace |
|---|---|---|
| `where` | `UPPER(LOCALIDAD)='KENNEDY'` | Filtra los paraderos por localidad. El valor se env├¡a en **may├║sculas** porque as├¡ lo exige la API. |
| `outFields` | `NOMBRE,LOCALIDAD,DIRECCION_,LATITUD,LONGITUD,CENEFA` | Campos que se desean recibir por cada paradero. |
| `f` | `geojson` | Formato de respuesta GeoJSON. |

## Datos obtenidos

La API responde en **formato GeoJSON**: un objeto `FeatureCollection` cuyo arreglo `features` contiene un elemento por paradero, con sus coordenadas (punto) y sus atributos. De cada paradero se obtuvo:

- **CENEFA**: c├│digo identificador del paradero.
- **NOMBRE**: nombre del paradero (ej.: "Pq. Alto de los Lagartos").
- **DIRECCION_**: direcci├│n o cruce aproximado (ej.: "AV. Boyac├í - AC 127").
- **LATITUD** y **LONGITUD**: coordenadas geogr├íficas.
- **LOCALIDAD**: localidad a la que pertenece.

Por ejemplo, la consulta para la localidad **Kennedy** devolvi├│ alrededor de **896 paraderos**, y para **Suba** unos **829**. La p├ígina los presenta en una tabla HTML con c├│digo, nombre, direcci├│n y coordenadas, e incluye manejo de errores:

- si la API no responde,
- si no hay resultados,
- si la localidad no existe o est├í mal escrita.

## Nota

El servicio de paraderos puede volverse lento o responder vac├¡o en momentos de carga alta (es una consideraci├│n indicada en el propio enunciado de la actividad). En esos casos basta con reintentar la consulta, y la p├ígina muestra un mensaje amigable en lugar de un error de PHP.
