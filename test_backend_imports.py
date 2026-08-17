#!/usr/bin/env python
import sys
sys.path.insert(0, '.')

try:
    from backend.app.main import app
    print('SUCCESS: Backend imports successful')
    print('FastAPI app:', app.title)
except Exception as e:
    print('ERROR: Import failed')
    print(str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
