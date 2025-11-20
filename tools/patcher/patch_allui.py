#!/usr/bin/env python3

import os
import re
import argparse
import subprocess
import multiprocessing
import sys
import stat
import configparser

import rebuild_sysmes
from functools import partial

game = None
allpac_name = None
nxx = None

# Where should we look for the input files
ALLUI_BASENAME = None

# Where to place the updated files
OUTPUT_DIR = None
OUTPUT_BASENAME = None

# Temporary directory for extracted files
MRG_TEMP_DIR = None

# Temporary dir for DDS versions of images to insert
PNG_TEMP_DIR = None

# External texture replacement program
REPLACER = 'bntx_replace/bntx_replace'
SCRIPT_TRANSLATIONS_FOLDER = '../../'

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

def main(lock):

    global game, allpac_name, nxx, ALLUI_BASENAME, OUTPUT_DIR, \
            OUTPUT_BASENAME, MRG_TEMP_DIR, PNG_TEMP_DIR

    parser = argparse.ArgumentParser(description='Patch allui')
    parser.add_argument('game', type=str, help='Short name of game (tsuki_re_ja)')
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read('config.ini')

    game = args.game
    name = '%s_ALLUI' % game.upper()
    update_sysmes = config.getboolean(name, 'update')
    allui_name = config[name]['name']
    sysmes = config[name]['sysmes']
    lang = config[name]['lang']
    nxx = config[name]['nxx']
    additional = config.get(name, 'additional').split()

    ALLUI_BASENAME = '_mrgs/%s/%s' % (game, allui_name)
    OUTPUT_DIR = '_new_mrgs/%s/' % game
    OUTPUT_BASENAME = os.path.join(OUTPUT_DIR, allui_name)
    MRG_TEMP_DIR = '.allui_extracted/%s' % game
    PNG_TEMP_DIR = '.user_interface_dds/%s' % game
    USER_INTERFACE_DIR = '../../images/en_user_interface/%s/' % game

    # Make temp dirs
    for dirname in [MRG_TEMP_DIR, PNG_TEMP_DIR, OUTPUT_DIR]:
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    # Read the MRG entries so that we can scan through for files to replace
    mrg_entries = get_mrg_entries(ALLUI_BASENAME)

    sysmes_index = 0
    for entry in mrg_entries.values():
        if not entry.name:
            continue
        if entry.name.lower() == sysmes.lower():
            sysmes_index = entry.index

    sysmes_name='%s.%08d.%s.dat' % (allui_name, sysmes_index, sysmes)

    if update_sysmes:
        # Extract the entries we care about
        # subprocess.run(['mrg_extract', '-i', str(sysmes_index),
                        # ALLUI_BASENAME, MRG_TEMP_DIR])
        subprocess.run(['mangetsu_tools', '-mre', '-i', str(sysmes_index),
                        '-a', ALLUI_BASENAME, '-p', MRG_TEMP_DIR])

    if not update_sysmes:
        # Unpack allui
        # subprocess.run(['mrg_extract', ALLUI_BASENAME, MRG_TEMP_DIR])
        subprocess.run(['mangetsu_tools', '-mre', '-a', ALLUI_BASENAME,
                        '-p', MRG_TEMP_DIR])

        # Decompress all NXX files
        bntx_to_recompress = []
        dat_files = []
        for entry in os.scandir(MRG_TEMP_DIR):
            if not entry.is_file():
                continue
            if not entry.path.endswith('%s.%s' % (lang, nxx)) and \
                not entry.path.endswith(tuple(additional)):
                continue
            dat_files.append(entry.path)

        for entry in dat_files:
            decompressed_filename = re.sub(nxx, 'BNTX', entry)
            # print("Decompressing %s..." % entry)
            # subprocess.run(['nxx_decompress', entry, decompressed_filename])
            subprocess.run(['mangetsu_tools', '-nxd', '-a', entry,
                            '-p', decompressed_filename])
            bntx_to_recompress.append((decompressed_filename, entry))

        # Convert PNG resources into DDS
        resources_to_inject = []
        patch_dirs = []
        for subdir, dirs, files in os.walk(USER_INTERFACE_DIR):
            for filename in files:
                if not filename.endswith('.png'):
                    continue

                new_filename = re.sub('.png', '.dds', filename)
                input_path = os.path.join(subdir, filename)
                input_nxgz = os.path.split(subdir)[-1]
                output_dir = os.path.join(PNG_TEMP_DIR, input_nxgz)
                output_path = os.path.join(output_dir, new_filename)
                os.makedirs(output_dir, exist_ok=True)
                resources_to_inject.append((input_nxgz, new_filename,
                                            output_path))
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
        for nxgz_name in patch_dirs:
            # Get all the BNTX files that need to be modified
            bntx_matches = [
                name for name in os.scandir(MRG_TEMP_DIR)
                if name.is_file()
                and name.path.endswith(nxgz_name + ".BNTX")
            ]

            # Replace (in-place) this texture in the relevant files
            for match in bntx_matches:
                # replacer_args = []
                # if sys.platform.startswith('win'):
                    # replacer_args = ['%s.exe' % REPLACER]
                # else:
                replacer_args = [sys.executable, '%s.py' % REPLACER]

                replacer_args += [match.path, PNG_TEMP_DIR, MRG_TEMP_DIR,
                                    '-d', nxgz_name]

                print("Replacing textures in pack %s" % nxgz_name)
                subprocess.run(replacer_args)

    # Rebuild the SYSMES strings table (in place)
    rebuild_sysmes.rebuild_sysmes(
        os.path.join(MRG_TEMP_DIR, sysmes_name),
        os.path.join(
            SCRIPT_TRANSLATIONS_FOLDER,
            'system_strings',
            'sysmes_text_%s.en' % game),
        os.path.join(MRG_TEMP_DIR, sysmes_name)
    )

    if not update_sysmes:
        # Recompress texture files
        print("Performing parallel compression of %d files with %d threads" % (
                len(bntx_to_recompress), multiprocessing.cpu_count()))
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
    subprocess.run(
        # ['mrg_pack', OUTPUT_BASENAME, '--names', 'mrg_names_%s.txt' % game] +
        # mrg_component_files)
        ['mangetsu_tools', '-mrp', '-a', OUTPUT_BASENAME, '-n',
            'mrg_names_%s.txt' % game, '-p'] + mrg_component_files)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    manager = multiprocessing.Manager()
    lock = manager.Lock()
    main(lock)
