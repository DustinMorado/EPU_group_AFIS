#!/usr/bin/env python
#. -*- coding: utf-8 -*-
"""Sort EPU AFIS data into Optics Groups for RELION 3.1

Written By Dustin Reed Morado
Last updated 20.06.2020
"""

from __future__ import print_function, division

import os
import argparse
import numpy as np
import matplotlib.pyplot as plt

from fnmatch import fnmatch
from xml.etree import ElementTree
from sklearn.cluster import KMeans, AgglomerativeClustering

def main(xml_dir = os.getcwd(), n_clusters = 1, apix = 1.00,
         mtf_fn = 'MTF.star', voltage = 300.0, cs = 2.7, q0 = 0.1,
         ftype = 'mrc', movie_dir = '', output_fn = 'movies.star',
         algorithm = 'kmeans', quiet = False):

    metadata_fns = []

    for dirpath, dirnames, filenames in os.walk(xml_dir, followlinks=True):
        for filename in filenames:
            if (fnmatch(filename, 'FoilHole_*_Data_*.xml')
                    and not fnmatch(filename, '*ractions.xml')):

                metadata_fns.append(os.path.join(dirpath, filename))

    if len(metadata_fns) == 0:
        raise ValueError('No EPU XML metadata files found')

    namespace = {'fei' :
            'http://schemas.datacontract.org/2004/07/Fei.SharedObjects'}

    beam_shifts = []

    for metadata_fn in metadata_fns:
        metadata = ElementTree.parse(metadata_fn)
        beam_shift = metadata.findall(
                'fei:microscopeData/fei:optics/fei:BeamShift', namespace)

        if len(beam_shift) == 0:
            raise ValueError('No BeamShift found in {}'.format(metadata_fn))
        elif len(beam_shift[0]) != 2:
            raise ValueError('Improper BeamShift found in {}'.format(
                    metadata_fn))

        beam_shifts.append([float(x.text) for x in beam_shift[0]])

    shift_array = np.array(beam_shifts)

    if n_clusters == 1:
        figure = plt.figure()
        axes = figure.add_subplot(111)
        axes.set_title('EPU AFIS Beam Shift Values')
        axes.set_xlabel('Beam Shift X (a.u.)')
        axes.set_ylabel('Beam Shift Y (a.u.)')
        axes.scatter(shift_array[:, 0], shift_array[:, 1])
        plt.show(block = False)

        while n_clusters <= 1:
            n_user = input('How many Optics Groups (or Ctrl-C to abort): ')

            try:
                n_clusters = int(n_user)
            except ValueError:
                print('Please enter a positive integer greater than 1!')
            else:
                if n_clusters <=1:
                    print('Please enter a positive integer greater than 1!')

        plt.close('all')

    if len(beam_shifts) < n_clusters:
        raise ValueError('Number of clusters greater than number of points')

    optics_clusters = None
    cluster_centers = None

    if algorithm == 'kmeans':
        k_means = KMeans(n_clusters = n_clusters,
                         init = 'k-means++',
                         n_init = 100,
                         algorithm = 'elkan').fit(shift_array)

        optics_clusters = k_means.predict(shift_array)
        cluster_centers = k_means.cluster_centers_
    else:
        hac = AgglomerativeClustering(n_clusters = n_clusters,
                                      linkage = 'complete').fit(shift_array)

        optics_clusters = hac.labels_
        cluster_centers = [[np.average(shift_array[optics_clusters==x][:,0]),
                            np.average(shift_array[optics_clusters==x][:,1])]
                           for x in set(sorted(optics_clusters))]

    radii = [x[0]**2 + x[1]**2 for x in cluster_centers]
    sort_idxs = sorted(enumerate(radii), key=lambda x:x[1])
    origin = cluster_centers[sort_idxs[0][0]]

    x_vec = (1, 0)
    x_unit = (1, 0)
    x_angle = np.pi
    x_length = 1

    y_vec = (0, 1)
    y_unit = (0, 1)
    y_angle = np.pi
    y_length = 1

    for idx in range(1,5):
        point = cluster_centers[sort_idxs[idx][0]]
        x_coord = point[0] - origin[0]
        y_coord = point[1] - origin[1]

        if x_coord > 0 and x_coord > abs(y_coord):
            x_vec = (x_coord, y_coord)
            x_angle = np.arctan2(y_coord, x_coord)
            x_length = np.sqrt(x_vec[0]**2 + x_vec[1]**2)
            x_unit = (x_vec[0] / x_length, x_vec[1] / x_length)


        if y_coord > 0 and y_coord > abs(x_coord):
            y_vec = (x_coord, y_coord)
            y_angle = np.arctan2(y_coord, x_coord)
            y_length = np.sqrt(y_vec[0]**2 + y_vec[1]**2)
            y_unit = (y_vec[0] / y_length, y_vec[1] / y_length)

    grid_dists = []

    for idx, center in enumerate(cluster_centers):
        point = (center[0] - origin[0], center[1] - origin[1])
        grid_x = np.round(
            (point[0] * x_unit[0] + point[1] * x_unit[1]) / x_length)

        grid_y = np.round(
            (point[0] * y_unit[0] + point[1] * y_unit[1]) / y_length)

        dist = max(abs(grid_x), abs(grid_y))
        angle = (np.degrees(np.arctan2(grid_y, grid_x)) + 360) % 360
        grid_dists.append((idx, grid_x, grid_y, dist, angle))

    sort_idxs = [x[0] for x in sorted(grid_dists, key=lambda x:(x[3], x[4]))]
    optics_groups = [sort_idxs.index(x) + 1 for x in optics_clusters]

    if not quiet:
        figure = plt.figure()
        axes = figure.add_subplot(111)
        axes.set_title('EPU AFIS Beam Shift Values')
        axes.set_xlabel('Beam Shift X (a.u.)')
        axes.set_ylabel('Beam Shift Y (a.u.)')
        axes.scatter(shift_array[:, 0], shift_array[:, 1], c=optics_groups,
                cmap='tab20')

        for optics_group in range(n_clusters):
            axes.annotate('{0:d}'.format(optics_group + 1),
                    xy = cluster_centers[sort_idxs[optics_group]],
                    textcoords = 'offset pixels', xytext=(10, 10))

        plt.show(block = False)
        _ = input('If happy with cluster press any key (Ctrl-C to abort)')
        plt.close('all')

    entries = sorted(zip(metadata_fns, optics_groups),
            key=lambda x:(x[0], x[1]))

    with open(output_fn, 'w') as f:
        f.write('\n# version 30001\n\n')
        f.write('data_optics\n\nloop_\n')
        f.write('_rlnOpticsGroupName #1 \n')
        f.write('_rlnOpticsGroup #2 \n')
        f.write('_rlnMtfFileName #3 \n')
        f.write('_rlnMicrographOriginalPixelSize #4 \n')
        f.write('_rlnVoltage #5 \n')
        f.write('_rlnSphericalAberration #6 \n')
        f.write('_rlnAmplitudeContrast #7 \n')

        for optics_group in range(1, n_clusters + 1):
            f.write(('opticsGroup{0:d}\t{1:d}\t{2}\t{3:15.6f}\t{4:15.6f}\t'
                     '{5:15.6f}\t{6:15.6f}\n').format(optics_group,
                     optics_group, mtf_fn, apix, voltage, cs, q0))

        f.write(' \n\n# version 30001\n\n')
        f.write('data_movies\n\nloop_\n')
        f.write('_rlnMicrographMovieName #1 \n')
        f.write('_rlnOpticsGroup #2 \n')

        for metadata_fn, optics_group in entries:
            base = os.path.basename(metadata_fn)
            root, ext = os.path.splitext(base)
            movie_glob = '*{0}*ractions.{1}'.format(root, ftype)
            movie_fn = None

            for dirpath, dirnames, filenames in os.walk(movie_dir, followlinks=True):
                for filename in filenames:
                    if fnmatch(filename, movie_glob):
                        movie_fn = os.path.join(dirpath, filename)
                        break

                if movie_fn is not None:
                    break

            if movie_fn is None:
                movie_fn = '{0}_Fractions.{1}'.format(
                        os.path.join(movie_dir, root), ftype)

            f.write('{0}\t{1:d}\n'.format(movie_fn, optics_group))

        f.write(' \n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description = "Create Optics Groups from EPU AFIS data",
            epilog = "Writted by Dustin Morado 20.06.2020")

    parser.add_argument('--xml_dir', '-i', type = str, required = True,
            help = ('Path to directory with EPU record metadata XML files. '
                    '[REQUIRED]'))

    parser.add_argument('--n_clusters', '-n', type = int, default = 1,
            help = 'Number of Optics Groups (1 = interactively choose. [1]')

    parser.add_argument('--algorithm', type = str, default = 'kmeans',
            choices = ['kmeans', 'hac'],
            help = 'Clustering algorthim to use. {kmeans, hac} [kmeans]')

    parser.add_argument('--apix', type = float, default = 1.00,
            help = 'Pixel size of micrographs. [1.00]')

    parser.add_argument('--mtf_fn', type = str, default = 'MTF.star',
            help = 'Path to MTF STAR file. [MTF.star]')

    parser.add_argument('--voltage', type = float, default = 300.0,
            help = 'Voltage of micrscope in keV. [300.0]')

    parser.add_argument('--cs', type = float, default = 2.7,
            help = 'Spherical Aberration of objective lens in mm. [2.7]')

    parser.add_argument('--q0', type = float, default = 0.1,
            help = 'Fraction of amplitude contrast [0 - 1]. [0.1]')

    parser.add_argument('--ftype', type = str, default = 'mrc',
            help = 'Filetype of micrograph movies. [mrc]')

    parser.add_argument('--movie_dir', '-d', type = str, default = '.',
            help = 'Path to directory with micrograph movies. [.]')

    parser.add_argument('--output_fn', '-o', type = str,
            default = 'movies.star',
            help = 'Path to output STAR file. [movies.star]')

    parser.add_argument('--quiet', '-q', action = 'store_true',
            help = 'Run non-interactively with no plotting. [False]')

    args = parser.parse_args()
    main(xml_dir = args.xml_dir,
         n_clusters = args.n_clusters,
         apix = args.apix,
         mtf_fn = args.mtf_fn,
         voltage = args.voltage,
         cs = args.cs,
         q0 = args.q0,
         ftype = args.ftype,
         movie_dir = args.movie_dir,
         output_fn = args.output_fn,
         algorithm = args.algorithm,
         quiet = args.quiet)
