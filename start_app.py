import subprocess
import time
import sys
import os

def start_backend():
    print("Starting backend server on http://localhost:8000...")
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=os.getcwd()
    )

def start_frontend():
    print("Starting frontend server on http://localhost:3000...")
    return subprocess.Popen(
        [sys.executable, "-m", "http.server", "3000"],
        cwd=os.path.join(os.getcwd(), "frontend")
    )

if __name__ == "__main__":
    backend_proc = start_backend()
    frontend_proc = start_frontend()
    
    try:
        print("\nApplication is running!")
        print("Backend: http://localhost:8000")
        print("Frontend: http://localhost:3000")
        print("\nPress Ctrl+C to stop all servers.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Done.")
