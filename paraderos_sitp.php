<?php
/* ===================================================================
   PROYECTO PARADAS SITP - Consumo de una API REST publica desde PHP
   ===================================================================
   QUE HACE:
   Pagina web dinamica en PHP que consume un servicio REST publico
   (ArcGIS/GeoJSON) con los paraderos del SITP de Bogota, filtra por
   localidad y muestra los resultados en una tabla HTML estilizada.

   PARA QUE SIRVE:
   Demuestra el flujo completo de consumo de una API:
     1. El usuario ingresa una localidad en un formulario.
     2. PHP construye la URL de la API con ese dato.
     3. PHP llama a la API con file_get_contents().
     4. PHP interpreta la respuesta JSON con json_decode().
     5. PHP recorre el arreglo con foreach y genera una tabla HTML.
     6. El navegador recibe solo HTML (el PHP ya se ejecuto en el servidor).

   EN QUE CASOS PUEDO USARLO:
   Sirve de base o plantilla para consumir CUALQUIER API REST publica:
   - Endpoints que devuelven GeoJSON (ArcGIS, OpenStreetMap, etc.).
   - APIs JSON de clima, paises, transporte, datos abiertos de gobierno.
   - Aplicaciones donde hay que filtrar datos por un parametro (aqui, la
     localidad) y mostrarlos como tabla.

   ENDPOINT UTILIZADO:
   https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services/
       Mapa_Referencia/Mapa_Referencia/MapServer/8/query
   Capa: "Paraderos Zonales SITP" (capa 8)
   Parametros: where (filtro), outFields (campos), f (formato geojson)

   COMO EJECUTARLO:
   Estando en la carpeta del archivo:
       php -S localhost:8000
   Luego abrir: http://localhost:8000/paraderos_sitp.php
   (Requiere PHP con la extension OpenSSL habilitada en php.ini.)
   =================================================================== */

// ---------------------------------------------------------------------
// SECCION 1: RECOGER EL DATO DEL FORMULARIO
// ---------------------------------------------------------------------
// El formulario envia la localidad por GET (mas abajo, en el HTML).
// isset() evita errores si aun no se ha enviado nada.
$localidad = isset($_GET['localidad']) ? $_GET['localidad'] : '';

// trim() quita espacios al inicio y final (" Suba " -> "Suba").
// strip_tags() elimina cualquier etiqueta HTML/script que el usuario
// pudiera escribir. Es una medida basica de seguridad contra inyeccion.
$localidad = trim(strip_tags($localidad));

// ---------------------------------------------------------------------
// SECCION 2: VARIABLE DE SALIDA
// ---------------------------------------------------------------------
// $mensaje acumula TODO lo que se mostrara en la zona de resultados:
// mensajes de error, avisos o la tabla completa de paraderos.
$mensaje = '';

// ---------------------------------------------------------------------
// SECCION 3: VALIDACION DEL DATO INGRESADO
// ---------------------------------------------------------------------
// Si el usuario envio el formulario pero dejo la localidad vacia,
// mostramos un aviso amigable en lugar de continuar con la consulta.
if ($_SERVER['REQUEST_METHOD'] === 'GET' && isset($_GET['localidad']) && $localidad === '') {
    $mensaje = '<p class="error">Escribe el nombre de una localidad para consultar.</p>';
}

