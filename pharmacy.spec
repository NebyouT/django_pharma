# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

hidden_imports = collect_submodules('django') + [
    'django.template.defaulttags',
    'django.template.defaultfilters',
    'django.template.loader_tags',
    'django.contrib.admin.templatetags.admin_list',
    'django.contrib.staticfiles',
    'django.contrib.auth.models',
    'django.contrib.contenttypes.models',
    'django.contrib.sessions.models',
    'django.contrib.messages.models',
    'crispy_forms',
    'pharmacy',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
]

# Collect Django template files
template_files = [
    ('pharmacy/templates', 'pharmacy/templates'),
    ('pharmacy_management/static', 'pharmacy_management/static'),
]

# Collect Django migration files
migration_files = [
    ('pharmacy/migrations', 'pharmacy/migrations'),
]

# Collect Django admin static files
admin_files = collect_data_files('django.contrib.admin')

datas = template_files + migration_files + admin_files

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PharmacyManagement',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
