import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tonutils",
    version="0.4.8",
    author="nessshon",
    description=(
        "Tonutils is a high-level, object-oriented Python library "
        "designed to facilitate seamless interactions with the TON blockchain."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nessshon/tonutils",
    project_urls={
        "Documentation": "https://nessshon.github.io/tonutils",
        "Examples": "https://github.com/nessshon/tonutils/tree/main/examples",
        "Source": "https://github.com/nessshon/tonutils",
        "TON": "https://ton.org",
    },
    packages=setuptools.find_packages(include=["tonutils", "tonutils.*"]),
    package_data={"tonutils": ["py.typed"]},
    python_requires=">=3.10",
    install_requires=[
        "aiohttp>=3.7.0,<=3.12.2",
        "aiolimiter~=1.2.1",
        "cachetools~=5.5.0",
        "pycryptodomex~=3.20.0",
        "PyNaCl~=1.5.0",
        "pytoniq-core~=0.1.41",
    ],
    extras_require={
        "pytoniq": ["pytoniq~=0.1.40"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: AsyncIO",
        "Environment :: Console",
    ],
    keywords="TON, The Open Network, TON blockchain, blockchain, crypto, asynchronous, smart contracts",
    license="MIT",
)
