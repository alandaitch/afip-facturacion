#!/bin/bash
# Genera clave privada RSA 2048 + CSR para AFIP/ARCA.
# Uso: ./generar_certificado.sh <CUIT> "<NOMBRE APELLIDO>"
# Requiere AFIP_HOME exportado (default ~/afip).

set -e

CUIT="${1:?Falta CUIT como primer argumento}"
NOMBRE="${2:?Falta nombre como segundo argumento}"
AFIP_HOME="${AFIP_HOME:-$HOME/afip}"
CERT_DIR="$AFIP_HOME/certs"

mkdir -p "$CERT_DIR"

echo "=== Generando clave privada RSA 2048 ==="
openssl genrsa -out "$CERT_DIR/private_key.key" 2048
chmod 600 "$CERT_DIR/private_key.key"

echo ""
echo "=== Generando CSR ==="
openssl req -new \
    -key "$CERT_DIR/private_key.key" \
    -subj "/C=AR/O=$NOMBRE/CN=$NOMBRE/serialNumber=CUIT $CUIT" \
    -out "$CERT_DIR/request.csr"

echo ""
echo "=== Archivos generados ==="
echo "  Clave privada: $CERT_DIR/private_key.key"
echo "  CSR:           $CERT_DIR/request.csr"
echo ""
echo "=== SIGUIENTES PASOS ==="
echo "1. Ingresa a https://auth.afip.gob.ar con clave fiscal"
echo "2. Administrador de Relaciones → agregar servicio → 'Administración de Certificados Digitales'"
echo "3. Subí $CERT_DIR/request.csr como nuevo certificado (alias libre, ej: 'facturacion')"
echo "4. Descargá el .crt y guardalo como $CERT_DIR/certificate.crt"
echo "5. En 'Administrador de Relaciones' asociá ese certificado al servicio 'Facturación Electrónica'"
echo "6. En 'Regímenes de Facturación y Registración (REAR/RECE/RFI)' dá de alta un punto de venta 'Web Services'"
