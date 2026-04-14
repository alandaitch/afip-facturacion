"""
Generador de PDF de facturas electronicas AFIP/ARCA.
Genera el comprobante con QR code segun la normativa vigente,
replicando el formato oficial de ARCA.
"""
import base64
import json
import os
from datetime import datetime
from io import BytesIO

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from config import CUIT, EMISOR_CONFIG_PATH, FACTURAS_LOG_PATH


def _cargar_emisor():
    try:
        with open(EMISOR_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"razon_social": "", "cuit": str(CUIT), "condicion_iva": "",
                "domicilio": "", "ingresos_brutos": "", "inicio_actividades": ""}


# Cargar datos del emisor desde archivo de configuracion
EMISOR = _cargar_emisor()

TIPOS_CBTE_NOMBRE = {
    11: "FACTURA",
    12: "NOTA DE DEBITO",
    13: "NOTA DE CREDITO",
}

TIPOS_CBTE_LETRA = {
    11: "C",
    12: "C",
    13: "C",
}


def generar_qr_afip(datos_factura):
    """Genera el QR code segun especificacion AFIP RG 4291/2018."""
    fecha = datos_factura["fecha"]
    if len(fecha) == 8:
        fecha = f"{fecha[:4]}-{fecha[4:6]}-{fecha[6:8]}"

    qr_data = {
        "ver": 1,
        "fecha": fecha,
        "cuit": CUIT,
        "ptoVta": datos_factura["punto_venta"],
        "tipoCmp": datos_factura["tipo_cbte"],
        "nroCmp": datos_factura["numero"],
        "importe": datos_factura["monto"],
        "moneda": "PES",
        "ctz": 1,
        "tipoDocRec": 99,
        "nroDocRec": 0,
        "tipoCodAut": "E",
        "codAut": int(datos_factura["cae"]),
    }

    json_str = json.dumps(qr_data)
    b64 = base64.b64encode(json_str.encode()).decode()
    url = f"https://www.afip.gob.ar/fe/qr/?p={b64}"

    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def formatear_fecha(fecha_str):
    """Convierte YYYYMMDD a DD/MM/YYYY."""
    if len(fecha_str) == 8:
        return f"{fecha_str[6:8]}/{fecha_str[4:6]}/{fecha_str[:4]}"
    return fecha_str


def _draw_centered_text(c, text, y, font="Helvetica", size=10, page_width=None):
    """Helper para texto centrado."""
    c.setFont(font, size)
    w = page_width or A4[0]
    c.drawCentredString(w / 2, y, text)


