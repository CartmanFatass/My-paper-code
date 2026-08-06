#!/usr/bin/env node
/**
 * External Pro review transport, with conversation resume.
 *
 * WHY THIS EXISTS
 * ---------------
 * Standing process rule (user, 2026-08-05): External Pro questions in the SAME
 * research direction go in ONE conversation; different directions get different
 * conversations. Until now every dispatch called POST /conversations/new, which
 * was correct only because every dispatch happened to open a new direction.
 * Submitting a follow-up -- results, an alignment audit, a clarification -- into
 * an existing direction needs true resume, and that is what --resume adds.
 *
 * The full-lesson sequence is preserved in both modes:
 *   refuse if a query is already active;
 *   verify the visible "Pro" label BEFORE sending;
 *   send exactly once and NEVER resend;
 *   classify a post-abort submission via GET /status, never POST /status
 *     (a ~5 minute `fetch failed` is an undici client abort and means the
 *      question WAS submitted);
 *   observe completion by short-timeout wait-response polling.
 *
 * USAGE
 *   node scripts/pro_review_transport.mjs --question <path> --out <dir>
 *   node scripts/pro_review_transport.mjs --question <path> --out <dir> \
 *        --resume https://chatgpt.com/c/<conversation-id>
 */

import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const AGENTIFY_ROOT = process.env.AGENTIFY_ROOT || 'C:/Projects/agentify-desktop';
const OBSERVE_BUDGET_MS = 75 * 60_000;
const MIN_REAL = 400;
const SETTLE_MS = 8_000;

function arg(name, fallback = null) {
  const index = process.argv.indexOf(`--${name}`);
  if (index === -1 || index + 1 >= process.argv.length) return fallback;
  return process.argv[index + 1];
}

const QUESTION = arg('question');
const OUT_DIR = arg('out');
const RESUME_URL = arg('resume');

if (!QUESTION || !OUT_DIR) {
  console.error('usage: --question <path> --out <dir> [--resume <conversation-url>]');
  process.exit(2);
}

const RESULTS = path.join(OUT_DIR, 'results.json');

const { ensureDesktopRunning } = await import(
  pathToFileURL(path.join(AGENTIFY_ROOT, 'mcp-lib.mjs')).href
);
const { defaultStateDir } = await import(
  pathToFileURL(path.join(AGENTIFY_ROOT, 'state.mjs')).href
);

const conn = await ensureDesktopRunning({ stateDir: defaultStateDir(), showTabs: false });
const H = { 'content-type': 'application/json', authorization: `Bearer ${conn.token}` };

