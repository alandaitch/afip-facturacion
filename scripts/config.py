"""
Configuración central del skill afip-facturacion.
Lee datos del emisor desde $AFIP_HOME/emisor_config.json.
"""
import json
import os

# Directorio de trabajo del usuario (certs, config, log)
AFIP_HOME = os.environ.get("AFIP_HOME", os.path.expanduser("~/afip"))

CERTS_DIR = os.path.join(AFIP_HOME, "certs")
EMISOR_CONFIG_PATH = os.path.join(AFIP_HOME, "emisor_config.json")
PRIVATE_KEY_PATH = os.path.join(CERTS_DIR, "private_key.key")
CERTIFICATE_PATH = os.path.join(CERTS_DIR, "certificate.crt")
TOKEN_CACHE_PATH = os.path.join(CERTS_DIR, "token_cache.json")
FACTURAS_LOG_PATH = os.path.join(AFIP_HOME, "facturas_log.json")

# BASE_DIR apunta al directorio de datos del usuario (usado por generar_pdf para el QR base)
BASE_DIR = AFIP_HOME


def cargar_emisor():
    """Carga los datos del emisor. Aborta si falta el archivo."""
    if not os.path.exists(EMISOR_CONFIG_PATH):
        raise FileNotFoundError(
            f"No se encontró {EMISOR_CONFIG_PATH}\n"
            f"Creá el archivo con los datos del emisor. Ver references/setup.md."
        )
    with open(EMISOR_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# Cargar datos del emisor al importar (fallback vacío si no existe, para permitir setup)
try:
    _EMISOR = cargar_emisor()
    CUIT = int(str(_EMISOR["cuit"]).replace("-", ""))
    PUNTO_VENTA = int(_EMISOR.get("punto_venta", 1))
except (FileNotFoundError, KeyError, ValueError):
    _EMISOR = {}
    CUIT = 0
    PUNTO_VENTA = 1


# Ambiente: produccion o homologacion
_ENV = os.environ.get("AFIP_ENV", "prod").lower()
if _ENV in ("homo", "homologacion", "test"):
    WSAA_URL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?WSDL"
    WSFE_URL = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
else:
    WSAA_URL = "https://wsaa.afip.gov.ar/ws/services/LoginCms?WSDL"
    WSFE_URL = "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL"