def generar_pdf(datos_factura, output_path=None, emisor_data=None):
    """
    Genera el PDF de la factura electronica replicando el formato oficial ARCA.

    Args:
        datos_factura: dict con los datos de la factura
        output_path: ruta donde guardar el PDF (opcional)
        emisor_data: dict con datos del emisor (opcional, usa EMISOR por defecto)

    Returns:
        ruta del PDF generado
    """
    emisor = emisor_data if emisor_data is not None else EMISOR
    if output_path is None:
        pv = datos_factura["punto_venta"]
        num = datos_factura["numero"]
        output_path = f"factura_{pv:04d}_{num:08d}.pdf"

    tipo_cbte = datos_factura["tipo_cbte"]
    tipo_nombre = TIPOS_CBTE_NOMBRE.get(tipo_cbte, f"COMPROBANTE {tipo_cbte}")
    letra = TIPOS_CBTE_LETRA.get(tipo_cbte, "C")

    w, h = A4
    c = canvas.Canvas(output_path, pagesize=A4)

    # Margenes
    margin_x = 15 * mm
    content_w = w - 2 * margin_x

    # === "ORIGINAL" banner ===
    y_original = h - 18 * mm
    c.setFillColor(colors.black)
    c.rect(margin_x, y_original - 2 * mm, content_w, 10 * mm, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, y_original, "ORIGINAL")
    c.setFillColor(colors.black)

    # === ENCABEZADO principal (dentro del recuadro) ===
    y_header_top = y_original - 2 * mm
    header_height = 57 * mm
    y_header_bottom = y_header_top - header_height

    # Recuadro exterior del encabezado
    c.setLineWidth(1)
    c.rect(margin_x, y_header_bottom, content_w, header_height)

    # Linea vertical central
    center_x = w / 2
    c.line(center_x, y_header_top, center_x, y_header_bottom)

    # Recuadro de la letra (centrado arriba, con fondo blanco para tapar la linea central)
    box_w = 22 * mm
    box_h = 22 * mm
    box_x = center_x - box_w / 2
    box_y = y_header_top - box_h - 1 * mm
    c.setLineWidth(1.5)
    c.setFillColor(colors.white)
    c.rect(box_x, box_y, box_w, box_h, fill=1, stroke=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(center_x, box_y + 7 * mm, letra)
    c.setFont("Helvetica", 7)
    c.drawCentredString(center_x, box_y + 2 * mm, f"COD. 0{tipo_cbte}")

    # --- Column boundaries to avoid C box overlap ---
    left_max_x = box_x - 3 * mm        # left column must not exceed this x
    right_start_x = box_x + box_w + 3 * mm  # right column starts after this x

    # --- Lado izquierdo ---
    lx = margin_x + 5 * mm
    ly = y_header_top - 10 * mm

    c.setFont("Helvetica-Bold", 13)
    c.drawString(lx, ly, emisor["razon_social"])

    ly -= 7 * mm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(lx, ly, "Razon Social: ")
    c.setFont("Helvetica", 8)
    c.drawString(lx + 42 * mm, ly, emisor["razon_social"])

    ly -= 5 * mm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(lx, ly, "Domicilio Comercial: ")
    c.setFont("Helvetica", 7.5)
    dom = emisor["domicilio"]
    max_dom_w = left_max_x - lx
    c.drawString(lx, ly - 4 * mm, dom)

    ly -= 12 * mm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(lx, ly, f"Condicion frente al IVA:   ")
    c.setFont("Helvetica-Bold", 8)
    c.drawString(lx + 45 * mm, ly, emisor["condicion_iva"])

    # --- Lado derecho ---
    rx = right_start_x
    ry = y_header_top - 8 * mm

    c.setFont("Helvetica-Bold", 20)
    c.drawString(rx, ry, tipo_nombre)

    ry -= 9 * mm
    pv = datos_factura["punto_venta"]
    num = datos_factura["numero"]
    rx_end = w - margin_x - 3 * mm  # borde derecho interno
    c.setFont("Helvetica-Bold", 9)
    c.drawString(rx, ry, "Punto de Venta:")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(rx + 28 * mm, ry, f"{pv:05d}")
    c.setFont("Helvetica-Bold", 9)
    c.drawString(rx + 45 * mm, ry, "Comp. Nro:")
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(rx_end, ry, f"{num:08d}")

    ry -= 6 * mm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(rx, ry, f"Fecha de Emision:  ")
    c.setFont("Helvetica", 8)
    c.drawString(rx + 33 * mm, ry, formatear_fecha(datos_factura["fecha"]))

    ry -= 6 * mm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(rx, ry, f"CUIT: ")
    c.setFont("Helvetica", 8)
    c.drawString(rx + 14 * mm, ry, emisor["cuit"])

    ry -= 5 * mm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(rx, ry, f"Ingresos Brutos:  ")
    c.setFont("Helvetica", 8)
    c.drawString(rx + 30 * mm, ry, emisor["ingresos_brutos"])

    ry -= 5 * mm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(rx, ry, f"Fecha de Inicio de Actividades:   ")
    c.setFont("Helvetica", 8)
    c.drawString(rx + 57 * mm, ry, emisor["inicio_actividades"])

    # === PERIODO FACTURADO (solo para servicios concepto 2 o 3) ===
    concepto = datos_factura.get("concepto", 1)
    y_cursor = y_header_bottom

    if concepto in (2, 3):
        periodo_h = 8 * mm
        y_periodo = y_cursor - periodo_h
        # Fondo gris para la barra de periodo
        c.setFillColor(colors.Color(0.85, 0.85, 0.85))
        c.rect(margin_x, y_periodo, content_w, periodo_h, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 8)
        fecha_desde = datos_factura.get("fecha_desde", "")
        fecha_hasta = datos_factura.get("fecha_hasta", "")
        fecha_vto_pago = formatear_fecha(datos_factura["fecha"])
        if fecha_desde and len(fecha_desde) == 8:
            fecha_desde = formatear_fecha(fecha_desde)
        if fecha_hasta and len(fecha_hasta) == 8:
            fecha_hasta = formatear_fecha(fecha_hasta)
        c.drawString(lx, y_periodo + 2.5 * mm,
                     f"Periodo Facturado Desde:   {fecha_desde}        "
                     f"Hasta:   {fecha_hasta}        "
                     f"Fecha de Vto. para el pago:   {fecha_vto_pago}")
        y_cursor = y_periodo
    else:
        # Sin periodo, solo una linea
        pass

    # === DATOS DEL RECEPTOR ===
    receptor_h = 20 * mm
    y_receptor_top = y_cursor
    y_receptor_bottom = y_receptor_top - receptor_h
    c.setLineWidth(0.5)
    c.rect(margin_x, y_receptor_bottom, content_w, receptor_h)

    ry2 = y_receptor_top - 5 * mm
    c.setFont("Helvetica-Bold", 8)

    # Receptor data from invoice or defaults
    doc_tipo = datos_factura.get("doc_tipo", 99)
    doc_nro = datos_factura.get("doc_nro", 0)
    receptor_nombre = datos_factura.get("receptor_nombre", "")
    receptor_iva = datos_factura.get("receptor_iva", "Consumidor Final")
    receptor_domicilio = datos_factura.get("receptor_domicilio", "")
    receptor_condicion_venta = datos_factura.get("condicion_venta", "Contado")

    if doc_tipo == 80:
        doc_label = "CUIT:"
    elif doc_tipo == 96:
        doc_label = "DNI:"
    else:
        doc_label = "CUIT:"

    # Row 1: CUIT + Nombre
    c.drawString(lx, ry2, doc_label)
    c.setFont("Helvetica", 8)
    doc_nro_str = str(doc_nro) if doc_nro else ""
    c.drawString(lx + 15 * mm, ry2, doc_nro_str)

    c.setFont("Helvetica-Bold", 8)
    c.drawString(lx + 45 * mm, ry2, "Apellido y Nombre / Razon Social:")
    c.setFont("Helvetica-Bold", 8)
    c.drawString(lx + 105 * mm, ry2, receptor_nombre)

    # Row 2: Condicion IVA + Domicilio
    ry2 -= 5 * mm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(lx, ry2, "Condicion frente al IVA:")
    c.setFont("Helvetica", 8)
    c.drawString(lx + 42 * mm, ry2, receptor_iva)

    c.setFont("Helvetica-Bold", 8)
    c.drawString(rx, ry2, "Domicilio:")
    c.setFont("Helvetica", 7)
    c.drawString(rx + 20 * mm, ry2, receptor_domicilio)

    # Row 3: Condicion de venta
    ry2 -= 5 * mm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(lx, ry2, "Condicion de venta:")
    c.setFont("Helvetica", 8)
    c.drawString(lx + 35 * mm, ry2, receptor_condicion_venta)

    # === TABLA DE DETALLE ===
    y_table_top = y_receptor_bottom

    # Header de la tabla (fondo oscuro)
    table_header_h = 7 * mm
    y_th = y_table_top - table_header_h
    c.setFillColor(colors.Color(0.2, 0.2, 0.2))
    c.rect(margin_x, y_th, content_w, table_header_h, fill=1, stroke=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 7)

    # Columnas de la tabla - posiciones de las lineas verticales separadoras
    right_edge = w - margin_x
    col_sep_1 = margin_x + 15 * mm      # despues de Codigo
    col_sep_2 = margin_x + 90 * mm      # despues de Producto/Servicio
    col_sep_3 = margin_x + 108 * mm     # despues de Cantidad
    col_sep_4 = margin_x + 125 * mm     # despues de U. Medida
    col_sep_5 = margin_x + 145 * mm     # despues de Precio Unit.
    col_sep_6 = margin_x + 158 * mm     # despues de % Bonif
    col_sep_7 = margin_x + 172 * mm     # despues de Imp. Bonif.

    thy = y_th + 2 * mm
    c.setFont("Helvetica-Bold", 6.5)
    c.drawCentredString((margin_x + col_sep_1) / 2, thy, "Codigo")
    c.drawCentredString((col_sep_1 + col_sep_2) / 2, thy, "Producto / Servicio")
    c.drawCentredString((col_sep_2 + col_sep_3) / 2, thy, "Cantidad")
    c.drawCentredString((col_sep_3 + col_sep_4) / 2, thy, "U. Medida")
    c.drawCentredString((col_sep_4 + col_sep_5) / 2, thy, "Precio Unit.")
    c.drawCentredString((col_sep_5 + col_sep_6) / 2, thy, "% Bonif")
    c.drawCentredString((col_sep_6 + col_sep_7) / 2, thy, "Imp. Bonif.")
    c.drawCentredString((col_sep_7 + right_edge) / 2, thy, "Subtotal")

    c.setFillColor(colors.black)

    # Filas de la tabla
    y_row = y_th - 6 * mm
    c.setFont("Helvetica", 7.5)

    descripcion = datos_factura.get("descripcion", "Servicio profesional")
    monto = datos_factura["monto"]
    cantidad = datos_factura.get("cantidad", 1)
    u_medida = datos_factura.get("u_medida", "unidades")
    precio_unit = monto / cantidad if cantidad else monto

    c.drawCentredString((col_sep_1 + col_sep_2) / 2, y_row, descripcion)
    c.drawRightString(col_sep_3 - 2 * mm, y_row, f"{cantidad:.2f}")
    c.drawCentredString((col_sep_3 + col_sep_4) / 2, y_row, u_medida)
    c.drawRightString(col_sep_5 - 2 * mm, y_row, f"{precio_unit:,.2f}")
    c.drawRightString(col_sep_6 - 2 * mm, y_row, "0,00")
    c.drawRightString(col_sep_7 - 2 * mm, y_row, "0,00")
    c.drawRightString(right_edge - 2 * mm, y_row, f"{monto:,.2f}")

    # Recuadro de la zona de detalle (hasta los totales)
    y_detail_bottom = y_th - 120 * mm
    c.setLineWidth(0.5)
    c.rect(margin_x, y_detail_bottom, content_w, y_table_top - y_detail_bottom)

    # Lineas verticales de la tabla (en el header)
    for col_line_x in [col_sep_1, col_sep_2, col_sep_3, col_sep_4,
                       col_sep_5, col_sep_6, col_sep_7]:
        c.line(col_line_x, y_table_top, col_line_x, y_th)

    # === TOTALES ===
    y_totals = y_detail_bottom + 5 * mm

    c.setFont("Helvetica-Bold", 9)
    label_x = w - margin_x - 80 * mm
    val_x = w - margin_x - 5 * mm

    c.drawRightString(label_x + 45 * mm, y_totals + 18 * mm, "Subtotal: $")
    c.setFont("Helvetica", 9)
    c.drawRightString(val_x, y_totals + 18 * mm, f"{monto:,.2f}")

    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(label_x + 45 * mm, y_totals + 12 * mm, "Importe Otros Tributos: $")
    c.setFont("Helvetica", 9)
    c.drawRightString(val_x, y_totals + 12 * mm, "0,00")

    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(label_x + 45 * mm, y_totals + 4 * mm, "Importe Total: $")
    c.drawRightString(val_x, y_totals + 4 * mm, f"{monto:,.2f}")

    # === PIE DE PAGINA ===
    y_footer_top = y_detail_bottom
    y_footer = y_footer_top - 5 * mm

    # Linea separadora del footer
    c.setLineWidth(0.5)

    # QR Code
    qr_buf = generar_qr_afip(datos_factura)
    qr_img = ImageReader(qr_buf)
    qr_size = 28 * mm
    c.drawImage(qr_img, margin_x + 2 * mm, y_footer - qr_size - 5 * mm,
                width=qr_size, height=qr_size)

    # ARCA logo area (texto, no tenemos el logo real)
    arca_x = margin_x + 40 * mm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(arca_x, y_footer - 8 * mm, "ARCA")
    c.setFont("Helvetica", 5.5)
    c.drawString(arca_x, y_footer - 12 * mm, "AGENCIA DE RECAUDACION")
    c.drawString(arca_x, y_footer - 15 * mm, "Y CONTROL ADUANERO")

    # Pag
    c.setFont("Helvetica", 8)
    c.drawCentredString(w / 2, y_footer - 8 * mm, "Pag. 1/1")

    # CAE info (derecha)
    cae_x = w - margin_x - 5 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(cae_x, y_footer - 5 * mm,
                      f"CAE N°: {datos_factura['cae']}")
    c.drawRightString(cae_x, y_footer - 11 * mm,
                      f"Fecha de Vto. de CAE: {formatear_fecha(datos_factura['cae_vencimiento'])}")

    # Comprobante autorizado
    y_auth = y_footer - qr_size - 8 * mm
    c.setFont("Helvetica-BoldOblique", 8)
    c.drawString(arca_x, y_auth, "Comprobante Autorizado")

    c.setFont("Helvetica-Oblique", 6)
    c.drawString(arca_x, y_auth - 5 * mm,
                 "Esta Agencia no se responsabiliza por los datos ingresados en el detalle de la operacion")

    c.save()
    return output_path


if __name__ == "__main__":
    try:
        with open(FACTURAS_LOG_PATH, "r") as f:
            log = json.load(f)
        if log:
            ultima = log[-1]
            if ultima.get("estado") == "A":
                pdf = generar_pdf(ultima)
                print(f"PDF generado: {pdf}")
            else:
                print("La ultima factura no fue aprobada")
        else:
            print("No hay facturas en el log")
    except FileNotFoundError:
        print("No se encontro facturas_log.json")
