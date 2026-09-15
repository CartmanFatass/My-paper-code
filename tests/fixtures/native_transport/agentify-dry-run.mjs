// Import the installed Agentify implementation; replace only browser/controller effects.
// All state and output is owned by the caller's pytest temp directory. No external Send.
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const [source, scratch, handoffPath] = process.argv.slice(2);
const handoff = JSON.parse(await fs.readFile(handoffPath, 'utf8'));
const load = (name) => import(pathToFileURL(path.join(source, name)).href);
const { runReviewQuery, archiveReviewResponse } = await load('review-transport.mjs');
const { readReviewTransportState } = await load('state.mjs');
const { REVIEW_PLAIN_TEXT_MODEL, reviewPlainTextIdentity } = await load('review-text-identity.mjs');
const { REVIEW_COMPOSER_REPLACEMENT_MODEL } = await load('review-composer-replacement.mjs');
const sha = (text) => crypto.createHash('sha256').update(text).digest('hex');
const actual = JSON.parse(await fs.readFile(path.join(path.dirname(fileURLToPath(import.meta.url)), 'mgtap-presend.json'), 'utf8'));
const text = '# Fixture response\nFull exact UTF-8 answer: 配对。\n';
let sends = 0;

function fixture(name, uncertain = false) {
  const stateDir = path.join(scratch, name);
  let failKey = !uncertain;
  let crashAfterBoundary = uncertain;
  let waiting = !uncertain;
  const prompt = handoff.prompt;
  assert.equal(sha(prompt), actual.promptSha256);
  const request = { stableKey: actual.stableKey, provider: actual.provider,
    productModel: actual.productModel, reasoningEffort: actual.reasoningEffort,
    conversationUrl: actual.conversationUrl, conversationId: actual.conversationId,
    idempotencyKey: actual.idempotencyKey, prompt, promptSha256: sha(prompt),
    responsePath: path.join(stateDir, 'response.md'), existingTabId: 'bad-key-tab', timeoutMs: 1000 };
  const identity = { conversationUrl: request.conversationUrl, conversationId: request.conversationId, userMessageId: 'current-user' };
  const controller = {
    async runExclusive(fn) { return await fn(); },
    async reviewQuery(args) {
      assert.equal(args.requireTargetPreflight, true);
      assert.equal(args.productModel, 'Latest');
      assert.equal(args.reasoningEffort, 'Pro');
      assert.ok(args.timeoutMs <= 60000);
      await args.onPrepared({ baselineMessageIds: ['historical-user'] });
      const canonical = reviewPlainTextIdentity(args.prompt).canonicalSha256;
      await args.onComposerVerified({ ok: true, textModel: REVIEW_PLAIN_TEXT_MODEL,
        replacementModel: REVIEW_COMPOSER_REPLACEMENT_MODEL, sourceSha256: sha(args.prompt),
        canonicalPromptSha256: canonical, observedCanonicalSha256: canonical });
      await args.onSendAttempted(); // persisted before the mocked external effect
      sends++;
      if (crashAfterBoundary) { crashAfterBoundary = false; throw new Error('fixture_effect_uncertain'); }
      await args.onUserTurnObserved(identity);
      return identity;
    },
    async observeReviewUserTurn() { return identity; },
    async observeReviewResponse(args) {
      assert.equal(args.userMessageId, identity.userMessageId);
      if (waiting) { waiting = false; return { status: 'SENT_WAITING' }; }
      return { ...identity, assistantMessageId: 'paired-assistant', text,
        snapshots: [1000, 4000].map(observedAt => ({ assistantMessageId: 'paired-assistant', textSha256: sha(text), observedAt })),
        controls: { stop: false, continue: false, retry: false }, clickedControls: [] };
    }
  };
  const tabs = {
    async adoptTab(args) {
      assert.equal(args.key, actual.stableKey);
      if (failKey) throw new Error('tab_key_mismatch');
      assert.equal(args.id, 'dedicated-keyed-tab');
    },
    async ensureTab() { return 'dedicated-keyed-tab'; },
    getWindowById() { return { async show() {} }; },
    getControllerById() { return controller; }
  };
  const run = () => runReviewQuery({ stateDir, tabs, request });
  const operation = async () => (await readReviewTransportState(stateDir)).operations[request.idempotencyKey];
  const repair = () => { failKey = false; request.existingTabId = 'dedicated-keyed-tab'; request.verifyExisting = true; };
  return { stateDir, request, run, operation, repair, tabs };
}

const before = fixture('verified-nonacceptance');
await assert.rejects(before.run(), /tab_key_mismatch/);
const failed = await before.operation();
assert.equal(failed.sendAttempted, false);
assert.equal(failed.error.code, 'TAB_KEY_MISMATCH');
assert.equal(sends, 0);
before.repair();
const accepted = await before.run();
assert.equal(accepted.operationId, failed.operationId);
assert.equal(accepted.sendAttempted, true);
assert.equal(accepted.providerUserMessageId, 'current-user');
assert.equal(sends, 1);
const archived = await before.run();
assert.equal(sends, 1);
assert.equal(archived.archive.sha256, sha(text));
assert.equal(archived.archive.sizeBytes, Buffer.byteLength(text));
assert.equal(await fs.readFile(archived.archive.path, 'utf8'), text);
await before.run(); // archived operation returns its receipt without browser work
assert.equal(sends, 1);
await assert.rejects(archiveReviewResponse({ responsePath: archived.archive.path, text: 'conflict' }), /path_conflict/);
assert.equal(await fs.readFile(archived.archive.path, 'utf8'), text);
await assert.rejects(runReviewQuery({ stateDir: before.stateDir, tabs: before.tabs,
  request: { ...before.request, prompt: 'changed', promptSha256: sha('changed') } }), /idempotency_conflict/);

const uncertain = fixture('uncertain-effect', true);
uncertain.request.existingTabId = 'dedicated-keyed-tab';
await assert.rejects(uncertain.run(), /fixture_effect_uncertain/);
const uncertainOperation = await uncertain.operation();
assert.equal(uncertainOperation.sendAttempted, true);
assert.equal(uncertainOperation.providerUserMessageId, null);
uncertain.repair();
const reconciled = await uncertain.run();
assert.equal(reconciled.operationId, uncertainOperation.operationId);
assert.equal(reconciled.archive.sha256, sha(text));
assert.equal(sends, 2);
await assert.rejects(runReviewQuery({ stateDir: path.join(scratch, 'unknown'), tabs: uncertain.tabs,
  request: { ...uncertain.request, verifyExisting: true } }), /observation_unavailable/);
assert.equal(sends, 2);
process.stdout.write(JSON.stringify({ sends, same_operation_after_repair: true,
  uncertain_observe_only: true, archive_exact: true, conflict_preserved: true }));
