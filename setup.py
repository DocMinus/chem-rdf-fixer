from pathlib import Path

from setuptools import setup

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="rdf_fixer",
    version="3.0.9",
    description="Chemical rdf file fixer for exports from Reaxys, SciFinder, Deepmatter, etc.",
    long_description=long_description,
    long_description_content_type="text/markdown",
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
