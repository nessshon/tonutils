import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tonutils",
    version="0.0.1",
    author="nessshon",
    description="Tonutils is a high-level OOP library for Python designed for interacting with the TON. It is built on top of three of the most popular libraries for working with TON in Python: pytoniq, pytonapi, and pytoncenter.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nessshon/tonutils/",
    packages=setuptools.find_packages(exclude=["examples"]),
    install_requires=[
        "pytoniq~=0.1.39",
        "pytoncenter~=0.0.14",
        "pytonapi~=0.3.2",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
