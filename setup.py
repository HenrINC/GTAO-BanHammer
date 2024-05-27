import os
import shutil
from pathlib import Path
from setuptools import setup, find_packages
from setuptools.command.install import install


setup(
    name="gta_banhammer",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        # Add your project dependencies here
    ],
    # Metadata for PyPi
    author="H0TF1X",
    author_email="H0TF1X_101@proton.me",
    description="A set of scripts to bring admin tools to GTA",
    license="Not defined yet",
    keywords="GTA GTAV GTA5 game gaming stand modding mod mod-menu admin tools",
    url="Not defined yet",
)

lua_files = Path("./lua").glob("*.lua")
shutil.copy(
    "config_template.json",
    os.path.expanduser("~\\AppData\\Roaming\\Stand\\config_template.json"),
)
for file in lua_files:
    shutil.copy(file, os.path.expanduser("~\\AppData\\Roaming\\Stand\\Lua Scripts\\"))
