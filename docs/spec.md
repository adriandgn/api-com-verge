# API Backend para RegistrationHub: FastAPI + Supabase + Vercel

**Proyecto:** Sistema de registro multi-perfil para COM/VERGE

**Stack tecnológico:** FastAPI (Python), Supabase (PostgreSQL), Vercel (Serverless), fastapi-mail

**Fecha:** Marzo 2026

**Autor:** Adrian Aguirre

## Resumen Ejecutivo

Este documento define la solución que utiliza FastAPI desplegado en Vercel como serverless functions, Supabase para almacenamiento PostgreSQL gratuito, y fastapi-mail para notificaciones por email.

### Ventajas de esta arquitectura

\begin{itemize}
\item \textbf{Costo cero inicial:} Supabase free tier (500MB storage, 50k rows), Vercel free tier (100GB bandwidth, 100 serverless invocations/día)
\item \textbf{Control total:} Propiedad completa de los datos y lógica de negocio
\item \textbf{Escalabilidad:} Arquitectura serverless que escala automáticamente
\item \textbf{Velocidad de desarrollo:} FastAPI con validación automática via Pydantic
\item \textbf{Professional:} Sistema de emails transaccionales, webhooks personalizados, analytics propios
\end{itemize}

## Arquitectura del Sistema

### Diagrama de flujo

┌─────────────────────┐
│  NextJS Frontend    │
│  (RegistrationHub)  │
└──────────┬──────────┘
           │ HTTP POST
           ▼
┌─────────────────────────────┐
│   Vercel Edge Network       │
│   (FastAPI Serverless)      │
│                             │
│  /api/registrations/{profile}│
└──────────┬──────────────────┘
           │
           ├─────► Supabase PostgreSQL
           │       (registrations table)
           │
           └─────► fastapi-mail
                   (Email confirmations)

### Componentes principales

\begin{enumerate}
\item \textbf{Frontend (NextJS):} RegistrationHub.tsx con formularios multi-perfil
\item \textbf{API (FastAPI):} Endpoints REST con validación Pydantic
\item \textbf{Base de datos (Supabase):} PostgreSQL con Row Level Security
\item \textbf{Email (fastapi-mail):} Sistema de notificaciones transaccionales
\item \textbf{Deployment (Vercel):} Serverless functions con auto-scaling
\end{enumerate}

## Base de Datos: Supabase PostgreSQL

### Esquema de tabla principal

-- Tabla registrations: almacena todos los perfiles
CREATE TABLE IF NOT EXISTS registrations (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    profile VARCHAR(50) NOT NULL CHECK (profile IN ('creator', 'expert', 'event-host', 'participant', 'volunteer')),
    data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    email VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'archived'))
);

-- Índices para queries rápidas
CREATE INDEX idx_registrations_profile ON registrations(profile);
CREATE INDEX idx_registrations_created_at ON registrations(created_at DESC);
CREATE INDEX idx_registrations_email ON registrations(email);
CREATE INDEX idx_registrations_status ON registrations(status);
CREATE INDEX idx_registrations_data_gin ON registrations USING GIN (data);

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_registrations_updated_at
    BEFORE UPDATE ON registrations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

### Mapeo de campos por perfil

Basado en el análisis del archivo RegistrationHub.tsx, los campos JSONB por perfil son:

\begin{table}
\begin{tabular}{|l|l|}
\hline
\textbf{Profile} & \textbf{Campos en JSONB data} \\
\hline
creator & name, studio\_brand, city, links, practice\_description, \\
 & podcast\_interest (bool), suggested\_topics \\
\hline
expert & name, organization, field\_expertise, city, \\
 & proposed\_topic, preferred\_format, bio\_links \\
\hline
event-host & organization\_name, type, city\_country, event\_type, \\
 & audience\_size, contact\_name, email \\
\hline
participant & name, email, city\_country, interests (array) \\
\hline
volunteer & name, email, city\_country, skills\_idea, \\
 & availability, motivation \\
\hline
\end{tabular}
\caption{Mapeo de campos por perfil de usuario}
\end{table}

### Row Level Security (RLS)

-- Habilitar RLS
ALTER TABLE registrations ENABLE ROW LEVEL SECURITY;

-- Policy: solo API puede insertar (usando service_role key)
CREATE POLICY "API can insert registrations"
    ON registrations FOR INSERT
    WITH CHECK (true);

