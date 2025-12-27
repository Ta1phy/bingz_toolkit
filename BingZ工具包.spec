# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['ai_tool_manager.py'],
    pathex=[],
    binaries=[],
    datas=[('ai_tools.json', '.'), ('icon', 'icon')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BingZ工具包',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon/Bingz.png'],
)
app = BUNDLE(
    exe,
    name='BingZ工具包.app',
    icon='icon/Bingz.png',
    bundle_identifier=None,
)
