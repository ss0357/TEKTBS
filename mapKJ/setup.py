from distutils.core import setup
import py2exe


setup(console = ['mapJK.py'],
        zipfile = None,
    options = {"py2exe":{"compressed": 1, "optimize": 2, "bundle_files": 1}})