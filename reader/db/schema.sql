-- QA Automation Course reader — схема для Neon (обычный Postgres, без RLS:
-- доступ проверяется в коде serverless-функций в /api, а не на уровне БД).
-- Выполнить один раз в Neon SQL Editor (или через `psql "$DATABASE_URL" -f reader/db/schema.sql`).

-- gen_random_uuid() работает на Neon из коробки, без create extension.

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  password_hash text not null,
  role text not null default 'student' check (role in ('student', 'teacher')),
  display_name text,
  last_lesson_id text,
  created_at timestamptz not null default now()
);

create table if not exists progress (
  user_id uuid not null references users (id) on delete cascade,
  lesson_id text not null,
  done_at timestamptz not null default now(),
  primary key (user_id, lesson_id)
);

create index if not exists progress_user_id_idx on progress (user_id);
