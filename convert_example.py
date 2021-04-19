# -*- coding: utf-8 -*-
"""
Created on Tues Feb 23 21:00:00 2021
RDF converter & fixer
Version 2.00 (Apr 19 21:26:00 2021)

@author: Alexander Minidis (DocMinus)

license: MIT License
Copyright (c) 2021 DocMinus
"""

import warnings

warnings.filterwarnings("ignore")
import sys
from rdfmodule import rdf_fixer


def main():
    """Here the files are loaded & converted.
    RDF file or path to files as as input.
    The corrected file as ends up as fixed.RDF output.
    As well as tabular CSV output file.
    The original file remains untouched

    This demo script is after V2 even more light-weight.
    Usage:
    convert_example.py /home/user/my_rdf_file.rdf
    or
    convert_example.py /home/user/subdir/
    """

    try:
        sys.argv[1]
    except IndexError:
        print("You need to specify an input file or directory!")
        sys.exit(1)
    # argparse would be an alternative. check the jupyter book for an example

    print("Initiating conversion...")
    rdf_fixer.fix(sys.argv[1])
    print("And done.")

    return None


if __name__ == "__main__":
    main()
