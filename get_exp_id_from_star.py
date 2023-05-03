#!/usr/bin/env python
"""Apply optics groups from Relion .star file to Cryosparc .cs file."""
# . -*- coding: utf-8 -*-
import numpy as np

try:
    import pyem
except ImportError:
    print(
        "Couldn't import pyem, try activating pyem Conda environment:"
        "\n\n$ conda activate pyem\n"
    )
    import sys

    sys.exit()

import argparse
import re
import tqdm


def exposure_groups_from_star(
    starfnam,
    csfile,
    outputfilename,
    fnam_regex_template="FoilHole_[0-9]*_Data_[0-9]*_[0-9]*_[0-9]*",
    backupcs=True,
    verbose=True,
):
    """Apply groups in star file to those in a Cryosparc cs file.

    This is accomplished by matching movie filenames between the star
    and cs files

    Parameters
    ----------
    starfnam : string
        Filename of the .star file from which micrograph optics groups
        will be taken
    csfile : string
        Filename of the crysoparc .cs file to which optics groups will
        be applied to matching filenames
    outputfilename : string
        Filename of the output .cs file
    fnam_regex_template : string, optional
        Regular expression template for matching of filenames, this
        helps avoid errors in matching due to file extensions (eg.
        doseweighted, eer, etc) that might be added in the processing
        pipeline
    backupcs : bool, optional
        If True create a back up of csfile
    verbose : bool, optional
        Option for verbose command line output
    """
    # Parse star file, getting group and micrograph information
    dfs = pyem.star.parse_star(starfnam)

    Micrographs = dfs

    # Get total number of optics groups
    maxgroup = max(dfs[pyem.star.Relion.OPTICSGROUP])

    # Save a backup copy of the input cs file if it is to be overwritten
    if backupcs:
        import shutil

        backup = csfile + ".bak"
        prompt = ("\nCreating backup of {0}, {1}. Use --nobackup flag "
                  "to turn this off\n").format(
            csfile, backup
        )
        if verbose:
            print(prompt)
        shutil.copyfile(csfile, backup)

    # Load cryosparc cs_file
    cs_items = np.load(csfile)

    # Strip directory and extension from file names and convert to list
    star_micrograph_names = dfs[pyem.star.Relion.MICROGRAPHMOVIE_NAME]

    star_micrographs = [
        re.search(fnam_regex_template, x).group()
        for x in star_micrograph_names
    ]

    # Cs parameters to change
    targets = ["mscope_params/exp_group_id", "ctf/exp_group_id"]

    # Find which targets exist inside cs file
    presenttargets = list(set(cs_items.dtype.names) & set(targets))

    if len(presenttargets) < 1:
        raise Exception(
            ("Couldn't find any of the following parameters in {0}:\n"
             "\n{1}\n\n try a different cs file that contains exposure"
             " group ids?").format(
                csfile, "\n".join(targets)
            )
        )

    # Possible tags under which the micrograph filename is stored
    tags = ["movie_blob/path", "blob/path", "location/micrograph_path"]

    # Find which tag is present for these
    for itag, tag in enumerate(tags):
        if cs_items.dtype.names.count(tag) > 0:
            break

    errorstring = "Couldn't find {0} from {1} in {2}"

    if verbose:
        print(
            "Applying optics groups from {0} to items in {1}\n".format(
                starfnam, csfile
            )
        )

    # Iterate over items in cs file
    for micrograph in tqdm.tqdm(cs_items, desc="items"):

        # Get Group ID
        micrograph_path = micrograph[tag].decode(encoding="utf-8")
        micrograph_fnam = re.search(
            fnam_regex_template, micrograph_path
        ).group()

        # Exception handling for micrograph from cs file not existing
        # in star file - these are lumped into a final group
        try:
            # Iterate over star_micrographs and store the index if the
            # t value matche she micrograph filename we're looking for
            ii = [
                idx
                for idx, s in enumerate(star_micrographs)
                if s in micrograph_fnam
            ][0]
            group_id = Micrographs[pyem.star.Relion.OPTICSGROUP][ii]
        except IndexError:
            if verbose:
                print(errorstring.format(micrograph_fnam, csfile, starfnam))

                # Assign group id maxgroup +1
                group_id = maxgroup + 1

        # Apply group id to cryosparc params
        for target in presenttargets:
            micrograph[target] = group_id

    # Save new cs file
    # Default is to overwrite existing cs file, otherwise write to
    # user inputted cs file.
    if outputfilename is None:
        out = open(csfile, "wb")
    else:
        out = open(outputfilename, "wb")
    np.save(out, cs_items)


if __name__ == "__main__":

    # Parse command line arguments

    parser = argparse.ArgumentParser(
        description=("Update Cryosparc exposure IDs in a .cs file from"
                     " Relion micrographs .star file"),
        epilog="Writted by Hamish Brown 01.11.2022",
    )

    parser.add_argument(
        "--csout",
        "-o",
        type=str,
        required=False,
        default=None,
        help=("Output cs file, default is to overwrite input cs file"),
    )

    parser.add_argument(
        "--nobackup",
        "-n",
        required=False,
        action="store_true",
        help=("Do not backup the .cs file"),
    )

    parser.add_argument(
        "--verbose",
        "-v",
        required=False,
        action="store_true",
        help=("Verbose output"),
    )

    parser.add_argument(
        "--star",
        "-i",
        type=str,
        required=True,
        help=("Path to micrographs .star file " "[REQUIRED]"),
    )

    parser.add_argument(
        "--cs",
        "-i2",
        type=str,
        required=True,
        help=("Input cryosparc cs file [REQUIRED]"),
    )

    args = parser.parse_args()

    exposure_groups_from_star(
        args.star,
        args.cs,
        args.csout,
        backupcs=not args.nobackup,
        verbose=args.verbose,
    )
