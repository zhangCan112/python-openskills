import os
import shutil
from setuptools import setup
from setuptools.command.build_py import build_py


class CleanBuildPy(build_py):
    def run(self):
        for d in ['build', 'dist']:
            if os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)
        for root, dirs, _files in os.walk('.'):
            for dirname in dirs:
                if dirname == '__pycache__':
                    shutil.rmtree(os.path.join(root, dirname), ignore_errors=True)
        super().run()


setup(
    cmdclass={
        'build_py': CleanBuildPy,
    },
)
