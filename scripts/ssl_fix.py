"""
Fix para el error SSL DH_KEY_TOO_SMALL de los servidores de AFIP.
AFIP usa claves Diffie-Hellman debiles en sus servidores WSFE.
"""
import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context


class AFIPSSLAdapter(HTTPAdapter):
    """Adapter que baja el nivel de seguridad SSL para compatibilidad con AFIP."""
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


def get_afip_session():
    """Retorna una session de requests configurada para AFIP."""
    session = requests.Session()
    session.mount("https://", AFIPSSLAdapter())
    return session
