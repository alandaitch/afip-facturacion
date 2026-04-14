#!/usr/bin/env python3
"""
Facturación electrónica AFIP/ARCA — Factura C (monotributo) a Consumidor Final.

Uso:
    export AFIP_HOME=~/afip
    python3 facturar.py --monto 5000 --descripcion "Consultoría"
    python3 facturar.py --monto 5000 --concepto 2 --desde 2026-04-01 --hasta 2026-04-30
"""
import argparse
import json
import sys
from datetime import datetime

import zeep

from config import WSFE_URL, CUIT, PUNTO_VENTA, FACTURAS_LOG_PATH
from wsaa import obtener_credenciales
from generar_pdf import generar_pdf

TIPOS_CBTE = {"factura_c": 11, "nota_debito_c": 12, "nota_credito_c": 13}
DOC_CONSUMIDOR_FINAL = 99


def conectar_wsfe(token, sign):
    from ssl_fix import get_afip_session
    from zeep.transports import Transport
    session = get_afip_session()
    transport = Transport(session=session)
    client = zeep.Client(wsdl=WSFE_URL, transport=transport)
    auth = {"Token": token, "Sign": sign, "Cuit": CUIT}
    return client, auth


def ultimo_comprobante(client, auth, tipo_cbte=11, punto_venta=None):
    pv = punto_venta or PUNTO_VENTA
    response = client.service.FECompUltimoAutorizado(
        Auth=auth, PtoVta=pv, CbteTipo=tipo_cbte,
    )
    if response.Errors:
        for err in response.Errors.Err:
            print(f"Error: {err.Code} - {err.Msg}")
        return None
    return response.CbteNro


def crear_factura(client, auth, monto, concepto=1, fecha_desde=None, fecha_hasta=None,
                  tipo_cbte=11, punto_venta=None):
    pv = punto_venta or PUNTO_VENTA
    last = ultimo_comprobante(client, auth, tipo_cbte, pv)
    if last is None:
        raise Exception("No se pudo obtener el último comprobante")
    next_num = last + 1
    today = datetime.now().strftime("%Y%m%d")

    detalle = {
        "Concepto": concepto,
        "DocTipo": DOC_CONSUMIDOR_FINAL,
        "DocNro": 0,
        "CbteDesde": next_num,
        "CbteHasta": next_num,
        "CbteFch": today,
        "ImpTotal": monto,
        "ImpTotConc": 0,
        "ImpNeto": monto,
        "ImpOpEx": 0,
        "ImpIVA": 0,
        "ImpTrib": 0,
        "MonId": "PES",
        "MonCotiz": 1,
    }

    if concepto in (2, 3):
        if not fecha_desde or not fecha_hasta:
            raise ValueError("Para servicios debe indicar fecha_desde y fecha_hasta")
        detalle["FchServDesde"] = fecha_desde.replace("-", "") if isinstance(fecha_desde, str) else fecha_desde.strftime("%Y%m%d")
        detalle["FchServHasta"] = fecha_hasta.replace("-", "") if isinstance(fecha_hasta, str) else fecha_hasta.strftime("%Y%m%d")
        detalle["FchVtoPago"] = today

    request = {
        "FeCabReq": {"CantReg": 1, "PtoVta": pv, "CbteTipo": tipo_cbte},
        "FeDetReq": {"FECAEDetRequest": [detalle]},
    }

    response = client.service.FECAESolicitar(Auth=auth, FeCAEReq=request)

    resultado = {
        "punto_venta": pv, "tipo_cbte": tipo_cbte, "numero": next_num,
        "fecha": today, "monto": monto,
    }

    if response.Errors:
        for err in response.Errors.Err:
            print(f"ERROR: {err.Code} - {err.Msg}")
        resultado["estado"] = "ERROR"
        return resultado

    det = response.FeDetResp.FECAEDetResponse[0]
    resultado["cae"] = det.CAE
    resultado["cae_vencimiento"] = det.CAEFchVto
    resultado["estado"] = det.Resultado

    if det.Observaciones:
        resultado["observaciones"] = [f"{o.Code}: {o.Msg}" for o in det.Observaciones.Obs]

    return resultado


def main():
    parser = argparse.ArgumentParser(description="Facturar electrónicamente por AFIP/ARCA")
    parser.add_argument("--monto", type=float, default=1.0)
    parser.add_argument("--concepto", type=int, default=1, choices=[1, 2, 3])
    parser.add_argument("--desde", type=str)
    parser.add_argument("--hasta", type=str)
    parser.add_argument("--punto-venta", type=int)
    parser.add_argument("--tipo", type=str, default="factura_c", choices=TIPOS_CBTE.keys())
    parser.add_argument("--descripcion", type=str, default="Servicio profesional")
    parser.add_argument("--condicion-venta", type=str, default="Contado")
    args = parser.parse_args()

    if CUIT == 0:
        print("ERROR: emisor_config.json no configurado. Ver references/setup.md.")
        return 1

    tipo_cbte = TIPOS_CBTE[args.tipo]

    print("=" * 50)
    print("FACTURACIÓN ELECTRÓNICA AFIP/ARCA")
    print("=" * 50)

    token, sign = obtener_credenciales()
    client, auth = conectar_wsfe(token, sign)

    last = ultimo_comprobante(client, auth, tipo_cbte, args.punto_venta)
    print(f"Último comprobante: {last}")
    print(f"Próximo: {last + 1}  |  Monto: ${args.monto}  |  Concepto: {args.concepto}")
    print("-" * 50)

    resultado = crear_factura(
        client, auth,
        monto=args.monto, concepto=args.concepto,
        fecha_desde=args.desde, fecha_hasta=args.hasta,
        tipo_cbte=tipo_cbte, punto_venta=args.punto_venta,
    )
    resultado["descripcion"] = args.descripcion
    resultado["concepto"] = args.concepto
    resultado["condicion_venta"] = args.condicion_venta
    if args.desde:
        resultado["fecha_desde"] = args.desde.replace("-", "")
    if args.hasta:
        resultado["fecha_hasta"] = args.hasta.replace("-", "")

    print()
    if resultado["estado"] == "A":
        print("FACTURA APROBADA!")
        print(f"  Número: {resultado['punto_venta']:04d}-{resultado['numero']:08d}")
        print(f"  CAE: {resultado['cae']}")
        print(f"  Vencimiento CAE: {resultado['cae_vencimiento']}")
        print(f"  Monto: ${resultado['monto']}  |  Fecha: {resultado['fecha']}")
    else:
        print("FACTURA RECHAZADA")
        for obs in resultado.get("observaciones", []):
            print(f"  Obs: {obs}")

    if resultado["estado"] == "A":
        pdf_path = generar_pdf(resultado)
        print(f"  PDF: {pdf_path}")

    try:
        with open(FACTURAS_LOG_PATH, "r") as f:
            log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log = []
    log.append(resultado)
    with open(FACTURAS_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2, default=str)
    print(f"\nLog: {FACTURAS_LOG_PATH}")

    return 0 if resultado["estado"] == "A" else 1


if __name__ == "__main__":
    sys.exit(main())
