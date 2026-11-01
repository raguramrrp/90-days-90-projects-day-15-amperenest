import os
import sys
import time
import subprocess
import urllib.request

PORT = 8015
URL_BASE = f"http://127.0.0.1:{PORT}"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(EDGE_PATH):
    EDGE_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

print(f"Using Browser: {EDGE_PATH}")

# Start Django server
env = os.environ.copy()
env['DEBUG'] = 'True'
python_exe = sys.executable

server_proc = subprocess.Popen(
    [python_exe, "manage.py", "runserver", f"127.0.0.1:{PORT}"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=env
)

time.sleep(3)

# Verify server is up
try:
    with urllib.request.urlopen(f"{URL_BASE}/accounts/login/") as resp:
        print(f"Server is up! Status: {resp.status}")
except Exception as e:
    print(f"Error reaching server: {e}")
    server_proc.terminate()
    sys.exit(1)

os.makedirs("screenshots", exist_ok=True)
user_data_dir = os.path.abspath("screenshots/browser_profile")
os.makedirs(user_data_dir, exist_ok=True)

targets = [
    ("dashboard.png", f"{URL_BASE}/accounts/login/?demo_auth=1&next=/"),
    ("readings.png", f"{URL_BASE}/consumption/readings/"),
    ("bill_calculator.png", f"{URL_BASE}/billing/calculator/"),
    ("appliances.png", f"{URL_BASE}/appliances/"),
    ("savings_planner.png", f"{URL_BASE}/analytics/savings-planner/"),
    ("budgets_goals.png", f"{URL_BASE}/budgets/"),
    ("alerts.png", f"{URL_BASE}/alerts/"),
]

for filename, url in targets:
    out_path = os.path.abspath(os.path.join("screenshots", filename))
    print(f"Capturing {filename} from {url}...")
    cmd = [
        EDGE_PATH,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        f"--user-data-dir={user_data_dir}",
        "--window-size=1280,850",
        f"--screenshot={out_path}",
        url
    ]
    subprocess.run(cmd, timeout=15)
    if os.path.exists(out_path):
        print(f"  Captured successfully: {out_path} ({os.path.getsize(out_path)} bytes)")
    else:
        print(f"  Failed to capture {filename}")

server_proc.terminate()
print("Done capturing screenshots!")
