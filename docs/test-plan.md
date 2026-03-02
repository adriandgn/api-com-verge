# Plan de testeo: API RegistrationHub

## Objetivo
Validar que la API de registros multi-perfil funcione de forma correcta, segura y estable en escenarios locales y en Vercel, incluyendo persistencia en Supabase y envio de emails.

## Alcance
1. API FastAPI (endpoints y middlewares).
2. Persistencia en Supabase (insercion, lectura, indices basicos).
3. Servicio de email (fastapi-mail).
4. Integracion con frontend (contrato JSON).
5. Observabilidad y errores.

## Fuera de alcance
1. UI/UX del frontend.
2. Performance a gran escala mas alla del tier gratuito.
3. Integraciones externas futuras (Slack, webhooks, etc.).

## Entornos
1. Local: `uvicorn api.index:app --reload`.
2. Staging/Prod: Vercel serverless con variables reales.
3. Supabase: proyecto dedicado con RLS habilitado.

## Datos de prueba
1. Payloads validos para cada perfil.
2. Payloads invalidos (campos faltantes, longitudes invalidas, perfil incorrecto).
3. Emails de prueba (dominios controlados).

## Tipos de pruebas

### 1. Unitarias (Pydantic + validaciones)
**Objetivo:** asegurar reglas de validacion y errores claros.
**Casos clave:**
1. Creator: falta `name` o `practice_description` -> 422.
2. Expert: `field_expertise` corto -> 422.
3. Participant: `interests` fuera de lista -> 422.
4. URLs invalidas en `links` -> 422.

### 2. Integracion (API + DB)
**Objetivo:** validar flujo completo de escritura en Supabase.
**Casos clave:**
1. POST valido por cada perfil -> 200 + `registration_id`.
2. POST con `profile` en path distinto al body -> 400.
3. GET `/api/registrations` con `profile=creator` -> solo registros creator.
4. GET con `limit` -> maximo n registros.
5. Verificar que `ip_address` y `user_agent` se guarden.

### 3. Email (fastapi-mail)
**Objetivo:** asegurar envio de confirmacion y notificacion.
**Casos clave:**
1. Registro con email -> dispara confirmacion.
2. Registro sin email -> solo notificacion interna.
3. Error SMTP -> no debe romper respuesta del POST.

### 4. Seguridad y RLS
**Objetivo:** validar que solo service role pueda insertar.
**Casos clave:**
1. Insert directo sin service role -> falla (RLS).
2. API con service role -> inserta OK.
3. GET admin sin JWT admin -> bloqueado (si se implementa auth).

### 5. Observabilidad
**Objetivo:** asegurar logs basicos y errores controlados.
**Casos clave:**
1. Excepcion inesperada -> 500 + error handler global.
2. Logs visibles en Vercel para requests fallidas.

### 6. Smoke tests (post-deploy)
**Objetivo:** validar entorno Vercel en minutos.
**Casos clave:**
1. GET `/` -> `{"status":"healthy"}`.
2. POST `/api/registrations/creator` -> respuesta exitosa.
3. GET `/api/health` -> `{"status":"healthy"}`.

## Ejemplos de payloads

### Creator
```json
{
  "profile": "creator",
  "name": "Test Creator",
  "studio_brand": "Test Studio",
  "city": "Berlin",
  "links": "https://example.com",
  "practice_description": "Long description",
  "podcast_interest": false,
  "suggested_topics": "Materials"
}
```

### Participant
```json
{
  "profile": "participant",
  "name": "Test User",
  "email": "test@example.com",
  "city_country": "Berlin, DE",
  "interests": ["Craft Innovation"]
}
```

## Criterios de aceptacion
1. Todos los perfiles se validan con mensajes claros.
2. Inserciones exitosas guardan `uuid`, `profile`, `data`, `ip_address`, `user_agent`.
3. Emails se encolan sin bloquear el POST.
4. Health checks responden en < 500 ms.
5. El smoke test pasa en Vercel despues de cada deploy.

## Herramientas sugeridas
1. `pytest` + `fastapi.testclient` para pruebas automatizadas.
2. `curl` para smoke tests rapidos.
3. Supabase dashboard para verificacion manual de datos.
