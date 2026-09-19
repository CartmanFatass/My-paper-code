"""Offline checks of the Jev Pro transport driver: no browser, no network, no model call."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

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


def test_compose_names_the_document_by_file_and_hash(tmp_path):
    message = tmp_path/'full.txt'
    message.write_text('line one\n\nline two\n', encoding='utf-8')
    args = argparse.Namespace(message_file=str(message), slug='example-question', subject='d', out_dir=str(tmp_path))
    made = driver.command_compose(args, {})
    document = Path(made['document'])
    assert document.read_text(encoding='utf-8') == 'line one\n\nline two\n'
    short = Path(made['short_message']).read_text(encoding='utf-8')
    assert document.name in short and made['document_sha256'] in short
    with pytest.raises(driver.PreSendFailure):
        driver.command_compose(argparse.Namespace(**{**vars(args), 'slug': 'Bad Slug'}), {})


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
