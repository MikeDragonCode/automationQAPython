import { sql } from '../lib/db.js';
import { requireSession } from '../lib/auth.js';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }
  const session = requireSession(req, res);
  if (!session) return;

  const { lessonId } = req.body || {};
  if (!lessonId) {
    res.status(400).json({ error: 'lessonId обязателен' });
    return;
  }

  const db = sql();
  await db`update users set last_lesson_id = ${lessonId} where id = ${session.uid}`;
  res.status(200).json({ ok: true });
}
