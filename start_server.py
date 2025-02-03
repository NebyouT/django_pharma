import os
import subprocess

# Activate virtual environment if it exists
venv_path = os.path.join(os.getcwd(), '.venv', 'Scripts', 'activate')
if os.path.exists(venv_path):
    activate_command = f'{venv_path} && '
else:
    activate_command = ''

# Install dependencies from requirements.txt
requirements_path = os.path.join(os.getcwd(), 'requirements.txt')
if os.path.exists(requirements_path):
    subprocess.run(f'{activate_command}pip install -r {requirements_path}', shell=True)

# Run the Django server
subprocess.run(f'{activate_command}python manage.py runserver', shell=True)
