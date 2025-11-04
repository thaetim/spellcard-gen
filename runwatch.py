import time, subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_PATHS = [
    'generate.py',
    'templates/',
    'data/Spells.csv'
]

class WatchHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.last_run = 0
        self.debounce_seconds = 1
    
    def on_any_event(self, event):
        if not event.is_directory:
            now = time.time()
            if now - self.last_run < self.debounce_seconds:
                return
            self.last_run = now
            print(f"\n[change detected] {event.src_path}")
            subprocess.run(['python', 'generate.py'])

if __name__ == "__main__":
    event_handler = WatchHandler()
    observer = Observer()
    for path in WATCH_PATHS:
        observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print("Watching for changes... (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
