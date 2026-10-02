# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(SPECPATH)

analysis = Analysis(
    [str(project_root / "Start_Water_Puppy.pyw")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(str(path), "assets") for path in (project_root / "assets").iterdir()
           if path.is_file() and not path.name.startswith("rig_walk_") and path.name != "walk_rig_motion.json"],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="WaterPanda",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    contents_directory=".",
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "assets" / "panda.ico"),
)

bundle = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="WaterPanda",
)
