from os.path import join, dirname, exists
import os
import kivy


def thorvg_load_egl(platform: str):
    # iOS: framework paths are tried directly in the patched tvgGl.cpp
    # (TARGET_OS_IPHONE → @executable_path/Frameworks/libGLESv2.framework/libGLESv2)
    # macOS: kivy ships .dylibs alongside kivy/__init__.py; set env vars so the
    #        tvgGl.cpp fallback can find them.
    if platform == "darwin":
        _dylibs = join(dirname(kivy.__file__), ".dylibs")
        _gles = join(_dylibs, "libGLESv2.dylib")
        _egl  = join(_dylibs, "libEGL.dylib")
        if exists(_gles):
            os.environ.setdefault("THORVG_LIBGLESV2", _gles)
        if exists(_egl):
            os.environ.setdefault("THORVG_LIBEGL", _egl)
