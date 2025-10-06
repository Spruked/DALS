import subprocess
import time
import requests

# Start server
server = subprocess.Popen([
    'python', '-c',
    'import uvicorn; from iss_module.api.api import app; uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")'
])

# Wait for server to start
time.sleep(3)

try:
    # Test health endpoint
    response = requests.get('http://127.0.0.1:8000/api/health')
    print('Status Code:', response.status_code)
    print('Response:', response.json())
except Exception as e:
    print('Error:', e)
finally:
    server.terminate()
    server.wait()