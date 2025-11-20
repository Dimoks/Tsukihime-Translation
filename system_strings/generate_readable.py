#!/usr/bin/env python3
import argparse
import hashlib
import sys

def main():
    # Parse command-line arguments for input files
    parser = argparse.ArgumentParser(description='Process Japanese and English text files.')
    parser.add_argument('jp_file', type=str, help='Path to the Japanese text file')
    parser.add_argument('en_file', type=str, help='Path to the English text file')
    args = parser.parse_args()

    # Read the two source files
    with open(args.jp_file, 'r', encoding='utf-8') as f:
        jp_text = f.read()
    with open(args.en_file, 'r', encoding='utf-8') as f:
        en_text = f.read()

    # Generate a map of SHA -> EN text
    line_by_sha = {}
    jp_line_by_sha = {}
    for jp, en in zip(jp_text.split("\n"), en_text.split("\n")):
        sha = hashlib.sha1(jp.encode('utf-8')).hexdigest()
        line_by_sha[sha] = en
        jp_line_by_sha[sha] = jp

    print(f"Total lines: {len(line_by_sha)}")

    file=open('sysmes.txt', 'w', encoding='utf-8')

    for sha, en in line_by_sha.items():
        file.write("[sha:%s] {\n" % sha)
        file.write("-- %s\n" % jp_line_by_sha[sha])
        file.write("%s\n" % en)
        file.write("}\n")

    print("System messages saved to sysmes.txt")

#        print("[sha:%s] {" % sha)
#        print("-- %s" % jp_line_by_sha[sha])
#        print("%s" % en)
#        print("}")

    file.close()

if __name__ == '__main__':
    main()
