#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

import os
import sys
import subprocess

VERSION_MIN = (1, 6, 0)
VERSION_MAX_RECOMMENDED = (1, 6, 0)
AUTOPEP8_FORMAT_CMD = "autopep8"

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
os.chdir(BASE_DIR)


extensions = (
    ".py",
)

ignore_files = {
    "release/scripts/modules/rna_manual_reference.py",  # Large generated file, don't format.
}


def compute_paths(paths, use_default_paths):
    # Optionally pass in files to operate on.
    if use_default_paths:
        paths = (
            "build_files",
            "release",
            "doc",
            "source",
            "tests",
        )

    if os.sep != "/":
        paths = [f.replace("/", os.sep) for f in paths]
    return paths


def source_files_from_git(paths, changed_only):
    if changed_only:
        cmd = ("git", "diff", "HEAD", "--name-only", "-z", "--", *paths)
    else:
        cmd = ("git", "ls-tree", "-r", "HEAD", *paths, "--name-only", "-z")
    files = subprocess.check_output(cmd).split(b'\0')
    return [f.decode('ascii') for f in files]


def autopep8_ensure_version():
    global AUTOPEP8_FORMAT_CMD
    autopep8_format_cmd = None
    version_output = None
    # TODO: search paths.
    for _ in (None,):
        autopep8_format_cmd = "autopep8"
        try:
            version_output = subprocess.check_output((autopep8_format_cmd, "--version")).decode('utf-8')
        except FileNotFoundError as e:
            continue
        AUTOPEP8_FORMAT_CMD = autopep8_format_cmd
        break
    version = next(iter(v for v in version_output.split() if v[0].isdigit()), None)
    if version is not None:
        version = version.split("-")[0]
        version = tuple(int(n) for n in version.split("."))
    if version is not None:
        print("Using %s (%d.%d.%d)..." % (AUTOPEP8_FORMAT_CMD, version[0], version[1], version[2]))
    return version


def autopep8_format(files):
    cmd = [AUTOPEP8_FORMAT_CMD, "--recursive", "--in-place", "--jobs=0"] + files
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT)


def argparse_create():
    import argparse

    # When --help or no args are given, print this help
    usage_text = "Format source code"
    epilog = "This script runs autopep8 on multiple files/directories"
    parser = argparse.ArgumentParser(description=usage_text, epilog=epilog)
    parser.add_argument(
        "--changed-only",
        dest="changed_only",
        default=False,
        action='store_true',
        help=(
            "Format only edited files, including the staged ones. "
            "Using this with \"paths\" will pick the edited files lying on those paths. "
            "(default=False)"
        ),
        required=False,
    )
    parser.add_argument(
        "paths",
        nargs=argparse.REMAINDER,
        help="All trailing arguments are treated as paths."
    )

    return parser


def main():
    version = autopep8_ensure_version()
    if version is None:
        print("Unable to detect 'autopep8 --version'")
        sys.exit(1)
    if version < VERSION_MIN:
        print("Version of autopep8 is too old:", version, "<", VERSION_MIN)
        sys.exit(1)
    if version > VERSION_MAX_RECOMMENDED:
        print(
            "WARNING: Version of autopep8 is too recent:",
            version, ">", VERSION_MAX_RECOMMENDED,
        )
        print(
            "You may want to install autopep8-%d.%d, "
            "or use the precompiled libs repository." %
            (VERSION_MAX_RECOMMENDED[0], VERSION_MAX_RECOMMENDED[1]),
        )

    args = argparse_create().parse_args()

    use_default_paths = not (bool(args.paths) or bool(args.changed_only))

    paths = compute_paths(args.paths, use_default_paths)
    print("Operating on:" + (" (%d changed paths)" % len(paths) if args.changed_only else ""))
    for p in paths:
        print(" ", p)

    files = [
        f for f in source_files_from_git(paths, args.changed_only)
        if f.endswith(extensions)
        if f not in ignore_files
    ]

    autopep8_format(files)


if __name__ == "__main__":
    main()
