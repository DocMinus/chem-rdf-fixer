#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Chemical RDF converter & fixer.
Version 3.0.8 (Feb 09, 14:15:00 2022)
Update: Mar 17, 2024.
No code changes, only pypi updates to installer.

run by calling
rdf_fixer.fix(filename or path, flag)
flag = False; or True (default)

@author: Alexander Minidis (DocMinus)

license: MIT License
Copyright (c) 2021-2024 DocMinus
"""


import os
import re
from enum import Enum
from typing import Tuple

import numpy as np
import pandas as pd
import rdkit.Chem as rdc
from rdkit import RDLogger
from rdkit.Chem.MolStandardize import rdMolStandardize

# Important, or else waaaay too many RDkit details in output
RDLogger.logger().setLevel(RDLogger.CRITICAL)


class Files:
    """
    Collects the filenames into a class, thus less variables needed for function declarations
    """

    def __init__(self, provided_rdf_source, provided_rdf_fixed, provided_csv_file):
        self.rdf_source = provided_rdf_source
        self.rdf_fixed = provided_rdf_fixed
        self.csv_file = provided_csv_file

    def rdf_to_rdffix_zipped(self):
        return zip(self.rdf_source, self.rdf_fixed)
        # comment to myself: sort of kind of optional,
        # one could access variables in init instead.


def files_to_read(rdf_source: str) -> Files:
    """Retrieving all .RDF files in a subdirectory recursively, or only a single rdf file.
    Is called by the fix() function.
    Parts of os.walk snippet originated on Reddit somewhere, forgot where though.
    Args:
        rdf_source: filename, alt. directory and subdirectories to scan
    Returns:
        resolved filenames via Files() class.
    """

    file_list_in = []
    file_list_ok = []
    file_list_csv = []

    if os.path.isfile(rdf_source):
        if rdf_source.endswith(("rdf", "RDF")):
            file_list_in.append(os.path.join(rdf_source))
            if rdf_source.endswith("_fixed.rdf"):
                # checks for existing fixed files and removes from the list
                # as well as the 'unfixed" file (since already done)
                print("File already fixed: ", rdf_source)
                del file_list_in[-1]
                file_list_in.remove(rdf_source)
                # since single file, could just as well use file_list_in.clear()
            else:
                file_list_ok.append(os.path.splitext(rdf_source)[0] + "_fixed.rdf")
                file_list_csv.append(os.path.splitext(rdf_source)[0] + ".csv")

    elif os.path.isdir(rdf_source):
        for subdir, dirs, files in os.walk(rdf_source):
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

    return Files(file_list_in, file_list_ok, file_list_csv)


def fix(rdf_source: str, convert_to_csv=True) -> None:
    """Fix erroneous entries (empty mols) by deleting those entries
    Entry function. Calls files_to_read and, when True, convert.
    Args:
        rdf_source: filename, alt. directory and subdirectories to scan.
        convert_to_csv: default is True, then it will also convert to csv.
    Returns:
        None. Indirectly, converted files are the result.
    """

    myfiles = files_to_read(rdf_source)
    for rdf_file_in, rdf_file_ok in myfiles.rdf_to_rdffix_zipped():
        print("Fixing File: ", rdf_file_in)
        with open(rdf_file_in) as file_in:
            seed_line = file_in.readline()
        previous_line = seed_line  # get first line as "seed" for upcoming loop
        with open(rdf_file_ok, "w") as file_out:
            write_to_file: str = "dummy"  # was bool before, now a tidbit cleaner
            counter = 0  # in case one needs to change entry enumeration
            for current_line in open(rdf_file_in):
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
                    current_line.startswith("$DTYPE")
                    and previous_line.startswith("$RFMT")
                )

                # here a correction for ICSynth RDFs that have one empty row to many
                if current_line == "\n" and previous_line.startswith("M  END"):
                    continue

                # old entries use lower case rxn. Change to upper case. faster without if check.
                previous_line = previous_line.replace("rxn:", "RXN:")

                # here a correction for (old) Spresi Rdfs (also Marvin???)
                # else a csv conversion won't work without extensive changes
                previous_line = previous_line.replace(
                    "$RFMT\n", ("$RFMT $RIREG " + str(counter) + "\n")
                )
                counter += 1

                if write_to_file:
                    file_out.write(previous_line)

                previous_line = current_line

            file_out.write(previous_line)
            # the last line is not caught in the loop, hence written out here.

    if convert_to_csv:
        convert(myfiles)

    return None


def convert(myfiles: Files) -> None:
    """
    called by fix function, calls the create csv in a loop.
    no return.
    """
    for rdf_file_ok, rdf_file_csv in zip(myfiles.rdf_fixed, myfiles.csv_file):
        csv_from_rdf(rdf_file_ok, rdf_file_csv)

    return None


def csv_from_rdf(rdf_file_ok: str, rdf_file_csv: str) -> None:
    """CSV from RDF convert function
    Args:
        rdf_file_ok: new RDF file with corrections (if any)
        rdf_file_csv: resulting CSV file (incl. path)
    Returns:
        None - output are the new files.
    """

    class RdfSource(Enum):
        UNKNOWN = ""
        SCIFINDER = "RXN:"
        INFOCHEM = "RXN:"
        REAXYS = "ROOT:"

    def rdf_origin(in_file: str) -> str:
        """
        Determines the source of an RDF file by inspecting its contents.

        Args:
            in_file (str): The filename of the RDF file to be checked.

        Returns:
            A string indicating the source of the RDF file. The returned string
            is used by multiple `string.replace()` methods to make the script
            independent of the source.

            Possible return values are:
            - RdfSource.SCIFINDER if the file was generated by Scifinder.
            - RdfSource.INFOCHEM if the file was generated by Infochem ICSynth or (corrected) SPRESI.
            - RdfSource.REAXYS if the file was generated by Reaxys.
        """
        pattern_scifinder = re.compile(".+SCHEME")
        pattern_infochem = re.compile(".+Infochem|.+ACS")
        pattern_reaxys = re.compile(".+Marvin")

        with open(in_file) as f:
            for line in f:
                if pattern_scifinder.match(line) and pattern_infochem.match(line):
                    return RdfSource.INFOCHEM.value
                elif (
                    pattern_scifinder.match(line)
                    and pattern_infochem.search(line) is None
                ):
                    return RdfSource.SCIFINDER.value
                elif pattern_reaxys.match(line):
                    return RdfSource.REAXYS.value

        return RdfSource.UNKNOWN.value

        """
        original hardcoded, for documentation's sake remaining here:

        f = open(in_file)
        NUMBER_OF_LINES = 12
        line: str = []
        for i in range(NUMBER_OF_LINES):
            line.append(f.readline())
        f.close()
        _rdf = "RXN:"
        if re.match(".+SCHEME", line[2]) and re.match(".+Infochem", line[10]):
            # Infochem ICSynth and (corrected) SPRESI
            pass
        if re.match(".+SCHEME", line[2]) and re.match(".+ACS", line[11]):
            # CAS: Scifinder
            pass
        if (not re.match(".+SCHEME", line[2])) and re.match(".+Marvin", line[5]):
            # Reaxys
            _rdf = "ROOT:"
        return _rdf

        """

    def build_empty_table(in_file: str, rdf_type: str) -> Tuple[pd.DataFrame, int, int]:
        """
        Scans the RDF file to determine the number of reagents, products, and
        columns, and constructs an empty pandas DataFrame with the appropriate
        size and column names.

        Args:
            in_file (str): The filename of the corrected RDF file.
            rdf_type (str): A string indicating the source of the RDF file,
                which is used in replacements.
                "RXN:" (scifinder/infochem) or string "ROOT:" (reaxys)

        Returns:
            da_table (object): the (empty) pandas df working table
            max_reagents (int): number for later positioning of reagents smiles in table
            max_products (int): <> (products)
        """

        # Get the IDs and use as row index
        list_of_IDs = []
        with open(in_file) as f:
            for line in f:
                if line.startswith("$RFMT"):
                    list_of_IDs.append(line.strip().split(" ")[2])

        # Determine max no of reagents/products
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

        # Build the column headers
        columns = [f"Reagent{i}" for i in range(max_reagents)]
        columns += [f"Product{i}" for i in range(max_products)]
        with open(in_file) as f:
            for line in f:
                if line.startswith("$DTYPE"):
                    columns.append((line.strip().split(" ")[1]).replace(rdf_type, ""))

        # Construct the empty table
        # da_table = pd.DataFrame(index=list_of_IDs, columns=list(OrderedDict.fromkeys(columns)))
        da_table = pd.DataFrame(index=list_of_IDs, columns=columns)
        return da_table, max_reagents, max_products

    print("Converting to csv: ", rdf_file_ok)
    ##############################################################
    # Initialize Table and diverse variables
    # get string replacement variable depending on RDF source
    RDF_TYPE = rdf_origin(rdf_file_ok)
    # build table according to files specs. get max no of reagents & products at the same time.
    my_table, max_reagents, max_products = build_empty_table(rdf_file_ok, RDF_TYPE)

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
    with open(rdf_file_ok) as file_in:
        seed_line = file_in.readline()
    previous_line = seed_line

    for line in open(rdf_file_ok):
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
                        my_table.loc[rxn_id, my_table.columns[counter_reagents]] = (
                            smiles
                        )
                        counter_reagents += 1
                    else:
                        my_table.loc[
                            rxn_id,
                            my_table.columns[counter_products + max_reagents],
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

    for line in open(rdf_file_ok):
        current_line = line

        # get reaction ID
        if current_line.startswith("$RFMT"):
            rxn_id = str(current_line.strip().split(" ")[2])
            # flag = 0
            continue

        if previous_line.startswith("$DTYPE") and current_line.startswith("$DATUM"):
            current_column = previous_line.strip().split(" ")[1].replace(RDF_TYPE, "")
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

    for line in open(rdf_file_ok):
        current_line = line

        # get reaction ID
        if current_line.startswith("$RFMT"):
            rxn_id = str(current_line.strip().split(" ")[2])
            flag = 0
            continue

        # get experimental section
        if RDF_TYPE.upper() == "RXN:":
            if re.match(".+EXP_PROC", previous_line) or flag == 5:
                # start of the experimental section. spans over multiple line
                if re.match(".+EXP_PROC", previous_line):
                    current_column = (
                        previous_line.strip().split(" ")[1].replace(RDF_TYPE, "")
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
                        previous_line.strip().split(" ")[1].replace(RDF_TYPE, "")
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

    for line in open(rdf_file_ok):
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
                    previous_line.strip().split(" ")[1].replace(RDF_TYPE, "")
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

    for line in open(rdf_file_ok):
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
                    previous_line.strip().split(" ")[1].replace(RDF_TYPE, "")
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

    for line in open(rdf_file_ok):
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
                    previous_line.strip().split(" ")[1].replace(RDF_TYPE, "")
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

    for line in open(rdf_file_ok):
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
                    previous_line.strip().split(" ")[1].replace(RDF_TYPE, "")
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

    my_table = my_table.replace(np.nan, "", regex=True)  # need to remove NaN
    my_table.drop(
        list(my_table.filter(regex="COPYRIGHT")), axis=1, inplace=True
    )  # skip the copyright (optional)
    my_table.to_csv(rdf_file_csv, sep="\t", header=True, index=True)

    # end of script
    # one could add a return value for better error handling.
    return None
