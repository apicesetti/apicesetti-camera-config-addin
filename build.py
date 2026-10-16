"""Genera los JSON de instalación del add-in para MyGeotab.

Hay dos formas de instalarlo:

- dist/config_addin_camaras.json (recomendada): el add-in se carga desde GitHub Pages.
  Para actualizar todas las bases alcanza con hacer push a main; no hay que tocar MyGeotab.
- dist/config_addin_camaras_embebido.json (respaldo): el HTML va dentro del JSON y no
  depende de GitHub. Hay que volver a pegarlo en cada base con cada cambio.

Uso:
    python build.py            -> genera ambos JSON con la versión de VERSION
    python build.py 1.2.0      -> actualiza VERSION y genera ambos JSON con esa versión
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "cameraConfig.html"
VERSION_FILE = ROOT / "VERSION"
DIST = ROOT / "dist"
PAGES_URL = "https://apicesetti.github.io/apicesetti-camera-config-addin/cameraConfig.html"

ITEM = {
    "path": "EngineMaintenanceLink/",
    "menuName": {"es": "Configuración de cámaras", "en": "Camera configuration"},
}


def base_config(version: str) -> dict:
    return {
        "name": "Configuración de cámaras",
        "supportEmail": "soporte@cesetti.com.ar",
        "version": version,
        # Crea en Autorizaciones la casilla "View Configuración de cámaras add-in": solo los
        # usuarios cuya autorización la tenga activada ven el add-in en el menú.
        "enableViewSecurityId": True,
        "isSigned": False,
    }


def embeddable(html: str) -> str:
    # MyGeotab rechazó ("El objeto de configuración no es válido") una versión embebida con el
    # CSS en un template literal de JS. Para el JSON embebido se convierte a una cadena común.
    m = re.search(r"var CSS = `(.*?)`;", html, re.S)
    if m:
        html = html[:m.start()] + "var CSS = " + json.dumps(m.group(1), ensure_ascii=True) + ";" + html[m.end():]
    if "`" in html:
        sys.exit("Quedan comillas invertidas (`) en el HTML; MyGeotab puede rechazar la configuración embebida.")
    return html


def write(path: pathlib.Path, config: dict) -> None:
    # ensure_ascii=True: acentos y símbolos van como \uXXXX, así el JSON es ASCII puro.
    path.write_text(json.dumps(config, ensure_ascii=True, indent=2) + "\n", encoding="ascii")
    print(f"Generado {path.relative_to(ROOT)} ({path.stat().st_size // 1024 or 1} KB)")


def main() -> None:
    if len(sys.argv) > 1:
        version = sys.argv[1].strip()
        if not re.fullmatch(r"\d+\.\d+\.\d+", version):
            sys.exit("La versión tiene que tener el formato X.Y.Z, por ejemplo 1.2.0")
        VERSION_FILE.write_text(version + "\n", encoding="utf-8")
    version = VERSION_FILE.read_text(encoding="utf-8").strip()

    html = SRC.read_text(encoding="utf-8")
    if "geotab.addin.cameraConfig" not in html:
        sys.exit("cameraConfig.html tiene que registrar geotab.addin.cameraConfig "
                 "(el nombre tiene que coincidir con el nombre del archivo).")

    DIST.mkdir(exist_ok=True)
    hosted = base_config(version)
    hosted["items"] = [dict(ITEM, url=PAGES_URL)]
    write(DIST / "config_addin_camaras.json", hosted)

    embedded = base_config(version)
    embedded["items"] = [dict(ITEM, url="cameraConfig.html")]
    embedded["files"] = {"cameraConfig.html": embeddable(html)}
    write(DIST / "config_addin_camaras_embebido.json", embedded)
    print(f"Versión {version}")


if __name__ == "__main__":
    main()
