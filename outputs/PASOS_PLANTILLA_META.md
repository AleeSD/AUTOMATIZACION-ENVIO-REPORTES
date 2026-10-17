# Solicitar la plantilla para el PDF diario

La automatización local ya está instalada y publicada a las **08:00 de Lima** para procesar el día anterior. Falta una plantilla aprobada para iniciar el envío diario sin depender de que los coordinadores escriban primero. Por decisión del usuario, se enviará **PDF** y se conservará el **Excel local**.

## Crear y enviar a revisión
1. Entrar a [WhatsApp Manager](https://business.facebook.com/wa/manage/message-templates/) con la cuenta que administra el WhatsApp Business de esta aplicación. Elegir la cuenta asociada al remitente usado en la prueba; no los teléfonos de los empleados, que son receptores.
2. Abrir **Plantillas de mensajes / Message templates → Crear plantilla**. Los nombres de las pantallas pueden variar por cuenta.
3. Proponer categoría **Utilidad / Utility**, al tratarse de un reporte operativo solicitado. Meta decide su clasificación y aprobación; no está garantizada. No añadir promoción, publicidad ni ventas al texto.
4. Nombre: `reporte_gps_empresa_diario`. Idioma: **Español**. Anotar el código exacto que muestre Meta (por ejemplo `es`); se debe usar ese mismo código en la configuración.
5. Seleccionar variables **numéricas/posicionales** si se ofrece esa elección. Encabezado: **Documento**. Subir `outputs/PLANTILLA_EJEMPLO_FICTICIO.pdf`, que contiene datos ficticios. No subir XLSX como muestra de plantilla; el Excel permanece local.
6. Copiar el cuerpo propuesto y proporcionar las muestras de las cuatro variables que pida Meta.
7. Pie opcional: `O.S. Logistics Perú S.A.C.`. No hacen falta botones.
8. Enviar a revisión y esperar estado **Aprobada / Approved**. Si queda Pendiente, Rechazada o Pausada, no configurar su nombre como lista para enviar. Revisar el motivo específico antes de modificarla.

## Cuerpo propuesto

Hola, coordinador de {{1}}. Adjuntamos el reporte GPS solicitado correspondiente al {{2}}. Incluye {{3}} unidades con exportación y {{4}} alertas de conducción y seguridad. Por favor, revise el documento adjunto.

| Variable | Contenido que enviará el sistema | Muestra ficticia |
|---|---|---|
| {{1}} | Nombre de la empresa | EMPRESA DEMO S.A.C. |
| {{2}} | Fecha del reporte | 2026-10-15 |
| {{3}} | Cantidad de placas con exportación | 1 |
| {{4}} | Cantidad de alertas seleccionadas | 2 |

## Después de la aprobación
Abrir `config/daily.json` y completar únicamente el nombre e idioma aprobados:

```json
"template": {
  "name": "reporte_gps_empresa_diario",
  "language": "es",
  "body_parameters": ["empresa", "fecha", "placas", "alertas"]
}
```

Usar `es` solo si coincide con el idioma real de la plantilla aprobada. Mantener el orden de las variables. La propiedad `send` ya está en `true` por la solicitud de automatización: completar el nombre habilita el envío en la siguiente ejecución programada, siempre que el lote esté listo y no exista envío previo. No hace falta volver a publicar n8n para cambiar el nombre de plantilla.

Para probarla inmediatamente, usar «Ejecutar ahora» en el flujo o `scripts/procesar_dia_anterior.cmd`. El día 15/10/2026 ya tiene envíos registrados: el sistema los omitirá para evitar duplicados, aunque ahora el formato sea PDF. Para probar otro día, preparar su lote real; no borrar el registro de envíos.

Si la cuenta de prueba no ofrece creación de plantillas, revisar en Meta la cuenta WhatsApp Business seleccionada y los permisos del portafolio. El responsable de ese negocio deberá habilitar el acceso o la cuenta correspondiente. Esto no requiere ser administrador de Windows. No registrar los números receptores como remitentes empresariales para resolverlo.

## Token para varios días
El token de desarrollo puede caducar. Para el piloto de varios días, el responsable del portafolio debe configurar un token de usuario del sistema con acceso al WhatsApp Business y permiso de mensajería, según las opciones de Meta. Guardar el reemplazo con `scripts/configurar_meta.cmd`; no pegarlo en el chat ni en el flujo. El cifrado y la cuenta Windows actual se mantienen.

## Referencias
- [Ejemplo oficial de Meta de plantilla con documento](https://www.postman.com/meta/whatsapp-business-platform/request/ep5w4rc/create-template-w-document-header-text-body-a-phone-number-button-and-a-url-button).
- [Documentación oficial Cloud API](https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api).
- [Limitación documentada de XLSX en plantillas de WhatsApp](https://help.twilio.com/articles/30691359630107-Creating-WhatsApp-content-template-for-media-files-not-working-for-DOCS-and-XLSX-files). La plantilla usa PDF; el XLSX continúa disponible para revisión local.
