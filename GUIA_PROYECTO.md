# Automatización GPS - O.S. Logistics Perú S.A.C.

Versión 0.4 · 16/10/2026 · guía de referencia vigente.

## Objetivo y decisiones
Entrada manual de reportes Onway. Un reporte por empresa con las placas que tengan exportación, destinado al coordinador asignado. Solo conducción y seguridad, sin puntajes al conductor. El envío automático será **PDF**, conservando el **Excel local**, por elección del usuario. La programación es a las **08:00 America/Lima del día siguiente**, para los datos del día anterior.

El piloto conserva tres empresas y números autorizados: AP. Transportes → …532; Estrella Servicargo → …741; Transporte y Logística ABIB → …566. Las demás empresas generan documentos locales y quedan fuera del envío. No se amplían ni reasignan receptores automáticamente.

## Arquitectura
Descarga manual Onway → carpeta por día → confirmación `_LISTO.json` con hashes → n8n 08:00 Lima → POST autenticado a Python en loopback → pandas/openpyxl + padrón → Excel por empresa y PDF con resumen/detalle → Meta Cloud API con plantilla PDF aprobada → registro SQLite contra duplicados.

El proceso Python calcula ayer en Lima, no utiliza la fecha fija de la demo original. Las entradas siguen siendo manuales; no hay acceso automático al GPS. El servicio no publica archivos ni acepta rutas o fechas arbitrarias por HTTP.

## Instalación y requisitos
Windows sin administrador, sin instaladores del sistema, servicios Windows ni Docker. Python 3.12 y entorno `.venv` local con dependencias en `requirements.lock.txt`. n8n 2.43.7 y Node 24.22.0 portable exclusivos del proyecto. Tu Node 26.12.0 y npm 11.20.0 del PATH permanecen sin cambios. La descarga de Node local fue verificada con el SHA-256 oficial.

n8n está instalado, importado, publicado y activo. Su interfaz está en http://127.0.0.1:5678 y el usuario creó la contraseña local. Se probó el flujo en el motor real. La versión queda fijada porque las instalaciones npm fuera de contenedor tienen cambios anunciados en versiones futuras; no actualizar a latest.

## Carpetas y configuración
- `REPORTES ONWAY/DD-MM-AAAA` o `AAAA-MM-DD`: un solo directorio por fecha, con CSV/XLSX manuales y `_LISTO.json`.
- `UNIDADES Y RUC.xlsx`: padrón PLACA/EMPRESA/RUC.
- `config/onway.json`: campos y categorías de alertas, generación PDF.
- `config/daily.json`: 08:00, America/Lima, envío PDF y nombre/idioma/variables de plantilla. Actualmente el nombre está vacío porque falta aprobación.
- `config/destinatarios.local.json`: números privados y una empresa por receptor.
- `config/meta.local.json`: token cifrado Windows DPAPI para esta cuenta, Phone Number ID y versión Graph.
- `.runtime/node24`, `.runtime/n8n`, `.runtime/npm-cache`: herramientas locales.
- `.runtime/state/.n8n`: base y credenciales de n8n; conservar su clave de cifrado.
- `.runtime/whatsapp/envios.sqlite`: registro persistente de envíos y confirmaciones manuales.
- `.runtime/daily`: lote reutilizable por día y huellas de entrada/configuración.
- `outputs/reportes/FECHA/LOTE`: seis Excel y PDF de empresa en el caso de prueba.
- `outputs/ESTADO_AUTOMATIZACION.json`: estado operativo actual, sin secretos.
- `scripts/`, `gps_demo/`, `n8n/`, `tests/`: arranque, programa, flujo/lockfile y pruebas.
- `work/`: apoyo, vistas previas y respaldo de versiones anteriores.

## Rutina diaria
Copiar completamente los reportes del día anterior en su carpeta. Esperar al menos 60 segundos desde la última modificación. Ejecutar `scripts/marcar_reportes_listos.cmd` e ingresar la fecha ISO del reporte. Si cambian archivos, repetir la confirmación. El marcador es una declaración del operador de que el lote está completo, además de validación técnica; no demuestra que Onway haya exportado toda la flota.

Mantener PC encendida, sesión iniciada, equipo sin suspensión e Internet a las 08:00. Hay arranque al iniciar sesión solo de esta cuenta mediante acceso en Inicio de Windows. Cerrar el navegador no detiene los procesos. Un equipo apagado no ejecuta horarios perdidos; usar ejecución manual al volver. Si faltan archivos a las 08:00, corregir y ejecutar manualmente: aún no hay reintentos periódicos.

Arranque: `scripts/iniciar_automatizacion.cmd`. Parada: `scripts/detener_automatizacion.cmd`. Ejecutar ahora: botón manual del flujo o `scripts/procesar_dia_anterior.cmd`. Reinstalar: detener primero y ejecutar `scripts/instalar_n8n.cmd`. Cambiar horario: editar hour/minute, detener, ejecutar `scripts/configurar_n8n.cmd` y reiniciar.

