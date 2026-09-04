import { sql } from '../../lib/db.js';
import { requireSession } from '../../lib/auth.js';

// Разовый перенос локального прогресса (localStorage, из версии ридера до аккаунтов)
// в БД при первом входе — см. миграцию в reader/template.html.
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }
  const session = requireSession(req, res);
  if (!session) return;

  const { lessonIds } = req.body || {};
  if (!Array.isArray(lessonIds) || !lessonIds.length) {
    res.status(400).json({ error: 'lessonIds обязателен' });
    return;
  }

  const db = sql();
  await db`
    insert into progress (user_id, lesson_id)
    select ${session.uid}, unnest(${lessonIds}::text[])
    on conflict (user_id, lesson_id) do nothing
  `;
  res.status(200).json({ ok: true });
}
