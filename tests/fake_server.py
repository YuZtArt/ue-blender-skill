"""Local protocol fixture. Never connects to an editor."""
import base64
import json
import sys
import time


for line in sys.stdin:
    request = json.loads(line)
    if 'id' not in request:
        continue
    method = request['method']
    if method == 'initialize':
        result = {'protocolVersion': '2025-03-26', 'capabilities': {'tools': {}},
                  'serverInfo': {'name': 'fixture', 'version': '1'}}
    elif method == 'tools/list':
        result = {'tools': [{'name': name, 'inputSchema': {'type': 'object',
                   'properties': {'user_prompt': {'type': 'string'}}}}
                  for name in ['get_scene_info', 'monolith_status', 'echo', 'fail', 'slow', 'drop', 'image']]}
    else:
        name = request['params']['name']
        if name == 'slow':
            time.sleep(2)
        if name == 'drop':
            sys.exit(1)
        result = {'content': [{'type': 'text', 'text': json.dumps(request['params']['arguments'])}]}
        if name == 'fail':
            result['isError'] = True
        if name == 'image':
            result = {'content': [{'type': 'image', 'mimeType': 'image/png',
                      'data': base64.b64encode(b'fixture-image-bytes').decode()}]}
    print(json.dumps({'jsonrpc': '2.0', 'id': request['id'], 'result': result}), flush=True)