## Contrato y reportes
CSV UTF-8 o XLSX, primera hoja. Obligatorias: Placa/Patente, Fecha, Hora, Alerta. Fechas Onway DD/MM/AAAA y hora HH:MM:SS, o celdas nativas Excel. Padrón sin placas duplicadas y RUC de 11 dígitos. Se normalizan placas para el cruce y se conservan nombres del padrón. Se eliminan duplicados idénticos ignorando Secuencia/formato de placa, sin fusionar eventos diferentes por solo hora/tipo.

Categorías incluidas/excluidas explícitas. Nuevas categorías y placas fuera del padrón bloquean para revisión. Se incluyen Bache como seguridad vial y Fuente principal desconectada como seguridad del equipo. No se atribuye culpa al conductor. No se consideran vehículos sin archivo como vehículos sin incidentes.

El Excel conserva nombres y orden de campos útiles Onway, omite vacíos/administrativos y añade Resumen. El PDF incluye dashboard de conteos y todas las alertas seleccionadas en un detalle compacto con fecha, hora, placa, alerta, velocidad y zona. Campos adicionales, incluidas coordenadas, permanecen en el Excel local. Los documentos son fotografías de la ejecución; regenerar si cambian datos. El envío verifica hashes para impedir adjuntar documentos editados después de generar.

## Meta y fases
1. Completado: parser, empresa, Excel, simulación y primer envío supervisado de Excel. El 16/10 se enviaron tres reportes del 15/10 y el usuario confirmó recepción en los tres números.
2. Completado: instalación n8n local, horario 08:00 publicado, autenticación, PDFs, entrada confirmada, día anterior, reutilización de lotes y arranque de sesión. Se probó n8n → Python y el bloqueo por plantilla ausente.
3. Pendiente externo: crear y aprobar plantilla de documento PDF. Seguir `outputs/PASOS_PLANTILLA_META.md`; muestra ficticia disponible. Completar nombre e idioma aprobados en config/daily.json. `send` ya está true por la solicitud del usuario; configurar una plantilla válida habilita el siguiente horario. No se cambió el formato sin autorización: el usuario eligió PDF automático y Excel local.
4. Pendiente de validar: envío real por esa plantilla, recepción de PDF y seguimiento automático mediante webhook. También preparar token apto para varios días si el de desarrollo caduca.

Las plantillas de documento usan PDF; no asumir que una plantilla de bienvenida habilita Excel ni que enviarla abre la ventana de atención. El comando supervisado histórico de Excel sigue disponible con respuesta reciente confirmada, separado de la programación diaria.

## Seguridad y límites
Solo loopback: n8n 5678 y servicio Python 8766. Peticiones POST requieren token local; no aceptan rutas/fechas del solicitante. Meta usa token DPAPI local, fuera de n8n y Git; no se imprime ni se coloca en logs. Archivos reales, receptores, secretos y bases se excluyen de Git. Secretos leídos con esta cuenta Windows, sin elevación. El token expuesto fue revocado según confirmación del usuario.

Registro único por remitente/empresa/día/receptor, independiente de PDF/Excel o regeneración. No borrar la base para repetir. Se reserva antes de la red y se bloquean reintentos inciertos. Un fallo detiene el lote. Aceptación Meta no garantiza entrega; en el primer piloto se confirmó manualmente. Retención propuesta de archivos: siete días durante demo, pendiente de política interna; no hay borrado automático.

Límites: 10 MB por entrada/documento y 50 000 filas por archivo/día seleccionado. El marcador protege cambios y copia parcial, pero el operador debe confirmar la integridad del lote. No hay descarga GPS, evaluación disciplinaria, disponibilidad permanente, reintentos ciegos ni webhook público. No se crearon servicios Windows, Docker, reglas de firewall ni instalación global npm.

## Validación
31 pruebas automatizadas verificadas por la suite base y las pruebas afectadas. Incluyen fechas, clasificación, deduplicación, aislamiento de empresa/receptor, listas autorizadas, fórmulas como texto, hashes Excel/PDF, simulación sin red, ventana/plantilla, multipart, idempotencia y entradas tardías/cambiadas. Se probaron autenticación HTTP 403 y rutas 404, DPAPI, inicio/parada y flujo real n8n. Se revisaron visualmente todas las páginas PDF generadas y la muestra ficticia. El cron está publicado con timezone America/Lima; no se ha observado aún una ejecución futura de las 08:00. El envío por plantilla depende de su aprobación y prueba real.

## Documentación práctica
- `outputs/OPERACION_DIARIA_N8N.md`: rutina y estado operativo.
- `outputs/PASOS_PLANTILLA_META.md`: solicitud y activación de plantilla PDF.
- `outputs/ASIGNACION_PRUEBA.md`: empresa y receptor del piloto.
- `outputs/RESULTADO_PRUEBA_WHATSAPP.md`: resultado histórico del primer envío de Excel.

Fuentes: https://docs.n8n.io/hosting/installation/npm/ ; https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api ; https://help.twilio.com/articles/30691359630107-Creating-WhatsApp-content-template-for-media-files-not-working-for-DOCS-and-XLSX-files .
