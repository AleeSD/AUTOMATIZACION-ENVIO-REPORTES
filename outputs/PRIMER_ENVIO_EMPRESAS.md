# Primer envío supervisado de reportes por empresa

**Nota 0.4:** este documento conserva el procedimiento de Excel supervisado ya probado. Para automatización diaria se usará PDF por empresa con plantilla aprobada y Excel local, según la decisión posterior del usuario. Ver `OPERACION_DIARIA_N8N.md` y `PASOS_PLANTILLA_META.md`.

Versión 0.3 · 16/10/2026. Información del día 15/10/2026 para probar el día anterior.

**Prueba completada:** Meta aceptó los tres documentos y el usuario confirmó que llegaron a los tres números. Consultar `RESULTADO_PRUEBA_WHATSAPP.md`. El registro evita repetir el mismo lote.

## Selección del piloto
Se generan los seis reportes de empresa del lote, pero solo se envían estos tres, uno por número:

| Número terminado en | Empresa simulada del coordinador | Placas incluidas | Alertas |
|---|---|---|---:|
| 532 | AP. TRANSPORTES GENERALES E.I.R.L. | AAR-880, ARY-825 | 15 |
| 741 | ESTRELLA SERVICARGO E.I.R.L | C6E-921 | 62 |
| 566 | TRANSPORTE Y LOGISTICA ABIB E.I.R.L | BUR-735 | 74 |

Los números completos están en la configuración privada. Ningún reporte de otra empresa se adjunta a estos mensajes. Las otras empresas quedan fuera de la prueba. Los lotes históricos por placa/coordinador no se usan ni son aceptados por el nuevo adaptador.

Los scripts toman el último lote de empresa terminado correctamente, indicado en `outputs/reportes/ultimo_lote_empresa.json`. Esto respeta el día usado al generar, aunque sea el día anterior. El plan muestra siempre la fecha y la ruta. También se puede fijar un lote explícito con `-Lote "RUTA_DEL_LOTE"`. El servicio n8n todavía usa la fecha fija de `config/onway.json` y debe actualizarse manualmente.

## Pasos desde la carpeta del proyecto
1. Abrir `scripts\configurar_meta.cmd`. Pegar el **token nuevo** en la entrada oculta. El token anterior ya fue revocado según confirmación del usuario y no se utiliza. La configuración conserva Phone Number ID `1390443250816204` y versión `v25.0` aportados en el ejemplo. Si Meta cambia esos valores, modificar únicamente esos campos no secretos en `config/meta.local.json`.
2. Abrir `scripts\whatsapp.cmd`. Solo muestra el plan: empresa, teléfono enmascarado, Excel, placas y conteo; no sube archivos ni envía mensajes. No necesita token para simular.
3. Pedir a los tres compañeros que escriban «PRUEBA» al **número remitente de prueba de Meta**. La verificación del receptor en Meta y su respuesta son cosas distintas. El usuario confirmó que están verificados y que escribirán; falta comprobar las respuestas efectivas. La plantilla `hello_world` de bienvenida no adjunta reportes ni sustituye esa respuesta.
4. Abrir una consola normal en la raíz del proyecto y ejecutar `scripts\whatsapp.cmd -Enviar`. Se imprime el plan y se pregunta si los tres receptores escribieron al remitente hace menos de 24 horas. Escribir `SI` solo cuando se haya comprobado. El programa sube cada Excel a Meta y envía un documento con resumen en la leyenda: un mensaje por receptor.
5. Confirmar en los teléfonos que llegó el archivo y abre correctamente. `aceptado_meta` indica aceptación de la solicitud; no garantiza entrega. El seguimiento automático por webhook todavía no está implementado.

No ejecutar el envío real hasta guardar el token nuevo y comprobar las respuestas de los tres receptores. Fuera de la ventana de atención se necesita una plantilla aprobada compatible con documento; este adaptador aún no la envía. Si Meta devuelve error, el lote se detiene y no se intenta convertir automáticamente a otro tipo de mensaje.

## Protección y repetición de la prueba
El token se guarda con cifrado Windows DPAPI para esta cuenta, en `config/meta.local.json`, excluido de Git. No se muestra, no se registra y no hace falta pegarlo en el chat. Los scripts no requieren elevación ni cambian la política de ejecución permanente; el permiso de ejecución se limita al proceso de PowerShell del script.

El programa comprueba destinatario autorizado, empresa, contenido y hash del Excel antes de tocar la red. Los envíos se registran en `.runtime/whatsapp/envios.sqlite`. Una empresa/día/receptor/remitente ya registrada se omite en ejecuciones posteriores, incluso si se regenera el Excel. Un fallo durante el envío queda como incierto y no se reintenta automáticamente. Si se interrumpe la PC, no borrar el registro: revisar primero en Meta y en el teléfono.

Para repetir deliberadamente un envío del mismo día, hace falta revisar el caso y preparar un mecanismo explícito de repetición; no borrar la base para forzarlo. La demo actual prioriza evitar duplicados.

## Node y n8n
Se verificó el PATH de la cuenta: `C:\Users\transporte.ope3\tools\nodejs`. Funcionan Node **26.12.0** y npm **11.20.0**. Esta sesión prioriza el Node de la aplicación, por lo que el lanzador n8n prefiere explícitamente el portable del usuario.

n8n todavía no está instalado ni probado. Su documentación npm indica Node 20.19–24.x y deprecación npm desde 3.0; los metadatos del paquete consultado `n8n@2.43.7` indican engine `>=24.0.0`. Node 26 no debe darse por validado con n8n por solo pasar esa comprobación. Se puede probar una versión exacta en carpeta local o usar Node 24 portable separado; no se modifica el PATH de la cuenta. **La prueba de envío Python puede hacerse sin n8n.**

Referencias: [instalación oficial n8n](https://docs.n8n.io/hosting/installation/npm/), [paquete oficial en npm](https://www.npmjs.com/package/n8n), [Cloud API de Meta](https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api).

## Estado de validación
23 pruebas automatizadas pasaron. Se probó DPAPI, el lanzador Windows y la API real con el token nuevo: tres mensajes aceptados y recepción confirmada manualmente por el usuario. La apertura y revisión del contenido de cada Excel aún no se ha confirmado. El seguimiento automático por webhook y el motor n8n siguen pendientes.
