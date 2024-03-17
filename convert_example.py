# -*- coding: utf-8 -*-
"""
Created on Tues Feb 23 21:00:00 2021
RDF converter & fixer
Version 2.2.3 (Dec 08 12:56:00 2022)
Updated Dec 30, 2022

@author: Alexander Minidis (DocMinus)

license: MIT License
Copyright (c) 2021-2024 DocMinus
"""

import warnings

warnings.filterwarnings("ignore")
import sys

from rdfmodule import rdf_fixer


def main():
    """Here the files are loaded & converted.
    Single RDF file or whole path to files as input.
    The corrected file ends up as "_fixed.RDF" file,
    as well as a tabular CSV output file.
    The original file remains untouched.

    Usage:
    convert_example.py /home/user/my_rdf_file.rdf True/False
    or
    convert_example.py /home/user/subdir/
    the flag True/False is optional;
    default is True and will do both, fix and convert
    False will only fix the file(s), not create csv file.
    """

    try:
        sys.argv[1]
    except IndexError:
        print("You need to specify an input file or directory!")
        sys.exit(1)
    # argparse would be an alternative. check the jupyter book for an example

    print("Initiating conversion...")
    rdf_fixer.fix(sys.argv[1])
    # or below example without csv creation
    rdf_fixer.fix(sys.argv[1], False)
    print("And done.")

    return None


if __name__ == "__main__":
    main()
