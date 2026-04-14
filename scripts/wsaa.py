"""
WSAA - Web Service de Autenticacion y Autorizacion de AFIP/ARCA
Genera el token y sign necesarios para operar con los web services.
"""
import json
import os
import time
import base64
import datetime
from lxml import etree
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7
from cryptography.x509 import load_pem_x509_certificate
import zeep

from config import WSAA_URL, PRIVATE_KEY_PATH, CERTIFICATE_PATH, TOKEN_CACHE_PATH


def crear_tra(service="wsfe"):
    """Crea el Ticket de Requerimiento de Acceso (TRA) XML."""
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3)))
    unique_id = str(int(time.time()))
    generation = now.strftime("%Y-%m-%dT%H:%M:%S-03:00")
    expiration = (now + datetime.timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S-03:00")

    tra = etree.Element("loginTicketRequest", version="1.0")
    header = etree.SubElement(tra, "header")
    etree.SubElement(header, "uniqueId").text = unique_id
    etree.SubElement(header, "generationTime").text = generation
    etree.SubElement(header, "expirationTime").text = expiration
    etree.SubElement(tra, "service").text = service

    return etree.tostring(tra, xml_declaration=True, encoding="UTF-8")


def firmar_tra(tra_xml):
    """Firma el TRA con la clave privada y el certificado usando PKCS#7/CMS."""
    with open(PRIVATE_KEY_PATH, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    with open(CERTIFICATE_PATH, "rb") as f:
        certificate = load_pem_x509_certificate(f.read())

    # Firmar usando PKCS7 (CMS)
    signed = pkcs7.PKCS7SignatureBuilder().set_data(
        tra_xml
    ).add_signer(
        certificate, private_key, hashes.SHA256()
    ).sign(
        serialization.Encoding.DER, [pkcs7.PKCS7Options.Binary]
    )

    return base64.b64encode(signed).decode("utf-8")


def login_cms(signed_tra):
    """Envia el TRA firmado al WSAA y obtiene token + sign."""
    from ssl_fix import get_afip_session
    from zeep.transports import Transport
    session = get_afip_session()
    transport = Transport(session=session)
    client = zeep.Client(wsdl=WSAA_URL, transport=transport)
    response = client.service.loginCms(in0=signed_tra)

    # Parsear la respuesta XML
    root = etree.fromstring(response.encode("utf-8"))
    token = root.find(".//token").text
    sign = root.find(".//sign").text
    expiration = root.find(".//expirationTime").text

    return token, sign, expiration


def obtener_credenciales(force=False):
    """
    Obtiene token y sign, usando cache si es valido.
    Retorna (token, sign).
    """
    # Intentar usar cache
    if not force and os.path.exists(TOKEN_CACHE_PATH):
        with open(TOKEN_CACHE_PATH, "r") as f:
            cache = json.load(f)

        # Verificar si el token aun es valido (con 5 min de margen)
        exp_time = datetime.datetime.fromisoformat(cache["expiration"])
        now = datetime.datetime.now(exp_time.tzinfo)
        if now < exp_time - datetime.timedelta(minutes=5):
            print("Usando token cacheado (valido hasta {})".format(cache["expiration"]))
            return cache["token"], cache["sign"]

    # Generar nuevo token
    print("Solicitando nuevo token a WSAA...")
    tra_xml = crear_tra("wsfe")
    signed_tra = firmar_tra(tra_xml)
    token, sign, expiration = login_cms(signed_tra)

    # Cachear
    with open(TOKEN_CACHE_PATH, "w") as f:
        json.dump({
            "token": token,
            "sign": sign,
            "expiration": expiration
        }, f)

    print("Token obtenido (valido hasta {})".format(expiration))
    return token, sign


if __name__ == "__main__":
    token, sign = obtener_credenciales(force=True)
    print(f"Token: {token[:50]}...")
    print(f"Sign: {sign[:50]}...")