-- Policy: admin puede leer todo
CREATE POLICY "Admin can read all"
    ON registrations FOR SELECT
    USING (auth.jwt() ->> 'role' = 'admin');

### Configuración de conexión

En Supabase Dashboard → Project Settings → Database:

\begin{itemize}
\item \textbf{Connection String (Direct):} Para desarrollo local
\item \textbf{Connection Pooling (Transaction):} Para Vercel serverless
\item \textbf{Service Role Key:} Para autenticación backend (settings → API)
\end{itemize}

Variables de entorno necesarias:

SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres:[password]@db.xxxxx.supabase.co:6543/postgres

## API Backend: FastAPI

### Estructura del proyecto

fastapi-registration-api/
├── api/
│   ├── __init__.py
│   ├── index.py              # Entry point para Vercel
│   ├── models.py             # Pydantic models
│   ├── database.py           # Supabase connection
│   ├── email_service.py      # fastapi-mail setup
│   └── routes/
│       ├── __init__.py
│       └── registrations.py  # Endpoints de registro
├── templates/                # HTML email templates
│   ├── confirmation.html
│   └── notification.html
├── requirements.txt
├── vercel.json               # Configuración Vercel
├── .env.example
└── README.md

### requirements.txt

fastapi==0.115.0
pydantic[email-validator]==2.9.0
pydantic-settings==2.5.2
supabase==2.9.0
fastapi-mail==1.4.1
python-multipart==0.0.9

### vercel.json

{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ],
  "env": {
    "SUPABASE_URL": "@supabase_url",
    "SUPABASE_SERVICE_ROLE_KEY": "@supabase_service_role_key",
    "DATABASE_URL": "@database_url",
    "MAIL_USERNAME": "@mail_username",
    "MAIL_PASSWORD": "@mail_password",
    "MAIL_FROM": "@mail_from"
  }
}

### api/index.py (Entry point)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.routes.registrations import router as registrations_router

app = FastAPI(
    title="COM/VERGE Registration API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS para NextJS frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://comverge.rived.community",
        "https://*.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "COM/VERGE Registration API"}

# Rate limiting básico
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Implementar rate limiting con Redis o in-memory cache
    response = await call_next(request)
    return response

# Incluir rutas
app.include_router(registrations_router, prefix="/api", tags=["registrations"])

# Error handler global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

### api/models.py (Pydantic Models)

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Literal
from datetime import datetime

# Base model
class RegistrationBase(BaseModel):
    profile: Literal["creator", "expert", "event-host", "participant", "volunteer"]

# Creator profile
class CreatorRegistration(RegistrationBase):
    name: str = Field(..., min_length=2, max_length=100)
    studio_brand: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=2, max_length=100)
    links: Optional[str] = Field(None, max_length=500)
    practice_description: str = Field(..., min_length=10, max_length=1000)
    podcast_interest: bool = False
    suggested_topics: Optional[str] = Field(None, max_length=500)
    
    @validator('links')
    def validate_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Links must be valid URLs')
        return v

# Expert profile
class ExpertRegistration(RegistrationBase):
    name: str = Field(..., min_length=2, max_length=100)
    organization: Optional[str] = Field(None, max_length=100)
    field_expertise: str = Field(..., min_length=5, max_length=200)
    city: str = Field(..., min_length=2, max_length=100)
    proposed_topic: Optional[str] = Field(None, max_length=500)
    preferred_format: Optional[Literal["talk", "panel", "workshop", "demo"]] = None
    bio_links: str = Field(..., min_length=10, max_length=1000)

# Event Host profile
class EventHostRegistration(RegistrationBase):
    organization_name: str = Field(..., min_length=2, max_length=100)
    type: Optional[str] = Field(None, max_length=100)
    city_country: str = Field(..., min_length=2, max_length=100)
    event_type: str = Field(..., min_length=5, max_length=200)
    audience_size: str = Field(..., max_length=50)
    contact_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr

# Participant profile
class ParticipantRegistration(RegistrationBase):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    city_country: str = Field(..., min_length=2, max_length=100)
    interests: List[str] = Field(default_factory=list)
    
    @validator('interests')
    def validate_interests(cls, v):
        allowed = ["Craft Innovation", "Tech Applications", "Markets Regulation", "Impact Culture"]
        if not all(interest in allowed for interest in v):
            raise ValueError(f'Interests must be one of {allowed}')
        return v

