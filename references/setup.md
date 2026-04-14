# Setup inicial — AFIP Facturación Electrónica

Esto se hace **una sola vez** por monotributista. Después, emitir facturas es un solo comando.

## 0. Prerrequisitos

- Python 3.8+
- `pip install zeep cryptography lxml qrcode reportlab Pillow`
- `openssl` (viene con macOS/Linux)
- Clave fiscal AFIP nivel 3
- Monotributo activo

## 1. Elegir directorio de datos

Por defecto `~/afip/`. Para otro lugar, `export AFIP_HOME=/ruta/que/quieras`.

```bash
mkdir -p ~/afip/certs
export AFIP_HOME=~/afip
```

## 2. Crear `emisor_config.json`

En `$AFIP_HOME/emisor_config.json`:

```json
{
  "cuit": "20XXXXXXXXX",
  "punto_venta": 1,
  "razon_social": "APELLIDO NOMBRE",
  "condicion_iva": "Responsable Monotributo",
  "domicilio": "Calle 123 - Ciudad",
  "ingresos_brutos": "Exento",
  "inicio_actividades": "DD/MM/YYYY"
}
```

Datos fiscales: se sacan de la constancia de inscripción (https://seti.afip.gob.ar/padron-puc-constancia-internet/).

## 3. Generar clave privada + CSR

```bash
bash scripts/generar_certificado.sh 20XXXXXXXXX "APELLIDO NOMBRE"
```

Genera `$AFIP_HOME/certs/private_key.key` y `request.csr`.

## 4. Subir el CSR a AFIP

1. https://auth.afip.gob.ar → clave fiscal.
2. "Administrador de Relaciones de Clave Fiscal" (si no aparece, agregá el servicio).
3. Adherir servicio → AFIP → Servicios Interactivos → **"Administración de Certificados Digitales"**. Cerrá sesión y volvé a entrar.
4. Abrí "Administración de Certificados Digitales" → "Agregar alias" → nombre libre (ej. `facturacion`) → subí el `.csr`.
5. Descargá el `.crt` resultante y guardalo como `$AFIP_HOME/certs/certificate.crt`.

## 5. Asociar certificado al servicio WSFE

En "Administrador de Relaciones":

1. Nueva Relación.
2. Representado: tu CUIT.
3. Servicio: buscar "Facturación Electrónica" → AFIP → WebServices → **"Facturación Electrónica"**.
4. Representante: seleccioná el certificado que acabás de crear (por alias).
5. Confirmar con clave fiscal.

## 6. Dar de alta el punto de venta

Si todavía no tenés un punto de venta tipo "Web Services":

1. Ingresá al portal con clave fiscal.
2. Servicio "Regímenes de Facturación y Registración (REAR/RECE/RFI)" (adherirlo si no está).
3. ABM de puntos de venta → Agregar → Sistema de Facturación: **"Web Services"**.
4. Anotá el número y ponelo en `emisor_config.json` como `punto_venta`.

## 7. Probar

```bash
export AFIP_HOME=~/afip
cd <ruta-del-skill>/scripts
python3 wsaa.py   # debería imprimir un token
python3 facturar.py --monto 1
```

Si la factura se aprueba, se genera el PDF en el directorio actual y queda registrada en `$AFIP_HOME/facturas_log.json`.

## Homologación (testing)

Para probar sin emitir facturas reales:

```bash
export AFIP_ENV=homo
```

El entorno de homologación requiere un certificado separado (creado desde "Administración de Certificados Digitales" con alias en el ambiente de homologación, en https://wsass-homo.afip.gov.ar/wsass/portal/main.aspx).
