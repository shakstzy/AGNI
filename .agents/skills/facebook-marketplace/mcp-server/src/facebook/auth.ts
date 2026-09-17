import crypto from "node:crypto";
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import Database from "better-sqlite3";
import type { FacebookCookie } from "./types.js";

const CHROME_SALT = "saltysalt";
const CHROME_ITERATIONS_MAC = 1003;
const CHROME_ITERATIONS_LINUX = 1;
const CHROME_KEY_LENGTH = 16;
const CHROME_IV = Buffer.alloc(16, " ");

function deriveKey(password: string, iterations: number): Buffer {
  return crypto.pbkdf2Sync(
    password,
    CHROME_SALT,
    iterations,
    CHROME_KEY_LENGTH,
    "sha1"
  );
}

function decryptCookieValue(encrypted: Buffer, key: Buffer): string {
  if (!encrypted || encrypted.length === 0) return "";

  const prefix = encrypted.slice(0, 3).toString("ascii");
  if (prefix !== "v10" && prefix !== "v11") {
    return encrypted.toString("utf8");
  }

  try {
    const data = encrypted.slice(3);
    const decipher = crypto.createDecipheriv("aes-128-cbc", key, CHROME_IV);
    decipher.setAutoPadding(false);

    let decoded = Buffer.concat([decipher.update(data), decipher.final()]);

    const padding = decoded[decoded.length - 1];
    if (padding && padding > 0 && padding <= 16) {
      decoded = decoded.slice(0, decoded.length - padding);
    }

    if (decoded.length > 32) {
      decoded = decoded.slice(32);
    }

    return decoded.toString("utf8");
  } catch {
    return "";
  }
}

export function parseCookieString(cookieStr: string, domain = "facebook.com"): FacebookCookie[] {
  const cookies: FacebookCookie[] = [];
  const parts = cookieStr.split(";").map((p) => p.trim()).filter(Boolean);
  for (const part of parts) {
    const eqIdx = part.indexOf("=");
    if (eqIdx === -1) continue;
    const name = part.slice(0, eqIdx).trim();
    const value = part.slice(eqIdx + 1).trim();
    if (name) {
      cookies.push({
        host: `.${domain}`,
        name,
        value,
        path: "/",
        expires: Math.floor(Date.now() / 1000) + 86400 * 30,
        secure: true,
        httpOnly: true,
      });
    }
  }
  return cookies;
}

function loadCookiesFromEnv(): FacebookCookie[] | null {
  const envVal = process.env.FB_COOKIES || process.env.FB_COOKIE_STRING;
  if (!envVal) return null;

  const trimmed = envVal.trim();
  if (trimmed.startsWith("[") && trimmed.endsWith("]")) {
    try {
      const parsed = JSON.parse(trimmed);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed.map((c: any) => ({
          host: c.host || c.domain || ".facebook.com",
          name: c.name,
          value: c.value,
          path: c.path || "/",
          expires: c.expires || 0,
          secure: c.secure !== false,
          httpOnly: c.httpOnly !== false,
        }));
      }
    } catch {
      // Fall through to string parser
    }
  }
  return parseCookieString(trimmed);
}

function loadCookiesFromFile(): FacebookCookie[] | null {
  const candidatePaths = [
    process.env.FB_COOKIES_PATH,
    path.join(os.homedir(), ".fb-marketplace", "cookies.json"),
    path.join(os.homedir(), ".fb-marketplace", "session.json"),
    "/home/shakstzy/HADES/.agents/skills/browser/sitemaps/facebook.com/profiles/adithya/cookies.json",
    path.join(process.cwd(), "config", "cookies.json"),
    path.join(process.cwd(), "data", "session.json"),
  ].filter(Boolean) as string[];

  for (const filePath of candidatePaths) {
    if (fs.existsSync(filePath)) {
      try {
        const raw = fs.readFileSync(filePath, "utf8").trim();
        if (raw.startsWith("[") || raw.startsWith("{")) {
          const parsed = JSON.parse(raw);
          if (Array.isArray(parsed)) {
            return parsed;
          }
          if (parsed.cookies && Array.isArray(parsed.cookies)) {
            return parsed.cookies;
          }
          if (parsed.cookie_string || parsed.cookieHeader) {
            return parseCookieString(parsed.cookie_string || parsed.cookieHeader);
          }
        } else if (raw.length > 0) {
          return parseCookieString(raw);
        }
      } catch {
        // try next file
      }
    }
  }
  return null;
}

