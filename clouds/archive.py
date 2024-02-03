from pathlib import Path
import os
import os.path
from os.path import commonpath, relpath

from fs.base import FS

import pyminizip

# from progress.bar import Bar, FillingCirclesBar

"""
@url https://github.com/smihica/pyminizip

@see  pyminizip-README.md
"""


def compress_fs_0(fs: FS, zip_path: str, password=None, show_progress=True, compression_level=5):
    """
    Create a zip containing all files within fs with optional password protection.
    :param fs: a PyfileSystem fs
    :param zip_path: path to save output zip to
    :param password: an utf-8 string with password
    :param show_progress: pass False to avoid printing anything to console
    :param compression_level: int in range [1..9]
    :return: None
    """
    files = []
    paths = []

    for step in fs.walk():
        for file_info in step.files:
            files += [fs.getsyspath(file_info.make_path(step.path))]
            paths += [step.path]

    # if show_progress:
    #     bar = Bar('Creating aip archive', max=len(files))
    #     def progress(_): bar.next()
    #     progress(1)
    #     progress(2)
    # else:
    #     progress = lambda *_: None
    # Note ! progress arg breaks the following call.
    # pyminizip.compress_multiple(files, paths, zip_path, password, compression_level, progress)

    pyminizip.compress_multiple(files, paths, zip_path, password, compression_level)


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


def compress_files(filepaths: list[str | Path], zip_path: str, base_path: str | Path = None,
                   password=None, compression_level=5):
    base_path = base_path or commonpath(filepaths)
    paths = [
        str(Path(relpath(p, base_path)).parent)
        for p in filepaths]

    pyminizip.compress_multiple(filepaths, paths, zip_path, password, compression_level)


def uncompress(zip_path: str, target_dir: str | Path = None, password=None,
               keep_relative_paths=True, clear_target_contents=True):
    """
    Create/clean a folder and extract there all files from zip with optional password for decryption.
    :param zip_path: a zip file to extract
    :param target_dir: path to save files to
    :param password: None or an utf-8 string with password
    :param keep_relative_paths: pass False to extract all files to the same dir (ignoring source tree structure)
    :param clear_target_contents: if True (the default), remove everything from target_dir before extracting;
            pass False if unpacking to the same directory.
    :return: None
    """
    if target_dir:
        if clear_target_contents:
            delete_dir_contents(target_dir)
        os.makedirs(target_dir, exist_ok=True)
    pyminizip.uncompress(zip_path, password, target_dir, not keep_relative_paths)


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


def main():
    # try it.

    # src_paths = r"""c:\Temp\11\-ttls\styles.css
    # c:\Temp\11\-ttls\tests\behat\coursesize.feature
    # c:\Temp\11\-ttls\README.md
    # c:\Temp\11\-ttls\db\access.php
    # c:\Temp\11\-ttls\db\caches.php
    # c:\Temp\11\-ttls\course.php
    # c:\Temp\11\-ttls\index.php
    # c:\Temp\11\-ttls\locallib.php
    # c:\Temp\11\-ttls\classes\privacy\provider.php
    # c:\Temp\11\-ttls\classes\task\report_async.php
    # c:\Temp\11\-ttls\lang\en\report_coursesize.php
    # c:\Temp\11\-ttls\settings.php
    # c:\Temp\11\-ttls\db\tasks.php
    # c:\Temp\11\-ttls\db\upgrade.php
    # c:\Temp\11\-ttls\version.php
    # c:\Temp\11\-ttls\tests\fixtures\COPYING.txt
    # c:\Temp\11\-ttls\db\install.xml
    # c:\Temp\11\-ttls\.github\workflows\ci.yml""".splitlines()
    #
    # src_dir = r'c:\Temp\11\-ttls'
    #
    # zip_dirs = [str(Path(p.replace(src_dir, '')).parent) for p in src_paths]
    #
    # def progress(n):
    #     print('done:', n)
    #
    # pyminizip.compress_multiple(src_paths, zip_dirs, r"c:\Temp\11\ttls_pwd.zip", "sol+fasol+vermishel_123", 4, progress)

    if 0:
        from fs import open_fs
        compress_fs(
            open_fs(r'c:\D\OpenServer\domains\moodle.loc\local\filecleanup'),
            '../filecleanup.zip', '123', compression_level=9)

    if 1:
        uncompress('../filecleanup.zip', r'c:\Temp\11\fi-cleanup', '123', )

if __name__ == '__main__':
    main()
    print('done.')
