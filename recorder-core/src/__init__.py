import os
import sys
from pathlib import Path
from .initializer import check_node

current_file_path = Path(__file__).resolve()
current_dir = current_file_path.parent
JS_SCRIPT_PATH = current_dir / 'javascript'

execute_dir = os.environ.get('LIVE_RECORDER_DATA_ROOT', os.path.split(os.path.realpath(sys.argv[0]))[0])
node_execute_dir = Path(execute_dir) / 'node'
current_env_path = os.environ.get('PATH')
os.environ['PATH'] = str(node_execute_dir) + os.pathsep + current_env_path
if not getattr(sys, "frozen", False):
    # A packaged GUI must never run an installer or subprocess probe during
    # import. JavaScript-based platforms can report a missing Node.js on use.
    check_node()
