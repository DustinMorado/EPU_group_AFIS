# EPU_GROUP_AFIS

Forked from [https://github.com/DustinMorado/EPU_group_AFIS](https://github.com/DustinMorado/EPU_group_AFIS)

Takes the XML metadata from an EPU session that used AFIS (_Aberration Free
Image Shift_) for faster acquisition and organizes the collected micrograph
movies into RELION Optics Groups. In RELION version 3.1 where these groups were
introduced they can be used to further reduce the effects of high-order
aberrations on the data induced by collecting using large amounts of beam-image
shift.

There is a Notebook here that goes through how the processing is done and then a
script that is for actual processing.

To transfer this information into Cryosparc use the get_exp_id_from_star.py script

## Requirements

It should be consistent across older versions of Python, but this was what I
tested it using:

 * Python (_Version >= 3.7.6_)
 * numpy (_Version >= 1.18.1_)
 * scikit-learn (_Version >= 0.22.1_) 
 * matplotlib (_Version >= 3.1.3_)
 * [pyem](https://github.com/asarnow/pyem)
 
### Installation

Follow instructions on installation of pyem[https://github.com/asarnow/pyem/wiki/Install-pyem-with-Miniconda]. 
You can create a seperate conda environment (eg. pyem-EPUgroup) if you would like to avoid changing an existing pyem environment.

Make sure that you have activated the pyem environment:

```
$ conda activate pyem
```

Clone this repository and run the setup script:

```
$ git clone https://github.com/HamishGBrown/EPU_group_AFIS.git
$ cd EPU_group_AFIS
$ pip install -e .
```

The EPU_Group_AFIS.py and get_exp_id_from_stary.py scripts should now be available from anywhere via the command line.


## Usage
```
usage: EPU_Group_AFIS.py [-h] --xml_dir XML_DIR [--n_clusters N_CLUSTERS]
                         [--apix APIX] [--mtf_fn MTF_FN] [--voltage VOLTAGE]
                         [--cs CS] [--q0 Q0] [--ftype FTYPE]
                         [--movie_dir MOVIE_DIR] [--output_fn OUTPUT_FN]
                         [--quiet]

Create Optics Groups from EPU AFIS data

optional arguments:
  -h, --help            show this help message and exit
  --xml_dir XML_DIR, -i XML_DIR
                        Path to directory with EPU record metadata XML files.
                        [REQUIRED]
  --n_clusters N_CLUSTERS, -n N_CLUSTERS
                        Number of Optics Groups (1 = interactively choose. [1]
  --apix APIX           Pixel size of micrographs. [1.00]
  --mtf_fn MTF_FN       Path to MTF STAR file. [MTF.star]
  --voltage VOLTAGE     Voltage of micrscope in keV. [300.0]
  --cs CS               Spherical Aberration of objective lens in mm. [2.7]
  --q0 Q0               Fraction of amplitude contrast [0 - 1]. [0.1]
  --ftype FTYPE         Filetype of micrograph movies. [mrc]
  --movie_dir MOVIE_DIR, -d MOVIE_DIR
                        Path to directory with micrograph movies. [.]
  --output_fn OUTPUT_FN, -o OUTPUT_FN
                        Path to output STAR file. [movies.star]
  --quiet, -q           Run non-interactively with no plotting. [False]

Writted by Dustin Morado 20.06.2020

usage: get_exp_id_from_star.py [-h] [--csout CSOUT] [--nobackup] [--verbose] --star STAR --cs CS

Update Cryosparc exposure IDs in a .cs file from Relion micrographs .star file

optional arguments:
  -h, --help            show this help message and exit
  --csout CSOUT, -o CSOUT
                        Output cs file, default is to overwrite input cs file
  --nobackup, -n        Do not backup the .cs file
  --verbose, -v         Verbose output
  --star STAR, -i STAR  Path to micrographs .star file [REQUIRED]
  --cs CS, -i2 CS       Input cryosparc cs file [REQUIRED]

Writted by Hamish Brown 01.11.2022

```

## Licensing

Distributed under the MIT License please see LICENSE.txt for more information.
