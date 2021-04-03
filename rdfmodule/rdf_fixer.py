#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tues Feb 23 21:00:00 2021
Chemical RDF converter & fixer.
Version 1.04b (Apr 03, 12:12:00 2021)

@author: Alexander Minidis (DocMinus)

license: MIT License
Copyright (c) 2021 DocMinus
"""

import warnings

warnings.filterwarnings("ignore")

import os
import re
import pandas as pd
import rdkit.Chem as rdc
from collections import OrderedDict


def subdir_walk(root_dir: str) -> list:
    """Retrieving all .RDF files in a subdirectory recursively. Return as list.
    No error checking is done within this function (such as if file and not path)
    Parts of snippet originated on Reddit somewhere, forgot where though.
    Args:
        root_dir = directory and subdirectories to scan
    Returns:
        zipped list of these three lists:
            file_list_in = list of all rdf files incl. their path
            file_list_ok = list of the (future) corrected rdf files
            file_list_csv = list of final output csv files
    """

    file_list_in = []
    file_list_ok = []
    file_list_csv = []
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(("rdf", "RDF")):
                file_list_in.append(os.path.join(subdir, file))
                file_list_ok.append(
                    os.path.join(subdir, os.path.splitext(file)[0] + "_fixed.rdf")
                )
                file_list_csv.append(
                    os.path.join(subdir, os.path.splitext(file)[0] + ".csv")
                )

    return zip(file_list_in, file_list_ok, file_list_csv)


def convert(RDF_IN_FILE: str, RDF_OK_FILE: str, RDF_CSV_FILE: str):
    """original script with single file usage wrapped into this 'convert' function
    Args:
        RDF_IN_FILE: original input RDF file including path
        RDF_OK_FILE: new RDF file with corrections (if any)
        RDF_CSV_FILE: resulting CSV file (incl. path)
    Returns:
        None - output are the new files.
        :rtype: object
    """

    ##############################################################
    # Fix erroneous entries (empty mols) by deleting those entries

    with open(RDF_IN_FILE) as file_in:
        seed_line = file_in.readline()
    previous_line = seed_line  # get first line as "seed" for upcoming loop
    # seed_line is later reused again
    with open(RDF_OK_FILE, "w") as file_out:
        write_to_file = True
        for current_line in open(RDF_IN_FILE):
            # prevent first line from being written twice
            if current_line.startswith("$RDFILE") and previous_line.startswith(
                "$RDFILE"
            ):
                continue

            # correct molecule block
            # True
            write_to_file = current_line.startswith(
                "$RXN"
            ) and previous_line.startswith("$RFMT")
            # else for empty molecule block
            write_to_file = not (
                current_line.startswith("$DTYPE") and previous_line.startswith("$RFMT")
            )

            if write_to_file:
                file_out.write(previous_line)

            previous_line = current_line

        file_out.write(previous_line)
        # the last line is not caught in the loop, hence written out here.

    # end of fix section
    ####################

    def scifi_or_reax(in_file: str) -> str:
        """Determine if Scifinder or Reaxys rdf file
        (Scifinder contains 'SCHEME' in the enumeration)
        Returned string is multiple string.replace() methods,
        to render script independent of source

        Args:
            in_file (str): filename of the corrected file (in principle,
                           the original one would work as well;
                           alt even global variable possible instead)
        Returns:
            SCI_REAX (str): "RXN:" (scifinder) or string "ROOT:" (reaxys)
        """

        f = open(in_file)
        NUMBER_OF_LINES = 3

        for i in range(NUMBER_OF_LINES):
            line_three = f.readline()

        return "RXN:" if re.match(".+SCHEME", line_three) else "ROOT:"

    def build_empty_table(in_file: str, SCI_REAX: str):
        """Scans file three times to build a pandas df used as main table
        Args:
            in_file (str): filename of the corrected file: RDF_OK_FILE
            SCI_REAX (str): "RXN:" (scifinder) or string "ROOT:" (reaxys) used in replacements
        Returns:
            da_table (object): the (empty) pandas df working table
            max_reagents (int): number for later positioning of reagents smiles in table
            max_products (int): <> (products)
        """

        # get the IDs and use as row index
        list_of_IDs = []  # i.e. rows
        for line in open(in_file):
            if line.startswith("$RFMT"):
                list_of_IDs.append(line.strip().split(" ")[2])

        # determine max no of reagents/products
        flag = 0
        max_reagents = 0
        max_products = 0
        for line in open(in_file):
            if line.startswith("$RXN") | flag == 1:
                flag = 1
                if re.match("\s\s[0-9]\s\s[0-9]\n", line):
                    # analyse the "  y  z" line.
                    # implies: y reactants, z products.
                    x = line.strip().split("  ")
                    number_reagents = int(x[0])
                    number_products = int(x[1])
                    if number_reagents > max_reagents:
                        max_reagents = number_reagents
                    if number_products > max_products:
                        max_products = number_products
                    flag = 0

        # build the column headers
        fields = []
        for i in range(max_reagents):
            tmp_name = "Reagent" + str(i)
            fields.append(tmp_name)

        for i in range(max_products):
            tmp_name = "Product" + str(i)
            fields.append(tmp_name)

        for line in open(in_file):
            if line.startswith("$DTYPE"):
                fields.append((line.strip().split(" ")[1]).replace(SCI_REAX, ""))

        # finally, build the table
        da_table = pd.DataFrame(
            index=list_of_IDs, columns=list(OrderedDict.fromkeys(fields))
        )

        return da_table, max_reagents, max_products

    ##############################################################
    # Initialize Table and diverse variables

    # get string replacement variable depending on source
    SCI_REAX = scifi_or_reax(RDF_OK_FILE)
    # build table according to files specs. get max no of reagents & products at the same time.
    my_table, max_reagents, max_products = build_empty_table(RDF_OK_FILE, SCI_REAX)

    ####################################################################
    # Here comes the actual data extraction and addition to pandas table

    #
    ############### GET MOLECULES #############
    # (structure same for Reaxys and Scifinder)
    #

    flag = 0
    # 0 = generic
    # 1 = start of reaction block
    # 2 = single MOL (molecules)
    # 9 = skip

    molecule = []
    number_reagents = 0
    number_products = 0
    number_molecules = 0
    iterate_molecules = 0
    mol_string = ""
    rxn_id = ""
    multiple_row_text = ""

    # get first line as "seed" for upcoming loop
    previous_line = seed_line

    for line in open(RDF_OK_FILE):
        current_line = line

        # get reaction ID
        if current_line.startswith("$RFMT"):
            rxn_id = str(current_line.strip().split(" ")[2])
            flag = 0
            continue

        # start of a new reaction block
        if current_line.startswith("$RXN") | flag == 1:
            flag = 1
            if re.match("\s\s[0-9]\s\s[0-9]\n", current_line):
                # analyse the "  y  z" line. Not hard-coding this since it might change?
                # implies: y reactants, z product.
                x = current_line.strip().split("  ")
                number_reagents = int(x[0])
                number_products = int(x[1])
                number_molecules = number_reagents + number_products
                # create fresh list of max no of molecules, for use in $MOL block
                # yes, always same size within a *given file*, could change from file to file(!)
                for i in range(number_molecules):
                    molecule.append([])

            if current_line == "\n" or re.match("\s\s[0-9]\s\s[0-9]\n", current_line):
                # checks for empty lines and the number of molecules lines and skips them
                continue

        # after determining a block, find the molecules within the block
        if (current_line == "$MOL\n") | (flag == 2):
            flag = 2

            if current_line != "$MOL\n" and (iterate_molecules < number_molecules):
                molecule[iterate_molecules].append(current_line)

            if current_line == "M  END\n":
                iterate_molecules += 1

            # end of the complete reaction block
            if current_line.startswith("$D") & (previous_line == "M  END\n"):
                flag = 9  # could just use flag = 0(?)
                # rebuild the string of a molecule
                counter_reagents = 0
                counter_products = 0
                num_mols_this_instance = len(molecule)
                # should always be max_mol now, so doesn't matter

                for mol in range(len(molecule)):
                    mol_string = "".join(molecule[mol])
                    if mol_string == "":
                        smiles = ""
                    else:
                        smiles = rdc.MolToSmiles(
                            rdc.MolFromMolBlock(mol_string, sanitize=False)
                        )
                    # some mols might be empty, this if/else positions reagents/products accordingly
                    if counter_reagents + 1 <= number_reagents:
                        my_table.loc[
                            rxn_id, my_table.columns[counter_reagents]
                        ] = smiles
                        counter_reagents += 1
                    else:
                        my_table.loc[
                            rxn_id, my_table.columns[counter_products + max_reagents]
                        ] = smiles
                        counter_products += 1

                        # reset variables
                iterate_molecules = 0
                molecule = []
                mol_string = ""

        previous_line = current_line
    ################################

    #
    ######### GET single line data ##########
    #

    # Nota bene: this will write first line of multiline columns as well
    # but doesn't matter since those will be correctly overwritten later on

    rxn_id = ""
    previous_line = seed_line

    for line in open(RDF_OK_FILE):
        current_line = line

        # get reaction ID
        if current_line.startswith("$RFMT"):
            rxn_id = str(current_line.strip().split(" ")[2])
            # flag = 0
            continue

        if previous_line.startswith("$DTYPE") and current_line.startswith("$DATUM"):
            current_column = previous_line.strip().split(" ")[1].replace(SCI_REAX, "")
            row_text = current_line.replace("\n", " ")
            # flag = 1
            my_table.loc[rxn_id, current_column] = row_text.replace("$DATUM ", "")

        previous_line = current_line
    ################################

    #
    ### Extract Experimental Procedure ###
    # Multiline, both,
    # Reaxys and Scifinder
    #

    flag = 0
    # 0 = generic
    # 5 = exp procedure text over multiple lines
    # 9 = skip
    rxn_id = ""
    multiple_row_text = ""
    previous_line = seed_line

    for line in open(RDF_OK_FILE):
        current_line = line

        # get reaction ID
        if current_line.startswith("$RFMT"):
            rxn_id = str(current_line.strip().split(" ")[2])
            flag = 0
            continue

        # get experimental section
        if SCI_REAX == "RXN:":
            if re.match(".+EXP_PROC", previous_line) or flag == 5:
                # start of the experimental section. spans over multiple line
                if re.match(".+EXP_PROC", previous_line):
                    current_column = (
                        previous_line.strip().split(" ")[1].replace(SCI_REAX, "")
                    )

                if re.match(".+NOTES", current_line) or re.match(
                    ".+REFERENCE.+", current_line
                ):
                    # this is the end of experimental block
                    flag = 9
                    my_table.loc[rxn_id, current_column] = multiple_row_text.replace(
                        "$DATUM ", ""
                    )
                    multiple_row_text = ""
                else:
                    multiple_row_text += current_line.replace("\n", " ")
                    flag = 5
        else:  # Reaxys
            if re.match(".+TXT", previous_line) or flag == 5:
                # start of the experimental section. spans over multiple line
                if re.match(".+TXT", previous_line):
                    current_column = (
                        previous_line.strip().split(" ")[1].replace(SCI_REAX, "")
                    )

                if re.match(".+STP", current_line):
                    # this is the end of experimental block
                    flag = 9
                    my_table.loc[rxn_id, current_column] = multiple_row_text.replace(
                        "$DATUM ", ""
                    )
                    multiple_row_text = ""
                else:
                    multiple_row_text += current_line.replace("\n", " ")
                    flag = 5

        previous_line = current_line
    ################################

    #
    ######## Extract Notes ########
    # (only Scifinder)
    #

    flag = 0
    # 0 = generic
    # 6 = notes, text potentially over multiple lines
    # 9 = skip

    rxn_id = ""
    multiple_row_text = ""
    previous_line = seed_line

    for line in open(RDF_OK_FILE):
        current_line = line

        # get reaction ID
        if current_line.startswith("$RFMT"):
            rxn_id = str(current_line.strip().split(" ")[2])
            flag = 0
            continue

            # Get Notes
        if re.match(".+NOTES", previous_line) or flag == 6:
            flag = 6
            # start of the Notes section. might span over multiple line
            if re.match(".+NOTES", previous_line):
                current_column = (
                    previous_line.strip().split(" ")[1].replace(SCI_REAX, "")
                )

            if current_line.startswith("$DTYPE"):
                # this is the end of Notes block
                flag = 9
                my_table.loc[rxn_id, current_column] = multiple_row_text.replace(
                    "$DATUM ", ""
                )
                multiple_row_text = ""
            else:
                multiple_row_text += current_line.replace("\n", " ")
                flag = 6

        previous_line = current_line
    ################################

    #
    ######## Extract title ########
    # (only Scifinder)
    #

    flag = 0
    # 0 = generic
    # 7 = title
    # 9 = skip

    rxn_id = ""
    multiple_row_text = ""
    previous_line = seed_line

    for line in open(RDF_OK_FILE):
        current_line = line

        # get reaction ID
        if current_line.startswith("$RFMT"):
            rxn_id = str(current_line.strip().split(" ")[2])
            flag = 0
            continue

            # Get Title
        if re.match(".+TITLE", previous_line) or flag == 7:
            flag = 7
            # start of the Title section. might span over multiple line
            if re.match(".+TITLE", previous_line):
                current_column = (
                    previous_line.strip().split(" ")[1].replace(SCI_REAX, "")
                )

            if current_line.startswith("$DTYPE"):
                # this is the end of title block
                flag = 9
                my_table.loc[rxn_id, current_column] = multiple_row_text.replace(
                    "$DATUM ", ""
                )
                multiple_row_text = ""
            else:
                multiple_row_text += current_line.replace("\n", " ")
                flag = 7

        previous_line = current_line
    ################################

    #
    ####### Extract authors ########
    # (only Scifinder)
    #

    flag = 0
    # 0 = generic
    # 8 = authors
    # 9 = skip

    rxn_id = ""
    multiple_row_text = ""
    previous_line = seed_line

    for line in open(RDF_OK_FILE):
        current_line = line

        # get reaction ID
        if current_line.startswith("$RFMT"):
            rxn_id = str(current_line.strip().split(" ")[2])
            flag = 0
            continue

            # Get Authors
        if re.match(".+AUTHOR", previous_line) or flag == 8:
            flag = 8
            if re.match(".+AUTHOR", previous_line):
                current_column = (
                    previous_line.strip().split(" ")[1].replace(SCI_REAX, "")
                )

            if current_line.startswith("$DTYPE"):
                # this is the end of author block
                flag = 9
                my_table.loc[rxn_id, current_column] = multiple_row_text.replace(
                    "$DATUM ", ""
                )
                multiple_row_text = ""
            else:
                multiple_row_text += current_line.replace("\n", " ")
                flag = 8

        previous_line = current_line
    ################################

    #
    ### Extract citation (i.e. source) ###
    #
    # This is done last, since for Scifinder
    # this is the last entry in a file
    # not necessary for reaxys, but it will go through it anyway
    # (less ifs and doesn't screw anything up)
    #

    flag = 0
    # 0 = generic
    # 9 = skip
    # 4 = citation

    rxn_id = ""
    multiple_row_text = ""
    previous_line = seed_line

    for line in open(RDF_OK_FILE):
        current_line = line

        # get reaction ID
        if current_line.startswith("$RFMT"):
            rxn_id = str(current_line.strip().split(" ")[2])
            flag = 0
            continue

            # Get Citation
        if re.match(".+CITATION", previous_line) or flag == 4:
            flag = 4
            if re.match(".+CITATION", previous_line):
                current_column = (
                    previous_line.strip().split(" ")[1].replace(SCI_REAX, "")
                )

            if current_line.startswith("$DTYPE"):
                # this is the end of citation block
                flag = 9
                my_table.loc[rxn_id, current_column] = multiple_row_text.replace(
                    "$DATUM ", ""
                )
                multiple_row_text = ""
            else:
                multiple_row_text += current_line.replace("\n", " ")
                flag = 4

        previous_line = current_line
    ################################

    # End of file scanning #

    ############################################
    # Finish table for export to csv file format

    my_table = my_table.replace(pd.np.nan, "", regex=True)  # need to remove NaN
    my_table.drop(
        list(my_table.filter(regex="COPYRIGHT")), axis=1, inplace=True
    )  # skip the copyright (optional)
    my_table.to_csv(RDF_CSV_FILE, sep="\t", header=True, index=True)

    # end of script
    # one could add a return value for better error handling.
    return None
