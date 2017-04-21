rem c:\python27\Scripts\pip.exe uninstall kivy
rem c:\python27\Scripts\pip.exe uninstall kivy.deps.gstreamer
rem c:\python27\Scripts\pip.exe uninstall kivy.deps.glew
rem c:\python27\Scripts\pip.exe uninstall kivy.deps.sdl2
c:\python27\Scripts\pip.exe install --upgrade pip wheel setuptools
c:\python27\Scripts\pip.exe install docutils pygments pypiwin32 kivy.deps.sdl2 kivy.deps.glew
c:\python27\Scripts\pip.exe install kivy.deps.gstreamer-0.1.7-cp27-cp27m-win32.whl
c:\python27\Scripts\pip.exe install kivy
c:\python27\Scripts\pip.exe install ovh
c:\python27\Scripts\pip.exe install linphone
c:\python27\Scripts\pip.exe install PyInstaller
pause