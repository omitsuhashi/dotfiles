#!/usr/bin/env python3

import argparse
import os

import pyperclip


def copy_files_to_clipboard(root_dirs, extensions, file_paths=None, exclude_dirs=None, exclude_files=None, exclude_ext=None):
    combined_content = ''
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_files is None:
        exclude_files = []
    if exclude_ext is None:
        exclude_ext = []
    if isinstance(root_dirs, str):
        root_dirs = [root_dirs]
    if not root_dirs:
        root_dirs = ['.']
        if root_dirs == ['.'] and file_paths:
            root_dirs = []

    if file_paths is None:
        file_paths = []
    if isinstance(file_paths, str):
        file_paths = [file_paths]

    for root_dir in root_dirs:
        for dirpath, dir_names, filenames in os.walk(root_dir):
            dir_names[:] = [d for d in dir_names if d not in exclude_dirs]
            for filename in filenames:
                if filename in exclude_files:
                    continue
                if exclude_ext and filename.endswith(tuple(exclude_ext)):
                    continue
                if not extensions or filename.endswith(tuple(extensions)):
                    filepath = os.path.join(dirpath, filename)
                    with open(filepath, 'r', encoding='utf-8', errors='replace') as file:
                        file_content = file.read()
                        comment_command = '#' if filepath.endswith('.py') else '//'
                        combined_content += f'{comment_command} filepath: {filepath}\n{file_content}\n\n'
    for filepath in file_paths:
        if os.path.basename(filepath) in exclude_files:
            continue
        if exclude_ext and filepath.endswith(tuple(exclude_ext)):
            continue
        if extensions and not filepath.endswith(tuple(extensions)):
            continue
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as file:
                file_content = file.read()
                comment_command = '#' if filepath.endswith('.py') else '//'
                combined_content += f'{comment_command} filepath: {filepath}\n{file_content}\n\n'
        except FileNotFoundError:
            continue
    pyperclip.copy(combined_content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Copy files content to clipboard')
    parser.add_argument(
        '--dir',
        nargs='*',
        default=[],
        help='Target directory paths (optional). If omitted, the current directory is used.',
    )
    parser.add_argument(
        '--ext',
        nargs='*',
        default=[],
        help='Target file extensions (optional). If omitted, all extensions are included.',
    )
    parser.add_argument('--file', nargs='*', default=[], help='Specific file paths to include (multiple allowed).')
    parser.add_argument('--exclude-dir', nargs='*', default=[], help='Directories to exclude (multiple allowed).')
    parser.add_argument('--exclude-file', nargs='*', default=[], help='Files to exclude (multiple allowed).')
    parser.add_argument('--exclude-ext', nargs='*', default=[], help='File extensions to exclude (multiple allowed).')

    args = parser.parse_args()
    copy_files_to_clipboard(args.dir, args.ext, args.file, args.exclude_dir, args.exclude_file, args.exclude_ext)
