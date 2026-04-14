# afip-facturacion

Skill de [Claude Code](https://claude.com/claude-code) para emitir **Factura C** (monotributo argentino) vía los web services de AFIP/ARCA: autenticación WSAA, obtención de CAE por WSFEv1 y generación de PDF oficial con QR según RG 4291/2018.

Pensado para monotributistas que quieren facturar desde la terminal con un comando, sin depender de webapps de terceros ni del portal de ARCA.

## ⚠️ Leé esto antes de usarlo

**Esto es algo que hice para mí y comparto "as-is" por si le sirve a alguien más.** No es un producto, no es un servicio, no es software mantenido. Es un script personal publicado en público.

- **No tiene mantenimiento.** No voy a responder issues, no voy a revisar pull requests, no voy a contestar preguntas. Si algo no funciona en tu setup, estás solo — forkealo, adaptalo, rompelo, mejoralo. Esa es toda la interacción que existe.
- **Puede fallar.** AFIP cambia formatos, endpoints, reglas de validación y servicios sin aviso. Algo que funciona hoy puede dejar de funcionar mañana y yo no lo voy a arreglar.
- **Puede tener bugs.** No está testeado exhaustivamente. Puede generar comprobantes incorrectos, calcular mal, o romper de formas que no anticipé.
- **Sin garantías de ningún tipo.** Ver [LICENSE](LICENSE): el software se provee "AS IS", sin garantía de funcionamiento, idoneidad, ni ausencia de errores. El autor no es responsable de ningún daño derivado de su uso.
- **Emitir facturas es irreversible y tiene consecuencias fiscales.** Un CAE emitido queda registrado en AFIP; anular requiere nota de crédito. Probá SIEMPRE primero en homologación (`AFIP_ENV=homo`) antes de apuntar a producción. La responsabilidad fiscal de lo que emitas es 100% tuya.
- **No soy contador ni asesor fiscal.** El skill es solo una herramienta técnica contra los web services de AFIP. Si no entendés qué es un CAE, qué implica emitir Factura C, o cómo tributa tu actividad, consultá con tu contador antes de correr cualquier cosa de acá.

Si después de leer todo esto querés usarlo igual, adelante. Pero el trato es: **lo usás bajo tu propio riesgo, sin expectativa de soporte de mi parte**.

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
