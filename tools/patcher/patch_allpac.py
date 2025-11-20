#!/usr/bin/env python3

import os
import re
import subprocess
import hashlib
import multiprocessing
import sys
import stat
import configparser
import argparse
import shutil
from functools import partial

game = None
allpac_name = None
allpac_path = None
nxx = None

# This script is targeted against the v1.0.2 version of allpac.
# Other file versions may not have the same number of entries
EXPECTED_ALLPAC_MD5 = ''

# Where should we look for the input files
ALLPAC_BASENAME = None

# Where to place the updated files
OUTPUT_DIR = None
OUTPUT_BASENAME = None

# Temporary directory for extracted files
MRG_TEMP_DIR = None

# Temporary dir for DDS versions of images to insert
PNG_TEMP_DIR = None

# Source dir with game CG images to replace
GAMECG_TEXTURES_DIR = None
GAMECG_RAW_DIR = None

# External texture replacement program
REPLACER = 'bntx_replace/bntx_replace'


class MrgEntry:
    def __init__(self, index, offset, size, uncompressed_size, name=None):
        self.index = int(index)
        self.offset = int(offset, 16)
        self.size = int(size, 16)
        self.uncompressed_size = int(uncompressed_size, 16)
        self.name = name.decode('utf-8')

    def __repr__(self):
        return "%d: @0x%08x + 0x%08x '%s'" % (
            self.index,
            self.offset,
            self.size,
            self.name,
        )


def get_mrg_entries(basename):
    # raw_csv = subprocess.check_output(['mrg_info', '--csv', basename])
    raw_csv = subprocess.check_output(['mangetsu_tools', '--csv',
                                        '-a', basename])
    ret = {}
    for row in raw_csv.split(b'\n'):
        split = row.rstrip().split(b',')
        if len(split) == 1:
            break
        ret[split[0]] = MrgEntry(*split)
    return ret


def get_format(filename):
    name, extension = os.path.splitext(os.path.basename(filename))

    last_dot_index = name.rfind('.')

    if last_dot_index > 0:
        part_between = name[last_dot_index + 1:]
        if part_between.lower() == 'nxgz':
            return 'nxgx'
        elif part_between.lower() == 'nxz':
            return 'nxcx'
        else:
            return None
    else:
        return None


def compress_nxx(args, lock):
    decompressed_file = args[0]
    compressed_file = args[1]
    format = get_format(compressed_file)
    if format:
        # command = '%s_compress' % format
        command = '-%s' % format
        # print("Compressing %s..." % compressed_file)
        # subprocess.run([command, decompressed_file, compressed_file])
        result = subprocess.run(['mangetsu_tools', command, '-p',
                                    decompressed_file, '-a', compressed_file],
                                    capture_output=True, text=True)

        with lock:
            if result.stdout:
                print(result.stdout, end='')
            if result.stderr:
                print(result.stderr, file=sys.stderr, end='')
    else:
        print("Unknown format of file %s" % compressed_file)


def decompress_nxx(args, lock):
    compressed_file = args[0]
    decompressed_file = args[1]
    # print("Decompressing %s..." % compressed_file)
    # subprocess.run(['nxx_decompress', compressed_file, decompressed_file])
    result = subprocess.run(['mangetsu_tools', '-nxd', '-a', compressed_file,
                                '-p', decompressed_file],
                                capture_output=True, text=True)

    with lock:
        if result.stdout:
            print(result.stdout, end='')
        if result.stderr:
            print(result.stderr, file=sys.stderr, end='')


def md5_file(filename):
    with open(filename, 'rb') as f:
        context = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            context.update(chunk)
            chunk = f.read(8192)
        return context.hexdigest()


def get_images_to_insert():
    ret = {}
    for entry in os.scandir(PNG_TEMP_DIR):
        if entry.is_file():
            ret[entry.name] = entry.path
    return ret


def replace_btnx(allpac_name, MRG_TEMP_DIR, args):
    index, dds = args
    # Get the path to the extracted texture file
    candidate_files = [
        f.path for f in os.scandir(MRG_TEMP_DIR)
        if f.name.startswith("%s.%08d" % (allpac_name, index))
        and f.name.endswith(".BNTX")
    ]
    assert len(candidate_files) == 1, "Failed to replacement idx %s" % index

    # Invoke the external texture replacer
    source_bntx = candidate_files[0]

    # replacer_args = []
    # if sys.platform.startswith('win'):
        # replacer_args = ['%s.exe' % REPLACER]
    # else:
    replacer_args = [sys.executable, '%s.py' % REPLACER]

    replacer_args += [source_bntx, dds, MRG_TEMP_DIR]

    # print("Replacing texture in pack %s" % (source_bntx))
    subprocess.run(replacer_args)


