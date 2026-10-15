"""Genera el JSON de instalación del add-in para MyGeotab.

El add-in se instala como "embebido": el HTML va dentro del JSON de configuración,
así corre desde el dominio de MyGeotab. Alojarlo en GitHub Pages no funciona porque
media-services.geotab.com bloquea por CORS las llamadas desde github.io.

Uso:
    python build.py            -> dist/config_addin_camaras.json con la versión de VERSION
    python build.py 1.2.0      -> actualiza VERSION y genera el JSON con esa versión
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src" / "cameraConfig.html"
VERSION_FILE = ROOT / "VERSION"
OUT = ROOT / "dist" / "config_addin_camaras.json"


def main() -> None:
    if len(sys.argv) > 1:
        version = sys.argv[1].strip()
        if not re.fullmatch(r"\d+\.\d+\.\d+", version):
            sys.exit("La versión tiene que tener el formato X.Y.Z, por ejemplo 1.2.0")
        VERSION_FILE.write_text(version + "\n", encoding="utf-8")
    version = VERSION_FILE.read_text(encoding="utf-8").strip()

    html = SRC.read_text(encoding="utf-8")
    if "geotab.addin.cameraConfig" not in html:
        sys.exit("src/cameraConfig.html tiene que registrar geotab.addin.cameraConfig "
                 "(el nombre tiene que coincidir con el archivo cameraConfig.html).")

    config = {
        "name": "Configuración de cámaras",
        "supportEmail": "soporte@cesetti.com.ar",
        "version": version,
        "items": [{
            "url": "cameraConfig.html",
            "path": "EngineMaintenanceLink/",
            "menuName": {"es": "Configuración de cámaras", "en": "Camera configuration"},
        }],
        "files": {"cameraConfig.html": html},
        "isSigned": False,
    }

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generado {OUT.relative_to(ROOT)} (versión {version}, {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
