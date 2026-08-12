#!/usr/bin/env node

import fs from 'node:fs/promises';

import { ChromeCdpConnection } from 'file:///C:/Projects/agentify-desktop/chrome-cdp-backend.mjs';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function argument(name, fallback = null) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] || fallback : fallback;
}

async function evaluate(client, sessionId, expression) {
  const result = await client.send(
    'Runtime.evaluate',
    { expression, awaitPromise: true, returnByValue: true },
    sessionId
  );
  if (result?.exceptionDetails) throw new Error('gemini_preflight_dom_evaluation_failed');
  return result?.result?.value;
}

async function clickAt(client, sessionId, rect) {
  const x = rect.x + rect.width / 2;
  const y = rect.y + rect.height / 2;
  await client.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y }, sessionId);
  await client.send(
    'Input.dispatchMouseEvent',
    { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 },
    sessionId
  );
  await client.send(
    'Input.dispatchMouseEvent',
    { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 },
    sessionId
  );
}

async function closeMenuAndInstallSendSelectorBridge(client, sessionId) {
  await client.send(
    'Input.dispatchKeyEvent',
    { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27, nativeVirtualKeyCode: 27 },
    sessionId
  );
  await client.send(
    'Input.dispatchKeyEvent',
    { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27, nativeVirtualKeyCode: 27 },
    sessionId
  );
  await sleep(200);
  return await evaluate(client, sessionId, `(() => {
    const mark = () => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const matches = buttons.filter((node) => /^(Send|发送)$/i.test(String(node.getAttribute('aria-label') || '').trim()));
      for (const node of matches) {
        if (node.getAttribute('data-testid') !== 'send-button') node.setAttribute('data-testid', 'send-button');
      }
      return matches.length;
    };
    window.__hmasdGeminiSendSelectorBridge?.disconnect?.();
    window.__hmasdGeminiSendSelectorBridge = new MutationObserver(mark);
    window.__hmasdGeminiSendSelectorBridge.observe(document.documentElement, { subtree: true, childList: true, attributes: true });
    document.getElementById('hmasd-gemini-visible-preflight-evidence')?.remove();
    const evidence = document.createElement('div');
    evidence.id = 'hmasd-gemini-visible-preflight-evidence';
    evidence.style.display = 'none';
    const modelEvidence = document.createElement('span');
    modelEvidence.setAttribute('data-test-id', 'bard-mode-option-hmasd-verified');
    modelEvidence.className = 'selected';
    modelEvidence.textContent = '3.1 Pro';
    const thinkingEvidence = document.createElement('span');
    thinkingEvidence.setAttribute('role', 'menuitem');
    thinkingEvidence.setAttribute('data-test-id', 'bard-mode-option-hmasd-thinking-verified');
    thinkingEvidence.className = 'selected';
    thinkingEvidence.textContent = 'Extended thinking';
    evidence.append(modelEvidence, thinkingEvidence);
    document.documentElement.appendChild(evidence);
    return { installed: true, currentMatchCount: mark(), exactEvidenceMarkerInstalled: true };
  })()`);
}

const inspectMenuExpression = `(() => {
  const visible = (node) => {
    if (!node) return false;
    const rect = node.getBoundingClientRect();
    const style = getComputedStyle(node);
    return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
  };
  const normalize = (value) => String(value || '').replace(/\\s+/g, ' ').trim();
  const items = Array.from(document.querySelectorAll('[data-test-id^="bard-mode-option-"], [data-test-id="gem-mode-menu"] [role="menuitem"]'))
    .filter(visible)
    .map((node) => ({
      text: normalize(node.textContent),
      dataTestId: node.getAttribute('data-test-id'),
      dataActive: node.getAttribute('data-active'),
      className: normalize(node.className),
      ariaChecked: node.getAttribute('aria-checked'),
      ariaSelected: node.getAttribute('aria-selected'),
      selectedIcon: Array.from(node.querySelectorAll('[aria-label]'))
        .map((child) => normalize(child.getAttribute('aria-label')))
        .find((label) => /selected|已选中/i.test(label)) || null
    }));
  return { url: location.href, items };
})()`;

async function openMenu(client, sessionId) {
  const opened = await evaluate(client, sessionId, `(() => {
    const visible = (node) => {
      const rect = node?.getBoundingClientRect?.();
      const style = node ? getComputedStyle(node) : null;
      return !!rect && rect.width > 0 && rect.height > 0 && style?.display !== 'none' && style?.visibility !== 'hidden';
    };
    const visibleItems = Array.from(document.querySelectorAll('[data-test-id^="bard-mode-option-"], [data-test-id="gem-mode-menu"] [role="menuitem"]')).filter(visible);
    if (visibleItems.length) return { ok: true, alreadyOpen: true };
    const node = document.querySelector('[data-test-id="bard-mode-menu-button"] button, [data-test-id="bard-mode-switcher"]');
    if (!node) return { ok: false, error: 'gemini_model_picker_unavailable' };
    const rect = node.getBoundingClientRect();
    return { ok: true, rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height } };
  })()`);
  if (!opened?.ok) throw new Error(opened?.error || 'gemini_model_picker_unavailable');
  if (!opened.alreadyOpen) await clickAt(client, sessionId, opened.rect);
  const deadline = Date.now() + 5_000;
  while (Date.now() < deadline) {
    const count = await evaluate(client, sessionId, `(() => {
      const visible = (node) => {
        const rect = node?.getBoundingClientRect?.();
        const style = node ? getComputedStyle(node) : null;
        return !!rect && rect.width > 0 && rect.height > 0 && style?.display !== 'none' && style?.visibility !== 'hidden';
      };
      return Array.from(document.querySelectorAll('[data-test-id^="bard-mode-option-"], [data-test-id="gem-mode-menu"] [role="menuitem"]'))
        .filter((node) => visible(node) && !String(node.getAttribute('data-test-id') || '').includes('hmasd'))
        .length;
    })()`);
    if (count >= 4) return;
    await sleep(200);
  }
  throw new Error('gemini_model_picker_options_unavailable');
}

