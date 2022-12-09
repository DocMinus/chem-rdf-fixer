#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Chemical RDF converter & fixer.
Version 2.6.2 (Feb 09, 14:15:00 2022)
Update: Dec 08, 2022.
Added support for Infochem based rdf files.
Removed unnecessary zip list return

run by calling
rdf_fixer.fix(filename or path)
(not via rdf_fixer.convert() even though that is possible)

@author: Alexander Minidis (DocMinus)

license: MIT License
Copyright (c) 2021-2022 DocMinus
"""


import os
import re
import pandas as pd
from collections import OrderedDict
import rdkit.Chem as rdc
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit import RDLogger

# Important, or else waaaay too many RDkit details in output
RDLogger.logger().setLevel(RDLogger.CRITICAL)


def fix(RDF_IN: str):
    """Retrieving all .RDF files in a subdirectory recursively.
    Then submit to conversion (i.e. fixing)
    Parts of os.walk snippet originated on Reddit somewhere, forgot where though.
    Rewritten to check for & stop fixing fixed files.
    Args:
        RDF_IN = filename, alt. directory and subdirectories to scan
    Returns:
        Originally None. Current the zipped list of paths. Usefull for Knime.
    """

    file_list_in = []
    file_list_ok = []
    file_list_csv = []

    if os.path.isfile(RDF_IN):
        if RDF_IN.endswith(("rdf", "RDF")):
            file_list_in.append(os.path.join(RDF_IN))
            if RDF_IN.endswith("_fixed.rdf"):
                # checks for existing fixed files and removes from the list
                # as well as the 'unfixed" file (since already done)
                print("File already fixed: ", RDF_IN)
                del file_list_in[-1]
                file_list_in.remove(RDF_IN)
                # since single file, could just as well use file_list_in.clear()
            else:
                file_list_ok.append(os.path.splitext(RDF_IN)[0] + "_fixed.rdf")
                file_list_csv.append(os.path.splitext(RDF_IN)[0] + ".csv")

    elif os.path.isdir(RDF_IN):
        for subdir, dirs, files in os.walk(RDF_IN):
            _item_to_remove = []
            for file in files:
                if file.endswith(("rdf", "RDF")):
                    full_path_in = os.path.join(subdir, file)
                    file_list_in.append(full_path_in)
                    if file.endswith("_fixed.rdf"):
                        # checks for existing fixed files and removes from the list
                        # as well as the 'unfixed" file (since already done)
                        print("File already fixed: ", full_path_in)
                        del file_list_in[-1]
                        # temp list for later removal of any original
                        # (not here in case of different file order)
                        _item_to_remove.append(full_path_in.replace("_fixed", ""))
                    else:
                        file_list_ok.append(
                            os.path.join(
                                subdir, os.path.splitext(file)[0] + "_fixed.rdf"
                            )
                        )
                        file_list_csv.append(
                            os.path.join(subdir, os.path.splitext(file)[0] + ".csv")
                        )
            for x in _item_to_remove:
                file_list_in.remove(x)

    if len(file_list_in) > 0:
        zipped = zip(file_list_in, file_list_ok, file_list_csv)
        # note: zip gets unpacked upon usage and disappears!
        for file_in, file_ok, file_csv in zipped:
            print("Converting file: ", file_in)
            convert(file_in, file_ok, file_csv)

    return


def convert(RDF_IN_FILE: str, RDF_OK_FILE: str, RDF_CSV_FILE: str):
    """original script with single file usage wrapped into this 'convert' function
    Args:
        RDF_IN_FILE: original input RDF file including path
        RDF_OK_FILE: new RDF file with corrections (if any)
        RDF_CSV_FILE: resulting CSV file (incl. path)
    Returns:
        None - output are the new files.
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
            # here a correction for Infochem RDFS that has one empty row to many
            if current_line == "\n" and previous_line.startswith("M  END"):
                continue

            # old entries use lower case rxn. Change to upper case. fast without if check.
            previous_line = previous_line.replace("rxn:", "RXN:")

            if write_to_file:
                file_out.write(previous_line)

            previous_line = current_line

        file_out.write(previous_line)
        # the last line is not caught in the loop, hence written out here.

    # end of fix section
    ####################

    def scifi_or_reax(in_file: str) -> str:
        """Determine if Scifinder, Reaxys or ICSynth rdf file
        (Scifinder contains 'SCHEME' in the enumeration;
        Infochem uses "Infochem" in RXN or MOL field)
        Returned string is used by multiple string.replace() methods,
        to render script independent of source

        Args:
            in_file (str): filename of the corrected file (in principle,
                           the original one would work as well;
                           alt even global variable possible instead)
        Returns:
            SCI_REAX (str): "RXN:" (scifinder & Infochem) or "ROOT:" (reaxys)
        """

        f = open(in_file)
        NUMBER_OF_LINES = 3

        for i in range(NUMBER_OF_LINES):
            line_three = f.readline()
        _scireax = "RXN:" if re.match(".+SCHEME", line_three) else "ROOT:"
        # since this is ambigeous between Infochem and Reaxys, another check 3 lines after:
        for i in range(NUMBER_OF_LINES):
            line_six = f.readline()
        _scireaxinfochem = "RXN:" if re.match(".+INFOCHEM", line_six) else _scireax

        f.close()
        return _scireaxinfochem

    def build_empty_table(in_file: str, SCI_REAX: str):
        """Scans file (unfortunately) three times to build a pandas df used as main table
        Args:
            in_file (str): filename of the corrected file: RDF_OK_FILE
            SCI_REAX (str): "RXN:" (scifinder/infochem) or string "ROOT:" (reaxys) used in replacements
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
    SCI_REAX = scifi_or_reax(RDF_IN_FILE)  
    # switching back to in_file instead of RDF_OK_FILE.
    # build table according to files specs. get max no of reagents & products at the same time.
    my_table, max_reagents, max_products = build_empty_table(RDF_OK_FILE, SCI_REAX)

    ####################################################################
    # Here comes the actual data extraction and addition to pandas table

    #
    ############### GET MOLECULES #############
    # (structure same for Reaxys and Scifinder - and Infochem(?))
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

                for mol in range(num_mols_this_instance):
                    mol_string = "".join(molecule[mol])
                    if mol_string == "":
                        smiles = ""
                    else:
                        mol = rdc.MolFromMolBlock(mol_string, sanitize=False)
                        if mol is None:
                            continue

                        try:
                            rdc.SanitizeMol(mol)
                        except ValueError as _e:
                            print("Error: ", _e)
                            continue

                        mol.UpdatePropertyCache(strict=False)
                        rdc.SanitizeMol(
                            mol,
                            sanitizeOps=(
                                rdc.SANITIZE_ALL
                                ^ rdc.SANITIZE_CLEANUP
                                ^ rdc.SANITIZE_PROPERTIES
                            ),
                        )
                        mol = rdMolStandardize.Normalize(mol)
                        smiles = rdc.MolToSmiles(mol)

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
    # Multiline, for all,
    # Reaxys, Scifinder, Infochem
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
        if SCI_REAX.upper() == "RXN:":
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