async function postJson(p, body, abortMs) {
  const res = await fetch(`${conn.baseUrl}${p}`, {
    method: 'POST',
    headers: H,
    body: JSON.stringify(body),
    signal: abortMs ? AbortSignal.timeout(abortMs) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data?.ok === false) {
    const err = new Error(data?.message || data?.error || `http_${res.status}`);
    err.body = data;
    throw err;
  }
  return data;
}

async function getStatus() {
  try {
    const res = await fetch(`${conn.baseUrl}/status`, {
      headers: { authorization: H.authorization },
      signal: AbortSignal.timeout(20_000),
    });
    return await res.json();
  } catch {
    return null;
  }
}

async function persist(row) {
  await fs.mkdir(OUT_DIR, { recursive: true });
  await fs.writeFile(
    RESULTS,
    JSON.stringify(
      {
        contract: 'AGENTIFY_REVIEW_BATCH_RESULT',
        provider: 'chatgpt',
        status: row.status === 'COMPLETE' ? 'COMPLETE' : 'ERROR',
        results_path: RESULTS,
        error: row.error || '',
        items: [row],
      },
      null,
      2
    ),
    'utf8'
  );
}

function fail(row, message) {
  row.error = message;
  return persist(row).then(() => {
    console.log(`AGENTIFY_REVIEW_BATCH_RESULT status=ERROR results_path=${RESULTS}`);
    process.exit(1);
  });
}

/** chatgpt.com/c/<id> -> <id>; null when the shape is unexpected. */
function conversationId(value) {
  const match = /chatgpt\.com\/c\/([0-9a-f-]+)/i.exec(String(value || ''));
  return match ? match[1].toLowerCase() : null;
}

const row = {
  question_path: QUESTION,
  status: 'ERROR',
  response: '',
  conversation_url: '',
  mode: RESUME_URL ? 'resume' : 'new',
  error: '',
};

const st0 = await getStatus();
if (st0?.activeQuery) {
  await fail(row, `preexisting_active_query id=${st0.activeQuery.id}; refusing to send`);
}

// ---------------------------------------------------------------------------
// Land on the correct conversation
// ---------------------------------------------------------------------------
if (RESUME_URL) {
  const wanted = conversationId(RESUME_URL);
  if (!wanted) {
    await fail(row, `resume url is not a chatgpt conversation: ${RESUME_URL}`);
  }
  await postJson('/navigate', { url: RESUME_URL, model: 'chatgpt', key: 'default' }, 120_000);
  try {
    await postJson('/ensure-ready', { model: 'chatgpt', key: 'default', timeoutMs: 300_000 }, 320_000);
  } catch (err) {
    // ensure-ready is a convenience; the settle plus URL check below is the
    // real guard, so a transient failure here must not abort a valid resume.
    console.error(`[ensure-ready transient: ${String(err?.message || err).slice(0, 120)}]`);
  }
  await new Promise((r) => setTimeout(r, SETTLE_MS));

  // Verify we actually landed on the requested conversation. A silent redirect
  // to a fresh chat would otherwise split a research direction across two
  // conversations, which is exactly what this mode exists to prevent.
  const landed = await getStatus();
  const got = conversationId(landed?.url);
  if (got !== wanted) {
    await fail(row, `resume landed on the wrong conversation: wanted ${wanted}, got ${got || landed?.url}`);
  }
  row.conversation_url = landed.url;
} else {
  await postJson('/conversations/new', { model: 'chatgpt', key: 'default' }, 60_000);
  await new Promise((r) => setTimeout(r, SETTLE_MS));
}

// ---------------------------------------------------------------------------
// Verify the visible model BEFORE sending. Fail closed.
// ---------------------------------------------------------------------------
const page = await postJson('/read-page', { model: 'chatgpt', key: 'default' }, 60_000);
const pageText = String(page?.text || '').trim();
// A fresh conversation ends with the composer, so the label sits in the last
// few characters. A resumed conversation ends with the previous answer, so the
// label is further back -- widen the window rather than skip the check.
const labelWindow = RESUME_URL ? pageText.slice(-400) : pageText.slice(-40);
if (!/\bPro\b/.test(labelWindow)) {
  await fail(
    row,
    `visible_model_label_not_pro mode=${row.mode} window=${JSON.stringify(labelWindow.slice(-160))}`
  );
}

// ---------------------------------------------------------------------------
// Exactly one send.
// ---------------------------------------------------------------------------
const prompt = await fs.readFile(QUESTION, 'utf8');
let submitted = false;
let text = '';
let meta = null;
try {
  const data = await postJson('/query', {
    source: 'mcp',
    model: 'chatgpt',
    expectedModel: 'Pro',
    key: 'default',
    prompt,
    timeoutMs: 2_700_000,
  });
  submitted = true;
  text = data?.result?.text || '';
  meta = data?.result?.meta || null;
} catch (err) {
  const msg = String(err?.message || err);
  await new Promise((r) => setTimeout(r, 15_000));
  const st = await getStatus();
  const url = st?.url || '';
  if (st?.activeQuery || /chatgpt\.com\/c\//.test(url)) {
    submitted = true;
    row.conversation_url = /chatgpt\.com\/c\//.test(url) ? url : row.conversation_url;
    console.error(`[client abort after submission: ${msg}; activeQuery=${!!st?.activeQuery} url=${url}] observing`);
  } else {
    await fail(row, `query_failed_pre_send: ${msg}${err?.body ? ' body=' + JSON.stringify(err.body).slice(0, 600) : ''}`);
  }
}

if (submitted && !text) {
  const deadline = Date.now() + OBSERVE_BUDGET_MS;
  while (Date.now() < deadline) {
    let w = null;
    try {
      w = await postJson('/wait-response', { model: 'chatgpt', key: 'default', timeoutMs: 240_000 }, 270_000);
    } catch (err) {
      console.error(`[wait-response transient: ${String(err?.message || err).slice(0, 120)}]`);
      await new Promise((r) => setTimeout(r, 15_000));
      continue;
    }
    if (w?.inProgress === true) continue;
    text = w?.result?.text || '';
    meta = w?.result?.meta || meta;
    if (text) break;
    const st = await getStatus();
    if (st && !st.activeQuery) {
      try {
        const p2 = await postJson('/read-page', { model: 'chatgpt', key: 'default' }, 60_000);
        const t2 = String(p2?.text || '').trim();
        if (t2.length > MIN_REAL) {
          text = t2;
          row.error = 'recovered_from_read_page';
          break;
        }
      } catch {}
    }
    await new Promise((r) => setTimeout(r, 15_000));
  }
}

const t = String(text || '').trim();
if (!t || t.length < MIN_REAL) {
  await fail(row, `${row.error ? row.error + '; ' : ''}no_valid_completed_response (len=${t.length})`);
}

row.response = t;
row.conversation_url = meta?.conversationUrl || meta?.url || row.conversation_url || '';
if (!row.conversation_url) {
  const st = await getStatus();
  if (/chatgpt\.com\/c\//.test(st?.url || '')) row.conversation_url = st.url;
}
row.status = 'COMPLETE';
await persist(row);
console.log(`AGENTIFY_REVIEW_BATCH_RESULT status=COMPLETE results_path=${RESULTS}`);
