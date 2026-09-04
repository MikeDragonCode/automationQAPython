import { sql } from '../../lib/db.js';
import { verifyPassword, signSession, setSessionCookie } from '../../lib/auth.js';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }
  const { email, password } = req.body || {};
  if (!email || !password) {
    res.status(400).json({ error: 'Укажите email и пароль' });
    return;
  }

  const db = sql();
  const rows = await db`
    select id, password_hash, role, display_name, last_lesson_id
    from users
    where email = ${String(email).trim().toLowerCase()}
  `;
  const user = rows[0];
  if (!user || !(await verifyPassword(password, user.password_hash))) {
    res.status(401).json({ error: 'Неверный email или пароль' });
    return;
  }

  const token = signSession({ uid: user.id, role: user.role });
  setSessionCookie(res, token);
  res.status(200).json({
    role: user.role,
    displayName: user.display_name,
    lastLessonId: user.last_lesson_id,
  });
}
