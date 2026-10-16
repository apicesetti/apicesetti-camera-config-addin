# Configuración de cámaras — add-in de MyGeotab

Add-in para ver la configuración de todas las cámaras de una base de MyGeotab, detectar las que se apartan del estándar de la flota y ver cuáles están funcionando. Soporta GO Focus (Surfsight AI-12) y GO Focus Plus (Smarter AI).

- Resume cuántas cámaras están **funcionando** y cuántas **en falla**, en total y por modelo. Una cámara está en falla si no se conecta hace más de 3 días (o no tiene registro de conexión).
- Muestra la flota completa en un mosaico: una celda por cámara, en rojo las que tienen desvíos y con borde oscuro las que están en falla.
- El estándar se define a mano, por separado para cada modelo (cada uno tiene sus propios parámetros), parámetro por parámetro: Sí/No, una opción de la lista o un valor libre (brillo, tiempo de standby, PIN). Los parámetros sin definir no se controlan. "Completar con lo más común" llena los que falten con el valor más frecuente de la flota, como punto de partida.
- El estándar se guarda en la base de MyGeotab (AddInData), así que todos los usuarios de la base ven y editan el mismo.
- Lista cada diferencia de forma legible ("Grabación en cabina **No** en vez de Sí") y permite ver la configuración completa de cada cámara.
- Aplica el estándar en una o varias cámaras, con confirmación previa, y deja registro en la Auditoría de la base.
- Exporta a CSV la configuración de todas las cámaras visibles, con una fila de estándar.

Se probó en las bases `tsbsa` y `intcesetti`.

## Instalación en una base

1. En MyGeotab: **Administración → Sistema → Configuración del sistema → Add-ins**.
2. **Nuevo add-in** y pegar el contenido de [`dist/config_addin_camaras.json`](dist/config_addin_camaras.json).
3. Guardar y recargar. Aparece en el menú de **Mantenimiento** como **Configuración de cámaras**.

### Quién puede ver el add-in

La configuración incluye `"enableViewSecurityId": true`. Eso agrega en **Administración → Usuarios → Autorizaciones** la casilla **View Configuración de cámaras add-in**: solo los usuarios cuya autorización la tenga activada ven el add-in en el menú. Para dar acceso, se activa esa casilla en la autorización correspondiente (o se crea una autorización nueva con ella activada).

Si una base ya tenía instalada una versión anterior sin ese campo, hay que reemplazar la configuración del add-in con la nueva para que aparezca la casilla.

Esa configuración carga el add-in desde GitHub Pages:
`https://apicesetti.github.io/apicesetti-camera-config-addin/cameraConfig.html`.
Cada push a `main` actualiza el add-in en todas las bases que lo tengan instalado, sin tocar MyGeotab.

### Respaldo: versión embebida

[`dist/config_addin_camaras_embebido.json`](dist/config_addin_camaras_embebido.json) lleva el HTML adentro del JSON y no depende de GitHub. Sirve si una base no puede cargar páginas externas. Con cada cambio hay que volver a pegarlo en cada base.

## Cómo hacer cambios

1. Editar [`cameraConfig.html`](cameraConfig.html) (HTML, CSS y JS en un solo archivo).
2. Si el cambio es relevante, subir la versión y regenerar los JSON:

   ```bash
   python build.py 1.5.0
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
| Lista de cámaras y conexión | `GET https://media-services.geotab.com/api/DeviceMappings`. El proveedor sale de `partnerId` (`surfsight` o `smarterai`) y la última conexión real de `partnerMetaData.LastConnectedAt`. No usar `partnerDeviceLastOnlineAt`: se refresca aunque la cámara esté desconectada. |
| Configuración GO Focus | `GET https://media-services.geotab.com/api/Surfsight/DeviceSettings/{imei}`. Los valores vienen como `{"param":{"value":x}}`. |
| Configuración GO Focus Plus | `GET https://media-services.geotab.com/api/SmarterAi/DeviceSettings/deployedSchemes/{partnerDeviceId}`. Los valores vienen planos: `{"param": x}`. |
| Cambio de configuración (solo GO Focus) | `PATCH https://media-services.geotab.com/api/Surfsight/DeviceSettings` con `{"imeis":[...],"config":{"param":{"value":x}}}` |
| Vehículo de cada cámara | `Get Device` de la API de MyGeotab, cruzado por número de serie del GO. |
| Estándar | Un registro `AddInData` con `addInId` `a1BwanQJoRn-Mxo0iUvTCUA` y `details.kind = "cameraStandard"`; los valores van como lista `[{path, value}]`, con `path` = `proveedor:parámetro` (por ejemplo `smarterai:voiceAlertLanguage`). Los estándares guardados por la v1.3, sin proveedor, se leen como de GO Focus. No cambiar ese `addInId`: se perdería el estándar guardado en cada base. |
| Registro de cambios | `Add Audit` en la base, con vehículo, patente y parámetros cambiados. |

Las lecturas se hacen de a 6 cámaras en paralelo. En una base de unas 580 cámaras tarda alrededor de un minuto.

## Limitaciones conocidas

- **GO Focus Plus se lee pero no se corrige desde acá.** MyGeotab tiene un `PATCH /SmarterAi/DeviceSettings/{id}`, pero no se verificó el formato del cuerpo; las diferencias se marcan y se corrigen desde la configuración de la cámara en MyGeotab.
- **Parámetros compuestos sin corrección automática.** Privacidad por cámara, standby, hotspot y cifrado se detectan como desvío, pero se corrigen desde la configuración de la cámara en MyGeotab: el formato del PATCH para esos parámetros no está verificado.
- **El estándar es uno por base** y gana el último que guarda: si dos personas lo editan a la vez, queda la última versión. Si la lectura de AddInData falla, el add-in avisa y usa uno guardado en el navegador.
- **Cámaras offline:** el cambio se envía igual y la cámara lo toma al conectarse. Hasta entonces puede seguir mostrando el valor anterior.
- **Permisos:** cualquier usuario que pueda ver el add-in puede editar el estándar y aplicarlo. Para restringirlo, limitar quién tiene la casilla **View Configuración de cámaras add-in**.
- **El PIN del conductor se muestra enmascarado** (••••), pero se compara igual que el resto de los parámetros.
