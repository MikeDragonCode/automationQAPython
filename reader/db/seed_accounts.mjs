#!/usr/bin/env node
// Заводит служебные аккаунты (учитель + 2 демо-профиля) в Neon, и опционально — реальных
// учеников. Использует ту же функцию хеширования пароля, что и /api/auth/login.js, —
// поэтому пароли, заданные здесь, гарантированно подойдут для входа через сайт.
//
// Запускать ТОЛЬКО локально, не из браузера/CI:
//
//   DATABASE_URL="postgresql://...neon.tech/neondb?sslmode=require" node reader/db/seed_accounts.mjs
//   DATABASE_URL="..." node reader/db/seed_accounts.mjs --student a@ex.com --student b@ex.com
//
// Реальных учеников можно так же заводить вручную (INSERT в таблицу users через Neon SQL
// Editor, пароль — вывод hashPassword) — этот скрипт просто ускоряет массовое создание.

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { randomBytes } from 'crypto';
import { neon } from '@neondatabase/serverless';
import { hashPassword } from '../../lib/auth.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..', '..');
const INDEX_HTML = join(ROOT, 'reader', 'index.html');
const MID_COURSE_SECTION_CUTOFF = 'Модуль 4'; // всё до первой страницы этого раздела -> done

function loadPages() {
  let html;
  try {
    html = readFileSync(INDEX_HTML, 'utf8');
  } catch (e) {
    console.error(`Не найден ${INDEX_HTML} — сначала соберите ридер: python3 reader/build_reader.py`);
    process.exit(1);
  }
  const m = html.match(/<script id="course-data" type="application\/json">([\s\S]*?)<\/script>/);
  if (!m) {
    console.error('Не нашёл блок course-data в reader/index.html');
    process.exit(1);
  }
  return JSON.parse(m[1]);
}

function midCourseIds(pages) {
  const ids = [];
  for (const p of pages) {
    if (p.section.startsWith(MID_COURSE_SECTION_CUTOFF)) break;
    ids.push(p.id);
  }
  return ids;
}

function randomPassword() {
  return randomBytes(9).toString('base64url');
}

async function ensureAccount(db, { email, envPasswordVar, role, displayName, progressIds, lastLessonId }) {
  const password = process.env[envPasswordVar] || randomPassword();
  const existing = await db`select id from users where email = ${email}`;
  let userId;
  if (existing.length) {
    userId = existing[0].id;
    console.log(`  ${email}: уже существует (${userId}), обновляю профиль/прогресс`);
    await db`update users set role = ${role}, display_name = ${displayName}, last_lesson_id = ${lastLessonId ?? null} where id = ${userId}`;
  } else {
    const passwordHash = await hashPassword(password);
    const rows = await db`
      insert into users (email, password_hash, role, display_name, last_lesson_id)
      values (${email}, ${passwordHash}, ${role}, ${displayName}, ${lastLessonId ?? null})
      returning id
    `;
    userId = rows[0].id;
    console.log(`  ${email}: создан. Пароль: ${password}`);
  }
  if (progressIds) {
    await db`delete from progress where user_id = ${userId}`;
    if (progressIds.length) {
      await db`
        insert into progress (user_id, lesson_id)
        select ${userId}, unnest(${progressIds}::text[])
        on conflict (user_id, lesson_id) do nothing
      `;
    }
  }
  return userId;
}

async function main() {
  const args = process.argv.slice(2);
  const students = [];
  let skipDemo = false;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--student') students.push(args[++i]);
    else if (args[i] === '--skip-demo') skipDemo = true;
  }

  const url = process.env.DATABASE_URL;
  if (!url) {
    console.error('Задайте DATABASE_URL в переменных окружения');
    process.exit(1);
  }
  if (!process.env.SESSION_SECRET) {
    // hashPassword сам SESSION_SECRET не использует, но проверим заранее, чтобы не удивляться
    // позже при первом реальном логине через /api — обе переменные нужны в одном месте (Vercel env).
    console.warn('Предупреждение: SESSION_SECRET не задан — для локального запуска этого скрипта не нужен, но обязателен на Vercel для /api/auth/login.');
  }

  const db = neon(url);
  const pages = loadPages();
  const allIds = pages.map((p) => p.id);
  const midIds = midCourseIds(pages);

  if (!skipDemo) {
    console.log('Служебные аккаунты:');
    await ensureAccount(db, {
      email: 'teacher@qa-course.local',
      envPasswordVar: 'TEACHER_PASSWORD',
      role: 'teacher',
      displayName: 'Преподаватель',
      progressIds: null,
    });
    await ensureAccount(db, {
      email: 'demo-full@qa-course.local',
      envPasswordVar: 'DEMO_FULL_PASSWORD',
      role: 'student',
      displayName: 'Демо · курс пройден полностью',
      progressIds: allIds,
      lastLessonId: allIds[allIds.length - 1],
    });
    await ensureAccount(db, {
      email: 'demo-mid@qa-course.local',
      envPasswordVar: 'DEMO_MID_PASSWORD',
      role: 'student',
      displayName: 'Демо · середина курса',
      progressIds: midIds,
      lastLessonId: midIds[midIds.length - 1],
    });
  }

  if (students.length) {
    console.log('Ученики:');
    for (const email of students) {
      const envVar = `STUDENT_PASSWORD_${email.replace(/[^A-Za-z0-9]/g, '_').toUpperCase()}`;
      await ensureAccount(db, {
        email,
        envPasswordVar: envVar,
        role: 'student',
        displayName: email,
        progressIds: [],
      });
    }
  }

  console.log('\nГотово. Сохраните напечатанные пароли — при повторном запуске для существующих\nаккаунтов пароль не печатается (пользователь уже создан).');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
