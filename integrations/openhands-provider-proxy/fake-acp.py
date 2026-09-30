#!/usr/local/bin/python
"""Qualification adapter only: verify relay transport, then use synthetic ACP."""
import http.client
import json
import os
from pathlib import Path
import sys

assert os.environ['HTTPS_PROXY']=='http://127.0.0.1:3129'
assert os.environ['HTTP_PROXY']=='http://127.0.0.1:3129'
assert os.environ['ENABLE_CLAUDEAI_MCP_SERVERS']=='false'
assert os.environ['NO_PROXY']==''
connection=http.client.HTTPSConnection('127.0.0.1',3129,timeout=10)
connection.set_tunnel('api.anthropic.com',443)
connection.connect();assert connection.sock.getpeercert();connection.close()
denied=http.client.HTTPSConnection('127.0.0.1',3129,timeout=10)
denied.set_tunnel('example.com',443)
try:denied.connect()
except OSError as error:assert '403' in str(error)
else:raise AssertionError('Foreign host allowed')
finally:denied.close()
Path('/results/provider-fixture.json').write_text(json.dumps({
    'syntheticAcp':True,'proxyEnvironmentVerified':True,'accountConnectorsDisabled':True,
    'providerTlsVerified':True,'foreignHostDenied':True,'modelRequests':0}))
os.execv(sys.executable,[sys.executable,'/extension/budget_peer.py'])
