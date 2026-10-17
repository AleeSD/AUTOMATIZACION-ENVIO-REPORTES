# Lote revisado — 15/10/2026

Versión 0.3: se utilizan únicamente reportes de empresa. Consultar `reportes/ultimo_lote_empresa.json` para la carpeta activa. Las carpetas históricas v0.2 por placa/coordinador se conservan, pero no se envían.

818 filas originales → 3 duplicados exactos eliminados → 627 eventos operativos excluidos → **188 alertas seleccionadas**.

| Archivo de placa | Alertas |
|---|---:|
| AAR-880.xlsx | 10 |
| AKO-712.xlsx | 9 |
| ARY-825.xlsx | 5 |
| B1Y-801.xlsx | 1 |
| BUR-735.xlsx | 74 |
| BXQ-847.xlsx | 27 |
| C6E-921.xlsx | 62 |

El lote nuevo contiene seis Excel `EMPRESA_...xlsx` y `manifest.json` con trazabilidad y tres mensajes simulados, un documento por receptor: AP. Transportes (15 alertas) → …532, Estrella (62) → …741, ABIB (74) → …566. No se generan reportes por placa ni consolidados de coordinador. Las empresas se obtienen del padrón. La tabla anterior es un desglose de control de eventos por placa, no una lista de archivos que se vayan a enviar.

El diseño de dashboard conserva la estructura revisada. Se verificaron conteos y hashes: originales sin cambios. Las 23 pruebas pasaron. La API real se probó: Meta aceptó los tres documentos y el usuario confirmó recepción en los tres números. n8n sigue pendiente. El lote enviado fue `reportes/2026-10-15/88ed967b56`; las otras carpetas son históricas.

Abrir `VISTA_PREVIA_EMPRESA.png` para ver el diseño sin abrir Excel. Para volver a generar: ejecutar `scripts/onway.cmd` e ingresar la fecha. Para simular los tres envíos: `scripts/whatsapp.cmd`. Para el envío real supervisado: consultar `PRIMER_ENVIO_EMPRESAS.md`.

Hay cuatro registros SOS en ARY-825; revisar su significado y contexto en Onway. El resumen muestra lo exportado y no confirma por sí mismo una emergencia activa.
