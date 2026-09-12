import re

with open('core/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

import_thread = 'import threading\nfrom pathlib import Path'
code = code.replace('from pathlib import Path', import_thread)

thread_func = '''
def _cleanup_loop(settings: Settings):
    while True:
        time.sleep(3600)  # Sleep for 1 hour
        try:
            purge_stale(settings.upload_dir, settings.retention_hours)
            purge_stale(settings.results_dir, settings.retention_hours)
        except Exception as e:
            log.error(f"Cleanup thread error: {e}")
'''

code = code.replace('def create_app(', thread_func + '\ndef create_app(')

start_thread = '''
    if settings.retention_hours:
        purge_stale(settings.upload_dir, settings.retention_hours)
        purge_stale(settings.results_dir, settings.retention_hours)
        # Start background cleanup thread
        t = threading.Thread(target=_cleanup_loop, args=(settings,), daemon=True)
        t.start()
'''

# Use regex to replace the block
code = re.sub(r'    if settings\.retention_hours:.*?purge_stale\(settings\.results_dir, settings\.retention_hours\)', start_thread.strip('\n'), code, flags=re.DOTALL)

with open('core/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Cleanup loop added!')
