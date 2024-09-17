import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tonutils",
    version="0.0.8",
    author="nessshon",
    description="Tonutils is a high-level object-oriented library for Python designed to facilitate interactions with the TON blockchain.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nessshon/tonutils/",
    packages=setuptools.find_packages(exclude=["examples"]),
    install_requires=[
        "aiohttp~=3.9.5",
        "pycryptodomex~=3.20.0",
        "PyNaCl~=1.5.0",
        "pytoniq-core~=0.1.36",
    ],
    extras_require={
        "pytoniq": [
            "pytoniq~=0.1.39",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
