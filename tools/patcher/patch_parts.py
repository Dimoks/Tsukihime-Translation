#!/usr/bin/env python3

import os
import re
import argparse
import subprocess
import multiprocessing
import sys
import stat
import configparser
from functools import partial


PARTS_BASENAME = None
OUTPUT_DIR = None
OUTPUT_BASENAME = None
MRG_TEMP_DIR = None
PNG_TEMP_DIR = None
PNG_SOURCE_DIR = None
REPLACER = 'bntx_replace/bntx_replace'


def get_format(filename):

    dot_index = filename.rfind('.')

    if dot_index > 0:
        part = filename[:dot_index]
        if part.lower() == 'nxgz':
            return 'nxgx'
        elif part.lower() == 'nxz':
            return 'nxcx'
        else:
            return None
    else:
        return None

def compress_nxx(args, lock):
    decompressed_file = args[0]
    compressed_file = args[1]
    nxx = args[2]
    format = get_format(nxx)
    if format:
        # command = '%s_compress' % format
        command = '-%s' % format
        # print("Compressing %s..." % compressed_file)
        # subprocess.run([command, decompressed_file, compressed_file])
        result = subprocess.run(['mangetsu_tools', command, '-p',
                                decompressed_file, '-a', compressed_file],
                                capture_output=True, text=True)

        with lock:
            print(result.stdout, end='')
            if result.stderr:
                print(result.stderr, file=sys.stderr, end='')

    else:
        print("Unknown format of file %s" % compressed_file)


def main(lock):
    # Make temp dirs

    global PARTS_BASENAME, OUTPUT_DIR, OUTPUT_BASENAME, MRG_TEMP_DIR, \
            PNG_TEMP_DIR, PNG_SOURCE_DIR

    parser = argparse.ArgumentParser(description='Patch parts')
    parser.add_argument('game', type=str, help='Short name of game (tsuki_re_ja)')
    args = parser.parse_args()

    game = args.game
    name = '%s_ALLUI' % game.upper()

    config = configparser.ConfigParser()
    config.read('config.ini')
    nxx = config[name]['nxx']

    PARTS_BASENAME = '_mrgs/%s/parts' % game
    OUTPUT_DIR = '_new_mrgs/%s/' % game
    OUTPUT_BASENAME = os.path.join(OUTPUT_DIR, 'parts')
    MRG_TEMP_DIR = '.parts_extracted/%s' % game
    PNG_TEMP_DIR = '.parts_dds/%s' % game
    PNG_SOURCE_DIR = '../../images/parts/%s/' % game

    for dirname in [MRG_TEMP_DIR, PNG_TEMP_DIR, OUTPUT_DIR]:
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    # Unpack allui
    # subprocess.run(['mrg_extract', PARTS_BASENAME, MRG_TEMP_DIR])
    subprocess.run(['mangetsu_tools', '-mre', '-a', PARTS_BASENAME,
                        '-p', MRG_TEMP_DIR])

    # Decompress all NXGZ files
    bntx_to_recompress = []
    dat_files = []
    for entry in os.scandir(MRG_TEMP_DIR):
        if not entry.is_file():
            continue
        if not entry.path.endswith('.dat'):
            continue
        dat_files.append(entry.path)

    for entry in dat_files:
        decompressed_filename = re.sub('.dat', '.BNTX', entry)
        # print("Decompressing %s..." % entry)
        # subprocess.run(['nxx_decompress', entry, decompressed_filename])
        subprocess.run(['mangetsu_tools', '-nxd', '-a', entry,
                        '-p', decompressed_filename])
        bntx_to_recompress.append((decompressed_filename, entry, nxx))

    # Convert PNG resources into DDS
    resources_to_inject = []
    patch_dirs = []
    for subdir, dirs, files in os.walk(PNG_SOURCE_DIR):
        for filename in files:
            if not filename.endswith('.png'):
                continue

            new_filename = re.sub('.png', '.dds', filename)
            input_path = os.path.join(subdir, filename)
            input_nxgz = os.path.split(subdir)[-1]
            output_dir = os.path.join(PNG_TEMP_DIR, input_nxgz)
            output_path = os.path.join(output_dir, new_filename)
            os.makedirs(output_dir, exist_ok=True)
            resources_to_inject.append((input_nxgz, new_filename, output_path))
            if input_nxgz not in patch_dirs:
                patch_dirs.append(input_nxgz)

            # If the target is newer than the source, skip
            if os.path.exists(output_path):
                in_stat = os.stat(input_path)
                out_stat = os.stat(output_path)
                if in_stat[stat.ST_MTIME] < out_stat[stat.ST_MTIME]:
                    print("Output file %s newer than input, skipping" % (
                        output_path))
                    continue

            # subprocess.run(["compressonator", "-fd", "BC7",
                                # input_path, output_path])

            subprocess.run(["todds", "-v", "-rp", "-t", "-nm", "-o",
                            input_path, os.path.abspath(output_dir)])

    # Inject textures into the BNTX files using harphield's tools
    print(patch_dirs)
    for nxx_name in patch_dirs:
        # Get all the BNTX files that need to be modified
        bntx_matches = [
            name for name in os.scandir(MRG_TEMP_DIR)
            if name.is_file()
            and name.path.endswith(nxx_name + ".BNTX")
        ]

        # Replace (in-place) this texture in the relevant files
        for match in bntx_matches:
            # replacer_args = []
            # if sys.platform.startswith('win'):
                # replacer_args = ['%s.exe' % REPLACER]
            # else:
            replacer_args = [sys.executable, '%s.py' % REPLACER]

            replacer_args += [match.path, PNG_TEMP_DIR,
                                MRG_TEMP_DIR, '-d', nxx_name]

            print("Replacing textures in pack %s" % nxx_name)
            subprocess.run(replacer_args)

    # Recompress texture files
    print(
        "Performing parallel compression of %d files with %d threads" % (
            len(bntx_to_recompress), multiprocessing.cpu_count()))
    print(bntx_to_recompress)
    with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
        func = partial(compress_nxx, lock=lock)
        p.map(func, bntx_to_recompress)

    # Re-pack the allui
    mrg_component_files = sorted([
        entry.path for entry in os.scandir(MRG_TEMP_DIR)
        if entry.is_file()
        and entry.path.endswith(".dat")
    ])
    print("Merging final output into %s" % OUTPUT_BASENAME)
    # subprocess.run(['mrg_pack', OUTPUT_BASENAME] + mrg_component_files)
    subprocess.run(['mangetsu_tools', '-mrp', '-a', OUTPUT_BASENAME, '-p'] +
                    mrg_component_files)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    manager = multiprocessing.Manager()
    lock = manager.Lock()
    main(lock)
