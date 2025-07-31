#!/root/kampeonato/venv/bin/python3
import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, '/root/kampeonato')

# Configurar a variável de ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampeonato.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
