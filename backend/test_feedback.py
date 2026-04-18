import urllib.request
import json
import traceback

try:
    req = urllib.request.Request(
        'http://localhost:8000/feedback', 
        data=json.dumps({'patient_id': 'PAT-B-2024-0892', 'instruction': 'Patient B has naturally low BP, reconsider risk level...'}).encode('utf-8'), 
        headers={'Content-Type': 'application/json'}
    )
    res = urllib.request.urlopen(req)
    with open('test_feedback.json', 'w', encoding='utf-8') as f:
        f.write(res.read().decode('utf-8'))
    print("Success")
except Exception as e:
    with open('test_feedback.err', 'w') as f:
        f.write(traceback.format_exc())
    print(f"Failed: {e}")
