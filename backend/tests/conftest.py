import sys
import os

# Ensure backend directory is in sys.path
test_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(test_dir, ".."))
root_dir = os.path.abspath(os.path.join(backend_dir, ".."))

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if root_dir not in sys.path:
    sys.path.insert(1, root_dir)
