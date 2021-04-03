# -*- coding: utf-8 -*-
"""
Created on Tues Feb 23 21:00:00 2021
RDF converter & fixer
Version 1.04 (Apr 03 11:42:00 2021)

@author: Alexander Minidis (DocMinus)
"""

import warnings

warnings.filterwarnings("ignore")
import os
import sys
from rdfmodule import rdf_fixer


def main():
    """Loads & converts the file(s).
    RDF in, then CSV out.
    The corrected (fixed) RDF file is written at the same time with with the ending:
    _fixed.rdf (by the rdf_fixer function)
    This demo script is light-weight, only some simple error checking.
    Only argument giving is the filename including path, e.g.
    convert_example_no_helper.py /home/user/my_rdf_file.rdf
    or
    convert_example_no_helper.py /home/user/subdir/
    (parses all rdfs in all of subdir and recursively)
    """

    try:
        sys.argv[1]
    except IndexError:
        print("You need to specify an input file or directory\n")
        sys.exit(1)

    RDF_IN = sys.argv[1]
    if os.path.isfile(RDF_IN):
        print("Converting.")
        RDF_OK = os.path.splitext(RDF_IN)[0] + "_fixed.rdf"
        print(RDF_OK)
        RDF_CSV = os.path.splitext(RDF_IN)[0] + ".csv"
        rdf_fixer.convert(RDF_IN, RDF_OK, RDF_CSV)

    elif os.path.isdir(RDF_IN):
        zipped = rdf_fixer.subdir_walk(RDF_IN)
        for x, y, z in zipped:
            print("Converting file: ", x)
            rdf_fixer.convert(x, y, z)
    else:
        print("Input error!")

    print("And done.")

    return None


if __name__ == "__main__":
    main()
