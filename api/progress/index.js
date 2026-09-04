import { sql } from '../../lib/db.js';
import { requireSession } from '../../lib/auth.js';

export default async function handler(req, res) {
  const session = requireSession(req, res);
  if (!session) return;
  const db = sql();

  if (req.method === 'GET') {
    const rows = await db`select lesson_id from progress where user_id = ${session.uid}`;
    res.status(200).json({ lessonIds: rows.map((r) => r.lesson_id) });
    return;
  }

  if (req.method === 'POST') {
    const { lessonId, done } = req.body || {};
    if (!lessonId) {
      res.status(400).json({ error: 'lessonId обязателен' });
      return;
    }
    if (done) {
      await db`
        insert into progress (user_id, lesson_id)
        values (${session.uid}, ${lessonId})
        on conflict (user_id, lesson_id) do nothing
      `;
    } else {
      await db`delete from progress where user_id = ${session.uid} and lesson_id = ${lessonId}`;
    }
    res.status(200).json({ ok: true });
    return;
  }

  res.status(405).json({ error: 'Method not allowed' });
}
