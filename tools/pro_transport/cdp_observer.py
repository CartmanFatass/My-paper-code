"""Read a conversation through CDP, without Jev, an API key or model decisions.

Uses the existing browser interpreter's websockets package. Owns only its new tab.
No input, click, approval or generation controls are exposed.
"""
from __future__ import annotations

import json
import time
import urllib.request


class ConversationObserver:
    def __init__(self, url, cdp_url):
        from websockets.sync.client import connect

        self.browser = self  # the driver's page-fact reader only needs evaluate()
        self.target = None
        self.session = None
        self.sequence = 0
        with urllib.request.urlopen(cdp_url + '/json/version', timeout=3) as response:
            endpoint = json.load(response)['webSocketDebuggerUrl']
        self.connection = connect(endpoint, open_timeout=5, close_timeout=1, max_size=16 * 1024 * 1024)
        try:
            self.target = self.call('Target.createTarget', {'url': url})['targetId']
            self.session = self.call('Target.attachToTarget', {'targetId': self.target, 'flatten': True})['sessionId']
        except BaseException:
            self.close()
            raise

    def call(self, method, params, *, page=False):
        self.sequence += 1
        message = {'id': self.sequence, 'method': method, 'params': params}
        if page:
            message['sessionId'] = self.session
        self.connection.send(json.dumps(message))
        deadline = time.monotonic() + 10
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('CDP response deadline exceeded')
            response = json.loads(self.connection.recv(timeout=remaining))
            if response.get('id') == self.sequence:
                if 'error' in response:
                    raise RuntimeError('CDP operation failed: ' + str(response['error'].get('code')))
                return response['result']

    def evaluate(self, expression):
        result = self.call('Runtime.evaluate', {'expression': expression, 'returnByValue': True}, page=True)
        if 'exceptionDetails' in result:
            raise RuntimeError('CDP page observation failed')
        return result['result'].get('value')

    def close(self):
        try:
            if self.target is not None:
                self.call('Target.closeTarget', {'targetId': self.target})
                self.target = None
        finally:
            self.connection.close()
