from setuptools import setup

setup(
    name="eldpy",
    version="0.1",
    description="A Python package to download and analyze data from endangered language archives",
    author="Sebastian Nordhoff",
    author_email="sebastian.nordhoff@glottotopia.de",
    packages=["eldpy"],
    install_requires=[
        "numpy",
        "pandas",
        "pycryptodome",
        "lxml",
        "matplotlib",
        "rdflib",
        "sklearn",
        "tqdm",
        "requests",
        "urllib",
        "wptools",
        "squarify",
        "langdetect",
        "random2",
    ],
)
