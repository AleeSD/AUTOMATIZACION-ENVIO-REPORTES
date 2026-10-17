# Resultado de la prueba WhatsApp

Prueba realizada el 16/10/2026 con reportes Onway del 15/10/2026.

**Resultado: tres documentos aceptados por Meta y recepción en los tres números confirmada por el usuario en el chat.** La confirmación es manual; no se obtuvo de un webhook. La apertura y revisión detallada de cada Excel aún no está confirmada.

| Receptor (terminación) | Empresa | Placas | Alertas |
|---|---|---|---:|
| …532 | AP. TRANSPORTES GENERALES E.I.R.L. | AAR-880, ARY-825 | 15 |
| …741 | ESTRELLA SERVICARGO E.I.R.L | C6E-921 | 62 |
| …566 | TRANSPORTE Y LOGISTICA ABIB E.I.R.L | BUR-735 | 74 |

Se envió un único Excel de empresa por número, con resumen en la leyenda. Total: 151 alertas de las tres empresas seleccionadas. Las otras empresas del lote no se enviaron.

Lote enviado: `outputs/reportes/2026-10-15/88ed967b56`. Se usaron los archivos `EMPRESA_20390610409.xlsx`, `EMPRESA_20611282461.xlsx` y `EMPRESA_20601075530.xlsx`.

El registro privado `.runtime/whatsapp/envios.sqlite` conserva la aceptación Meta, los identificadores de mensaje y la confirmación manual separada. No contiene tokens. La protección contra duplicados impide repetir empresa/día/receptor/remitente. No borrar el registro para repetir pruebas.

Token nuevo cifrado con DPAPI para esta cuenta; token previo revocado según confirmación del usuario. No se guardan secretos ni teléfonos completos en este informe.

Validación: 23 pruebas automatizadas, simulación Windows, cifrado DPAPI, subida y envío reales y recepción confirmada. Node de cuenta verificado: 26.12.0; npm 11.20.0. Sin elevación, servicios Windows ni Docker.

Pendientes para automatización diaria: motor n8n instalado y probado, selección automática de fecha/archivo terminado, plantillas de documento fuera de ventana y webhook de estados. El envío de esta prueba fue supervisado.
