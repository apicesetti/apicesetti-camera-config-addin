# Configuración de cámaras — add-in de MyGeotab

Add-in para ver la configuración de todas las cámaras Surfsight (GO Focus / AI-12) de una base de MyGeotab y detectar las que se apartan del estándar de la flota.

- Muestra la flota completa en un mosaico: una celda por cámara, en rojo las que tienen desvíos.
- Calcula el estándar de cada parámetro con el valor más común de la flota. Se puede ajustar a mano o dejar de controlar un parámetro.
- Lista cada diferencia de forma legible ("Grabación en cabina **No** en vez de Sí") y permite ver la configuración completa de cada cámara.
- Aplica el estándar en una o varias cámaras, con confirmación previa, y deja registro en la Auditoría de la base.
- Exporta a CSV la configuración de todas las cámaras visibles, con una fila de estándar.

Se probó en la base `tsbsa`.

## Instalación en una base

1. En MyGeotab: **Administración → Sistema → Configuración del sistema → Add-ins**.
2. **Nuevo add-in** y pegar el contenido de [`dist/config_addin_camaras.json`](dist/config_addin_camaras.json).
3. Guardar y recargar. Aparece en el menú de **Mantenimiento** como **Configuración de cámaras**.

Para actualizar una base que ya lo tiene, se reemplaza el contenido del add-in existente con el JSON nuevo.

## Por qué es un add-in embebido y no está en GitHub Pages

El add-in lee la configuración de las cámaras desde `media-services.geotab.com`, el mismo servicio que usa la pantalla de cámaras de MyGeotab. Ese servicio rechaza por CORS las llamadas que salen de otros dominios, incluido `github.io`. Por eso el HTML va **embebido** en el JSON de configuración y corre desde el dominio de MyGeotab.

GitHub se usa como repositorio del código; la instalación siempre es con el JSON de `dist/`.

## Cómo hacer cambios

1. Editar [`src/cameraConfig.html`](src/cameraConfig.html) (HTML, CSS y JS en un solo archivo).
2. Generar el JSON con la nueva versión:

   ```bash
   python build.py 1.2.0
   ```

   Sin argumento, usa la versión que figura en `VERSION`.
3. Commitear `src/`, `VERSION` y `dist/` juntos, e instalar el JSON nuevo en las bases.

El nombre de la función del add-in (`geotab.addin.cameraConfig`) tiene que coincidir con el nombre del archivo `cameraConfig.html`; `build.py` lo verifica.

## Cómo funciona por dentro

| Qué | Cómo |
|---|---|
| Sesión | `api.getSession(callback, false)` — el segundo parámetro es booleano, no un callback de error. |
| Autenticación con media-services | Headers `X-MyGeotab-Database`, `X-MyGeotab-Username`, `X-MyGeotab-SessionId` y `X-MyGeotab-Path` con los datos de la sesión. No hace falta token Bearer. |
| Lista de cámaras | `GET https://media-services.geotab.com/api/DeviceMappings` |
| Configuración de una cámara | `GET https://media-services.geotab.com/api/Surfsight/DeviceSettings/{imei}` |
| Cambio de configuración | `PATCH https://media-services.geotab.com/api/Surfsight/DeviceSettings` con `{"imeis":[...],"config":{"param":{"value":x}}}` |
| Vehículo de cada cámara | `Get Device` de la API de MyGeotab, cruzado por número de serie del GO. |
| Registro de cambios | `Add Audit` en la base, con vehículo, patente y parámetros cambiados. |

Las lecturas se hacen de a 6 cámaras en paralelo. En una base de unas 580 cámaras tarda alrededor de un minuto.

## Limitaciones conocidas

- **Solo cámaras Surfsight.** Las GO Focus Plus (proveedor `smarterai`) usan otro endpoint y no se incluyen; el add-in informa cuántas quedaron afuera.
- **Parámetros compuestos sin corrección automática.** Privacidad por cámara, standby, hotspot y cifrado se detectan como desvío, pero se corrigen desde la configuración de la cámara en MyGeotab: el formato del PATCH para esos parámetros no está verificado.
- **El estándar ajustado a mano queda en el navegador** (`localStorage`) de quien lo configura. No se comparte entre usuarios ni equipos. "Volver al valor de la mayoría" lo descarta.
- **Cámaras offline:** el cambio se envía igual y la cámara lo toma al conectarse. Hasta entonces puede seguir mostrando el valor anterior.
- **Permisos:** cualquier usuario con acceso al add-in puede aplicar el estándar. Si hace falta restringirlo, hay que limitar quién ve el add-in en MyGeotab.
- **El PIN del conductor se muestra enmascarado** (••••), pero se compara igual que el resto de los parámetros.
