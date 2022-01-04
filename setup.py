from setuptools import setup

setup(
    name="rdf_fixer",
    version="2.3",
    description="Chemical rdf fixer for Reaxys and SciFinder exports",
    url="https://github.com/DocMinus/chem-rdf-fixer",
    author="Alexander Minidis, DocMinus",
    author_email="alex@pharmakarma.org",
    license="MIT",
    packages=["rdfmodule"],
    install_requires=[
        #'rdkit', #not available through git but conda
        "pandas"
    ],
)
