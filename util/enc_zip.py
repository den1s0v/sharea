from pathlib import Path
import os
import os.path
from os.path import commonpath, relpath

from fs.base import FS

import pyzipper


def compress_fs(fs: FS, zip_path: str, password=None, compression_level=5):
    """
    Create a zip containing all files within fs with optional password protection.
    :param fs: a PyfileSystem fs
    :param zip_path: path to save output zip to
    :param password: an utf-8 string with password
    :param compression_level: int in range [1..9]
    :return: None
    """
    files = [fs.getsyspath(path) for path in fs.walk.files()]
    base_path = fs.getsyspath('/')

    compress_files(files, zip_path, base_path, password, compression_level)


def compress_files(filepaths: list[str | Path],
                   zip_path: str,
                   base_path: str | Path = None,
                   password: str = None, compression_level=5):
    base_path = Path(base_path or commonpath(filepaths))
    if base_path.is_file():
        base_path = base_path.parent

    with pyzipper.AESZipFile(zip_path,
                             'w',
                             # compression=pyzipper.ZIP_LZMA,
                             compression=pyzipper.ZIP_DEFLATED,
                             compresslevel=compression_level,
                             encryption=pyzipper.WZ_AES if password else None
                             ) as zf:
        if password:
            zf.setpassword(password.encode())

        for p in filepaths:
            zip_path = relpath(p, base_path)
            ### print('zip_path', zip_path)
            zf.write(p, zip_path)


def uncompress(zip_path: str, target_dir: str | Path = None, password=None,
               keep_relative_paths=True, clear_target_contents=False):
    """
    Create/clean a folder (optionally) and extract there all files from zip with optional password for decryption.
    :param zip_path: a zip file to extract
    :param target_dir: path to save files to
    :param password: None or an utf-8 string with password
    :param keep_relative_paths: pass False to extract all files to the same dir (ignoring source tree structure)
    :param clear_target_contents: if True (the default), remove everything from target_dir before extracting;
            pass False if unpacking to the same directory.
    :return: None
    """
    if target_dir is not None:
        assert target_dir, target_dir
        if clear_target_contents:
            delete_dir_contents(target_dir)
        os.makedirs(target_dir, exist_ok=True)

    with pyzipper.AESZipFile(zip_path) as zf:
        if password:
            zf.setpassword(password.encode())
        zf.extractall(target_dir)

        # >>> print(zf.filelist)
        # [<AESZipInfo filename='./file.txt' compress_type=deflate file_size=11908 compress_size=11610>, ...]
        # print(zf.namelist())  # ['./file.txt', ...]
        # for zip_path in zf.namelist():
        #     file_bytes = zf.read(zip_path)


def delete_dir_contents(dir_path: str | Path):
    """@see https://stackoverflow.com/a/56151260/12824563"""
    from shutil import rmtree
    p = Path(dir_path)
    if p.exists():
        for path in p.iterdir():
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                rmtree(path)
