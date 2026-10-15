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

Esa configuración carga el add-in desde GitHub Pages:
`https://apicesetti.github.io/apicesetti-camera-config-addin/cameraConfig.html`.
Cada push a `main` actualiza el add-in en todas las bases que lo tengan instalado, sin tocar MyGeotab.

### Respaldo: versión embebida

[`dist/config_addin_camaras_embebido.json`](dist/config_addin_camaras_embebido.json) lleva el HTML adentro del JSON y no depende de GitHub. Sirve si una base no puede cargar páginas externas. Con cada cambio hay que volver a pegarlo en cada base.

## Cómo hacer cambios

1. Editar [`cameraConfig.html`](cameraConfig.html) (HTML, CSS y JS en un solo archivo).
2. Si el cambio es relevante, subir la versión y regenerar los JSON:

   ```bash
   python build.py 1.3.0
   ```

   Sin argumento, usa la versión que figura en `VERSION`.
3. Commitear y hacer push a `main`. GitHub Pages publica el cambio en uno o dos minutos.

Detalles a tener en cuenta:

- El nombre de la función del add-in (`geotab.addin.cameraConfig`) tiene que coincidir con el nombre del archivo `cameraConfig.html`; `build.py` lo verifica.
- Los estilos están en la constante `CSS` dentro del script, no en un `<style>` del `<head>`: en la versión embebida MyGeotab descarta el `<head>`, así que cualquier cosa que se ponga ahí no llega a la página.
- Para el JSON embebido, `build.py` convierte el CSS a una cadena común y escapa acentos y símbolos. Una versión con el CSS entre comillas invertidas fue rechazada por MyGeotab con "El objeto de configuración no es válido".

## Cómo funciona por dentro

| Qué | Cómo |
|---|---|
| Sesión | `api.getSession(callback, false)` — el segundo parámetro es booleano, no un callback de error. |
| Autenticación con media-services | Headers `X-MyGeotab-Database` (con `encodeURIComponent`), `X-MyGeotab-Username`, `X-MyGeotab-SessionId` y `X-MyGeotab-Path` con los datos de la sesión del usuario. No hace falta ningún token ni secreto guardado en el código. |
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
