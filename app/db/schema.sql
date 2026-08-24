-- Foto na Hora — schema Supabase (PostgreSQL) — MVP
-- ADR-0010 (stack) · ADR-0005 (privacidade/efemeridade) · ADR-0012 (créditos)
-- Rodar no SQL editor do Supabase. Auth de usuários usa o schema `auth` nativo do Supabase.
-- Extensão pgvector é opcional no MVP (match roda no worker, EXP-06); deixamos pronta.

create extension if not exists vector;

-- ---------------------------------------------------------------------------
-- FOTÓGRAFO (perfil do usuário pagante) — 1:1 com auth.users
-- ---------------------------------------------------------------------------
create table if not exists photographer (
  id            uuid primary key references auth.users(id) on delete cascade,
  name          text not null,
  credits       int  not null default 0,          -- ADR-0012: pagamento único = créditos por evento
  credits_total int  not null default 0,
  created_at    timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- EVENTO
-- ---------------------------------------------------------------------------
create table if not exists event (
  id             uuid primary key default gen_random_uuid(),
  photographer_id uuid not null references photographer(id) on delete cascade,
  name           text not null,
  event_date     date,
  code           text not null unique,             -- código curto do QR (ex.: 'A7K2')
  status         text not null default 'live',     -- live | done
  expires_at     timestamptz,                      -- ADR-0005: sessão do evento expira
  created_at     timestamptz not null default now()
);
create index if not exists idx_event_code on event(code);

-- ---------------------------------------------------------------------------
-- FOTO (tratada) — bytes ficam no Cloudflare R2 (ADR-0011), aqui só metadados
-- ---------------------------------------------------------------------------
create table if not exists photo (
  id           uuid primary key default gen_random_uuid(),
  event_id     uuid not null references event(id) on delete cascade,
  r2_key       text not null,                      -- caminho no bucket R2
  cdn_url      text not null,                      -- URL pública (egress zero)
  taken_at     timestamptz,                        -- shutter (correlação, §6 CLAUDE.md)
  published_at timestamptz not null default now(), -- entrou no feed
  latency_ms   int,                                -- shutter->publicado (observabilidade)
  n_faces      int not null default 0,
  created_at   timestamptz not null default now()
);
create index if not exists idx_photo_event on photo(event_id, published_at desc);

-- ---------------------------------------------------------------------------
-- ROSTO detectado numa foto — embedding p/ match (ADR-0007)
-- ---------------------------------------------------------------------------
create table if not exists face (
  id         uuid primary key default gen_random_uuid(),
  photo_id   uuid not null references photo(id) on delete cascade,
  event_id   uuid not null references event(id) on delete cascade,
  embedding  vector(128) not null,                 -- SFace 128-d (EXP-05)
  bbox       jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_face_event on face(event_id);

-- ---------------------------------------------------------------------------
-- CONVIDADO (efêmero, ADR-0005) — selfie NÃO é guardada; só o embedding, e some com o evento
-- ---------------------------------------------------------------------------
create table if not exists guest (
  id             uuid primary key default gen_random_uuid(),
  event_id       uuid not null references event(id) on delete cascade,
  selfie_embedding vector(128) not null,           -- selfie vira vetor e é descartada
  consent_at     timestamptz not null default now(),
  created_at     timestamptz not null default now()
);
create index if not exists idx_guest_event on guest(event_id);

-- ---------------------------------------------------------------------------
-- MATCH (convidado <-> foto) — resultado do reconhecimento; alimenta o feed pessoal
-- ---------------------------------------------------------------------------
create table if not exists match (
  guest_id   uuid not null references guest(id) on delete cascade,
  photo_id   uuid not null references photo(id) on delete cascade,
  score      real not null,                        -- similaridade cosseno
  created_at timestamptz not null default now(),
  primary key (guest_id, photo_id)
);

-- ---------------------------------------------------------------------------
-- RLS (Row Level Security) — cada fotógrafo só vê os próprios dados.
-- O feed do convidado é servido pelo worker com service key (bypass), com escopo do evento.
-- ---------------------------------------------------------------------------
alter table photographer enable row level security;
alter table event        enable row level security;
alter table photo        enable row level security;

create policy "own profile" on photographer
  for all using (auth.uid() = id);

create policy "own events" on event
  for all using (auth.uid() = photographer_id);

create policy "own photos" on photo
  for select using (
    exists (select 1 from event e where e.id = photo.event_id and e.photographer_id = auth.uid())
  );

-- Realtime: publicar inserts de `photo` e `match` p/ o feed ao vivo (ADR-0010).
-- (No painel do Supabase: Database > Replication > habilitar as tabelas.)
