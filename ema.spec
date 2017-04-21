# -*- mode: python -*-

from kivy.deps import sdl2, glew

block_cipher = None


a = Analysis(['ema.py'],
             pathex=['D:\\share\\Ema'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='ema',
          debug=False,
          strip=True,
          upx=True,
          console=False,
          icon='data\\images\\icon48.ico')

coll = COLLECT(exe,
               Tree('data\\', prefix="data", excludes="files.md5"),
               Tree('kv\\', prefix="kv"),
               Tree('libs\\', prefix="libs", excludes="*.pyc"),
               Tree('modules\\', prefix="modules", excludes="*.pyc"),
               Tree('settings\\', prefix="settings"),
               a.binaries,
               a.zipfiles,
               a.datas,
               *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
               strip=False,
               upx=True,
               name='ema')