function getCandidateDbPaths(profile = "Default"): string[] {
  const isDarwin = process.platform === "darwin";
  const home = os.homedir();

  if (isDarwin) {
    return [
      path.join(home, "Library/Application Support/Google/Chrome", profile, "Cookies"),
      path.join(home, "Library/Application Support/Google/Chrome", profile, "Network/Cookies"),
    ];
  }

  return [
    "/home/shakstzy/HADES/.agents/skills/browser/sitemaps/facebook.com/profiles/adithya/user_data/Default/Network/Cookies",
    "/home/shakstzy/HADES/.agents/skills/browser/sitemaps/facebook.com/profiles/adithya/user_data/Default/Cookies",
    path.join(home, ".config/google-chrome", profile, "Network/Cookies"),
    path.join(home, ".config/google-chrome", profile, "Cookies"),
    path.join(home, ".config/chromium", profile, "Network/Cookies"),
    path.join(home, ".config/chromium", profile, "Cookies"),
  ];
}

function extractFromSqlite(cookieDbPath: string, domain: string): FacebookCookie[] {
  const tmpPath = path.join(os.tmpdir(), `fbm_cookies_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`);
  try {
    fs.copyFileSync(cookieDbPath, tmpPath);
  } catch {
    return [];
  }

  let db: Database.Database;
  try {
    db = new Database(tmpPath, { readonly: true });
  } catch {
    try { fs.unlinkSync(tmpPath); } catch {}
    return [];
  }

  try {
    let key: Buffer;
    if (process.platform === "darwin") {
      const password = execSync('security find-generic-password -w -s "Chrome Safe Storage" -a "Chrome"', {
        stdio: ["pipe", "pipe", "pipe"],
      }).toString().trim();
      key = deriveKey(password, CHROME_ITERATIONS_MAC);
    } else {
      key = deriveKey("peanuts", CHROME_ITERATIONS_LINUX);
    }

    const rows = db
      .prepare(
        `SELECT host_key, name, value, encrypted_value, path, expires_utc,
                is_secure, is_httponly
         FROM cookies
         WHERE host_key LIKE ?`
      )
      .all(`%${domain}`) as Array<{
      host_key: string;
      name: string;
      value: string;
      encrypted_value: Buffer;
      path: string;
      expires_utc: number;
      is_secure: number;
      is_httponly: number;
    }>;

    return rows.map((row) => {
      let val = row.value;
      if (!val && row.encrypted_value && row.encrypted_value.length > 0) {
        val = decryptCookieValue(row.encrypted_value, key);
      }
      return {
        host: row.host_key,
        name: row.name,
        value: val,
        path: row.path,
        expires: row.expires_utc,
        secure: !!row.is_secure,
        httpOnly: !!row.is_httponly,
      };
    });
  } catch {
    return [];
  } finally {
    try { db.close(); } catch {}
    try { fs.unlinkSync(tmpPath); } catch {}
  }
}

export function extractChromeCookies(
  domain = "facebook.com",
  profile = "Default"
): FacebookCookie[] {
  const envCookies = loadCookiesFromEnv();
  if (envCookies && envCookies.length > 0) {
    return envCookies;
  }

  const fileCookies = loadCookiesFromFile();
  if (fileCookies && fileCookies.length > 0) {
    return fileCookies;
  }

  const candidateDbs = getCandidateDbPaths(profile);
  for (const dbPath of candidateDbs) {
    if (fs.existsSync(dbPath)) {
      const extracted = extractFromSqlite(dbPath, domain);
      if (extracted.length > 0 && extracted.some((c) => c.name === "c_user")) {
        return extracted;
      }
    }
  }

  for (const dbPath of candidateDbs) {
    if (fs.existsSync(dbPath)) {
      const extracted = extractFromSqlite(dbPath, domain);
      if (extracted.length > 0) {
        return extracted;
      }
    }
  }

  return [];
}

export function cookiesToHeader(cookies: FacebookCookie[]): string {
  return cookies
    .map((c) => {
      const safe = (c.value || "").replace(/[^\x00-\xFF]/g, "");
      return `${c.name}=${safe}`;
    })
    .join("; ");
}

export function getCookieValue(
  cookies: FacebookCookie[],
  name: string
): string | undefined {
  return cookies.find((c) => c.name === name)?.value;
}

