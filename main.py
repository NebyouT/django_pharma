import os
import sys
import django
from django.core.management import execute_from_command_line
from django.core.wsgi import get_wsgi_application
from django.conf import settings
import webview

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharmacy_management.settings')
    django.setup()
    
    # Disable autoreloader and run the server
    if len(sys.argv) == 1:
        sys.argv.extend(['runserver', '8000', '--noreload'])
    
    try:
        # Start the Django server
        execute_from_command_line(sys.argv)

        # Open the application in a PyWebview window
        webview.create_window('Pharmacy Management', 'http://127.0.0.1:8000')
        webview.start()
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")

if __name__ == '__main__':
    main()
