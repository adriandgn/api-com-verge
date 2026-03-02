# Plan de desarrollo: API RegistrationHub (FastAPI + Supabase + Vercel)

## Alcance y supuestos
1. La documentacion fuente es `docs/spec.md`.
2. La API sera serverless en Vercel con entry point `api/index.py`.
3. Base de datos en Supabase con tabla `registrations` y RLS.
4. Email transaccional via `fastapi-mail`.
5. El frontend es Next.js (proyecto separado).

## Objetivos de producto
1. Recepcion confiable de registros multi-perfil.
2. Validacion estricta y respuestas consistentes.
3. Persistencia segura con trazabilidad basica (IP, user-agent).
4. Confirmacion por email y notificacion interna.
5. Despliegue serverless repetible y con monitoreo basico.

## Epicas

### Epica 1: Fundacion del proyecto y despliegue

**User stories**
1. Como devops, quiero un proyecto FastAPI listo para Vercel para desplegar sin friccion.
2. Como backend, quiero configuraciones claras de entorno para desplegar en distintos ambientes.

**Tasks**
1. Crear estructura de carpetas `api/`, `templates/`, `requirements.txt`, `vercel.json`, `.env.example`.
2. Configurar `vercel.json` con `@vercel/python`, rutas y env vars.
3. Definir `requirements.txt` con versiones fijas de dependencias.
4. Documentar comandos de desarrollo local y despliegue.

### Epica 2: Base de datos y seguridad (Supabase)

**User stories**
1. Como backend, quiero una tabla unificada que soporte todos los perfiles.
2. Como owner del dato, quiero politicas RLS para proteger el acceso.

**Tasks**
1. Escribir SQL para crear tabla `registrations` con campos y restricciones.
2. Crear indices (profile, created_at, email, status, GIN sobre JSONB).
3. Crear trigger para `updated_at`.
4. Habilitar RLS y definir politicas de insercion y lectura admin.
5. Validar estrategia de conexiones (pooling vs direct) para Vercel.

### Epica 3: Modelos y validaciones (Pydantic)

**User stories**
1. Como backend, quiero validar payloads por perfil para evitar datos inconsistentes.
2. Como producto, quiero mensajes de error claros cuando un campo falla.

**Tasks**
1. Crear modelos base y modelos por perfil con restricciones de longitud y tipos.
2. Implementar validadores de URL y listas permitidas (interests).
3. Definir modelos de respuesta (success, message, registration_id).
4. Alinear los nombres de campos con los formularios del frontend.

### Epica 4: Persistencia y servicios auxiliares

**User stories**
1. Como backend, quiero una capa clara de acceso a datos.
2. Como operador, quiero envio de emails desacoplado de la respuesta HTTP.

**Tasks**
1. Implementar `database.py` con cliente Supabase cacheado.
2. Crear helpers `insert_registration` y `get_registrations`.
3. Implementar `email_service.py` con `fastapi-mail`.
4. Definir templates HTML base para confirmacion y notificacion.

### Epica 5: API REST y reglas de negocio

**User stories**
1. Como usuario, quiero enviar mi registro segun mi perfil y recibir confirmacion.
2. Como admin, quiero listar registros por perfil.
3. Como equipo, quiero health checks para monitoreo.

**Tasks**
1. Implementar POST `/api/registrations/{profile}` con validacion de perfil.
2. Verificar coincidencia entre path y payload.
3. Extraer IP y user-agent del request.
4. Insertar registro en Supabase y manejar errores.
5. Enviar emails via `BackgroundTasks`.
6. Implementar GET `/api/registrations` con `profile` y `limit`.
7. Implementar GET `/api/health`.
8. Implementar handler global de errores y CORS.

### Epica 6: Integracion frontend

**User stories**
1. Como frontend, quiero una integracion simple y segura contra CORS.

**Tasks**
1. Definir contrato JSON de cada perfil en un documento de referencia.
2. Proveer ejemplo de `handleSubmit` y conversion `FormData -> JSON`.
3. Proveer alternativa de proxy route en Next.js (`/app/api/registrations/[profile]/route.ts`).
4. Definir mensajes de respuesta para UX (success, error).

### Epica 7: Observabilidad y calidad

**User stories**
1. Como operador, quiero logs y metricas minimas para detectar fallos.
2. Como QA, quiero pruebas basicas automatizadas.

**Tasks**
1. Agregar logging basico de errores en endpoints.
2. Definir pruebas con `pytest` para health y POST valido.
3. Definir metricas objetivo (latencia, error rate, entrega email).
4. Documentar ubicacion de logs en Vercel y Supabase.

### Epica 8: Endurecimiento y escalabilidad

**User stories**
1. Como owner, quiero limitar abuso y proteger el backend.
2. Como equipo, quiero un camino claro para escalar.

**Tasks**
1. Implementar rate limiting con `slowapi`.
2. Evaluar proteccion adicional de endpoints admin (auth/keys).
3. Definir estrategia de backup y retencion de datos.
4. Documentar plan de migracion a tiers pagos (Supabase/Vercel).

## Roadmap sugerido

### Fase 1: Setup inicial (Dia 1)
1. Epica 1 completa.
2. Epica 2 tareas 1-3.

### Fase 2: Desarrollo backend (Dias 2-3)
1. Epica 3 completa.
2. Epica 4 completa.
3. Epica 5 tareas 1-5.

### Fase 3: Deploy y configuracion (Dia 4)
1. Epica 2 tareas 4-5.
2. Epica 5 tareas 6-8.

### Fase 4: Integracion frontend (Dia 5)
1. Epica 6 completa.

### Fase 5: Calidad y hardening (Dias 6-7)
1. Epica 7 completa.
2. Epica 8 completa.

## Criterios de aceptacion generales
1. Los cinco perfiles se validan y persisten correctamente.
2. La API devuelve `success` y `registration_id` en el POST exitoso.
3. Emails de confirmacion y notificacion se envian sin bloquear la respuesta.
4. Health checks responden en < 500 ms en condiciones normales.
5. Despliegue en Vercel sin configuraciones manuales adicionales.
