import { randomBytes, scrypt as scryptCb, timingSafeEqual, createHmac } from 'crypto';
import { promisify } from 'util';

const scrypt = promisify(scryptCb);
const KEY_LEN = 64;
const SESSION_MAX_AGE_SEC = 60 * 60 * 24 * 30; // 30 дней
const COOKIE_NAME = 'qa_session';

export async function hashPassword(password) {
  const salt = randomBytes(16);
  const derived = await scrypt(password, salt, KEY_LEN);
  return `scrypt:${salt.toString('hex')}:${derived.toString('hex')}`;
}

export async function verifyPassword(password, stored) {
  const [scheme, saltHex, hashHex] = (stored || '').split(':');
  if (scheme !== 'scrypt' || !saltHex || !hashHex) return false;
  const salt = Buffer.from(saltHex, 'hex');
  const expected = Buffer.from(hashHex, 'hex');
  const derived = await scrypt(password, salt, expected.length);
  return derived.length === expected.length && timingSafeEqual(derived, expected);
}

function getSecret() {
  const secret = process.env.SESSION_SECRET;
  if (!secret) throw new Error('SESSION_SECRET is not set');
  return secret;
}

// Токен сессии: <base64url(JSON payload)>.<base64url(HMAC-SHA256 подпись)> —
// самодостаточный, без таблицы сессий в БД. Секрет один на всё приложение (SESSION_SECRET).
export function signSession(payload) {
  const body = { ...payload, exp: Math.floor(Date.now() / 1000) + SESSION_MAX_AGE_SEC };
  const payloadB64 = Buffer.from(JSON.stringify(body)).toString('base64url');
  const sig = createHmac('sha256', getSecret()).update(payloadB64).digest();
  return `${payloadB64}.${sig.toString('base64url')}`;
}

export function verifySession(token) {
  if (!token || typeof token !== 'string' || !token.includes('.')) return null;
  const [payloadB64, sigB64] = token.split('.');
  const expectedSig = createHmac('sha256', getSecret()).update(payloadB64).digest();
  let gotSig;
  try {
    gotSig = Buffer.from(sigB64, 'base64url');
  } catch (e) {
    return null;
  }
  if (gotSig.length !== expectedSig.length || !timingSafeEqual(gotSig, expectedSig)) return null;
  let payload;
  try {
    payload = JSON.parse(Buffer.from(payloadB64, 'base64url').toString());
  } catch (e) {
    return null;
  }
  if (!payload.exp || payload.exp < Math.floor(Date.now() / 1000)) return null;
  return payload;
}

export function setSessionCookie(res, token) {
  res.setHeader(
    'Set-Cookie',
    `${COOKIE_NAME}=${token}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${SESSION_MAX_AGE_SEC}`
  );
}

export function clearSessionCookie(res) {
  res.setHeader('Set-Cookie', `${COOKIE_NAME}=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0`);
}

function parseCookies(req) {
  const header = req.headers.cookie;
  const out = {};
  if (!header) return out;
  header.split(';').forEach((part) => {
    const idx = part.indexOf('=');
    if (idx === -1) return;
    const k = part.slice(0, idx).trim();
    const v = part.slice(idx + 1).trim();
    out[k] = decodeURIComponent(v);
  });
  return out;
}

export function getSession(req) {
  const cookies = parseCookies(req);
  return verifySession(cookies[COOKIE_NAME]);
}

export function requireSession(req, res) {
  const session = getSession(req);
  if (!session) {
    res.status(401).json({ error: 'Не авторизован' });
    return null;
  }
  return session;
}