def main(lock):

    global game, allpac_name, allpac_path, nxx, ALLPAC_BASENAME, \
            OUTPUT_DIR, OUTPUT_BASENAME, MRG_TEMP_DIR, PNG_TEMP_DIR, \
            GAMECG_TEXTURES_DIR, GAMECG_RAW_DIR

    parser = argparse.ArgumentParser(description='Patch archive from the allpac archive set.')
    parser.add_argument('game', type=str, help='Short name of game (tsuki_re_ja)')
    parser.add_argument('name', type=str, help='Name of pac (allpac)')
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read('config.ini')

    name = args.name
    game = args.game
    allpac = '%s_%s' % (game, name)
    allpac_name = config.get(allpac.upper(), 'name')
    allpac_path = config.get(allpac.upper(), 'path')
    nxx = config.get(allpac.upper(), 'nxx').split()

    # Where should we look for the input files
    ALLPAC_BASENAME = '_mrgs/%s/%s' % (game, allpac_name)
    if allpac_path:
        ALLPAC_BASENAME = os.path.join(allpac_path, allpac_name)

    # Where to place the updated files
    OUTPUT_DIR = '_new_mrgs/%s/' % game
    OUTPUT_BASENAME = os.path.join(OUTPUT_DIR, allpac_name)

    # Temporary directory for extracted files
    MRG_TEMP_DIR = '.pacs_extracted/%s/%s' % (game, allpac_name)

    # Temporary dir for DDS versions of images to insert
    PNG_TEMP_DIR = '.gamecg_dds/%s/%s' % (game, allpac_name)

    # Source dir with game CG images to replace
    GAMECG_TEXTURES_DIR = '../../images/en_gamecg/%s/%s_textures' % (game, allpac_name)
    GAMECG_RAW_DIR = '../../images/en_gamecg/%s/%s_raw' % (game, allpac_name)

    # Test that input files exist and are of the expected version
    if False:
        print("Checking integrity of input %s..." % allpac_name)
        input_checksum = md5_file(ALLPAC_BASENAME + ".mrg")
        if input_checksum != EXPECTED_ALLPAC_MD5:
            print(
                "Input %s has unexpected MD5sum '%s' - "
                "expected a version 1.0.2 %s with MD5sum '%s'" % (
                    allpac_name, allpac_name,
                    input_checksum,
                    EXPECTED_ALLPAC_MD5
                )
            )

    # Make temp dirs
    for dirname in [MRG_TEMP_DIR, PNG_TEMP_DIR, OUTPUT_DIR]:
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    # Convert PNG resources into DDS
    for subdir, dirs, files in os.walk(GAMECG_TEXTURES_DIR):
        for filename in files:
            if not filename.endswith('.png'):
                continue

            # Source file
            input_path = os.path.join(subdir, filename)

            # New file name fragment
            new_filename = re.sub('.png', '.dds', filename)

            # Preserve path fragment from cg dir in output
            output_fragment = subdir[len(GAMECG_TEXTURES_DIR)+1:]
            output_dir = os.path.join(PNG_TEMP_DIR, output_fragment)
            output_path = os.path.join(output_dir, new_filename)
            os.makedirs(output_dir, exist_ok=True)

            # If the target is newer than the source, skip
            if os.path.exists(output_path):
                in_stat = os.stat(input_path)
                out_stat = os.stat(output_path)
                if in_stat[stat.ST_MTIME] < out_stat[stat.ST_MTIME]:
                    print("Output %s newer than input, skipping" % output_path)
                    continue

            # subprocess.run(["compressonator", "-fd", "BC7",
                                # input_path, output_path])

            subprocess.run(["todds", "-v", "-rp", "-t", "-nm", "-o",
                            input_path, os.path.abspath(output_dir)])

    # Read the MRG entries so that we can scan through for files to replace
    mrg_entries = get_mrg_entries(ALLPAC_BASENAME)

    # Fetch the list of image names that we want to substitute
    images_to_insert = get_images_to_insert()

    # Get the list of mrg indices we want to actually extract
    extract_entries = {}
    image_basenames = set([n.split('.')[0] for n in images_to_insert.keys()])
    for entry in mrg_entries.values():
        if not entry.name:
            continue
        entry_basename = entry.name.split('.')[0].lower()
        if entry_basename in image_basenames:
            extract_entries[entry.index] = entry

    # Extract the entries we care about
    for idx in extract_entries.keys():
        # subprocess.run([
            # 'mrg_extract', '-i', str(idx), ALLPAC_BASENAME, MRG_TEMP_DIR])
        subprocess.run(['mangetsu_tools', '-mre', '-i', str(idx),
                        '-a', ALLPAC_BASENAME, '-p', MRG_TEMP_DIR])

    # Decompress
    bntx_to_decompress = []
    bntx_to_recompress = []
    for entry in os.scandir(MRG_TEMP_DIR):
        if not entry.is_file():
            continue
        if not entry.path.endswith(tuple(nxx)):
            continue
        decompressed_filename = re.sub('NX.?Z.dat', 'BNTX', entry.path)
        bntx_to_decompress.append((entry.path, decompressed_filename))
        bntx_to_recompress.append((decompressed_filename, entry.path))

    print("Performing parallel decompression of %d files with %d threads" % (
            len(bntx_to_recompress), multiprocessing.cpu_count()))
    with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
        func = partial(decompress_nxx, lock=lock)
        p.map(func, bntx_to_decompress)

    # For each of the top level (non-thumbnail) images, find the extracted
    # files that match and pick the larger.
    replacement_pairs = {}
    for dds_file in os.scandir(PNG_TEMP_DIR):
        if not dds_file.is_file() or not dds_file.name.endswith(".dds"):
            continue

        dds_basename = dds_file.name.split('.')[0]
        candidate_entries = []
        for entry in extract_entries.values():
            if not entry.name.endswith(('Z', 'z')):
                continue
            entry_basename = entry.name.split('.')[0].lower()
            if dds_basename == entry_basename:
                candidate_entries.append(entry)

        if not candidate_entries:
            print("Failed to find replace candidates for %s" % dds_basename)
            return

        # If there's only one candidate, directly replacement
        if len(candidate_entries) == 1:
            replacement_pairs[candidate_entries[0].index] = dds_file.path
            continue

        # If there are 2 candidates, the smaller is a thumbnail
        if len(candidate_entries) == 2:
            # Sort entries largest -> smallest
            candidate_entries.sort(key=lambda x: x.size, reverse=True)
            # Larger entry gets this full size image
            replacement_pairs[candidate_entries[0].index] = dds_file.path
            # Smaller entry gets the thumbnail
            thumb_dds = os.path.join(PNG_TEMP_DIR, 'thumb', dds_file.name)
            replacement_pairs[candidate_entries[1].index] = thumb_dds
            continue

        # If there are more than 2 candidates... something is up
        print("Unhandled number of candidates for %s: %s" % (
            dds_basename, candidate_entries))
        return

    with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
        p.starmap(replace_btnx, [(allpac_name, MRG_TEMP_DIR, item)
                                for item in replacement_pairs.items()])

    # Recompress texture files
    print("Performing parallel compression "
            "of %d files with %d threads" % (
            len(bntx_to_recompress), multiprocessing.cpu_count()))

    with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
        func = partial(compress_nxx, lock=lock)
        p.map(func, bntx_to_recompress)

    # Regnerate the mrg file with the new texture packs
    # mrg_replace_args = ['mrg_replace', ALLPAC_BASENAME, OUTPUT_BASENAME]
    mrg_replace_args = ['mangetsu_tools', '-mrgr', '-t', ALLPAC_BASENAME,
                        '-a', OUTPUT_BASENAME]
    indexes = []
    paths = []
    for idx, entry in extract_entries.items():
        candidate_files = [
            f.path for f in os.scandir(MRG_TEMP_DIR)
            if f.name.startswith("%s.%08d" % (allpac_name, idx))
            and f.name.endswith(".dat")
        ]
        assert len(candidate_files) == 1, "Failed to find injection candidate"
        # replace_args = [
            # '-i%d' % idx,
            # candidate_files[0]
        # ]
        # mrg_replace_args += replace_args
        indexes.append(str(idx))
        paths.append(candidate_files[0])

    mrg_replace_args += ['-i'] + indexes + ['-p'] + paths

    # Also replace any raw files
    raw_files = {}
    for entry in os.scandir(GAMECG_RAW_DIR):
        if entry.is_file():
            raw_files[entry.name] = entry.path

    for entry in mrg_entries.values():
        if entry.name in raw_files:
            print("Replacing raw file %s" % entry.name)
            # replace_args = [
                # '-i%d' % entry.index, raw_files[entry.name]
            # ]
            # mrg_replace_args += replace_args
            shutil.copy2(os.path.join(GAMECG_RAW_DIR, entry.name),
                            os.path.join(MRG_TEMP_DIR,
                            "%s.%08d.%s.dat" % (allpac_name, entry.index, entry.name)))

    command_len = sum(len(s) for s in mrg_replace_args) + len(mrg_replace_args)

    if command_len >= 8191:
        paths_file = 'path_file.txt'
        with open(paths_file, 'w', encoding = 'utf-8', newline = '\n') as f:
            f.write("\n".join(paths))
        print("Paths to files saved to %s" % paths_file)
        mrg_replace_args = ['mangetsu_tools', '-mrgr', '-t', ALLPAC_BASENAME,
                            '-a', OUTPUT_BASENAME, '-n', paths_file,
                            '-i'] + indexes

    command_len = sum(len(s) for s in mrg_replace_args) + len(mrg_replace_args)
    print("Packing new MRG...")
    print("Length of command %d with %d files." % (command_len, len(indexes)))
    # print(mrg_replace_args)
    subprocess.run(mrg_replace_args)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    manager = multiprocessing.Manager()
    lock = manager.Lock()
    main(lock)