# Volunteer profile
class VolunteerRegistration(RegistrationBase):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    city_country: str = Field(..., min_length=2, max_length=100)
    skills_idea: str = Field(..., min_length=10, max_length=500)
    availability: Optional[str] = Field(None, max_length=200)
    motivation: str = Field(..., min_length=10, max_length=1000)

# Response models
class RegistrationResponse(BaseModel):
    success: bool
    message: str
    registration_id: Optional[str] = None

class RegistrationDetail(BaseModel):
    id: int
    uuid: str
    profile: str
    data: dict
    email: Optional[str]
    status: str
    created_at: datetime

### api/database.py (Supabase Connection)

from supabase import create_client, Client
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    supabase_url: str
    supabase_service_role_key: str
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

def get_supabase_client() -> Client:
    settings = get_settings()
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key
    )

# Helper function para insertar registro
async def insert_registration(profile: str, data: dict, email: str = None, ip: str = None, user_agent: str = None):
    supabase = get_supabase_client()
    
    result = supabase.table("registrations").insert({
        "profile": profile,
        "data": data,
        "email": email,
        "ip_address": ip,
        "user_agent": user_agent
    }).execute()
    
    return result.data[0] if result.data else None

# Helper function para obtener registros
async def get_registrations(profile: str = None, limit: int = 100):
    supabase = get_supabase_client()
    
    query = supabase.table("registrations").select("*")
    
    if profile:
        query = query.eq("profile", profile)
    
    result = query.order("created_at", desc=True).limit(limit).execute()
    
    return result.data

### api/email_service.py (fastapi-mail)

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List

class EmailSettings(BaseSettings):
    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int = 587
    mail_server: str = "smtp.gmail.com"
    mail_from_name: str = "COM/VERGE"
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    
    class Config:
        env_file = ".env"

def get_email_config():
    settings = EmailSettings()
    
    return ConnectionConfig(
        MAIL_USERNAME=settings.mail_username,
        MAIL_PASSWORD=settings.mail_password,
        MAIL_FROM=settings.mail_from,
        MAIL_PORT=settings.mail_port,
        MAIL_SERVER=settings.mail_server,
        MAIL_FROM_NAME=settings.mail_from_name,
        MAIL_STARTTLS=settings.mail_starttls,
        MAIL_SSL_TLS=settings.mail_ssl_tls,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
        TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates"
    )