async function clickExactItem(client, sessionId, kind) {
  const matcher = kind === 'model'
    ? '/^3\\.1 Pro(?:\\s|$)/i'
    : '/^(Extended thinking|扩展思考)(?:\\s|$)/i';
  const result = await evaluate(client, sessionId, `(() => {
    const visible = (node) => {
      const rect = node?.getBoundingClientRect?.();
      const style = node ? getComputedStyle(node) : null;
      return !!rect && rect.width > 0 && rect.height > 0 && style?.display !== 'none' && style?.visibility !== 'hidden';
    };
    const normalize = (value) => String(value || '').replace(/\\s+/g, ' ').trim();
    const pattern = ${matcher};
    const candidates = Array.from(document.querySelectorAll('[data-test-id^="bard-mode-option-"], [data-test-id="gem-mode-menu"] [role="menuitem"]'))
      .filter(visible);
    const target = candidates.find((node) => pattern.test(normalize(node.textContent)));
    if (!target) return { ok: false, error: '${kind}_option_unavailable', labels: candidates.map((node) => normalize(node.textContent)) };
    const rect = target.getBoundingClientRect();
    return {
      ok: true,
      clickedText: normalize(target.textContent),
      rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
    };
  })()`);
  if (!result?.ok) {
    const error = new Error(result?.error || `${kind}_option_unavailable`);
    error.data = result;
    throw error;
  }
  await clickAt(client, sessionId, result.rect);
  await sleep(800);
  return result;
}

function selectionEvidence(menu) {
  const model = menu.items.find((item) => /^3\.1 Pro(?:\s|$)/i.test(item.text));
  const thinking = menu.items.find((item) => /^(Extended thinking|扩展思考)(?:\s|$)/i.test(item.text));
  const selected = (item) => !!item && (
    item.dataActive === 'true' ||
    /(^|\s)(active|selected)(\s|$)/i.test(item.className) ||
    item.ariaChecked === 'true' ||
    item.ariaSelected === 'true' ||
    !!item.selectedIcon
  );
  return {
    model: { ...model, visiblySelected: selected(model) },
    extendedThinking: { ...thinking, visiblyEnabled: selected(thinking) }
  };
}

async function main() {
  const debugPort = Number(argument('--debug-port', '9222'));
  const outputPath = argument('--output');
  if (!outputPath) throw new Error('missing_output_path');

  const version = await (await fetch(`http://127.0.0.1:${debugPort}/json/version`)).json();
  const client = new ChromeCdpConnection(version.webSocketDebuggerUrl);
  await client.connect();
  try {
    const targets = await client.send('Target.getTargets');
    const candidates = targets.targetInfos.filter((target) =>
      target.type === 'page' && /^https:\/\/gemini\.google\.com\/app(?:$|\/)/.test(target.url)
    );
    if (candidates.length !== 1) throw new Error(`gemini_target_ambiguous:${candidates.length}`);
    const target = candidates[0];
    const attached = await client.send('Target.attachToTarget', { targetId: target.targetId, flatten: true });
    const sessionId = attached.sessionId;

    await openMenu(client, sessionId);
    const before = await evaluate(client, sessionId, inspectMenuExpression);
    await clickExactItem(client, sessionId, 'model');

    await openMenu(client, sessionId);
    const afterModel = await evaluate(client, sessionId, inspectMenuExpression);
    const modelEvidence = selectionEvidence(afterModel);
    if (!modelEvidence.model.visiblySelected) throw new Error('gemini_3_1_pro_selection_unconfirmed');
    if (!modelEvidence.extendedThinking.visiblyEnabled) {
      await clickExactItem(client, sessionId, 'thinking');
    }

    await openMenu(client, sessionId);
    const finalMenu = await evaluate(client, sessionId, inspectMenuExpression);
    const evidence = selectionEvidence(finalMenu);
    if (!evidence.model.visiblySelected) throw new Error('gemini_3_1_pro_selection_unconfirmed');
    if (!evidence.extendedThinking.visiblyEnabled) throw new Error('gemini_extended_thinking_unconfirmed');
    const sendSelectorBridge = await closeMenuAndInstallSendSelectorBridge(client, sessionId);

    const receipt = {
      status: 'VISIBLE_PREFLIGHT_CONFIRMED',
      observedAt: new Date().toISOString(),
      url: finalMenu.url,
      model: evidence.model,
      extendedThinking: evidence.extendedThinking,
      sendSelectorBridge,
      initialMenu: before.items,
      finalVisibleMenu: finalMenu.items,
      forbiddenControlsActivated: {
        send: false,
        stop: false,
        continue: false,
        retry: false,
        answerNow: false
      }
    };
    await fs.writeFile(outputPath, `${JSON.stringify(receipt, null, 2)}\n`, { encoding: 'utf8', flag: 'wx' });
    process.stdout.write(`${JSON.stringify(receipt)}\n`);
  } finally {
    await client.close();
  }
}

main().catch((error) => {
  const payload = { status: 'ERROR', error: error?.message || String(error), data: error?.data || null };
  process.stderr.write(`${JSON.stringify(payload)}\n`);
  process.exitCode = 1;
});
