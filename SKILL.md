---
name: afip-facturacion
description: Emitir facturas electrónicas de Argentina (AFIP/ARCA) para monotributistas — Factura C con CAE, PDF con QR según RG 4291/2018, vía web services WSAA/WSFE. Usar este skill cuando el usuario quiera facturar, emitir una factura, generar un comprobante electrónico AFIP/ARCA, obtener CAE, hacer un PDF de factura, o configurar facturación electrónica en Argentina. También aplica si mencionan "Factura C", "monotributo", "ARCA", "AFIP web services", punto de venta, o cualquier flujo que involucre emitir comprobantes fiscales argentinos.
---

# Facturación Electrónica AFIP/ARCA (Argentina)

Emite Factura C (monotributo) a Consumidor Final u otro receptor, obtiene el CAE vía WSFEv1 y genera el PDF oficial con QR code.

## Arquitectura

```
skill/
├── SKILL.md               (este archivo)
├── scripts/
│   ├── config.py          (lee emisor_config.json + cert paths)
│   ├── ssl_fix.py         (fix DH_KEY_TOO_SMALL)
│   ├── wsaa.py            (autenticación: TRA firmado → token/sign)
│   ├── facturar.py        (CLI: emite factura y genera PDF)
│   ├── generar_pdf.py     (PDF con QR, formato ARCA oficial)
│   └── generar_certificado.sh (genera clave privada + CSR)
└── references/
    ├── setup.md           (pasos completos de configuración inicial)
    └── troubleshooting.md (errores comunes)
```

**Datos del usuario** (NO viven dentro del skill): se guardan en un directorio de trabajo que el usuario elige, típicamente `~/afip/`:

```
~/afip/
├── emisor_config.json     (CUIT, razón social, domicilio, etc.)
├── certs/
│   ├── private_key.key    (RSA 2048, generada una vez)
│   ├── certificate.crt    (descargada de AFIP luego del CSR)
│   └── token_cache.json   (cache del token WSAA, auto-generado)
└── facturas_log.json      (log de facturas emitidas)
```

La variable de entorno `AFIP_HOME` apunta a este directorio; por defecto es `~/afip`.

## Cuándo usar este skill

Activá este skill cuando el usuario pida cualquiera de:

- "facturar", "emitir factura", "hacer una factura"
- "generá una factura C por $X"
- "necesito una factura de AFIP"
- "configurar facturación electrónica"
- "sacar CAE para una factura"
- "regenerar el PDF de una factura"

## Flujo de trabajo

### 1. Detectar si ya está configurado

Verificá si existe `$AFIP_HOME/emisor_config.json` y `$AFIP_HOME/certs/certificate.crt`. Si falta alguno, dirigí al usuario a la configuración inicial (ver `references/setup.md`).

### 2. Emitir factura

Desde el directorio de scripts del skill, con `AFIP_HOME` exportado:

```bash
export AFIP_HOME=~/afip
python3 scripts/facturar.py --monto 5000 --descripcion "Consultoría"
```

Parámetros importantes:
- `--monto N` — monto total (default 1.0)
- `--concepto 1|2|3` — 1=Productos, 2=Servicios, 3=Ambos (default 1)
- `--desde YYYY-MM-DD --hasta YYYY-MM-DD` — período facturado (requerido para concepto 2 o 3)
- `--descripcion "..."` — texto del renglón de detalle
- `--condicion-venta "Contado|Cuenta corriente|..."` — default Contado
- `--punto-venta N` — override del punto de venta (default: el de emisor_config.json)

Al aprobarse, el script:
1. Imprime número + CAE + vencimiento.
2. Genera `factura_NNNN_NNNNNNNN.pdf` en el directorio actual.
3. Append a `$AFIP_HOME/facturas_log.json`.

### 3. Regenerar PDF de una factura pasada

```bash
python3 scripts/generar_pdf.py   # usa la última del log
```

## Antes de emitir: verificar con el usuario

**Emitir una factura es una acción irreversible con consecuencias fiscales.** Antes de invocar `facturar.py`, mostrá al usuario monto, concepto, descripción y receptor, y pedí confirmación explícita en el chat. Una factura emitida queda registrada en AFIP y solo se puede anular emitiendo una nota de crédito.

## Edición de datos del emisor

`emisor_config.json` debe tener esta forma:

```json
{
  "cuit": "20XXXXXXXXX",
  "punto_venta": 3,
  "razon_social": "APELLIDO NOMBRE",
  "condicion_iva": "Responsable Monotributo",
  "domicilio": "Calle 123 - Ciudad",
  "ingresos_brutos": "Exento" o número de inscripción,
  "inicio_actividades": "01/05/2014"
}
```

Estos datos los ingresa el usuario una sola vez en el setup. AFIP bloquea los servicios de padrón (ws_sr_padron_*) para monotributistas, por eso no se pueden autocompletar.

## Ambiente: producción vs homologación

Por default el skill apunta a **producción** (servicios1.afip.gov.ar). Para pruebas, exportá `AFIP_ENV=homo` antes de correr los scripts — apunta a wsaahomo/wswhomo.

## Setup inicial

Ver `references/setup.md` para la guía completa: generar clave privada + CSR, subir al portal de AFIP, asociar el certificado al servicio "Facturación Electrónica", dar de alta el punto de venta por web services.

## Errores comunes

Ver `references/troubleshooting.md` — incluye DH_KEY_TOO_SMALL, "Computador no autorizado", tokens expirados, rechazos de CAE.