// ---------------------------------------------------------------------
// SECCION 4: CONSUMO DE LA API
// ---------------------------------------------------------------------
// Solo consultamos si escribieron una localidad y no hay ya un error.
// La condicion $mensaje === '' evita consultar cuando ya mostramos aviso.
if ($localidad !== '' && $mensaje === '') {

    // 4.1 Construir la URL del servicio REST
    // La API espera un filtro estilo SQL en el parametro "where".
    // La API compara en MAYUSCULAS Y CON TILDES exactas (verificado:
    // 'ENGATIVÁ' coincide, pero 'ENGATIVá' o 'ENGATIVA' devuelven 0).
    // strtoupper() solo pone en mayuscula las letras SIN tilde, por eso
    // primero strtr() convierte las tildes a su letra mayuscula.
    // urlencode() codifica la URL para que tildes y espacios sean validos.
    $conversorTildes = ['á' => 'Á', 'é' => 'É', 'í' => 'Í', 'ó' => 'Ó', 'ú' => 'Ú', 'ñ' => 'Ñ', 'ü' => 'Ü'];
    $localidadConsulta = strtoupper(strtr($localidad, $conversorTildes));

    $url = 'https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services/'
         . 'Mapa_Referencia/Mapa_Referencia/MapServer/8/query'
         . '?where=' . urlencode("UPPER(LOCALIDAD)='" . $localidadConsulta . "'")
         . '&outFields=NOMBRE,LOCALIDAD,DIRECCION_,LATITUD,LONGITUD,CENEFA'
         . '&f=geojson';

    // 4.2 Contexto HTTP de la llamada
    // stream_context_create() permite configurar opciones de red:
    //   timeout => 15   -> esperar maximo 15 segundos por la respuesta.
    //   ignore_errors   -> no falla si la API devuelve errores HTTP.
    $contexto = stream_context_create([
        'http' => ['timeout' => 15, 'ignore_errors' => true]
    ]);

    // 4.3 Hacer la llamada a la API
    // file_get_contents() es la forma mas simple de consumo HTTP en PHP.
    // Devuelve el contenido (JSON) o "false" si la conexion falla.
    // El simbolo @ silencia los warnings de PHP (los manejamos nosotros).
    $respuesta = @file_get_contents($url, false, $contexto);

    // 4.4 Caso de error: la API no respondio
    // Si "false", mostramos un mensaje amigable. El usuario no deberia
    // ver jamas un error tecnico de PHP en pantalla (requisito 5 del
    // enunciado: manejo de errores).
    if ($respuesta === false) {
        $mensaje = '<p class="error">No se pudo conectar con el servicio de la API. Intentalo mas tarde.</p>';
    } else {

        // 4.5 Convertir el JSON en un arreglo de PHP
        // json_decode() con "true" devuelve arreglos asociativos en vez
        // de objetos. La estructura queda:
        //   [features] => [ 0 => [properties => [NOMBRE => ..., ...]] ]
        $datos = json_decode($respuesta, true);

        // 4.6 Extraer la lista de paraderos
        // El arreglo "features" del GeoJSON contiene un elemento por
        // paradero. Si la clave no existe, usamos un arreglo vacio.
        $paraderos = isset($datos['features']) ? $datos['features'] : [];

        // 4.7 Caso: sin resultados
        // Puede pasar si la localidad no existe o la API esta saturada.
        // Avisamos sin romper la pagina (la API es pesada y a veces
        // responde vacia; basta con reintentar).
        if (count($paraderos) === 0) {
            $mensaje = '<p class="info">No se encontraron paraderos del SITP para la localidad "'
                     . htmlspecialchars($localidad) .
                     '". Verifica si la escribiste bien o intentalo de nuevo.</p>';
        } else {
            // 4.8 Construir la tabla HTML
            // Empezamos con un mensaje resumen (cuantos se encontraron) y
            // abrimos la tabla. La clase "tabla-caja" anade scroll con CSS.
            $mensaje = '<p class="ok">Se encontraron ' . count($paraderos)
                     . ' paraderos en la localidad "' . htmlspecialchars($localidad) . '".</p>';
            $mensaje .= '<div class="tabla-caja"><table>';
            $mensaje .= '<thead><tr><th>Codigo</th><th>Nombre del paradero</th>'
                      . '<th>Direccion / ubicacion</th><th>Latitud</th><th>Longitud</th></tr></thead>';
            $mensaje .= '<tbody>';

            // 4.9 Recorrer cada paradero con foreach
            // Por cada elemento extraemos sus propiedades. El operador ??
            // (o isset) nos da un valor por defecto si el campo falta.
            foreach ($paraderos as $paradero) {
                $prop   = $paradero['properties'];
                $codigo = isset($prop['CENEFA']) ? $prop['CENEFA'] : '-';
                $nombre = isset($prop['NOMBRE']) ? $prop['NOMBRE'] : 'Sin nombre';
                $dir    = isset($prop['DIRECCION_']) ? $prop['DIRECCION_'] : '-';
                $lat    = isset($prop['LATITUD']) ? $prop['LATITUD'] : '-';
                $lon    = isset($prop['LONGITUD']) ? $prop['LONGITUD'] : '-';

                // htmlspecialchars() es clave en seguridad: convierte
                // caracteres como < > " a entidades HTML, evitando que un
                // dato de la API escape a HTML (XSS).
                $mensaje .= '<tr>';
                $mensaje .= '<td>' . htmlspecialchars($codigo) . '</td>';
                $mensaje .= '<td>' . htmlspecialchars($nombre) . '</td>';
                $mensaje .= '<td>' . htmlspecialchars($dir) . '</td>';
                $mensaje .= '<td>' . htmlspecialchars($lat) . '</td>';
                $mensaje .= '<td>' . htmlspecialchars($lon) . '</td>';
                $mensaje .= '</tr>';
            }

            // 4.10 Cierre de la tabla
            $mensaje .= '</tbody></table></div>';
        }
    }
}
?>

<!DOCTYPE html>
<!--
  A partir de aqui termina la logica PHP y empieza la presentacion HTML.
  El navegador recibe SOLO este HTML: el bloque PHP de arriba ya se
  ejecuto en el servidor. Por eso al inspeccionar la pagina no se ve PHP.
