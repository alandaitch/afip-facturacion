# Troubleshooting

## `DH_KEY_TOO_SMALL` o `SSL: DH_KEY_TOO_SMALL`

AFIP usa claves Diffie-Hellman débiles. Ya está resuelto en `ssl_fix.py` (baja `SECLEVEL` a 1). Si aparece, verificá que `wsaa.py` y `facturar.py` estén importando `get_afip_session` de `ssl_fix`.

## `Computador no autorizado a acceder al servicio`

- Certificado no asociado al servicio WSFE. Volvé al paso 5 del setup.
- Estás usando el certificado de producción contra homologación o viceversa: son distintos.

## `El CEE no se encuentra autorizado a emitir comprobantes`

Punto de venta no dado de alta como "Web Services" en AFIP. Paso 6 del setup.

## Token expirado / `expired TA`

El token dura ~12 horas. Se cachea automáticamente en `$AFIP_HOME/certs/token_cache.json`. Para forzar renovación:

```bash
rm $AFIP_HOME/certs/token_cache.json
```

O en Python: `obtener_credenciales(force=True)`.

## Factura rechazada con `10015 Fecha del comprobante invalida`

La fecha debe estar dentro de ±5 días de hoy (productos) o ±10 (servicios). Verificá reloj del sistema.

## Padrón no autorizado (`ws_sr_padron_*`)

AFIP bloquea los servicios de padrón para monotributistas. Por eso los datos del receptor no se auto-completan — se pasan por parámetro o se deja Consumidor Final.

## PDF con QR que no escanea

El QR codifica JSON base64. Verificá que `datos_factura` tenga `cae` como número (no string vacío) y `fecha` en formato `YYYYMMDD` o `YYYY-MM-DD`.

## `openssl genrsa` pide passphrase

No uses `-aes256` ni `-des3`. La clave debe quedar sin cifrar (la protege el filesystem con `chmod 600`).
