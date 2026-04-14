# afip-facturacion

Skill de [Claude Code](https://claude.com/claude-code) para emitir **Factura C** (monotributo argentino) vía los web services de AFIP/ARCA: autenticación WSAA, obtención de CAE por WSFEv1 y generación de PDF oficial con QR según RG 4291/2018.

Pensado para monotributistas que quieren facturar desde la terminal con un comando, sin depender de webapps de terceros ni del portal de ARCA.

## ⚠️ Proyecto personal, sin mantenimiento activo

Lo comparto por si le sirve a otra persona. No tengo capacidad de responder issues, revisar PRs ni garantizar que funcione en tu setup. Forkealo y adaptalo como necesites.

- **Sin garantías.** Emitir una factura electrónica es un acto fiscal irreversible. Probá siempre primero en homologación (`AFIP_ENV=homo`) y verificá los resultados contra tu situación tributaria.
- **No soy contador.** El skill genera comprobantes técnicamente válidos contra los WS de AFIP; la responsabilidad fiscal es del emisor.

## Qué hace

- Autentica contra WSAA con certificado X.509 (PKCS#7 firma del TRA).
- Emite Factura C a Consumidor Final u otro receptor con CAE.
- Genera el PDF replicando el formato oficial de ARCA, con QR válido para verificación.
- Cachea el token (~12 h) y loguea todas las facturas emitidas.
- Soporta conceptos: productos, servicios, mixto.

## Instalación

```bash
git clone https://github.com/<tu-user>/afip-facturacion ~/.claude/skills/afip-facturacion
pip install zeep cryptography lxml qrcode reportlab Pillow
```

Setup inicial (certificados + asociación al servicio AFIP): ver [`references/setup.md`](references/setup.md).

## Uso

```bash
export AFIP_HOME=~/afip
python3 scripts/facturar.py --monto 5000 --descripcion "Consultoría"
```

O desde Claude Code: _"emití una factura C por $5000 de consultoría"_.

## Licencia

MIT — ver [`LICENSE`](LICENSE).
