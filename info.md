# RegistrationHub API — visión general

## 1. Contexto
- Proyecto objetivo: `api-com-landing`, backend FastAPI serverless pensado para recibir los formularios multi-perfil de COM/VERGE RegistrationHub.
- Stack principal: FastAPI (Python) + Supabase (PostgreSQL) + fastapi-mail (Gmail) desplegado en Vercel usando funciones serverless y rutas `/api/registrations/{profile}`.
- Las instrucciones completas están en `docs/spec.md` (marzo 2026, autor Adrian Aguirre). El archivo será la fuente de verdad para el desarrollo.

## 2. Arquitectura resumida
- Next.js (frontend) envía POST a Vercel; la función FastAPI valida, escribe en Supabase y dispara emails.
- Supabase almacena todo en `registrations` (campo JSONB `data` por perfil) y ejecuta Row Level Security para proteger los datos.
- fastapi-mail maneja el envío de confirmaciones al usuario y notificaciones internas.
- Vercel despliega el servicio con `api/index.py` como entry point (CORS, health check, middleware, router).

## 3. Base de datos y esquema
- Tabla `registrations`: `id`, `uuid`, `profile`, `data` (JSONB), `created_at`, `updated_at`, `ip_address`, `user_agent`, `email`, `status` con índices para `profile`, `created_at`, `email`, `status` y índice GIN sobre `data`.
- Trigger `update_registrations_updated_at` mantiene `updated_at` fresco.
- Política RLS: solo la API que usa `service_role` puede insertar; solo admins (JWT con role=admin) pueden leer.
- Variables de entorno requeridas: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL` (para conexiones transaccionales y desarrollo local).

## 4. Modelos y validación (api/models.py)
- Profile enumerado: `creator`, `expert`, `event-host`, `participant`, `volunteer`.
- Cada perfil tiene modelo Pydantic con `Field` y validaciones específicas (longitudes, URLs, emails, intereses permitidos).
- Response models: `RegistrationResponse` y `RegistrationDetail` para respuestas consistentes.

## 5. Lógica de persistencia y servicios auxiliares
- `api/database.py` encapsula la creación cacheada del cliente Supabase (`create_client`) y helpers `insert_registration` + `get_registrations`.
- `api/email_service.py` configura `fastapi-mail` leyendo variables de entorno (`MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM`, etc.) y define `send_confirmation_email` + `send_admin_notification` usando plantillas o contenido inline.

## 6. Endpoints (api/routes/registrations.py)
- POST `/api/registrations/{profile}`: valida el perfil, fuerza coincidencia entre path y body, extrae IP/user-agent, inserta en Supabase y dispara emails via `BackgroundTasks`.
- GET `/api/registrations`: admite filtrado por perfil y `limit`, pensado para admins (requiere protección en producción).
- GET `/api/health`: health check adicional del router.

## 7. Entry point FastAPI (api/index.py)
- App FastAPI con metadata (`title`, `version`), middleware CORS para dominios de frontend, middleware placeholder para rate limiting, handler global de excepciones y router de `registrations` con prefijo `/api`.

## 8. Frontend e integración
- Se recomienda que `RegistrationHub.tsx` use un handler `handleSubmit` que convierta `FormData` a JSON, controle checkboxes (intereses, podcast), incluya el perfil (`displayProfile`) y llame a `https://your-api.vercel.app/api/registrations/{profile}`.
- Alternativa sugerida: crear una ruta proxy en Next (`/app/api/registrations/[profile]/route.ts`) para evitar problemas de CORS y permitir usar `NEXT_PUBLIC_API_URL`.

## 9. Deploy y configuración
- `requirements.txt` fija FastAPI, supabase, fastapi-mail, pydantic-settings y multipart.
- `vercel.json` apunta a `api/index.py`, define variables de entorno (incluso con secretos referenciados `@supabase_url`, etc.).
- Proceso de despliegue: `vercel login`, `vercel`, uso del CLI o dashboard y configuración directa de env vars (Supabase, correo).
- Recomendaciones de mailing: usar Gmail con App Password (2FA habilitada) o proveedores alternativos (SendGrid, Mailgun, Resend).

## 10. Testing, monitoreo y SLOs
- Local: `pip install -r requirements.txt`, copiar `.env.example`, correr `uvicorn api.index:app --reload` y usar `curl` para health + POST.
- Automatizado propuesto: `tests/test_api.py` con FastAPI TestClient; pruebas de health, registro válido e invalid profile.
- Logs y métricas en Vercel (dashboard o `vercel logs`) y Supabase (Query Performance, Logs). Métricas sugeridas: response time <500ms, error rate <1%, email delivery >95%, DB <400MB.

## 11. Seguridad y próximos pasos
- Medidas incluidas: CORS limitado, validación Pydantic, rate limiting sugerido (slowapi/limiter), HTTPS garantizado por Vercel, uso de service role key, sanitización automática.
- Mejora prioritaria: implementar rate limiting + registrar logs/monitoring + agregar dashboard admin, export CSV, webhooks, double opt-in, API keys, backups automáticos.

## 12. Repositorio
- El directorio actual no está inicializado con Git (`fatal: not a git repository`). El documento espec define un repo objetivo en GitHub `https://github.com/adriandgn/api-com-verge.git`, que debe crearse y sincronizarse cuando se lance el servicio.
