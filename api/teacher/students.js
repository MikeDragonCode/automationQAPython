import { sql } from '../../lib/db.js';
import { requireSession } from '../../lib/auth.js';

export default async function handler(req, res) {
  const session = requireSession(req, res);
  if (!session) return;
  if (session.role !== 'teacher') {
    res.status(403).json({ error: 'Только для учителя' });
    return;
  }

  const db = sql();
  const students = await db`
    select id, email, display_name
    from users
    where role = 'student'
    order by display_name nulls last, email
  `;
  const progress = await db`
    select p.user_id, p.lesson_id, p.done_at
    from progress p
    join users u on u.id = p.user_id
    where u.role = 'student'
  `;
  res.status(200).json({ students, progress });
}
