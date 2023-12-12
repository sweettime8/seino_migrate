# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:/1.Learn/7.python/0.0.Project_fsoft/1.Seino/seinomigrate.py'],
    pathex=[],
    binaries=[],
    datas=[('D:/1.Learn/7.python/0.0.Project_fsoft/1.Seino/static', 'static/'), ('D:/1.Learn/7.python/0.0.Project_fsoft/1.Seino/templates', 'templates/')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='seinomigrate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['D:\\1.Learn\\7.python\\0.0.Project_fsoft\\1.Seino\\icon.ico'],
)
