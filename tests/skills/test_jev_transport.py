"""Offline checks of the Jev Pro transport driver: no browser, no network, no model call."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import types

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('jev_send', ROOT/'tools/pro_transport/jev_send.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


@pytest.mark.parametrize(
    'editors, expected_text, expected_form',
    [
        ([{'id': 'prompt-textarea', 'tag': 'DIV', 'role': 'textbox',
           'contenteditable': 'true', 'text': 'old draft'}], 'old draft', True),
        ([{'id': 'prompt-textarea', 'tag': 'TEXTAREA', 'value': 'old input'}], 'old input', True),
        ([{'tag': 'DIV', 'role': 'textbox', 'contenteditable': 'true',
           'markdown': True, 'text': 'new draft'}], 'new draft', True),
        ([{'id': 'pending-home-input', 'tag': 'TEXTAREA', 'value': 'Loading'},
          {'tag': 'DIV', 'role': 'textbox', 'contenteditable': 'true',
           'markdown': True, 'text': 'ready'}], 'ready', True),
        ([], None, False),
        ([{'id': 'pending-home-input', 'tag': 'TEXTAREA', 'value': 'Loading'}], None, False),
        ([{'id': 'prompt-textarea', 'tag': 'DIV', 'role': 'button',
           'contenteditable': 'true'}], None, False),
        ([{'tag': 'DIV', 'role': 'button', 'contenteditable': 'true',
           'markdown': True, 'text': 'wrong role'}], None, False),
        ([{'tag': 'DIV', 'role': 'textbox', 'contenteditable': 'true',
           'markdown': True, 'in_form': False}], None, False),
        ([{'id': 'prompt-textarea', 'tag': 'DIV', 'role': 'textbox', 'contenteditable': 'true'},
          {'tag': 'DIV', 'role': 'textbox', 'contenteditable': 'true', 'markdown': True}],
         None, False),
    ],
)
def test_composer_resolution_agrees_across_page_node_and_focus(editors, expected_text, expected_form):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js is needed to exercise the browser JavaScript')
    script = '''
const specs = SPECIFICATIONS;
const form = {innerText: 'model and attachment.pdf', querySelectorAll: () => []};
let focused = false;
const elements = specs.map(s => ({
  id: s.id || '', tagName: s.tag, value: s.value || '', innerText: s.text || '',
  getAttribute: name => name === 'role' ? (s.role || null) :
    name === 'contenteditable' ? (s.contenteditable || null) : null,
  hasAttribute: name => name === 'data-composer-markdown' && !!s.markdown,
  closest: selector => selector === 'form' && s.in_form !== false ? form : null,
  contains: () => false,
  focus: () => { focused = true; },
}));
const control = {
  id: 'effort', innerText: 'Pro',
  getAttribute: name => name === 'aria-haspopup' ? 'menu' : null,
  closest: selector => selector === 'form' ? form : null,
};
global.document = {
  title: 'ChatGPT', body: {innerText: ''},
  querySelectorAll: selector => selector === '#prompt-textarea, [data-composer-markdown]'
    ? elements.filter((e, i) => specs[i].id === 'prompt-textarea' || specs[i].markdown)
    : [],
  querySelector: () => null,
};
global.location = {href: 'https://chatgpt.com/', protocol: 'https:'};
global.window = {__jevFast: {nodes: new Map([[1, control]])}};
const page = eval(PAGE_FACTS);
const facts = eval(NODE_FACTS)(1);
let focus_error = null;
try { eval(FOCUS_COMPOSER); } catch (error) { focus_error = error.message; }
console.log(JSON.stringify({composer: page.composer, form_text: page.form_text,
  inside_composer_form: facts.inside_composer_form, focused, focus_error}));
'''.replace('SPECIFICATIONS', json.dumps(editors))
    for name in ('PAGE_FACTS', 'NODE_FACTS', 'FOCUS_COMPOSER'):
        script = script.replace(name, json.dumps(getattr(driver, name)))
    result = subprocess.run([node, '-e', script], check=True, capture_output=True, text=True)
    observed = json.loads(result.stdout)
    assert observed['composer'] == expected_text
    assert observed['inside_composer_form'] is expected_form
    assert observed['focused'] is expected_form
    assert observed['focus_error'] == (None if expected_form else 'composer unavailable')
    assert observed['form_text'] == ('model and attachment.pdf' if expected_form else '')


def test_send_attempted_key_never_reenters_browser(tmp_path, monkeypatch):
    cfg = {'state_dir': str(tmp_path)}
    prompt_file = tmp_path / 'prompt.txt'
    prompt_file.write_text('committed question\n', encoding='utf-8')
    operation = driver.Operation(cfg, 'already-sent')
    operation.save(send_attempted=True, send_effect='uncertain')
    monkeypatch.setattr(driver, 'chrome_start', lambda *_: pytest.fail('send was retried'))
    args = argparse.Namespace(prompt_file=str(prompt_file), key='already-sent')
    result = driver.command_send(args, cfg)
    assert result['send_attempted'] is True
    assert result['send_effect'] == 'uncertain'
    assert driver.Operation(cfg, args.key).data == operation.data


def run_browser_javascript(script, values, names):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js is needed to exercise the browser JavaScript')
    script = script.replace('SPECIFICATIONS', json.dumps(values))
    for name in names:
        script = script.replace(name, json.dumps(getattr(driver, name)))
    result = subprocess.run([node, '-e', script], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


@pytest.mark.parametrize(
    'buttons, files, expected_send, expected_upload',
    [
        ([{'testid': 'send-button'}], [{'id': 'upload-files'}], True, 'upload-files'),
        ([{'type': 'submit', 'label': '发送'}],
         [{'id': 'random123', 'label': '附加文件'},
          {'id': 'image1', 'label': '添加照片', 'accept': 'image/*'}], True, 'random123'),
        ([{'type': 'submit', 'label': 'Send'}],
         [{'id': 'random123', 'label': 'Attach files'}], True, 'random123'),
        ([{'type': 'submit', 'label': '发送', 'disabled': True}],
         [{'id': 'random123', 'label': '附加文件', 'accept': 'image/*'}], False, None),
        ([{'type': 'submit', 'label': 'Unknown'}],
         [{'id': 'random123', 'label': '添加照片'}], False, None),
        ([{'testid': 'send-button'}, {'type': 'submit', 'label': '发送'}],
         [{'id': 'one', 'label': '附加文件'}, {'id': 'two', 'label': '附加文件'}], False, None),
    ],
)
def test_send_and_upload_resolve_only_unique_composer_controls(
    buttons, files, expected_send, expected_upload
):
    script = '''
const specs = SPECIFICATIONS;
const editor = {
  id: '', tagName: 'DIV', innerText: '',
  getAttribute: name => name === 'role' ? 'textbox' : name === 'contenteditable' ? 'true' : null,
  hasAttribute: name => name === 'data-composer-markdown',
  closest: selector => selector === 'form' ? form : null,
  contains: () => false,
};
const buttons = specs.buttons.map(s => ({
  id: '', tagName: 'BUTTON', type: s.type || 'button', disabled: !!s.disabled, innerText: '',
  getAttribute: name => name === 'data-testid' ? (s.testid || null) :
    name === 'aria-label' ? (s.label || null) : null,
  closest: selector => selector === 'form' ? form : null,
  contains: () => false,
}));
const files = specs.files.map(s => ({
  id: s.id, getAttribute: name => name === 'accept' ? (s.accept || null) :
    name === 'aria-label' ? (s.label || null) : null,
}));
const form = {innerText: '', querySelectorAll: selector =>
  selector.startsWith('button[') ? buttons : selector === 'input[type="file"]' ? files : []};
global.document = {
  title: 'ChatGPT', body: {innerText: ''}, querySelector: () => null,
  querySelectorAll: selector =>
    selector === '#prompt-textarea, [data-composer-markdown]' ? [editor] :
    selector.startsWith('input[id="') ? files.filter(e => selector === 'input[id="' + e.id + '"]') : [],
};
global.location = {href: 'https://chatgpt.com/', protocol: 'https:'};
global.window = {__jevFast: {nodes: new Map([[1, buttons[0]]])}};
const send = eval('(' + SEND_LOOKUP + ')()');
const upload = eval('(' + UPLOAD_LOOKUP + ')()');
const node = buttons.length ? eval(NODE_FACTS)(1) : null;
const page = eval(PAGE_FACTS);
console.log(JSON.stringify({send: !!send, upload, node_send: node?.is_send || false,
  page_send: page.send_button}));
'''
    observed = run_browser_javascript(
        script, {'buttons': buttons, 'files': files},
        ('SEND_LOOKUP', 'UPLOAD_LOOKUP', 'NODE_FACTS', 'PAGE_FACTS')
    )
    assert observed == {'send': expected_send, 'upload': expected_upload,
                        'node_send': expected_send, 'page_send': expected_send}


@pytest.mark.parametrize(
    'changes, expected',
    [
        ({}, True),
        ({'model': '6 Fast'}, False),
        ({'effort': 'Medium'}, False),
        ({'selected': 'Older'}, False),
        ({'linked': False}, False),
        ({'menus': 2}, False),
        ({'sliders': 2}, False),
    ],
)
def test_modern_model_proof_uses_one_linked_menu_and_exact_controls(changes, expected):
    script = '''
const s = SPECIFICATIONS;
const editor = {
  id: '', tagName: 'DIV',
  getAttribute: name => name === 'role' ? 'textbox' : name === 'contenteditable' ? 'true' : null,
  hasAttribute: name => name === 'data-composer-markdown',
  closest: selector => selector === 'form' ? form : null,
};
const trigger = {
  id: 'model-control',
  getAttribute: name => ({'aria-label': '选择 ChatGPT 模型',
    'data-codex-intelligence-trigger': 'true',
    'data-composer-navigation-target': 'reasoning'})[name] || null,
};
const form = {querySelectorAll: selector => selector === '[aria-haspopup="menu"]' ? [trigger] : []};
const slider = {getAttribute: name => name === 'aria-valuenow' ? '4' :
  name === 'aria-valuemax' ? '4' : null};
const menu = {
  getAttribute: name => name === 'aria-labelledby' ? (s.linked ? 'model-control' : 'other') : null,
  querySelectorAll: selector => {
    if (selector.startsWith('[data-model-picker-view-toggle')) return [{innerText: s.model}];
    if (selector === '[data-maximum="true"]') return [{innerText: s.effort}];
    if (selector.startsWith('[data-reasoning-slider')) return Array(s.sliders).fill(slider);
    if (selector.startsWith('[role="menuitemradio"')) return [{innerText: s.selected}];
    return [];
  },
};
global.document = {querySelectorAll: selector =>
  selector === '#prompt-textarea, [data-composer-markdown]' ? [editor] :
  selector === '[role="menu"][aria-labelledby]' ? Array(s.menus).fill(menu) : []};
const proof = eval(MODEL_PROOF);
console.log(JSON.stringify({valid: !!proof && proof.model === '6 Pro' && proof.effort === 'Pro'
  && ['最新', 'Latest'].includes(proof.selected) && proof.now === proof.max}));
'''
    values = {'model': '6\nPro', 'effort': 'Pro', 'selected': '最新',
              'linked': True, 'menus': 1, 'sliders': 1, **changes}
    assert run_browser_javascript(script, values, ('MODEL_PROOF',))['valid'] is expected


def test_modern_effort_proof_closes_menu_before_fresh_observation(monkeypatch):
    monkeypatch.setattr(driver.time, 'sleep', lambda _seconds: None)
    opened = {'kind': 'click', 'label': 'Pro', 'node': 1, 'expanded': False}
    closed = {'actions': [opened], 'fingerprint': 'fresh-closed-page'}
    proof = {'model': '6 Pro', 'effort': 'Pro', 'selected': '最新',
             'now': 4, 'max': 4, 'trigger_id': 'model-control'}

    class Browser:
        def __init__(self):
            self.actions = []
            self.reads = 0

        def observe(self, **_kwargs):
            self.reads += 1
            return closed

        def evaluate(self, expression):
            if expression.startswith(driver.NODE_FACTS):
                return {'inside_composer_form': True, 'haspopup': 'menu',
                        'text': 'Pro', 'model_trigger': True}
            assert expression == driver.MODEL_PROOF
            return proof

        def act(self, action, page):
            self.actions.append(('open', action, page))

        def call(self, method, **kwargs):
            self.actions.append((method, kwargs['key']))

    browser = Browser()
    page, kind = driver.ensure_effort(browser, '6 Pro')
    assert page is closed and kind == 'modern' and browser.reads == 2
    assert browser.actions[0][0] == 'open'
    assert browser.actions[1:] == [('Input.dispatchKeyEvent', 'Escape')] * 2

    proof['model'] = '6 Fast'
    with pytest.raises(driver.PreSendFailure, match='does not prove configured effort'):
        driver.ensure_effort(Browser(), '6 Pro')


def test_attach_targets_validated_unique_document_input(monkeypatch, tmp_path):
    document = tmp_path / 'question.md'
    document.write_text('question', encoding='utf-8')
    monkeypatch.setattr(driver, 'wait_for', lambda *_args: {'attachment_cards': ['question(1).md']})
    monkeypatch.setattr(driver, 'ready_to_send', lambda *_args: None)

    class Browser:
        def __init__(self, upload_id):
            self.upload_id = upload_id
            self.calls = []

        def evaluate(self, expression):
            assert expression == f'({driver.UPLOAD_LOOKUP})()'
            return self.upload_id

        def call(self, command, **kwargs):
            self.calls.append((command, kwargs))
            if command == 'DOM.getDocument':
                return {'root': {'nodeId': 1}}
            if command == 'DOM.querySelector':
                return {'nodeId': 2}
            return {}

    browser = Browser('random123')
    displayed = driver.attach(browser, document, hashlib.sha256(document.read_bytes()).hexdigest())
    assert displayed == 'question(1).md'
    assert browser.calls[1] == ('DOM.querySelector',
                                {'nodeId': 1, 'selector': 'input[id="random123"]'})
    assert browser.calls[2] == ('DOM.setFileInputFiles',
                                {'nodeId': 2, 'files': [str(document)]})
    missing = Browser(None)
    with pytest.raises(driver.PreSendFailure, match='unique document upload input'):
        driver.attach(missing, document, hashlib.sha256(document.read_bytes()).hexdigest())
    assert missing.calls == []


@pytest.mark.parametrize('observed, expected, failure', [
    ([None, [], ['question(1).md']], 'question(1).md', None),
    ([None, ['other.md']], None, 'attachment card is not question.md'),
    ([None, ['question.md', 'other.md']], None, 'exactly one attachment card'),
])
def test_attach_waits_through_unready_card_but_rejects_wrong_or_multiple(
    monkeypatch, tmp_path, observed, expected, failure
):
    document = tmp_path / 'question.md'
    document.write_text('question', encoding='utf-8')
    seen = []
    pages = iter({'attachment_cards': cards} for cards in observed)
    monkeypatch.setattr(driver, 'facts', lambda _browser: next(pages))
    monkeypatch.setattr(driver.time, 'sleep', lambda _seconds: None)
    monkeypatch.setattr(driver, 'ready_to_send', lambda *_args: seen.append('ready'))

    class Browser:
        def evaluate(self, expression):
            assert expression == f'({driver.UPLOAD_LOOKUP})()'
            return 'upload-id'

        def call(self, command, **_kwargs):
            if command == 'DOM.getDocument':
                return {'root': {'nodeId': 1}}
            if command == 'DOM.querySelector':
                return {'nodeId': 2}
            if command == 'DOM.setFileInputFiles':
                seen.append('upload')
                return {}
            raise AssertionError(command)

    send = lambda: driver.attach(Browser(), document, hashlib.sha256(document.read_bytes()).hexdigest())
    if failure:
        with pytest.raises(driver.PreSendFailure, match=failure):
            send()
        assert seen == ['upload']
    else:
        assert send() == expected
        assert seen == ['upload', 'ready']


@pytest.mark.parametrize('cards, expected', [
    ([], None),
    (['question.md'], 'question.md'),
    (['question(1).md'], 'question(1).md'),
    (['question(12).md'], 'question(12).md'),
])
def test_attachment_display_name_accepts_only_literal_or_positive_collision_alias(cards, expected):
    assert driver.attachment_display_name(cards, 'question.md') == expected


@pytest.mark.parametrize('cards', [
    None, ['other.md'], ['question(0).md'], ['prefix-question.md'],
    ['question.md', 'other.md'],
])
def test_attachment_display_name_rejects_wrong_or_ambiguous_card(cards):
    with pytest.raises(driver.PreSendFailure):
        driver.attachment_display_name(cards, 'question.md')


@pytest.mark.parametrize('labels, expected', [
    ([], []),
    (['question.md', '移除 question.md'], ['question.md']),
    (['question(1).md', 'Remove question(1).md'], ['question(1).md']),
    (['question.md', '移除 question.md', 'other.md', '移除 other.md'], ['question.md', 'other.md']),
    (['question.md', '移除 question.md', '移除 question.md'], None),
    (['移除 question.md'], None),
])
def test_page_attachment_cards_require_same_form_filename_and_remove_pair(labels, expected):
    script = '''
const labels = SPECIFICATIONS;
const form = {innerText: 'The prompt mentions question.md', querySelectorAll: selector =>
  selector === 'button[aria-label]' ? labels.map(label => ({getAttribute: () => label})) : []};
const editor = {
  id: '', tagName: 'DIV', innerText: 'The prompt mentions question.md',
  getAttribute: name => name === 'role' ? 'textbox' : name === 'contenteditable' ? 'true' : null,
  hasAttribute: name => name === 'data-composer-markdown',
  closest: selector => selector === 'form' ? form : null,
};
global.document = {
  title: 'ChatGPT', body: {innerText: ''}, querySelector: () => null,
  querySelectorAll: selector => selector === '#prompt-textarea, [data-composer-markdown]'
    ? [editor] : [],
};
global.location = {href: 'https://chatgpt.com/', protocol: 'https:'};
const page = eval(PAGE_FACTS);
console.log(JSON.stringify({cards: page.attachment_cards, form_text: page.form_text}));
'''
    observed = run_browser_javascript(script, labels, ('PAGE_FACTS',))
    assert observed['form_text'] == 'The prompt mentions question.md'
    assert observed['cards'] == expected


def test_prompt_filename_without_card_cannot_complete_attachment_wait(monkeypatch, tmp_path):
    document = tmp_path / 'question.md'
    document.write_text('question', encoding='utf-8')
    browser = types.SimpleNamespace()
    browser.evaluate = lambda _expression: 'upload-id'

    def call(command, **_kwargs):
        if command == 'DOM.getDocument':
            return {'root': {'nodeId': 1}}
        if command == 'DOM.querySelector':
            return {'nodeId': 2}
        return {}

    browser.call = call

    def no_card(_browser, predicate, _seconds, _description):
        page = {'form_text': 'The prompt mentions question.md', 'attachment_cards': []}
        assert predicate(page) is False
        raise driver.PreSendFailure('no file card appeared')

    monkeypatch.setattr(driver, 'wait_for', no_card)
    with pytest.raises(driver.PreSendFailure, match='no file card appeared'):
        driver.attach(browser, document, hashlib.sha256(document.read_bytes()).hexdigest())


def test_same_key_attachment_bytes_cannot_change_before_browser(tmp_path, monkeypatch):
    cfg = {'state_dir': str(tmp_path / 'state')}
    prompt_file = tmp_path / 'prompt.txt'
    prompt_file.write_text('prepared question', encoding='utf-8')
    document = tmp_path / 'question.md'
    document.write_text('original bytes', encoding='utf-8')
    operation = driver.Operation(cfg, 'bound-question')
    operation.save(attachment=document.name,
                   attachment_sha256=hashlib.sha256(document.read_bytes()).hexdigest())
    document.write_text('mutated bytes', encoding='utf-8')
    monkeypatch.setattr(driver, 'chrome_start', lambda *_args: pytest.fail('opened browser'))
    args = argparse.Namespace(key='bound-question', prompt_file=str(prompt_file), attach=str(document))
    with pytest.raises(driver.PreSendFailure, match='different attachment bytes'):
        driver.command_send(args, cfg)
    assert driver.Operation(cfg, args.key).data['attachment_sha256'] == operation.data['attachment_sha256']


@pytest.mark.parametrize('chosen_click, change_fingerprint, failure, stale_send, card_at_send', [
    ('send', False, None, False, None),
    ('other', False, 'unrecognized click chosen before send', False, None),
    ('send', True, 'without fresh model and effort proof', False, None),
    ('send', False, None, True, None),
    ('send', False, None, False, 'question(1).md'),
    ('send', False, 'not question.md', False, 'other.md'),
    ('send', False, 'verified attachment card changed', False, ''),
])
def test_send_choice_needs_fresh_proof_and_recognized_target(
    tmp_path, monkeypatch, chosen_click, change_fingerprint, failure, stale_send, card_at_send
):
    prompt_file = tmp_path / 'question.txt'
    prompt_file.write_text('exact question\n', encoding='utf-8')
    document = tmp_path / 'question.md'
    if card_at_send is not None:
        document.write_text('document bytes', encoding='utf-8')
    proof_drafts = []
    monkeypatch.setattr(driver, 'chrome_start', lambda *_args: None)
    monkeypatch.setattr(driver, 'load_jev', lambda *_args: None)
    monkeypatch.setattr(driver.time, 'sleep', lambda _seconds: None)
    monkeypatch.setattr(driver, 'ready_to_send', lambda *_args: None)
    if card_at_send is not None:
        def fake_attach(browser, _path, _digest):
            browser.cards = [] if card_at_send == '' else ['question(1).md']
            return None if card_at_send == '' else 'question(1).md'
        monkeypatch.setattr(driver, 'attach', fake_attach)

    class Browser:
        def __init__(self):
            self.draft = ''
            self.acts = []
            self.sent_visible = False
            self.cards = []

        def observe(self, **_kwargs):
            action = ({'kind': 'fill', 'node': 1, 'id': 'fill', 'label': 'editor'}
                      if not self.draft else
                      {'kind': 'click', 'node': 2, 'id': 'click', 'label': chosen_click})
            return {'actions': [action], 'fingerprint': 'current'}

        def evaluate(self, expression):
            assert expression.startswith(driver.NODE_FACTS)
            if expression.endswith('(1)'):
                return {'is_composer': True, 'is_send': False}
            return {'is_composer': False, 'is_send': chosen_click == 'send'}

    class Agent:
        def __init__(self, _url, _goal):
            self.browser = Browser()
            self.state = {'status': 'ready', 'decision': None, 'page': None}
            self.goals = []

        def command(self, command, *_args):
            if command == 'predict':
                self.goals.append(self.state['goal'])
                action = self.state['page']['actions'][0]
                self.state['decision'] = {'choice': action['id'], 'operation': action['kind']}
                if card_at_send not in (None, '') and action['id'] == 'click':
                    self.browser.cards = [card_at_send]
                if change_fingerprint and action['id'] == 'click':
                    self.state['page']['fingerprint'] = 'stale'
            elif command == 'act':
                action = self.state['page']['actions'][0]
                self.browser.acts.append(action['kind'])
                if action['kind'] == 'fill':
                    self.browser.draft = 'exact question'
                elif stale_send and action['kind'] == 'click':
                    persisted = driver.Operation(cfg, args.key).data
                    assert persisted['send_attempted'] is True
                    assert persisted['send_effect'] == 'uncertain'
                    self.browser.sent_visible = True
                    raise StalePage('page changed during the one Send')
            else:
                raise AssertionError(command)

        def close(self):
            pass

    agent_module = types.ModuleType('jev_ultrafast.agent')
    agent_module.Agent = Agent
    agent_module.field_text = None
    browser_module = types.ModuleType('jev_ultrafast.browser')
    StalePage = type('StalePage', (Exception,), {})
    browser_module.StalePage = StalePage
    package = types.ModuleType('jev_ultrafast')
    package.agent = agent_module
    monkeypatch.setitem(sys.modules, 'jev_ultrafast', package)
    monkeypatch.setitem(sys.modules, 'jev_ultrafast.agent', agent_module)
    monkeypatch.setitem(sys.modules, 'jev_ultrafast.browser', browser_module)
    current_agent = []
    original_agent = Agent

    def make_agent(*args):
        agent = original_agent(*args)
        current_agent.append(agent)
        return agent

    agent_module.Agent = make_agent
    monkeypatch.setattr(driver, 'facts', lambda browser: {
        'composer': browser.draft, 'login': False, 'challenge': False, 'stop_button': False,
        'users': ['exact question'] if browser.sent_visible else [],
        'user_turns': ['exact question'] if browser.sent_visible else [],
        'form_text': '', 'attachment_cards': browser.cards, 'url': CONVERSATION,
    })

    def prove(browser, _effort):
        proof_drafts.append(browser.draft)
        return browser.observe(screenshot=False), 'modern'

    monkeypatch.setattr(driver, 'ensure_effort', prove)
    args = argparse.Namespace(prompt_file=str(prompt_file), key='fresh-proof', conversation='new',
                              mode='headless', effort='6 Pro',
                              attach=str(document) if card_at_send is not None else None,
                              dry_run=not stale_send)
    cfg = {'state_dir': str(tmp_path / 'state'), 'provider_root': 'https://chatgpt.com/'}
    if failure:
        with pytest.raises(driver.PreSendFailure, match=failure):
            driver.command_send(args, cfg)
    else:
        result = driver.command_send(args, cfg)
        if stale_send:
            assert result['send_attempted'] is True and result['send_effect'] == 'sent'
        else:
            assert result['dry_run'].startswith('reached the send button')
    assert proof_drafts == ['', 'exact question']
    assert 'Type the prepared message into the message box only' in current_agent[0].goals[0]
    assert 'Click the Send button exactly once' in current_agent[0].goals[1]
    assert current_agent[0].browser.acts == (['fill', 'click'] if stale_send else ['fill'])
    assert driver.Operation(cfg, args.key).data['send_attempted'] is stale_send
    if card_at_send is not None:
        expected = None if card_at_send == '' else 'question(1).md'
        assert driver.Operation(cfg, args.key).data['attachment_display_name'] == expected


def modern_conversation_page(specs):
    script = '''
const specs = SPECIFICATIONS;
const units = [];
for (let i = 0; i < specs.length; i++) {
  const s = specs[i];
  const key = 'turn-' + i;
  const footer = {
    closest: selector => selector === '[data-content-search-turn-key]' ? container : null,
    querySelectorAll: selector => selector.includes('重新生成回复') ? [{}] :
      selector.includes('回复不佳') ? [{}] : [],
  };
  const userFooter = {
    closest: selector => selector === '[data-content-search-turn-key]' ? container : null,
    querySelectorAll: () => [],
  };
  const container = {
    getAttribute: name => name === 'data-content-search-turn-key' ? key : null,
    querySelectorAll: selector => selector === '.turn-action-controls'
      ? [userFooter, ...Array(s.footers || 0).fill(footer)] : [],
  };
  const body = {innerText: s.user};
  const bubble = {
    querySelectorAll: selector => selector === '.whitespace-pre-wrap'
      ? Array(s.userBodies || 1).fill(body) : [],
    contains: node => Boolean(s.cardInBubble) && cards.includes(node),
  };
  const cards = s.attachment ? Array(s.cardCount || 1).fill(null).map(() => ({
    closest: selector => selector === '[data-chatgpt-search-unit-key]' ? userUnit : null,
    querySelectorAll: selector => selector === 'span[title].truncate.text-default.text-sm.font-semibold'
      ? [{innerText: s.attachment,
          getAttribute: name => name === 'title' ? (s.cardTitle || s.attachment) : null}] : [],
  })) : [];
  const userUnit = {
    innerText: s.user + (s.attachment ? '\\n' + s.attachment : ''),
    getAttribute: name => name === 'data-chatgpt-search-unit-key' ? key + ':0:user' : null,
    closest: selector => selector === '[data-content-search-turn-key]' ? container : null,
    querySelectorAll: selector => selector === '[data-user-message-bubble="true"]' ? [bubble]
      : selector === '[class~="group/resource-card"]' ? cards : [],
  };
  units.push(userUnit);
  for (let j = 0; j < s.assistants.length; j++) {
    const answer = s.assistants[j];
    units.push({
      innerText: answer || '',
      getAttribute: name => name === 'data-chatgpt-search-unit-key'
        ? (s.badKey ? 'wrong-turn' : key) + ':' + (j + 1) + ':assistant' : null,
      closest: selector => selector === '[data-content-search-turn-key]' ? container : null,
      querySelectorAll: selector => selector === '[data-markdown-text-style="assistant-message"]'
        ? answer === null ? [] : [{innerText: answer}] : [],
    });
  }
}
global.document = {
  title: 'ChatGPT', body: {innerText: ''}, querySelector: () => null,
  querySelectorAll: selector => selector === '[data-chatgpt-search-unit-key]' ? units : [],
};
global.location = {href: 'https://chatgpt.com/', protocol: 'https:'};
const page = eval(PAGE_FACTS);
console.log(JSON.stringify({turns: page.turns, users: page.users,
  user_turns: page.user_turns, assistants: page.assistants}));
'''
    return run_browser_javascript(script, specs, ('PAGE_FACTS',))


def test_modern_conversation_binds_prompt_body_attachment_and_own_last_final():
    page = modern_conversation_page([
        {'user': WAIT_PROMPT, 'attachment': 'question.md',
         'assistants': ['opening reply', 'complete answer'], 'footers': 1},
        {'user': 'second question', 'assistants': ['ongoing reply'], 'footers': 0},
        {'user': 'third question', 'assistants': ['another complete answer'], 'footers': 1},
    ])
    assert page['users'][0] == WAIT_PROMPT + '\nquestion.md'
    assert page['user_turns'][0] == WAIT_PROMPT + '\nquestion.md'
    assert page['turns'][0]['message_body'] == WAIT_PROMPT
    assert page['turns'][0]['attachment_names'] == ['question.md']
    assert page['turns'][3]['attachment_names'] == []
    assert page['turns'][1]['final_controls'] is False
    assert page['turns'][2]['final_controls'] is True
    assert page['turns'][4]['final_controls'] is False
    assert page['turns'][6]['final_controls'] is True
    operation = {'squashed_sha256': hashlib.sha256(WAIT_PROMPT.encode()).hexdigest(),
                 'attachment': 'question.md'}
    bound = driver._bind_operation_turn(page, operation, WAIT_PROMPT)
    assert bound == 0
    assert driver._answer_after_turn(page, bound) == 'complete answer'
    assert driver._answer_after_turn(page, 3) == ''


def test_modern_conversation_never_borrows_feedback_or_early_assistant_completion():
    page = modern_conversation_page([
        {'user': WAIT_PROMPT, 'assistants': ['still working'], 'footers': 0},
        {'user': 'other question', 'assistants': ['final other answer'], 'footers': 1},
        {'user': 'third question', 'assistants': ['opening', None], 'footers': 1},
    ])
    assert [turn['final_controls'] for turn in page['turns'] if turn['role'] == 'assistant'] == \
        [False, True, False, False]
    assert driver._answer_after_turn(page, 0) == ''
    assert driver._answer_after_turn(page, 4) == ''
    ambiguous = modern_conversation_page([
        {'user': WAIT_PROMPT, 'assistants': ['answer'], 'footers': 2},
    ])
    assert ambiguous['turns'][1]['final_controls'] is False
    malformed = modern_conversation_page([
        {'user': WAIT_PROMPT, 'assistants': ['answer'], 'footers': 1, 'badKey': True},
    ])
    assert malformed['turns'] == []


def test_modern_sent_card_evidence_is_independent_of_prompt_text():
    prompt = WAIT_PROMPT + ' The expected file is question.md.'
    page = modern_conversation_page([
        {'user': prompt, 'assistants': ['answer'], 'footers': 1},
    ])
    operation = {'squashed_sha256': hashlib.sha256(driver.squash(prompt).encode()).hexdigest(),
                 'attachment': 'question.md'}
    assert page['turns'][0]['attachment_names'] == []
    with pytest.raises(driver.MissingAttachmentEvidence):
        driver._bind_operation_turn(page, operation, prompt)

    alias = modern_conversation_page([
        {'user': prompt, 'attachment': 'question(1).md',
         'assistants': ['answer'], 'footers': 1},
    ])
    operation['attachment_display_name'] = 'question(1).md'
    assert driver._bind_operation_turn(alias, operation, prompt) == 0
    assert alias['turns'][0]['attachment_names'] == ['question(1).md']

    embedded = modern_conversation_page([
        {'user': prompt, 'attachment': 'question(1).md', 'cardInBubble': True,
         'assistants': ['answer'], 'footers': 1},
    ])
    with pytest.raises(driver.MissingAttachmentEvidence):
        driver._bind_operation_turn(embedded, operation, prompt)

    ambiguous = modern_conversation_page([
        {'user': prompt, 'attachment': 'question(1).md', 'cardCount': 2,
         'assistants': ['answer'], 'footers': 1},
    ])
    with pytest.raises(driver.MissingAttachmentEvidence):
        driver._bind_operation_turn(ambiguous, operation, prompt)

    wrong_title = modern_conversation_page([
        {'user': prompt, 'attachment': 'question(1).md', 'cardTitle': 'other.md',
         'assistants': ['answer'], 'footers': 1},
    ])
    assert wrong_title['turns'] == []

QUESTION = '## Pro question 2026-01-01 example'
NOTES = f'# notebook\n\n## earlier entry\ntext\n\n{QUESTION}\nQuestion: one?\n### Answer\n'


def test_key_is_the_documented_hash_and_masking_hides_only_the_address():
    key = driver.question_key('o/r', 'b', 'd', 'a' * 40, 'NOTES.md', QUESTION)
    assert key == driver.question_key('o/r', 'b', 'd', 'a' * 40, 'NOTES.md', QUESTION)
    assert key != driver.question_key('o/r', 'b', 'd', 'a' * 40, 'NOTES.md', QUESTION + ' ')
    shown = driver.public({'conversation_url': 'https://chatgpt.com/c/x', 'state': 'COMPLETE'}, False)
    assert shown == {'conversation_url': 'recorded locally', 'state': 'COMPLETE'}
    assert driver.public({'conversation_url': 'u'}, True) == {'conversation_url': 'u'}


def test_answer_block_needs_unique_headings():
    before, answer, after = driver.answer_block(NOTES + 'body\n\n## later entry\nmore\n', QUESTION, '### Answer')
    assert before.endswith('### Answer') and answer.strip() == 'body' and after.startswith('## later entry')
    assert driver.answer_block(NOTES + NOTES, QUESTION, '### Answer') is None
    assert driver.answer_block('# nothing here\n', QUESTION, '### Answer') is None


def test_answer_block_excludes_author_decision_but_keeps_nested_answer_content():
    body = ('answer\n\n#### Details\nnested\n```markdown\n## example question\n'
            '### example heading\n```\n')
    decision = '### Decision\nauthor judgment\n\n## later entry\nmore\n'
    before, answer, after = driver.answer_block(NOTES + body + decision, QUESTION, '### Answer')
    assert before.endswith('### Answer')
    assert answer == body.rstrip('\n')
    assert after == decision


def test_compose_keeps_document_hash_but_gives_pro_a_natural_cover_note(tmp_path):
    message = tmp_path/'full.txt'
    message.write_text('line one\n\nline two\n', encoding='utf-8')
    args = argparse.Namespace(message_file=str(message), slug='example-question', subject='d', out_dir=str(tmp_path))
    made = driver.command_compose(args, {})
    document = Path(made['document'])
    assert document.read_text(encoding='utf-8') == 'line one\n\nline two\n'
    assert made['document_sha256'] == hashlib.sha256(document.read_bytes()).hexdigest()
    short = Path(made['short_message']).read_text(encoding='utf-8')
    assert document.name in short and '请阅读全文' in short
    assert '优先将完整答复写入附件指定的 GitHub Answer' in short
    assert '若 GitHub 读取或写入不可用，请如实说明' in short
    assert '仍请在当前聊天中输出完整答复' in short
    assert '若缺少关键来源，请说明缺口' in short
    assert '若无法读取附件，请说明后停止' in short
    assert '不要凭记忆' in short and '不要假装已经阅读' in short
    assert made['document_sha256'] not in short
    assert all(field not in short for field in ('sha256', 'source_sha', 'branch'))
    with pytest.raises(driver.PreSendFailure):
        driver.command_compose(argparse.Namespace(**{**vars(args), 'slug': 'Bad Slug'}), {})


CONVERSATION = 'https://chatgpt.com/c/12345678-1234-1234-1234-123456789abc'
WAIT_PROMPT = 'read the attached complete question'
MISSING = object()


def wait_page(turns=(), *, stop=False, login=False, challenge=False, approval=(),
              page_error=False, url=CONVERSATION):
    return {
        'url': url,
        'title': 'ChatGPT',
        'composer': '',
        'send_button': False,
        'form_text': '',
        'user_turns': [turn['turn_text'] for turn in turns if turn['role'] == 'user'],
        'stop_button': stop,
        'login': login,
        'auth_required': login,
        'approval': list(approval),
        'approval_text': 'permission',
        'challenge': challenge,
        'page_error': page_error,
        'users': [turn['text'] for turn in turns if turn['role'] == 'user'],
        'assistants': [turn['text'] for turn in turns if turn['role'] == 'assistant'],
        'turns': list(turns),
    }


def user_turn(text=WAIT_PROMPT, attachment=None, *, message_body=MISSING):
    suffix = f'\n{attachment}' if attachment else ''
    turn = {'role': 'user', 'text': text + suffix, 'turn_text': text + suffix,
            'attachment_names': [attachment] if attachment else []}
    if message_body is MISSING:
        message_body = text
    if message_body is not None:
        turn['message_body'] = message_body
    return turn


def assistant_turn(text, *, final=True):
    return {'role': 'assistant', 'text': text, 'turn_text': text, 'final_controls': final}


class FakeWaitBrowser:
    def __init__(self, pages, on_read=None, close_delay=0):
        self.pages = list(pages)
        self.on_read = on_read
        self.close_delay = close_delay
        self.reads = 0
        self.closed = False

    def read(self):
        self.reads += 1
        if self.on_read:
            value = self.on_read(self)
            if value is not None:
                return value
        if len(self.pages) > 1:
            return self.pages.pop(0)
        return self.pages[0]


class FakeWaitAgent:
    def __init__(self, browser):
        self.browser = browser
        self.commands = []

    def command(self, *args, **kwargs):
        self.commands.append((args, kwargs))
        raise AssertionError('wait must not invoke a send action')

    def close(self):
        if self.browser.close_delay:
            time.sleep(self.browser.close_delay)
        self.browser.closed = True


def install_wait(tmp_path, monkeypatch, agents, *, alive=True, attachment=None,
                 recovery_attempts=3, rpc=.05, sample=0):
    tmp_path.mkdir(parents=True, exist_ok=True)
    cfg = {'state_dir': str(tmp_path/'state')}
    monkeypatch.setattr(driver, 'WAIT_RPC_SECONDS', rpc)
    monkeypatch.setattr(driver, 'WAIT_OPEN_SECONDS', rpc)
    monkeypatch.setattr(driver, 'WAIT_SAMPLE_SECONDS', sample)
    monkeypatch.setattr(driver, 'WAIT_RECOVERY_ATTEMPTS', recovery_attempts)
    key = 'wait-test'
    prompt_file = tmp_path/'prompt.txt'
    prompt_file.write_text(WAIT_PROMPT + '\n', encoding='utf-8')
    operation = driver.Operation(cfg, key)
    facts = {
        'key': key,
        'send_attempted': True,
        'send_effect': 'sent',
        'mode': 'headless',
        'conversation_url': CONVERSATION,
        'squashed_sha256': hashlib.sha256(driver.squash(WAIT_PROMPT).encode()).hexdigest(),
    }
    if attachment:
        facts.update(attachment=attachment, attachment_sha256='a' * 64)
    operation.save(**facts)
    environment = {'alive': alive, 'starts': 0}
    queue = list(agents)

    monkeypatch.setattr(driver, 'load_jev', lambda _cfg: pytest.fail('passive wait loaded Jev credentials'))
    monkeypatch.setattr(driver, 'cdp_version', lambda _cfg: {'Browser': 'Headless'} if environment['alive'] else None)

    def start(_cfg, _mode):
        environment['alive'] = True
        environment['starts'] += 1
        return {'chrome': 'started', 'mode': _mode}

    monkeypatch.setattr(driver, 'chrome_start', start)
    monkeypatch.setattr(driver, 'make_wait_observer', lambda _url, _cfg: queue.pop(0))
    monkeypatch.setattr(driver, 'facts', lambda browser: browser.read())
    args = argparse.Namespace(
        key=key,
        conversation_url=None,
        mode=None,
        prompt_file=str(prompt_file),
        answer_file=str(tmp_path/'answer.md'),
        timeout=1,
    )
    return cfg, args, environment, operation


def stable_answer_pages(answer, *, attachment=None, earlier=False):
    turns = []
    if earlier:
        turns += [user_turn('previous question'), assistant_turn('previous answer')]
    turns += [user_turn(attachment=attachment), assistant_turn(answer)]
    if earlier:
        turns += [user_turn('later question'), assistant_turn('later answer')]
    page = wait_page(turns)
    return [page, page, page, page]


def test_wait_starts_missing_chrome_and_collects_the_bound_answer(tmp_path, monkeypatch, capsys):
    agent = FakeWaitAgent(FakeWaitBrowser(stable_answer_pages('complete fallback answer')))
    cfg, args, environment, operation = install_wait(tmp_path, monkeypatch, [agent], alive=False)
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'COMPLETE' and result['recoveries'] == 1
    assert environment['starts'] == 1
    assert Path(result['answer_file']).read_text() == 'complete fallback answer\n'
    assert result['kind'] == 'chat answer'
    assert operation.data['send_attempted'] is True and agent.commands == []
    assert CONVERSATION not in capsys.readouterr().err


@pytest.mark.parametrize('missing_controls', [False, True])
def test_wait_does_not_complete_stable_opening_during_tool_work(
    tmp_path, monkeypatch, missing_controls
):
    opening = assistant_turn('I will read the sources and write the answer.', final=False)
    if missing_controls:
        opening.pop('final_controls')
    page = wait_page([
        user_turn('previous question'), assistant_turn('previous final answer'),
        user_turn(), opening,
        user_turn('later question'), assistant_turn('later final answer'),
    ])
    agent = FakeWaitAgent(FakeWaitBrowser([page]))
    cfg, args, _state, operation = install_wait(tmp_path, monkeypatch, [agent])
    args.timeout = .03
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'IN_PROGRESS'
    assert not Path(args.answer_file).exists()
    assert operation.data['send_attempted'] is True and agent.commands == []
    assert agent.browser.closed


def test_wait_collects_final_answer_after_stable_opening_without_stop_button(tmp_path, monkeypatch):
    opening = assistant_turn('I will read the sources and write the answer.', final=False)
    pending = wait_page([user_turn(), opening])
    final = wait_page([user_turn(), opening, assistant_turn('The complete scientific answer.')])
    agent = FakeWaitAgent(FakeWaitBrowser([pending] * 6 + [final] * 4))
    cfg, args, _state, operation = install_wait(tmp_path, monkeypatch, [agent])
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'COMPLETE'
    assert agent.browser.reads >= 10
    assert Path(args.answer_file).read_text() == 'The complete scientific answer.\n'
    assert operation.data['send_attempted'] is True and agent.commands == []


def test_wait_does_not_use_earlier_final_controls_for_last_partial_message(tmp_path, monkeypatch):
    page = wait_page([
        user_turn(), assistant_turn('Earlier finished fragment'),
        assistant_turn('The latest response is still running.', final=False),
    ])
    agent = FakeWaitAgent(FakeWaitBrowser([page]))
    cfg, args, _state, _operation = install_wait(tmp_path, monkeypatch, [agent])
    args.timeout = .03
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'IN_PROGRESS'
    assert not Path(args.answer_file).exists()


def test_wait_recovers_dead_chrome_without_restarting_the_pro_task(tmp_path, monkeypatch):
    environment = {}

    def die_after_read(_browser):
        environment['state']['alive'] = False
        return wait_page([user_turn()], stop=True)

    first = FakeWaitAgent(FakeWaitBrowser([], on_read=die_after_read))
    second = FakeWaitAgent(FakeWaitBrowser(stable_answer_pages('answer after reconnect')))
    cfg, args, state, operation = install_wait(tmp_path, monkeypatch, [first, second])
    environment['state'] = state
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'COMPLETE' and result['recoveries'] == 1
    assert state['starts'] == 1 and first.browser.closed
    assert Path(args.answer_file).read_text() == 'answer after reconnect\n'
    assert operation.data['send_attempted'] is True
    assert first.commands == second.commands == []


def test_hung_observation_and_close_are_bounded_then_recovered(tmp_path, monkeypatch):
    def hang(_browser):
        time.sleep(.3)

    first = FakeWaitAgent(FakeWaitBrowser([], on_read=hang, close_delay=.3))
    second = FakeWaitAgent(FakeWaitBrowser(stable_answer_pages('bounded recovery answer')))
    cfg, args, _state, operation = install_wait(
        tmp_path, monkeypatch, [first, second], rpc=.03
    )
    started = time.monotonic()
    result = driver.command_wait(args, cfg)
    elapsed = time.monotonic() - started
    assert result['state'] == 'COMPLETE' and elapsed < .5
    assert operation.data['send_attempted'] is True


def test_wait_timeout_escapes_helpers_that_catch_oserror():
    def swallow_oserror():
        try:
            time.sleep(.07)
        except OSError:
            return 'incorrectly swallowed'

    started = time.monotonic()
    with pytest.raises(driver.WaitCallTimeout):
        driver.bounded_wait_call(swallow_oserror, .01, 'review reproduction')
    assert time.monotonic() - started < .05


def test_recovery_limit_and_total_observation_deadline_are_finite(tmp_path, monkeypatch):
    cfg, args, _state, operation = install_wait(
        tmp_path, monkeypatch, [], recovery_attempts=1
    )
    monkeypatch.setattr(driver, 'make_wait_observer', lambda _url, _cfg: (_ for _ in ()).throw(RuntimeError('gone')))
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'ERROR'
    assert result['reason'] == 'browser recovery budget exhausted before the conversation was readable'
    assert result['error_type'] == 'RuntimeError'
    assert result['recoveries'] == 1 and operation.data['send_attempted'] is True

    thinking = wait_page([user_turn()], stop=True)
    agent = FakeWaitAgent(FakeWaitBrowser([thinking]))
    cfg2, args2, _state2, operation2 = install_wait(tmp_path/'deadline', monkeypatch, [agent])
    args2.timeout = .035
    monkeypatch.setattr(driver, 'WAIT_SAMPLE_SECONDS', .01)
    started = time.monotonic()
    result2 = driver.command_wait(args2, cfg2)
    assert result2['state'] == 'IN_PROGRESS'
    assert time.monotonic() - started < .2
    assert 'still thinking' in result2['reason']
    assert agent.browser.closed
    assert operation2.data['send_attempted'] is True


@pytest.mark.parametrize(
    'problem, expected_state, reason',
    [
        ({'login': True}, 'NEEDS_HUMAN', 'provider login is required'),
        ({'challenge': True}, 'NEEDS_HUMAN', 'provider human verification is required'),
        ({'page_error': True}, 'ERROR', 'provider page reported an unrecoverable error'),
        ({'approval': ['Deny']}, 'NEEDS_HUMAN', 'an authorization prompt requires human review'),
    ],
)
def test_wait_surfaces_auth_challenge_and_page_errors(tmp_path, monkeypatch, problem, expected_state, reason):
    page = wait_page([user_turn()], **problem)
    agent = FakeWaitAgent(FakeWaitBrowser([page]))
    cfg, args, _state, operation = install_wait(tmp_path, monkeypatch, [agent])
    result = driver.command_wait(args, cfg)
    assert result['state'] == expected_state and result['reason'] == reason
    assert operation.data['send_attempted'] is True


def test_wait_binds_message_body_separately_from_attachment_card(tmp_path, monkeypatch):
    attachment = 'question.md'
    agent = FakeWaitAgent(FakeWaitBrowser(stable_answer_pages(
        'complete attached answer', attachment=attachment
    )))
    cfg, args, _state, operation = install_wait(
        tmp_path, monkeypatch, [agent], attachment=attachment
    )
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'COMPLETE'
    assert Path(args.answer_file).read_text() == 'complete attached answer\n'
    assert driver.Operation(cfg, operation.data['key']).data['attachment_seen'] is True


def test_wait_binds_server_collision_name_saved_at_upload(tmp_path, monkeypatch):
    displayed = 'question(1).md'
    agent = FakeWaitAgent(FakeWaitBrowser(stable_answer_pages(
        'complete attached answer', attachment=displayed
    )))
    cfg, args, _state, operation = install_wait(
        tmp_path, monkeypatch, [agent], attachment='question.md'
    )
    operation.save(attachment_display_name=displayed)
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'COMPLETE'
    assert Path(result['answer_file']).read_text() == 'complete attached answer\n'
    assert driver.Operation(cfg, operation.data['key']).data['attachment_seen'] is True


@pytest.mark.parametrize('body', ['another prompt', WAIT_PROMPT + ' trailing text'])
def test_wait_rejects_wrong_or_superstring_message_body(tmp_path, monkeypatch, body):
    page = wait_page([user_turn(body)])
    agent = FakeWaitAgent(FakeWaitBrowser([page]))
    cfg, args, _state, operation = install_wait(tmp_path, monkeypatch, [agent])
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'ERROR'
    assert 'user turn' in result['reason']
    assert operation.data['send_attempted'] is True


def test_wait_rejects_duplicate_exact_message_bodies(tmp_path, monkeypatch):
    page = wait_page([user_turn(), assistant_turn('old answer'), user_turn()])
    agent = FakeWaitAgent(FakeWaitBrowser([page]))
    cfg, args, _state, _operation = install_wait(tmp_path, monkeypatch, [agent])
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'ERROR'
    assert result['reason'] == 'conversation does not contain exactly one user turn for this operation'


def test_wait_keeps_missing_sent_card_pending_after_exact_body_match(tmp_path, monkeypatch):
    page = wait_page([user_turn()])
    agent = FakeWaitAgent(FakeWaitBrowser([page]))
    cfg, args, _state, operation = install_wait(
        tmp_path, monkeypatch, [agent], attachment='question.md'
    )
    args.timeout = .03
    monkeypatch.setattr(driver, 'WAIT_SAMPLE_SECONDS', .01)
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'IN_PROGRESS'
    assert result['reason'] == 'observation window ended before the sent attachment card was observed'
    assert operation.data['send_attempted'] is True
    assert not Path(args.answer_file).exists()


def test_prompt_filename_text_without_sent_card_cannot_bind_attachment():
    prompt = 'read question.md and answer'
    turn = user_turn(prompt)
    assert 'question.md' in turn['text'] and turn['attachment_names'] == []
    operation = {'attachment': 'question.md',
                 'squashed_sha256': hashlib.sha256(prompt.encode()).hexdigest()}
    with pytest.raises(driver.WaitReadFailure, match='attachment is absent'):
        driver._bind_operation_turn(wait_page([turn]), operation, prompt)


def test_wait_falls_back_to_exact_full_message_when_body_field_is_absent(tmp_path, monkeypatch):
    turns = [user_turn(message_body=None), assistant_turn('legacy exact answer')]
    page = wait_page(turns)
    agent = FakeWaitAgent(FakeWaitBrowser([page, page, page, page]))
    cfg, args, _state, _operation = install_wait(tmp_path, monkeypatch, [agent])
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'COMPLETE'
    assert Path(args.answer_file).read_text() == 'legacy exact answer\n'


def test_wait_selects_answer_after_bound_turn_and_source_hash_is_not_a_receipt(tmp_path, monkeypatch):
    source_sha = 'b' * 40
    answer = f'GitHub write was unavailable. Full chat answer. Source SHA: {source_sha}'
    agent = FakeWaitAgent(FakeWaitBrowser(stable_answer_pages(answer, earlier=True)))
    cfg, args, _state, operation = install_wait(tmp_path, monkeypatch, [agent])
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'COMPLETE'
    assert Path(args.answer_file).read_text() == answer + '\n'
    assert result['kind'] == 'chat answer' and result['receipt_commits'] == []
    assert 'previous answer' not in Path(args.answer_file).read_text()
    assert 'later answer' not in Path(args.answer_file).read_text()
    assert operation.data['send_attempted'] is True and agent.commands == []


def test_wait_relocates_bound_turn_when_older_history_loads(tmp_path, monkeypatch):
    first = wait_page([user_turn(), assistant_turn('partial target answer')])
    shifted = wait_page([
        user_turn('older question'),
        assistant_turn('wrong older answer'),
        user_turn(),
        assistant_turn('correct target answer'),
    ])
    agent = FakeWaitAgent(FakeWaitBrowser([first, shifted, shifted, shifted, shifted]))
    cfg, args, _state, _operation = install_wait(tmp_path, monkeypatch, [agent])
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'COMPLETE'
    assert Path(args.answer_file).read_text() == 'correct target answer\n'
    assert 'wrong older answer' not in Path(args.answer_file).read_text()


def test_wait_allows_empty_initial_hydration_before_target_and_answer(tmp_path, monkeypatch):
    empty = wait_page([])
    target = wait_page([user_turn()], stop=True)
    final = wait_page([user_turn(), assistant_turn('answer after hydration')])
    agent = FakeWaitAgent(FakeWaitBrowser([empty, target, final, final, final, final]))
    cfg, args, _state, operation = install_wait(tmp_path, monkeypatch, [agent])
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'COMPLETE'
    assert Path(args.answer_file).read_text() == 'answer after hydration\n'
    assert operation.data['send_attempted'] is True


def _git(repo, *argv):
    return subprocess.run(['git', '-C', str(repo), *argv], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def delivery(tmp_path, monkeypatch):
    origin, work = tmp_path/'origin.git', tmp_path/'work'
    subprocess.run(['git', 'init', '--quiet', '--bare', '-b', 'main', str(origin)], check=True)
    subprocess.run(['git', 'clone', '--quiet', str(origin), str(work)], check=True, capture_output=True)
    for name, value in (('user.name', 't'), ('user.email', 't@example.invalid')):
        _git(work, 'config', name, value)
    (work/'NOTES.md').write_text(NOTES, encoding='utf-8')
    _git(work, 'add', 'NOTES.md')
    _git(work, 'commit', '--quiet', '-m', 'question')
    _git(work, 'push', '--quiet', 'origin', 'HEAD:main')
    monkeypatch.setattr(driver, 'REPO', work)

    def write(text, message, extra=None):
        (work/'NOTES.md').write_text(text, encoding='utf-8')
        if extra:
            (work/extra).write_text('x', encoding='utf-8')
            _git(work, 'add', extra)
        _git(work, 'commit', '--quiet', '-am', message)
        _git(work, 'push', '--quiet', 'origin', 'HEAD:main')
        return _git(work, 'rev-parse', 'HEAD')

    args = argparse.Namespace(key=None, remote='origin', branch='main', source_sha=_git(work, 'rev-parse', 'HEAD'),
                              target_path='NOTES.md', question_heading=QUESTION, answer_heading='### Answer',
                              answer_out=str(tmp_path/'answer.md'))
    return args, write


def test_deliver_accepts_an_answer_only_commit_and_ignores_unrelated_ones(delivery):
    args, write = delivery
    assert driver.command_deliver(args, {})['state'] == 'NOT_DELIVERED'
    answered = write(NOTES + 'the answer\n', 'answer')
    write(NOTES + 'the answer\n\n## later entry\nappended by someone else\n', 'unrelated append')
    result = driver.command_deliver(args, {})
    assert result['state'] == 'DELIVERED' and [c['commit'] for c in result['commits']] == [answered]
    assert result['commits'][0]['parent_is_source']
    assert Path(args.answer_out).read_text(encoding='utf-8') == 'the answer\n'


def test_deliver_ignores_decision_edits_and_accepts_later_answer(delivery):
    args, write = delivery
    decision = '\n### Decision\nindependent reviewer advice\n'
    write(NOTES + decision, 'author records a decision')
    assert driver.command_deliver(args, {})['state'] == 'NOT_DELIVERED'
    decision += 'author updates the plan\n'
    write(NOTES + decision, 'author revises the decision')
    assert driver.command_deliver(args, {})['state'] == 'NOT_DELIVERED'
    answered = write(NOTES + 'the Pro answer\n' + decision, 'Pro answers its assigned subsection')
    result = driver.command_deliver(args, {})
    assert result['state'] == 'DELIVERED'
    assert [commit['commit'] for commit in result['commits']] == [answered]
    assert Path(args.answer_out).read_text(encoding='utf-8') == 'the Pro answer\n'


@pytest.mark.parametrize('text, extra', [
    (NOTES.replace('Question: one?', 'Question: two?') + 'the answer\n', None),
    (NOTES + 'the answer\n', 'other.txt'),
])
def test_deliver_reports_a_changed_question_or_another_file_as_conflict(delivery, text, extra):
    args, write = delivery
    write(text, 'answer with a side effect', extra)
    result = driver.command_deliver(args, {})
    assert result['state'] == 'CONFLICT' and 'answer_out' not in result
    assert json.dumps(result)  # facts only, serialisable


def test_wait_allows_cdp_tab_navigation_without_jev(tmp_path, monkeypatch):
    loading = wait_page([], url='about:blank')
    final = wait_page([user_turn(), assistant_turn('passive CDP answer')])
    observer = FakeWaitAgent(FakeWaitBrowser([loading, final, final, final, final]))
    cfg, args, state, _operation = install_wait(tmp_path, monkeypatch, [observer])
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'COMPLETE'
    assert observer.commands == []
    assert state['starts'] == 0


def test_authorised_browser_interaction_is_the_only_jev_handoff(tmp_path, monkeypatch):
    approval = wait_page([user_turn()], approval=['Always allow'])
    approval['approval_text'] = 'Allow GitHub for this conversation'
    first = FakeWaitAgent(FakeWaitBrowser([approval]))
    last = FakeWaitAgent(FakeWaitBrowser(stable_answer_pages('answer after consent')))
    cfg, args, _state, _operation = install_wait(tmp_path, monkeypatch, [first, last])
    cfg.update(approval_policy='always_allow', approval_connectors=['GitHub'])
    interactions = []
    monkeypatch.setattr(driver, 'interact_with_connector', lambda url, op, settings: interactions.append(url) or True)
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'COMPLETE'
    assert interactions == [CONVERSATION]
    assert first.browser.closed and last.browser.closed
