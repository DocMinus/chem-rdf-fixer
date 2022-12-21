#!/usr/bin/env python
# coding: utf-8
"""
Pre-fix for Spresi RDF files.
"""
# diverse imports
import os
from os.path import expanduser
import warnings

warnings.filterwarnings("ignore")

def main():
    # Initialize file 
    data_path = os.path.join(expanduser("~"), "dev/data/new_rdfs/")
    file_in = "rdfile.rdf"
    file_base = os.path.splitext(file_in)[0]
    rdf_in = os.path.join(data_path, file_in)
    rdf_out = os.path.join(data_path + file_base + "_spresi.rdf")

    with open(rdf_out, "w") as file_out:
        counter = 0
        counter =+1
        for current_line in open(rdf_in):
            if current_line == ("$RFMT\n"):
                current_line = current_line.replace("$RFMT", ("$RFMT $RIREG SCHEME" + str(counter)))
                counter += 1
            file_out.write(current_line)


if __name__ == "__main__":
    main()