-->
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Paraderos SITP</title>

    <!-- CSS: colores, disposicion y estilos de la pagina.
         El CSS usa las etiquetas estructurales <header>, <main>,
         las filas de la tabla y las clases .error / .info / .ok. -->
    <style>
        /* Estilos generales */
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #f0f4f8;
            color: #1f2933;
        }

        /* Encabezado de la pagina */
        header {
            background: #0e7490;
            color: #ffffff;
            padding: 20px;
            text-align: center;
        }

        header h1 {
            margin: 0;
            font-size: 26px;
        }

        /* Contenedor principal (centra y limita el ancho) */
        main {
            max-width: 1100px;
            margin: 20px auto;
            padding: 0 15px;
        }

        /* Formulario */
        form {
            background: #ffffff;
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }

        form label {
            font-weight: bold;
        }

        form input[type="text"] {
            flex: 1;
            min-width: 220px;
            padding: 10px;
            border: 1px solid #bcccdc;
            border-radius: 6px;
            font-size: 15px;
        }

        form button {
            padding: 10px 22px;
            background: #0e7490;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            font-size: 15px;
            cursor: pointer;
        }

        form button:hover {
            background: #155e75;
        }

        /* Mensajes de error, aviso y exito */
        .error {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
            padding: 12px;
            border-radius: 6px;
        }

        .info {
            background: #ffedd5;
            color: #9a3412;
            border: 1px solid #fed7aa;
            padding: 12px;
            border-radius: 6px;
        }

        .ok {
            background: #dcfce7;
            color: #166534;
            border: 1px solid #bbf7d0;
            padding: 12px;
            border-radius: 6px;
        }

        /* Caja de la tabla: scroll vertical cuando hay muchos paraderos
           (algunas localidades superan los 800 registros). */
        .tabla-caja {
            max-height: 500px;
            overflow: auto;
            border-radius: 8px;
            border: 1px solid #d9e2ec;
            background: #ffffff;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }

        /* Encabezado fijo al hacer scroll */
        table thead th {
            background: #0e7490;
            color: #ffffff;
            padding: 10px;
            text-align: left;
            position: sticky;
            top: 0;
        }

        table tbody td {
            padding: 8px 10px;
            border-bottom: 1px solid #e4e7eb;
        }

        /* Filas alternadas para facilitar la lectura */
        table tbody tr:nth-child(even) {
            background: #f4f9fb;
        }

        table tbody tr:hover {
            background: #e0f2fe;
        }
    </style>
</head>
<body>
    <!-- Encabezado visual de la pagina -->
    <header>
        <h1>Paraderos del SITP en Bogota</h1>
    </header>

    <!-- Contenido principal -->
    <main>
        <!--
          Formulario de consulta. "method=get" envia los datos en la URL
          (...paraderos_sitp.php?localidad=Suba), que es lo que lee el
          PHP en $_GET. "action" apunta al mismo archivo.
        -->
        <form method="get" action="paraderos_sitp.php">
            <label for="localidad">Localidad de Bogota:</label>

            <!-- Campo de texto. "list" lo enlaza con el datalist siguiente.
                 El usuario puede escribir libremente (asi probamos el
                 manejo de errores) o elegir una sugerencia. -->
            <input type="text" id="localidad" name="localidad"
                   list="localidades" placeholder="Ej: Suba, Kennedy, Chapinero">

            <!-- Datalist: sugerencias de las 20 localidades de Bogota.
                 Es solo un asistente: no impide escribir otro valor.
                 NOTA: estas tildes se conservan a proposito porque la API
                 distingue mayusculas y tildes; por ejemplo, "USAQUEN"
                 (sin tilde) NO coincide y devuelve 0 resultados. -->
            <datalist id="localidades">
                <option value="Usaquén"><option value="Chapinero">
                <option value="Santa Fe"><option value="San Cristóbal">
                <option value="Usme"><option value="Tunjuelito">
                <option value="Bosa"><option value="Kennedy">
                <option value="Fontibón"><option value="Engativá">
                <option value="Suba"><option value="Barrios Unidos">
                <option value="Teusaquillo"><option value="Los Mártires">
                <option value="Antonio Nariño"><option value="Puente Aranda">
                <option value="La Candelaria"><option value="Rafael Uribe Uribe">
                <option value="Ciudad Bolívar"><option value="Sumapaz">
            </datalist>

            <button type="submit">Consultar</button>
        </form>

        <!-- Zona de resultados: aqui PHP imprime $mensaje con el error,
             el aviso sin resultados o la tabla de paraderos. -->
        <div id="resultado">
            <?php echo $mensaje; ?>
        </div>
    </main>
</body>
</html>