async def send_confirmation_email(email: str, name: str, profile: str):
    """Envía email de confirmación al registrante"""
    
    conf = get_email_config()
    
    message = MessageSchema(
        subject=f"¡Bienvenido a COM/VERGE como {profile.replace('-', ' ').title()}!",
        recipients=[email],
        body=f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <h2>Hola {name},</h2>
                <p>Gracias por registrarte en COM/VERGE como <strong>{profile.replace('-', ' ').title()}</strong>.</p>
                <p>Hemos recibido tu información y pronto nos pondremos en contacto contigo.</p>
                <p>Mientras tanto, sigue nuestras novedades en:</p>
                <ul>
                    <li>Instagram: @com.verge</li>
                    <li>Web: https://comverge.rived.community</li>
                </ul>
                <p>¡Nos vemos pronto!</p>
                <p><em>El equipo de COM/VERGE</em></p>
            </body>
        </html>
        """,
        subtype=MessageType.html
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

async def send_admin_notification(profile: str, data: dict):
    """Envía notificación interna al equipo"""
    
    conf = get_email_config()
    
    message = MessageSchema(
        subject=f"Nuevo registro: {profile}",
        recipients=["comverge@rived.community"],  
        body=f"""
        <html>
            <body>
                <h3>Nuevo registro recibido</h3>
                <p><strong>Perfil:</strong> {profile}</p>
                <p><strong>Datos:</strong></p>
                <pre>{data}</pre>
            </body>
        </html>
        """,
        subtype=MessageType.html
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

### api/routes/registrations.py (Endpoints)

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from api.models import (
    CreatorRegistration,
    ExpertRegistration,
    EventHostRegistration,
    ParticipantRegistration,
    VolunteerRegistration,
    RegistrationResponse
)
from api.database import insert_registration, get_registrations
from api.email_service import send_confirmation_email, send_admin_notification
from typing import Union

router = APIRouter()

# Helper para extraer IP
def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host if request.client else "unknown"

# Endpoint principal de registro
@router.post("/registrations/{profile}", response_model=RegistrationResponse)
async def create_registration(
    profile: str,
    registration: Union[
        CreatorRegistration,
        ExpertRegistration,
        EventHostRegistration,
        ParticipantRegistration,
        VolunteerRegistration
    ],
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Endpoint para crear registros según perfil:
    - creator
    - expert
    - event-host
    - participant
    - volunteer
    """
    
    # Validar perfil
    valid_profiles = ["creator", "expert", "event-host", "participant", "volunteer"]
    if profile not in valid_profiles:
        raise HTTPException(status_code=400, detail=f"Perfil inválido. Debe ser uno de {valid_profiles}")
    
    # Validar que el perfil del body coincide con el path
    if registration.profile != profile:
        raise HTTPException(status_code=400, detail="El perfil en el body no coincide con el path")
    
    try:
        # Convertir a dict
        data = registration.model_dump(exclude={"profile"})
        
        # Extraer email si existe en data
        email = data.get("email")
        
        # Obtener metadata
        ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        # Insertar en DB
        result = await insert_registration(
            profile=profile,
            data=data,
            email=email,
            ip=ip,
            user_agent=user_agent
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al guardar registro")
        
        # Enviar emails en background
        if email:
            name = data.get("name", "Usuario")
            background_tasks.add_task(send_confirmation_email, email, name, profile)
        
        background_tasks.add_task(send_admin_notification, profile, data)
        
        return RegistrationResponse(
            success=True,
            message=f"Registro {profile} creado exitosamente",
            registration_id=result.get("uuid")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Endpoint para listar registros (admin)
@router.get("/registrations")
async def list_registrations(
    profile: str = None,
    limit: int = 100
):
    """
    Lista registros (requiere autenticación admin en producción)
    """
    try:
        registrations = await get_registrations(profile=profile, limit=limit)
        return {"success": True, "count": len(registrations), "data": registrations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Endpoint de health check específico
@router.get("/health")
async def health():
    return {"status": "healthy", "service": "registrations"}

## Frontend: Integración NextJS

### Modificaciones a RegistrationHub.tsx

Reemplazar el form handler actual con llamada real a la API:

// En RegistrationHub.tsx, agregar función handleSubmit

const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault();
  
  const formData = new FormData(e.currentTarget);
  const data: Record<string, any> = {};
  
  // Convertir FormData a objeto
  formData.forEach((value, key) => {
    // Manejar checkboxes (interests, podcast_interest)
    if (key === 'interests' || key === 'podcast') {
      if (!data[key]) data[key] = [];
      data[key].push(value);
    } else {
      data[key] = value;
    }
  });
  
  // Convertir podcast array a boolean
  if (data.podcast) {
    data.podcast_interest = data.podcast.length > 0;
    delete data.podcast;
  }
  
  // Agregar profile al payload
  const payload = {
    profile: displayProfile,
    ...data
  };
  
  try {
    const response = await fetch(`https://your-api.vercel.app/api/registrations/${displayProfile}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    
    if (response.ok && result.success) {
      // Mostrar mensaje de éxito
      alert('¡Gracias! Tu registro fue enviado exitosamente.');
      
      // Resetear formulario
      e.currentTarget.reset();
      
      // Opcional: redirigir a página de confirmación
      // router.push('/registration-success');
    } else {
      alert(`Error: ${result.detail || 'No se pudo completar el registro'}`);
    }
    
  } catch (error) {
    console.error('Error en envío:', error);
    alert('Error de conexión. Por favor intenta nuevamente.');
  }
};

// Actualizar el <form> para usar el handler
<form className="hub-form" onSubmit={handleSubmit}>
  {/* ... campos existentes ... */}
</form>

### Alternativa: Proxy en NextJS (mejor para CORS)

Crear `/app/api/registrations/[profile]/route.ts`:

// app/api/registrations/[profile]/route.ts
import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://your-api.vercel.app';

export async function POST(
  request: NextRequest,
  { params }: { params: { profile: string } }
) {
  try {
    const body = await request.json();
    
    const response = await fetch(`${API_URL}/api/registrations/${params.profile}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body)
    });
    
    const data = await response.json();
    
    return NextResponse.json(data, { status: response.status });
    
  } catch (error) {
    return NextResponse.json(
      { success: false, detail: 'Error de servidor' },
      { status: 500 }
    );
  }
}

Luego en el frontend llamar a tu propio endpoint:

const response = await fetch(`/api/registrations/${displayProfile}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
});

## Deploy: Vercel

### Paso 1: Preparar repositorio

# Crear repo Git
git init
git add .
git commit -m "Initial FastAPI registration API"

# Push a GitHub
git remote add origin https://github.com/adriandgn/api-com-verge.git
git push -u origin main

### Paso 2: Deploy en Vercel

Opción A: Dashboard

\begin{enumerate}
\item Ve a https://vercel.com/new
\item Import Git Repository → Selecciona tu repo
\item Framework Preset: Other
\item Root Directory: /
\item Build Command: (dejar vacío)
\item Output Directory: (dejar vacío)
\item Install Command: pip install -r requirements.txt
\item Click Deploy
\end{enumerate}

Opción B: CLI

# Instalar Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Para producción
vercel --prod

### Paso 3: Configurar variables de entorno

En Vercel Dashboard → tu proyecto → Settings → Environment Variables:

SUPABASE_URL = https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY = eyJhbGciOi...
DATABASE_URL = postgresql://postgres:...
MAIL_USERNAME = your-email@gmail.com
MAIL_PASSWORD = your-app-password
MAIL_FROM = noreply@comvergence.com

Para Gmail con fastapi-mail:

\begin{enumerate}
\item Habilitar 2FA en tu cuenta Gmail
\item Generar App Password: https://myaccount.google.com/apppasswords
\item Usar ese password en MAIL\_PASSWORD
\end{enumerate}

### Paso 4: Testing

# Health check
curl https://your-api.vercel.app/

# Test endpoint de registro
curl -X POST https://your-api.vercel.app/api/registrations/creator \
  -H "Content-Type: application/json" \
  -d '{
    "profile": "creator",
    "name": "Test User",
    "studio_brand": "Test Studio",
    "city": "Berlin",
    "practice_description": "This is a test registration",
    "podcast_interest": false
  }'

## Configuración de Email (fastapi-mail)

### Opciones de proveedores SMTP

\begin{table}
\begin{tabular}{|l|l|l|}
\hline
\textbf{Proveedor} & \textbf{Free Tier} & \textbf{Config} \\
\hline
Gmail & 500 emails/día & SMTP: smtp.gmail.com:587 \\
\hline
SendGrid & 100 emails/día & API Key o SMTP \\
\hline
Mailgun & 5000 emails/mes & SMTP: smtp.mailgun.org:587 \\
\hline
Resend & 100 emails/día & API (recomendado) \\
\hline
\end{tabular}
\caption{Proveedores SMTP gratuitos}
\end{table}

### Configuración Gmail (más simple)

# En .env
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx  # App password
MAIL_FROM=tu-email@gmail.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587

### Templates HTML personalizados

Crear `/templates/confirmation.html`:

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: var(--accent-mint); padding: 20px; text-align: center; }
        .content { padding: 30px 20px; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>¡Bienvenido a COM/VERGENCE!</h1>
        </div>
        <div class="content">
            <p>Hola {{ name }},</p>
            <p>Gracias por registrarte como <strong>{{ profile }}</strong>.</p>
            <p>Hemos recibido tu información y pronto nos pondremos en contacto.</p>
        </div>
        <div class="footer">
            <p>COM/VERGENCE © 2026</p>
        </div>
    </div>
</body>
</html>

Usar template en `email_service.py`:

from fastapi_mail import MessageSchema, MessageType

message = MessageSchema(
    subject="Bienvenido",
    recipients=[email],
    template_body={"name": name, "profile": profile},
    subtype=MessageType.html
)

await fm.send_message(message, template_name="confirmation.html")

## Plan de Implementación

### Fase 1: Setup inicial (Día 1)

\begin{enumerate}
\item Crear proyecto Supabase
\item Ejecutar SQL para crear tabla registrations
\item Crear estructura de carpetas FastAPI
\item Configurar Git y GitHub
\end{enumerate}

### Fase 2: Desarrollo backend (Días 2-3)

\begin{enumerate}
\item Implementar models.py con todos los Pydantic models
\item Implementar database.py con Supabase client
\item Implementar routes/registrations.py con endpoints
\item Configurar email\_service.py con fastapi-mail
\item Testing local con uvicorn
\end{enumerate}

### Fase 3: Deploy y configuración (Día 4)

\begin{enumerate}
\item Deploy en Vercel
\item Configurar variables de entorno
\item Configurar Gmail App Password
\item Testing de endpoints en producción
\end{enumerate}

### Fase 4: Integración frontend (Día 5)

\begin{enumerate}
\item Modificar RegistrationHub.tsx con handleSubmit
\item Crear proxy API route en NextJS (opcional)
\item Testing end-to-end de formularios
\item UI feedback (loading states, success messages)
\end{enumerate}

### Fase 5: Refinamiento (Días 6-7)

\begin{enumerate}
\item Implementar rate limiting
\item Agregar logging y monitoring
\item Crear dashboard admin simple
\item Documentación final
\end{enumerate}

## Testing y Validación

### Testing local

# Instalar dependencias
pip install -r requirements.txt

# Crear .env con variables
cp .env.example .env

# Correr servidor de desarrollo
uvicorn api.index:app --reload --port 8000

# Testing manual
curl -X POST http://localhost:8000/api/registrations/creator \
  -H "Content-Type: application/json" \
  -d '{"profile":"creator","name":"Test","studio_brand":"Studio","city":"Berlin","practice_description":"Testing local development"}'

### Testing automatizado (pytest)

Crear `tests/test_api.py`:

from fastapi.testclient import TestClient
from api.index import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_creator_registration():
    payload = {
        "profile": "creator",
        "name": "Test Creator",
        "studio_brand": "Test Studio",
        "city": "Berlin",
        "practice_description": "This is a test"
    }
    response = client.post("/api/registrations/creator", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] == True

def test_invalid_profile():
    response = client.post("/api/registrations/invalid", json={})
    assert response.status_code == 400

Ejecutar tests:

pytest tests/ -v

## Monitoreo y Mantenimiento

### Logs en Vercel

Ver logs en tiempo real:

vercel logs your-deployment-url

O en Dashboard → tu proyecto → Deployments → [deployment] → Logs

### Supabase Dashboard

Monitorear queries:

\begin{itemize}
\item Database → Query Performance
\item Database → Logs (Postgres logs)
\item Reports → API Traffic
\end{itemize}

### Métricas importantes

\begin{table}
\begin{tabular}{|l|l|}
\hline
\textbf{Métrica} & \textbf{Umbral} \\
\hline
Response time & < 500ms \\
Error rate & < 1\% \\
Email delivery & > 95\% \\
Database size & < 400MB (Supabase free) \\
\hline
\end{tabular}
\caption{Métricas de salud del sistema}
\end{table}

## Costos y Escalabilidad

### Tier gratuito combinado

\begin{itemize}
\item \textbf{Supabase Free:} 500MB storage, 2GB bandwidth, 50k rows
\item \textbf{Vercel Free:} 100GB bandwidth, 100 serverless hours/mes
\item \textbf{Gmail:} 500 emails/día
\end{itemize}

**Capacidad estimada:** ~1000 registros/mes sin costo

### Escalamiento futuro

Cuando excedas los límites gratuitos:

\begin{enumerate}
\item \textbf{Supabase Pro (\$25/mes):} 8GB storage, 50GB bandwidth, unlimited rows
\item \textbf{Vercel Pro (\$20/mes):} 1TB bandwidth, unlimited functions
\item \textbf{SendGrid/Mailgun:} Planes desde \$15/mes para 50k emails
\end{enumerate}


## Seguridad

### Medidas implementadas

\begin{itemize}
\item \textbf{CORS configurado:} Solo dominios autorizados
\item \textbf{Validación Pydantic:} Todos los inputs validados
\item \textbf{Rate limiting:} Prevenir abuse (implementar con slowapi)
\item \textbf{HTTPS automático:} Vercel provee SSL gratis
\item \textbf{Service Role Key:} Supabase usa autenticación segura
\item \textbf{Input sanitization:} Pydantic limpia datos automáticamente
\end{itemize}

### Mejoras recomendadas

# Agregar rate limiting con slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/registrations/{profile}")
@limiter.limit("5/minute")  # 5 requests por minuto
async def create_registration(...):
    ...

## Próximos Pasos

### Features adicionales sugeridas

\begin{enumerate}
\item \textbf{Dashboard admin:} Panel para ver/filtrar registros
\item \textbf{Export CSV:} Descargar registros en formato CSV
\item \textbf{Webhooks:} Notificar a Slack/Discord en nuevo registro
\item \textbf{Analytics:} Gráficos de registros por perfil/fecha
\item \textbf{Email templates:} Diseños profesionales con Mjml
\item \textbf{Double opt-in:} Confirmación por email antes de activar
\item \textbf{API keys:} Autenticación para integraciones externas
\item \textbf{Backup automático:} Supabase daily backups
\end{enumerate}

## Recursos y Referencias

### Documentación oficial

\begin{itemize}
\item FastAPI: https://fastapi.tiangolo.com
\item Supabase Python: https://supabase.com/docs/reference/python
\item Vercel Serverless: https://vercel.com/docs/frameworks/backend/fastapi
\item fastapi-mail: https://sabuhish.github.io/fastapi-mail
\end{itemize}

### Tutoriales recomendados

\begin{itemize}
\item Deploy FastAPI on Vercel: https://dev.to/highflyer910/deploy-your-fastapi-app-on-vercel-the-complete-guide-27c0
\item Supabase + FastAPI: https://supabase.com/docs/guides/auth/server-side/creating-a-client
\item fastapi-mail examples: https://github.com/sabuhish/fastapi-mail
\end{itemize}

## Prompt para Agente AI de Desarrollo

Eres un desarrollador experto en Python FastAPI y necesitas implementar una API REST para gestionar registros multi-perfil.

CONTEXTO:
- Proyecto: API de registros para COM/VERGENCE
- Stack: FastAPI + Supabase (PostgreSQL) + Vercel serverless + fastapi-mail
- Frontend existente: NextJS con RegistrationHub.tsx (5 perfiles: creator, expert, event-host, participant, volunteer)

TAREAS:

1. SETUP INICIAL
   - Crear estructura de carpetas según especificación
   - Configurar requirements.txt con versiones específicas
   - Crear vercel.json para deployment serverless
   - Setup .env.example con todas las variables necesarias

2. DATABASE
   - Conectar a Supabase usando service_role_key
   - Implementar helpers para insert_registration y get_registrations
   - Usar tabla "registrations" con campos: id, uuid, profile, data (JSONB), created_at, email, ip_address, user_agent, status

3. MODELS (api/models.py)
   - Crear Pydantic models para cada perfil (5 total)
   - Validación de campos obligatorios y opcionales según especificación
   - Validators para URLs y emails
   - Response models para API responses

4. ENDPOINTS (api/routes/registrations.py)
   - POST /api/registrations/{profile}: recibe JSON con datos del formulario
   - Validar profile contra lista permitida
   - Extraer IP y user-agent del request
   - Insertar en Supabase
   - Enviar emails en background (confirmación + notificación admin)
   - Retornar success + registration_id

5. EMAIL (api/email_service.py)
   - Configurar fastapi-mail con Gmail SMTP
   - Función send_confirmation_email(email, name, profile)
   - Función send_admin_notification(profile, data)
   - Templates HTML básicos inline por ahora

6. MAIN APP (api/index.py)
   - Configurar FastAPI con CORS para NextJS
   - Health check endpoint en "/"
   - Incluir router de registrations con prefix "/api"
   - Middleware para rate limiting básico
   - Error handler global

REQUISITOS TÉCNICOS:
- Usar async/await en todos los handlers
- BackgroundTasks para emails (no bloquear response)
- Proper error handling con HTTPException
- Logging de errores
- Comments en español

OUTPUT ESPERADO:
- Código completo de todos los archivos mencionados
- Listo para: pip install -r requirements.txt && vercel deploy
- Testing: curl examples para cada endpoint

ESTILO DE CÓDIGO:
- Type hints en todas las funciones
- Docstrings para funciones públicas
- Separación clara de concerns (models/database/routes/email)
- Configuración via environment variables

COMENZAR con api/models.py (Pydantic models para los 5 perfiles).

**Ventajas clave:**

\begin{itemize}
\item Control total sobre datos y lógica
\item Escalable hasta 1000+ registros/mes gratis
\item Professional email confirmations
\item API documentada automáticamente (FastAPI Docs)
\item Deploy en minutos con Vercel
\item Fácil de extender con nuevas features
\end{itemize}

Tiempo estimado de implementación: **5-7 días** para sistema completo funcional.

Próximo paso recomendado: Comenzar con Fase 1 (Setup Supabase + estructura FastAPI).
