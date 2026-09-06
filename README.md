# Proyecto Paradas SITP

Consumo de una **API REST publica** desde PHP. Una pagina web dinamica que consulta los **paraderos del SITP de Bogota** (servicio ArcGIS/GeoJSON de Catastro Bogota), los filtra por localidad y los muestra en una tabla estilizada.

Actividad de aprendizaje: **Consumo de una API REST publica desde PHP** (ADSI).

## Contenido

```
proyecto-paradas-sitp/
|-- paraderos_sitp.php   # Pagina funcional (codigo muy comentado)
`-- informe.md           # Breve informe del endpoint y los datos obtenidos
```

## Como ejecutarlo

1. Tener **PHP 8+ instalado** con la extension **OpenSSL** habilitada (en `php.ini`, la linea `extension=openssl` sin el `;`). Sin OpenSSL PHP no puede conectarse por HTTPS.
2. En la carpeta del proyecto ejecutar:
   ```
   php -S localhost:8000
   ```
3. Abrir en el navegador:
   ```
   http://localhost:8000/paraderos_sitp.php
   ```
4. Escribir una localidad (ej: `Suba`, `Kennedy`, `Chapinero`) y pulsar **Consultar**.

## Como funciona (flujo)

1. El formulario envia la **localidad** por GET al mismo archivo.
2. PHP **valida** el dato (vacio, caracteres peligrosos).
3. PHP **construye la URL** del servicio REST con el filtro `where`.
4. PHP **llama a la API** con `file_get_contents()` (contexto con timeout).
5. PHP **decodifica** el JSON devuelto con `json_decode()`.
6. PHP **recorre** los resultados con `foreach` y arma una tabla HTML.
7. El navegador recibe **solo HTML** (el PHP ya se ejecuto en el servidor).

## Endpoint utilizado

| Elemento | Valor |
|---|---|
| Servicio | Paraderos Zonales SITP (capa 8 de `Mapa_Referencia`) |
| URL | `https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services/Mapa_Referencia/Mapa_Referencia/MapServer/8/query` |
| Filtro | `where=UPPER(LOCALIDAD)='SUBA'` (en mayusculas y con tildes) |
| Campos | `outFields=NOMBRE,LOCALIDAD,DIRECCION_,LATITUD,LONGITUD,CENEFA` |
| Formato | `f=geojson` |

Cada paradero devuelve: **CENEFA** (codigo), **NOMBRE**, **DIRECCION_**, **LOCALIDAD**, **LATITUD** y **LONGITUD**.

## Datos de ejemplo

| Codigo | Nombre | Direccion | Latitud | Longitud |
|---|---|---|---|---|
| 003A03 | Pq. Alto de los Lagartos | AV. Boyaca - AC 127 | 4.709208 | -74.080583 |
| 013A02 | Gimnasio Iragua | AV. Boyaca - AC 170 | 4.759866 | -74.066350 |

La localidad **Kennedy** devolvio, por ejemplo, alrededor de **896 paraderos**; **Suba** unos **829**.

## Manejo de errores implementado

- **API no responde** (`file_get_contents` devuelve `false`) -> mensaje amigable.
- **Sin resultados** o **localidad mal escrita / inexistente** -> aviso sin romper la pagina.
- **Formulario vacio** -> pide escribir una localidad.
- **Seguridad**: `strip_tags()`, `htmlspecialchars()` y `urlencode()`.

## En que otros casos sirve este codigo?

Es una plantilla reutilizable para consumir **cualquier API REST publica**:

- APIs JSON de clima (**Open-Meteo**), paises (**REST Countries**), transporte, datos abiertos.
- Servicios **ArcGIS/GeoJSON** (consulta de capas, filtros `where`).
- Busquedas con formulario donde se pasa un parametro y se muestran resultados en tabla.

Solo cambian la URL, el filtro y las columnas de la tabla; la logica del consumo (`file_get_contents` + `json_decode` + `foreach`) se mantiene igual.