from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in holistic/__init__.py
from holistic import __version__ as version

setup(
	name="holistic",
	version=version,
	description="Customization for patient booking",
	author="GreyCube Technologies",
	author_email="admin@greycube.in",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
