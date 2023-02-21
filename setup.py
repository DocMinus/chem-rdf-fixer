from setuptools import setup

setup(
    name="rdf_fixer",
    version="3.0.3",
    description="Chemical rdf fixer for Reaxys and SciFinder exports",
    url="https://github.com/DocMinus/chem-rdf-fixer",
    author="Alexander Minidis, DocMinus",
    author_email="alexander.minidis@gmail.com",
    license="MIT",
    packages=["rdfmodule"],
    install_requires=[
        'rdkit',
        'pandas',
        'numpy',
    ],
)
