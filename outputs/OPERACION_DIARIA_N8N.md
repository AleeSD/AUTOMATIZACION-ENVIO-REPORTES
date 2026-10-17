# Operación diaria local - O.S. Logistics Perú

Versión 0.4 · 16/10/2026.

## Estado de instalación
- n8n 2.43.7 instalado dentro de `.runtime/n8n` y probado en su motor real.
- Node 24.22.0 portable exclusivo para n8n, dentro de `.runtime/node24`, descarga verificada con SHA-256 oficial.
- Tu Node 26.12.0 y npm 11.20.0 permanecen sin cambios en el PATH de la cuenta.
- Flujo «O.S. Logistics - reportes de empresa 08:00 Lima» importado, publicado y activo, con zona America/Lima.
- n8n accesible en [http://127.0.0.1:5678](http://127.0.0.1:5678). Cuenta local creada por el usuario.
- Procesamiento Python local autenticado en 127.0.0.1:8766. No se publica en Internet.
- Arranque al iniciar sesión, solo para esta cuenta, mediante acceso «OS Logistics GPS local» en la carpeta Inicio de Windows. No se crearon servicios ni tareas elevadas.

## Lo que falta para enviar automáticamente
Meta todavía no ha aprobado la plantilla. El flujo funciona y genera los documentos, pero su estado actual es **requiere_plantilla_meta**, sin envío automático. Seguir `PASOS_PLANTILLA_META.md` y completar nombre/idioma aprobados en `config/daily.json`.

El PDF se envía por plantilla y el Excel se conserva local. Se genera un PDF con resumen y detalle compacto de todas las alertas seleccionadas de la empresa; el Excel conserva los campos útiles completos. Se mantienen los tres coordinadores y empresas de prueba; no se reasignan empresas ni se amplían receptores automáticamente.

## Rutina antes de las 08:00
1. Descargar manualmente de Onway los reportes del día anterior.
2. Colocarlos dentro de `REPORTES ONWAY\DD-MM-AAAA` o `REPORTES ONWAY\AAAA-MM-DD`. Utilizar un solo nombre de carpeta para el mismo día. Ejemplo: el 17/10 a las 08:00 se procesará `16-10-2026`.
3. Terminar de copiar todos los archivos y esperar al menos 60 segundos desde su última modificación.
4. Ejecutar `scripts/marcar_reportes_listos.cmd` e indicar la fecha del reporte en formato `AAAA-MM-DD`. Se validan archivos y se guarda `_LISTO.json` con sus hashes. Esta confirmación evita procesar una descarga parcial. Si luego se añade, reemplaza o elimina un archivo, volver a marcar el lote.
5. Mantener la PC encendida, la sesión iniciada, Internet disponible y el equipo sin suspensión a las 08:00. Los procesos permanecen en segundo plano aunque cierres el navegador. Si el equipo está apagado o suspendido, n8n no puede ejecutar el horario perdido automáticamente.

## A las 08:00
El flujo calcula el día anterior en Lima, comprueba la confirmación y estabilidad de los archivos, valida las empresas seleccionadas, genera/reutiliza un lote y prepara un PDF por empresa. Si hay plantilla aprobada configurada, sube y envía un documento a cada receptor autorizado. No adivina archivos faltantes ni reutiliza un día antiguo.

Los Excel y PDF se guardan en `outputs/reportes/FECHA/LOTE`. El manifiesto contiene hashes y la asignación de empresa/receptor sin teléfonos completos. Solo hay tres empresas seleccionadas para envío; las demás se generan localmente.

Si faltan archivos, empresas o plantilla, se informa el estado y no se envía el lote. Corregir el pendiente y ejecutar manualmente el flujo; no hay reintento periódico después de las 08:00 en esta versión.

## Consultar y ejecutar
- Estado legible: `outputs/ESTADO_AUTOMATIZACION.json` y salida del nodo de n8n «Generar y enviar empresas».
- Ejecutar ahora: abrir el flujo en n8n y pulsar su ejecución manual, o ejecutar `scripts/procesar_dia_anterior.cmd`. Esto puede enviar si la plantilla aprobada ya está configurada.
- Arrancar: `scripts/iniciar_automatizacion.cmd`.
- Detener los procesos de este proyecto: `scripts/detener_automatizacion.cmd`.
- Cambiar el horario: editar `hour`/`minute` en `config/daily.json`, detener procesos, ejecutar `scripts/configurar_n8n.cmd` y volver a iniciar. El horario publicado actualmente es 08:00.
- Reinstalar: detener primero, ejecutar `scripts/instalar_n8n.cmd`; usa versiones fijadas y caché local. Los datos de n8n están separados en `.runtime/state/.n8n`.

El acceso de inicio está en `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\OS Logistics GPS local.lnk`. Eliminar únicamente ese acceso desactiva el arranque al iniciar sesión. No borra reportes ni credenciales.

## Seguridad y límites
El token Meta permanece cifrado con DPAPI para esta cuenta Windows y no está dentro de n8n. n8n guarda cifrada la credencial de la API local. La base `.runtime/whatsapp/envios.sqlite` evita repetir empresa/día/receptor/remitente, incluso si se regenera el PDF o antes se envió el Excel. No borrar ese registro para repetir pruebas.

Ante error de envío, se detiene el lote y los resultados inciertos quedan bloqueados para revisión. No hay reintento automático ciego. «Aceptado Meta» no equivale a «entregado»; el seguimiento por webhook no está implementado. La recepción de la prueba previa con Excel fue confirmada manualmente por el usuario.

El procesador Python usa su propio entorno y HTTP local; no depende del nodo Code de n8n ni de su Python task runner. El aviso de ese runner en los logs de n8n no impide este flujo, cuya ejecución HTTP ya se probó.

La instalación npm está fijada a n8n 2.43.7 porque la documentación avisa de cambios futuros hacia contenedores. No actualizar automáticamente a latest ni introducir Docker. Se conserva `n8n/package-lock.json` para reinstalar las mismas dependencias.

## Validación realizada
31 pruebas automatizadas correctas. Validación DPAPI sin mostrar el secreto. Ejecución real n8n → HTTP autenticado → Python → PDF/Excel → bloqueo por plantilla ausente; sin reenvíos. Se verificó publicación/activación y zona horaria, rechazo HTTP 403 sin token y 404 para rutas con parámetros, arranque/parada, acceso de Inicio de la cuenta y PDF de cada empresa revisados visualmente. La prueba real por plantilla queda pendiente de aprobación Meta.
