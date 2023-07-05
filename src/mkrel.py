#!/usr/bin/env python3

from typing import Any, List, Union
import os
import sys
import stat
import argparse
from pathlib import Path

def perror(s: Union[str, Any], e: Union[BaseException, str]):
    if isinstance(e, BaseException):
        if isinstance(e, OSError) and e.strerror is not None:
            strerror = e.strerror
        else:
            strerror = e.__class__.__name__
    else:
        strerror = e
    print(f"{s}{': ' if s else ''}{strerror}", file = sys.stderr)

def get_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description = "Make symlinks relative")

    parser.add_argument("--dry-run", "-n",
        action = "store_true"
    )

    parser.add_argument("--resolve", "-r",
        action = "store_true"
    )

    parser.add_argument("paths",
        metavar = "PATH",
        nargs = "+",
        type = Path,
        help = "paths of symlinks to adjust"
    )

    args = parser.parse_args()

    return args

def make_relative(path: Path, dry_run: bool = True, resolve: bool = False) -> None:
    if not stat.S_ISLNK(path.lstat().st_mode):
        # the lstat here raises FileNotFoundError etc, instead of using path.is_symlink
        raise ValueError

    dest = path.readlink()
    dest = path.parent / dest # if `dest` is relative attach it to `path`'s parent
                              # lest `dest` be relative to cwd
                              # if `dest` is absolute this is a no-op

    # now make the parents of both `dest` and `path` relative to a common location.
    # the easiest way to do this is to make them both relative to the root directory.
    # if requested, resolve any symlink segments via Path.resolve
    if resolve:
        parent_normaliser = Path.resolve
    else:
        parent_normaliser = Path.absolute

    dest_relative = Path(os.path.relpath(
        parent_normaliser(dest.parent),
        parent_normaliser(path.parent)
    )) / dest.name

    print(f"{path} -> {dest_relative}")
    if not dry_run:
        path.unlink()
        path.symlink_to(dest_relative)

def main() -> None:
    args = get_cli_args()

    dry_run: bool = args.dry_run
    resolve: bool = args.resolve
    paths: List[Path] = args.paths

    for path in paths:
        try:
            make_relative(path, dry_run = dry_run, resolve = resolve)
        except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
            perror(path, e)
        except ValueError:
            perror(path, "not a symlink")

if __name__ == "__main__":
    main()
