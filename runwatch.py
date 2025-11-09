import time, subprocess, sys, os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_PATHS = [
    '.',
    'templates/',
    'data/'
]

# Define the specific files you want to watch in the root folder
WATCHED_FILES = [
    'generate.py',
    'card_generator.py',
    'spell_processing.py',
    'spell_styling.py',
    'text_formatting.py',
]

class WatchHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.last_run = 0
        self.debounce_seconds = 4
    
    def should_handle_event(self, event):
        """Check if we should handle this filesystem event"""
        if event.is_directory:
            return False
            
        # Get the absolute path of the changed file
        changed_file = os.path.abspath(event.src_path)
        
        # Check if the file is in the root directory and in our watch list
        file_dir = os.path.dirname(changed_file)
        current_dir = os.path.abspath('.')
        
        # If file is in root directory, check if it's in our watch list
        if file_dir == current_dir:
            filename = os.path.basename(changed_file)
            if filename in WATCHED_FILES:
                return True
        
        # For files in templates/ and data/ directories, handle all of them
        # (maintaining the original behavior for these directories)
        for path in WATCH_PATHS:
            if path != '.':
                watch_path_abs = os.path.abspath(path)
                if changed_file.startswith(watch_path_abs):
                    return True
        
        return False
    
    def on_any_event(self, event):
        if not self.should_handle_event(event):
            return
            
        now = time.time()
        if now - self.last_run < self.debounce_seconds:
            return
        self.last_run = now
        print(f"\n[change detected] {event.src_path}")
        subprocess.run([sys.executable, 'generate.py', '-d'])
        print()

if __name__ == "__main__":
    event_handler = WatchHandler()
    observer = Observer()
    
    # Add path validation to avoid FileNotFoundError
    valid_paths = []
    for path in WATCH_PATHS:
        if os.path.exists(path):
            valid_paths.append(path)
            observer.schedule(event_handler, path, recursive=True)
        else:
            print(f"Warning: Path '{path}' does not exist and will not be watched")
    
    if not valid_paths:
        print("Error: No valid paths to watch!")
        sys.exit(1)
        
    observer.start()
    print("Watching for changes... (Ctrl+C to stop)")
    print(f"Watching specific files in root: {WATCHED_FILES}")
    print(f"Watching all files in: {[p for p in valid_paths if p != '.']}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()