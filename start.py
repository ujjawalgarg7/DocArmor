import subprocess
import os
import signal
import time
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))

processes = []

try:
    auth = subprocess.Popen(
        ["bash", "-c",
         f"cd '{ROOT}/auth-service' && source venv/bin/activate && uvicorn app.main:app --reload"]
    )
    processes.append(auth)

    vault = subprocess.Popen(
        ["bash", "-c",
         f"cd '{ROOT}/vault-service' && source venv/bin/activate && uvicorn app.main:app --reload --port 8001"]
    )
    processes.append(vault)

    frontend = subprocess.Popen(
        ["bash", "-c",
         f"cd '{ROOT}/frontend' && python3 -m http.server 5500"]
    )
    processes.append(frontend)

    time.sleep(3)
    webbrowser.open("http://localhost:5500")

    print("DocArmor is running.")
    print("Press Ctrl+C to stop everything.")

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopping DocArmor...")

    for p in processes:
        p.terminate()

    for p in processes:
        p.wait()

    print("All services stopped.")