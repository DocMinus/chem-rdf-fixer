[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![GitHub](https://img.shields.io/github/license/docminus/chem-rdf-fixer)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/docminus/chem-rdf-fixer)
![Python](https://img.shields.io/badge/Python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)

# Chemistry RDF fixer / converter
Converts chemistry containing RDF files stemming from Scifinder or Reaxys. A new addition is the support for Infochem's ICsynth RDFs.<br>
It fixes missing molecule blocks by removing corresponding entries entirely and some potential small errors (remove certain empty lines, or use uppercase for certain tags)<br>
The resulting fixed RDF file is saved, as well as being converted to a tab separated CSV file.<br>
Structures in CSV are in SMILES format.<br>
Other sources e.g. MarvinSketch or ChemDraw should work with these converted files but have not been thoroughly enough tested.<br>

## Why would you need this?
Because RDF files that contain a missing structure might throw errors in certain programs or even make them crash.<br>
Examples are MarvinSketch or MarvinView. They sometimes are able to handle missing reaction structures, sometimes not.<br>
In Knime, the Erlwood extenstion "Chemical Reaction File Reader" won't work at all.

### Requirements:
Python >= V3.8.<br>
Windows or Linux. MacOS not tested. <br>
Type of installation shouldn't matter (Vanilla/Conda/Mamba/venv).


### Installation
#### Simplest: pip install (from Pypi)
```bash
pip install rdf-fixer
```

#### "Manualy"
If you downloaded/cloned the code:
```bash
pip install .
```
Yet another way, directly from the repository:
```bash
python -m pip install git+https://github.com/DocMinus/chem-rdf-fixer.git`
```


#### Optional: Jupyter notebook
This is only if you want to run the .ipynb file from your browser:
```bash
conda install -c anaconda jupyter
```


### Importing the module:<br>
```python
from rdfmodule import rdf_fixer
```


### Usage:
To fix a single RDF file, or a whole folder containing multiple RDF files:
```python
rdf_fixer.fix("file or directory name")
```
There is an optional flag (True/False), with default being True, creating csv files as well. To skip csv creation, set flag to False.
```python
rdf_fixer.fix("file or directory name", flag=False)
```


### Implement e.g. via the enclosed example script or Jupyter Notebook:<br>
`convert_example.py "./filename.rdf"` for single file usage (with or without quotes)<br>
`convert_example.py /directory/` for RDF files in directory including all subdirectories <br>
<br>


### Testing
The _testfiles_ folder contains three RDF files for a quick test; where e.g. the Scifinder one contains an erroneous (i.e. missing) structre. 
Please note that  copyright for the enclosed test data lies with the respective companies (see also License section).<br>


### Notes:
The parsing is by no means perfect, though a best effort was made. Suggestions for changes are welcome, please submit an issue or do your own fork.<br> 
Converting the current function(s) into a class has also been abandoned, there is no point really, since it doesn't have to be persistent the way it is applied here.<br>


### Update history
See the "VERSIONS.md" readme file.



### License
Independent of the code or whatever license, the test files provided are not to be included for further distribution other than ones initial testing.<br>
The copyright for the data for these files lies with the providers (Deepmatter/Infochem, ACS, Elsevier Life Sciences IP Limited) and not with the author or anyone reusing/changing this code.<br>
For the code section: Copyright (c) 2021-2024 DocMinus, MIT License (see also LICENSE file).<br>
If you add a shout-out to your code, I don't mind!

