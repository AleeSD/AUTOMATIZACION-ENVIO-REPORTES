# Asignación temporal para la demo

16/10/2026 · Versión 0.3. Asignación temporal guardada localmente; no representa responsables reales. Se seleccionaron tres de las seis empresas del lote para enviar un reporte de empresa por receptor. Los otros tres reportes permanecen locales.

| Alias temporal | Número autorizado (terminación) | Empresas del padrón | Placas del lote |
|---|---|---|---|
| Coordinador de prueba — AP. Transportes | …532 | AP. TRANSPORTES GENERALES E.I.R.L. | AAR-880, ARY-825 |
| Coordinador de prueba — Estrella | …741 | ESTRELLA SERVICARGO E.I.R.L | C6E-921 |
| Coordinador de prueba — ABIB | …566 | TRANSPORTE Y LOGISTICA ABIB E.I.R.L | BUR-735 |

Cada receptor recibe un reporte de su empresa, con todas sus placas con exportación: el piloto inicial recibió Excel; la automatización diaria 0.4 usará `EMPRESA_RUC.pdf` con plantilla aprobada y conservará el Excel local. No se mezclan empresas ni se adjuntan archivos por placa. Los números están en `config/destinatarios.local.json`, excluido de Git. El manifiesto de generación es simulado; el registro SQLite separa los envíos reales. Para cambiar de empresa, actualizar el RUC y regenerar.
