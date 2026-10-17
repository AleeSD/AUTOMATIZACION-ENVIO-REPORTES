# O.S. Logistics — demo local GPS

**Versión vigente 0.4:** n8n 2.43.7 instalado y activo a las 08:00 de Lima para el día anterior. PDF por empresa para envío automático mediante plantilla aprobada; Excel local conservado. Falta la aprobación de la plantilla Meta. Ver `outputs/OPERACION_DIARIA_N8N.md` y `outputs/PASOS_PLANTILLA_META.md`.

Empezar por [GUIA_PROYECTO.md](GUIA_PROYECTO.md), referencia de alcance y operación.

Se leen `REPORTES ONWAY` y `UNIDADES Y RUC.xlsx` y se generan reportes por empresa. El piloto mantiene tres empresas y un documento por número autorizado. La fecha 15/10/2026 se utilizó para la prueba con información del día anterior; la automatización calcula el día anterior en Lima en cada ejecución.

Generación manual: `scripts\onway.cmd`. PDF y Excel `EMPRESA_RUC` en `outputs/reportes/FECHA/LOTE`. Rutina diaria: copiar archivos en la carpeta del día, esperar 60 segundos, ejecutar `scripts\marcar_reportes_listos.cmd` con su fecha y mantener la PC encendida a las 08:00. Los originales permanecen intactos. Los lotes antiguos por placa/coordinador no se envían.

Para reinstalar: `scripts\setup.cmd`. Si Python es portable, establecer antes `set "GPS_PYTHON=C:\ruta\python.exe"`. Usar Python 3.12 para el archivo de dependencias fijadas `requirements.lock.txt`, que contiene las versiones probadas en esta PC.

Pasos externos: `outputs/PASOS_PLATAFORMAS.md`. Asignación temporal: `outputs/ASIGNACION_PRUEBA.md`. La asignación privada persistente está en `config/destinatarios.local.json`, excluida de Git.

Simulación: `scripts\whatsapp.cmd`. Configurar token nuevo cifrado: `scripts\configurar_meta.cmd`. Envío supervisado: `scripts\whatsapp.cmd -Enviar`, después de que los receptores escriban al remitente Meta. Instrucciones en `outputs/PRIMER_ENVIO_EMPRESAS.md`. **Prueba real completada el 16/10/2026: Meta aceptó los tres documentos y el usuario confirmó recepción en los tres números.** El registro evita repetir empresa/día/receptor/remitente. El seguimiento es manual; todavía no hay envío automático desde n8n.

Node de cuenta: 26.12.0 / npm 11.20.0, sin cambios. n8n usa Node 24.22.0 portable separado dentro del proyecto. Arranque: `scripts\iniciar_automatizacion.cmd`; parada: `scripts\detener_automatizacion.cmd`. n8n: http://127.0.0.1:5678 . Arranque automático al iniciar sesión de esta cuenta; no hay servicios Windows ni Docker.
