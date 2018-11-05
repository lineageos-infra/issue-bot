import setuptools

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
with open("requirements.txt", "r") as fh:
    requirements = fh.read().split()
setuptools.setup(
    name="bot",
    version="0.0.1",
    description="LineageOS Issues Bot",
    url="https://gitlab.com/lineageos/issues/bot.git",
    author_email="infra@lineageos.org",
    author="LineageOS Infrastructure Team",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"bot": "bot"},
    packages=setuptools.find_packages(),
    classifiers=("Programming Language :: Python 3"),
    install_requires=requirements,
)


