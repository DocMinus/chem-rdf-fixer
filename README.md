[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
# Chemistry RDF fixer / converter
Converts chemistry containing RDF files stemming from Scifinder or Reaxys.<br>
It fixes missing molecule blocks by removing corresponding entries entirely.<br>
The resulting fixed RDF file is saved, as well as being converted to a tab separated CSV file.<br>
Structures in CSV are in SMILES format.<br>
Other sources e.g. MarvinSketch or ChemDraw should work but have not yet been tested #TODO<br>

## Why would you need this?
Because RDF files that contain a missing structure might throw errors in certain programs or even make them crash.<br>
Examples are MarvinSketch or MarvinView. They sometimes are able to handle missing reaction structures, sometimes not.<br>
In Knime, the Erlwood extenstion "Chemical Reaction File Reader" won't work at all.

### Requirements:
#### Python 
V3.6, V3.7, V3.8 (not tested with lower versions, should work though)<br>
Windows or Linux. MacOS not tested. Preferably an (Ana)Conda installation.
#### RDKIT 
You will have to install this first, before installing the package, since not available via setup.<br>
`conda install -c conda-forge rdkit`<br>
(yields the latest one compatible with your current Python version)

### Installation
If you downloaded/cloned the code:<br>
`python setup.py install`<br>
or directly from the repository<br>
`python -m pip install git+https://github.com/DocMinus/chem-rdf-fixer.git`

#### Optional: Jupyter notebook
This is only if you want to run the .ipynb file from your browser:
`conda install -c anaconda jupyter`

### Importing the module:<br>
e.g.:
`from rdfmodule import rdf_fixer`

### Usage:
`rdf_fixer.fix("input RDF filename or path containing rdf files")`<br>
or<br>
`new_files_as_zip = rdf_fixer.fix(....)`<br>

### Implement e.g. via the enclosed example script or Jupyter Notebook:<br>
`convert_example.py "./filename.rdf"` for single file usage (with or without quotes)<br>
`convert_example.py /directory/` for RDF files in directory including all subdirectories <br>
<br>
**New V1.05:** added a Jupyter notebook:<br>
in your shell or cmd line type:
`jupyter notebook convert_example.ipynb`<br>
Follow instructions within.<br>
**New V2.00:** rewritten and simplified the module. Added setup to do pip install from git repo.<br>
**New V2.01:** function returns a zipped list containing all file names
**New V2.2:** small changes and slight version number format change
**New V2.3:** added minimum mol sanitizations else errors in structures would make it crash

### Testing
The _testfiles_ folder contains two RDF files for a quick test with the Scifinder one containing an erroneous (i.e. missing) structre. 
Please note that  copyright for the enclosed test data lies with the respective companies (see also License section).<br>

### Notes:
The parsing is by no means perfect, though a best effort was made. Suggestions for changes are welcome, please submit an issue or do your own fork.<br> 
Converting the current function(s) into a class has also been abandoned, there is no point really, since it doesn't have to be persistent the way it is applied here.<br>

### License
Independent of the code or whatever license, the test files provided are not to be included for further distribution other than ones initial testing.<br>
The copyright for the data for these two files lies with the providers (ACS, resp. Elsevier Life Sciences IP Limited) and not with the author or anyone reusing/changing this code.<br>
For the code section: Copyright (c) 2021 DocMinus, MIT License (see also LICENSE file).

