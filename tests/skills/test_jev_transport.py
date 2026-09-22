"""Offline checks of the Jev Pro transport driver: no browser, no network, no model call."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('jev_send', ROOT/'tools/pro_transport/jev_send.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)

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
    turn = {'role': 'user', 'text': text + suffix, 'turn_text': text + suffix}
    if message_body is MISSING:
        message_body = text
    if message_body is not None:
        turn['message_body'] = message_body
    return turn


def assistant_turn(text):
    return {'role': 'assistant', 'text': text, 'turn_text': text}


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


def test_wait_rejects_missing_attachment_after_exact_body_match(tmp_path, monkeypatch):
    page = wait_page([user_turn()])
    agent = FakeWaitAgent(FakeWaitBrowser([page]))
    cfg, args, _state, operation = install_wait(
        tmp_path, monkeypatch, [agent], attachment='question.md'
    )
    result = driver.command_wait(args, cfg)
    assert result['state'] == 'ERROR'
    assert result['reason'] == "the operation's attachment is absent from its user turn"
    assert operation.data['send_attempted'] is True


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
