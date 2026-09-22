"""CDP observation protocol uses only its own target and no interaction/model API."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import types

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('cdp_observer', ROOT/'tools/pro_transport/cdp_observer.py')
cdp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cdp)


class Connection:
    def __init__(self, fail_attach=False):
        self.calls = []
        self.closed = False
        self.fail_attach = fail_attach

    def send(self, message):
        self.calls.append(json.loads(message))

    def recv(self, timeout):
        assert 0 < timeout <= 10
        request = self.calls[-1]
        if request['method'] == 'Target.attachToTarget' and self.fail_attach:
            return json.dumps({'id': request['id'], 'error': {'code': -1}})
        results = {'Target.createTarget': {'targetId': 'owned-tab'},
                   'Target.attachToTarget': {'sessionId': 'owned-session'},
                   'Runtime.evaluate': {'result': {'value': 2}},
                   'Target.closeTarget': {'success': True}}
        return json.dumps({'id': request['id'], 'result': results[request['method']]})

    def close(self):
        self.closed = True


def install(monkeypatch, connection):
    client = types.ModuleType('websockets.sync.client')
    client.connect = lambda *args, **kwargs: connection
    monkeypatch.setitem(sys.modules, 'websockets', types.ModuleType('websockets'))
    monkeypatch.setitem(sys.modules, 'websockets.sync', types.ModuleType('websockets.sync'))
    monkeypatch.setitem(sys.modules, 'websockets.sync.client', client)
    monkeypatch.setattr(cdp.urllib.request, 'urlopen',
                        lambda *a, **k: io.StringIO('{"webSocketDebuggerUrl":"ws://local"}'))


def test_open_evaluate_close_only_owned_target(monkeypatch):
    connection = Connection()
    install(monkeypatch, connection)
    observer = cdp.ConversationObserver('about:blank', 'http://local')
    assert observer.evaluate('1+1') == 2
    observer.close()
    assert [c['method'] for c in connection.calls] == [
        'Target.createTarget', 'Target.attachToTarget', 'Runtime.evaluate', 'Target.closeTarget']
    assert connection.calls[2]['sessionId'] == 'owned-session'
    assert connection.calls[-1]['params'] == {'targetId': 'owned-tab'}
    assert connection.closed


def test_attach_error_still_closes_only_new_tab(monkeypatch):
    connection = Connection(fail_attach=True)
    install(monkeypatch, connection)
    with pytest.raises(RuntimeError, match='CDP operation failed'):
        cdp.ConversationObserver('about:blank', 'http://local')
    assert connection.calls[-1]['method'] == 'Target.closeTarget'
    assert connection.calls[-1]['params'] == {'targetId': 'owned-tab'}
    assert connection.closed
