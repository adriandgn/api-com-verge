-- Create table used by POST /api/sponsors
create table if not exists public.sponsor_inquiries (
  id bigserial primary key,
  uuid uuid not null default gen_random_uuid(),
  name text not null,
  company text not null,
  phone text,
  email text not null,
  message text not null,
  ip_address text,
  user_agent text,
  status text not null default 'new',
  created_at timestamptz not null default now()
);

create index if not exists sponsor_inquiries_created_at_idx
  on public.sponsor_inquiries (created_at desc);

