"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os
import shutil
from pathlib import Path

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()
app = application

# Initialize database in writable temp directory for Vercel serverless environment
if os.environ.get('VERCEL'):
    try:
        import tempfile
        from django.core.management import call_command
        target_db = Path(tempfile.gettempdir()) / 'db.sqlite3'
        source_db = Path(__file__).resolve().parent.parent / 'db.sqlite3'

        if not target_db.exists():
            if source_db.exists():
                shutil.copyfile(source_db, target_db)
                try:
                    os.chmod(target_db, 0o666)
                except Exception:
                    pass
            else:
                call_command('migrate', interactive=False)
    except Exception as e:
        print(f"Database initialization error on Vercel: {e}")
