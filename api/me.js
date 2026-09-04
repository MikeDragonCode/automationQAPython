import { sql } from '../lib/db.js';
import { requireSession } from '../lib/auth.js';

export default async function handler(req, res) {
  const session = requireSession(req, res);
  if (!session) return;

  const db = sql();
  const rows = await db`
    select role, display_name, last_lesson_id
    from users
    where id = ${session.uid}
  `;
  const user = rows[0];
  if (!user) {
    res.status(401).json({ error: 'Пользователь не найден' });
    return;
  }
  res.status(200).json({
    role: user.role,
    displayName: user.display_name,
    lastLessonId: user.last_lesson_id,
  });
}
