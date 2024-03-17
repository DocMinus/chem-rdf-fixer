from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="rdf_fixer",
    version="3.0.7",
    description="Chemical rdf file fixer for exports from Reaxys, SciFinder, Deepmatter, etc.",
    long_description=open("README.md").read(),
    url="https://github.com/DocMinus/chem-rdf-fixer",
    author="Alexander Minidis, DocMinus",
    author_email="alexander.minidis@gmail.com",
    license="MIT",
    packages=["rdfmodule"],
    install_requires=[
        "rdkit",
        "pandas",
        "numpy",
    ],
)
