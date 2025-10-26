from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess, sys, time, os

class ReloadHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("chat_azram_cpu.py"):
            print("♻️  Detected change, restarting...")
            os.execv(sys.executable, [sys.executable] + sys.argv)

observer = Observer()
observer.schedule(ReloadHandler(), path=".", recursive=False)
observer.start()
print("👁️  Watching for code changes...")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
