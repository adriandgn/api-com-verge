# Matriz de pruebas: RegistrationHub API

## Matriz por perfil

| Perfil | Caso | Input | Resultado esperado |
| --- | --- | --- | --- |
| creator | Valido | payload completo | 200, `success=true`, `registration_id` |
| creator | Falta `name` | payload sin `name` | 422 |
| creator | URL invalida | `links` sin `http`/`https` | 422 |
| expert | Valido | payload minimo | 200 |
| expert | `field_expertise` corto | string < 5 | 422 |
| event-host | Valido | payload completo | 200 |
| event-host | Email invalido | `email` malformado | 422 |
| participant | Valido | interests permitidos | 200 |
| participant | interests invalidos | array fuera de lista | 422 |
| volunteer | Valido | payload completo | 200 |
| volunteer | `motivation` corta | string < 10 | 422 |

## Matriz por endpoint

| Endpoint | Caso | Resultado esperado |
| --- | --- | --- |
| GET `/` | Health check | 200, `status=healthy` |
| GET `/api/health` | Health check router | 200, `status=healthy` |
| POST `/api/registrations/{profile}` | Perfil invalido | 400 |
| POST `/api/registrations/{profile}` | Path != body | 400 |
| GET `/api/registrations` | Sin auth | Requiere proteccion en prod |
| GET `/api/registrations?profile=creator` | Filtrado | Solo `creator` |

## Matriz de errores y resiliencia

| Escenario | Resultado esperado |
| --- | --- |
| Error de Supabase | 500 con mensaje controlado |
| Error SMTP | POST responde 200 pero loggea fallo |
| Timeout DB | 500, retry planificado |
