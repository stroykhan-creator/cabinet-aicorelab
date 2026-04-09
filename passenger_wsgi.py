import os, sys
 
#project directory
sys.path.append('/home/l/layerg/cabinet.aicorelab.ru/public_html/venv/lib/python3.12/site-packages')
sys.path.append('/home/l/layerg/cabinet.aicorelab.ru/public_html')
 
#project settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
 
#start server
 
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
