# Flujo local - versión 0.4

n8n 2.43.7 instalado y probado, Node 24.22.0 portable local. `daily.workflow.json` está importado, publicado y activo: 08:00 America/Lima → POST /daily autenticado → día anterior → PDF por empresa. La plantilla Meta está pendiente. El flujo anterior `demo.workflow.json` es histórico y no se ha activado.

La credencial Header Auth «GPS API local» ya está configurada y cifrada por n8n. El servicio diario escucha solo en 127.0.0.1:8766 y no expone archivos por HTTP. No hay token Meta dentro del flujo. El servicio anterior en 8765 no participa en la programación diaria.

Arrancar: `scripts/iniciar_automatizacion.cmd`. Detener: `scripts/detener_automatizacion.cmd`. Reconfigurar, con procesos detenidos: `scripts/configurar_n8n.cmd`. Reinstalar: `scripts/instalar_n8n.cmd`. El lockfile fija las dependencias locales; no usar latest.

Documentación vigente: `outputs/OPERACION_DIARIA_N8N.md` y `outputs/PASOS_PLANTILLA_META.md`. La ejecución real del motor n8n hacia Python fue exitosa; el envío por plantilla queda bloqueado mientras no exista una aprobada configurada.
