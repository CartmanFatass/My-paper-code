#!/usr/bin/env node

import crypto from 'node:crypto';
import fs from 'node:fs/promises';

import { ChromeCdpConnection } from 'file:///C:/Projects/agentify-desktop/chrome-cdp-backend.mjs';

const REQUIRED_HEADINGS = [
  'REVIEW_IDENTITY',
  'FORMAL_OBJECT_AND_ASSUMPTIONS',
  'DERIVATION_AND_CAUSAL_PATH',
  'ESTIMAND_AND_IDENTIFICATION',
  'SIMPLE_NULL_OR_EQUIVALENCE',
  'COUNTEREXAMPLES_AND_BOUNDARIES',
  'COMPLEXITY_AND_INTERFACES',
  'IDENTIFYING_TOY',
  'CONSTRUCTIVE_CORRECTIONS_AND_INSPIRATION',
  'RESIDUAL_UNCERTAINTY',
  'INDEPENDENT_RESEARCH_DIRECTION_PACKET'
];

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function argument(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] || null : null;
}

async function inspect(client, sessionId) {
  const result = await client.send(
    'Runtime.evaluate',
    {
      expression: `(() => {
        const visible = (node) => {
          const rect = node?.getBoundingClientRect?.();
          const style = node ? getComputedStyle(node) : null;
          return !!rect && rect.width > 0 && rect.height > 0 && style?.display !== 'none' && style?.visibility !== 'hidden';
        };
        const controls = Array.from(document.querySelectorAll('button, [role="button"]'))
          .filter(visible)
          .map((node) => ((node.getAttribute('aria-label') || '') + ' ' + (node.textContent || '')).replace(/\\s+/g, ' ').trim())
          .filter(Boolean);
        const responses = Array.from(document.querySelectorAll('model-response, [data-test-id="model-response"], [data-message-author-role="assistant"]'))
          .map((node) => String(node.innerText || node.textContent || '').trim())
          .filter(Boolean);
        return { url: location.href, controls, response: responses.at(-1) || '' };
      })()`,
      returnByValue: true
    },
    sessionId
  );
  if (result?.exceptionDetails) throw new Error('gemini_terminal_dom_unreadable');
  return result?.result?.value;
}

function headingCounts(response) {
  return Object.fromEntries(
    REQUIRED_HEADINGS.map((heading) => [
      heading,
      (response.match(new RegExp(`(?:^|\\n)${heading}(?:\\n|$)`, 'g')) || []).length
    ])
  );
}

async function main() {
  const outputPath = argument('--output');
  const questionPath = argument('--question');
  const preflightPath = argument('--preflight');
  const operationKey = argument('--operation-key');
  const conversationId = argument('--conversation-id');
  if (!outputPath || !questionPath || !preflightPath || !operationKey || !conversationId) {
    throw new Error('missing_archive_argument');
  }

  const transportState = JSON.parse(
    await fs.readFile('C:/Users/fires/.agentify-desktop/review-transport.json', 'utf8')
  );
  const operation = transportState.operations?.[operationKey];
  if (
    !operation || operation.sendCount !== 1 || operation.sendActionCount !== 1 ||
    operation.userMessageId !== 'user:0' || operation.conversationId !== conversationId
  ) {
    throw new Error('gemini_send_receipt_mismatch');
  }
  const question = await fs.readFile(questionPath, 'utf8');
  const questionSha256 = crypto.createHash('sha256').update(question, 'utf8').digest('hex');
  if (questionSha256 !== operation.promptSha256) throw new Error('gemini_prompt_sha_mismatch');
  const preflight = JSON.parse(await fs.readFile(preflightPath, 'utf8'));
  if (
    preflight.status !== 'VISIBLE_PREFLIGHT_CONFIRMED' ||
    preflight.model?.visiblySelected !== true ||
    preflight.extendedThinking?.visiblyEnabled !== true
  ) {
    throw new Error('gemini_visible_preflight_mismatch');
  }

  const version = await (await fetch('http://127.0.0.1:9222/json/version')).json();
  const client = new ChromeCdpConnection(version.webSocketDebuggerUrl);
  await client.connect();
  try {
    const targets = await client.send('Target.getTargets');
    const expectedUrl = `https://gemini.google.com/app/${conversationId}`;
    const target = targets.targetInfos.find((candidate) => candidate.type === 'page' && candidate.url === expectedUrl);
    if (!target) throw new Error('gemini_conversation_target_missing');
    const attached = await client.send('Target.attachToTarget', { targetId: target.targetId, flatten: true });
    const first = await inspect(client, attached.sessionId);
    await sleep(5_000);
    const second = await inspect(client, attached.sessionId);
    const activePattern = /answer now|\u7acb\u5373\u56de\u7b54|stop|\u505c\u6b62/i;
    if (first.response !== second.response || second.controls.some((label) => activePattern.test(label))) {
      throw new Error('gemini_generation_not_naturally_complete');
    }
    const counts = headingCounts(second.response);
    if (!second.response || Object.values(counts).some((count) => count !== 1)) {
      throw new Error('gemini_response_format_incomplete');
    }
    const responseSha256 = crypto.createHash('sha256').update(second.response, 'utf8').digest('hex');
    const archive = [{
      question_path: questionPath,
      question_sha256: questionSha256,
      status: 'COMPLETE',
      response: second.response,
      response_sha256: responseSha256,
      conversation_url: second.url,
      conversation_id: conversationId,
      model_evidence: 'Gemini 3.1 Pro extended',
      visible_preflight_path: preflightPath,
      visible_model_evidence: preflight.model,
      visible_extended_thinking_evidence: preflight.extendedThinking,
      operation_id: operation.operationId,
      user_message_id: operation.userMessageId,
      send_count: operation.sendCount,
      send_action_count: operation.sendActionCount,
      natural_completion_reconciled_at: new Date().toISOString(),
      required_heading_counts: counts,
      forbidden_controls_activated: {
        stop: false,
        continue: false,
        retry: false,
        answer_now: false,
        acceleration: false
      }
    }];
    await fs.writeFile(outputPath, `${JSON.stringify(archive, null, 2)}\n`, { encoding: 'utf8', flag: 'wx' });
    process.stdout.write(`${JSON.stringify({ status: 'COMPLETE', outputPath, conversationId, responseSha256, responseLength: second.response.length })}\n`);
  } finally {
    await client.close();
  }
}

main().catch((error) => {
  process.stderr.write(`${JSON.stringify({ status: 'ERROR', error: error?.message || String(error) })}\n`);
  process.exitCode = 1;
});
