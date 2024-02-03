"""
High-level operations (using some terms of version control systems, e.g. Git):
 * local area : working tree, live files.
 * staging area : temporary area, mirroring remote area
 * remote area : cloud content.


 - fetch (from remote to staging area)
 - rewrite (from staging area to local area, Dangerous! May cause data loss!)
    - pull = fetch + rewrite
 - stage (from local area to staging area)
 - push (from staging area to remote)
     - dump = stage + push

Normal everyday workflow:
 0) come to office
 1) fetch!
 2) manually compare and bring changes to local area (rewrite! may be used if no local changes discovered)
 3) update files in local area (do work)
 4) dump!
 5) go home
 6) repeat steps 1..4 at home

"""

from collections import ChainMap  # @see №5 in https://favtutor.com/blogs/merge-dictionaries-python
import os
from pathlib import Path

from adict import adict
from fs import open_fs
from fs.base import FS
from fs.copy import copy_file
import fs.errors
import fs.mirror
import yaml

from clouds.archive import compress_fs, uncompress, compress_files
from clouds.gdrive import make_google_drive_fs
from helpers import duration_report


class Folder:
    def __init__(self):
        # fs cache
        self._fs = None

    @property
    def fs(self):
        if not self._fs:
            self._fs = self.get_fs()
        return self._fs

    def get_fs(self) -> FS:
        # abstract method.
        raise NotImplementedError()


class LocalFolder(Folder):
    def __init__(self, root_path: str | Path):
        super().__init__()
        self.root_path = root_path

    def get_fs(self):
        os.makedirs(self.root_path, exist_ok=True)
        # Path(self.root_path).mkdir(parents=True, exist_ok=True)
        return open_fs(self.root_path)


class RemoteFolder(Folder):
    pass


class GoogleDriveFolder(RemoteFolder):
    def __init__(self, drive_path: str | Path):
        super().__init__()
        self.drive_path = drive_path

    def get_fs(self):
        return make_google_drive_fs(self.drive_path)


class DataClass(adict):
    def __init__(self, data: dict = None, **kw):
        params = adict(self._init_defaults)
        params.update(data or {})
        params.update(kw)
        super().__init__(params)


def mirror_fs_contents(src_fs: FS, dst_fs: FS, target_dir: str = None):
    """target_dir: relative to root of dst_fs (optional)."""
    if target_dir:
        dst_fs.makedirs(target_dir, recreate=True)
        dst_fs = dst_fs.opendir(target_dir)
    # if clear_target_contents:
    #     src_fs.removetree('/')  # this keeps directory itself
    print(end=' mirroring fs contents...')
    fs.mirror.mirror(src_fs, dst_fs, preserve_time=True)
    print(' done.')


class SharedFolderConfig(DataClass):
    # mandatory:
    name: str
    local_path: str
    # optional:
    type: str
    remote_kind: str
    staging_path: str
    # future options:
    # include_patterns: list
    # ignore_patterns: list
    # follow_gitignore: bool

    _init_defaults = dict(
        type='as-is',
        remote_kind='google-drive',
    )

    def __init__(self, data: adict = None, **kw):
        super().__init__(data, **kw)
        assert self.name  # must be unique!
        assert self.local_path  # should point to any existing location on local drive
        assert self.type
        assert self.type in ('as-is', 'archive')
        ### self.remote_kind = 'google-drive'
        # ignore_patterns: list
        # follow_gitignore: bool
        if 'remote_path' not in self:
            self.remote_path = fs.path.join(
                self.remote_root_path,
                self.remote_sub_path,
                self.name)
        if 'staging_path' not in self:
            self.staging_path = fs.path.join(
                self.staging_root_path,
                self.staging_sub_path,
                self.name)

    def password_for_archive(self):
        return self.salt + '~' + self.name[0].lower()


def load_shared_folders_configuration(config_file: str = './config/shared_folders.yml') -> list[SharedFolderConfig]:
    with open(config_file, encoding='utf-8') as f:
        data = yaml.safe_load(f)

    assert 'defaults' in data
    assert 'shared_folders' in data

    defaults = data['defaults']
    shared_folders = data['shared_folders']

    return [
        SharedFolderConfig(adict(
            name=name,
            **ChainMap(data, defaults)  # merge dicts, first one has priority
        ))
        for name, data in shared_folders.items()
    ]


class SharedFolderManager:
    """
     - fetch (from remote to staging area)
     - rewrite (from staging area to local area, dangerous! May cause data loss!)
        - pull = fetch + rewrite
     - stage (from local area to staging area)
     - push (from staging area to remote)
         - dump = stage + push"""

    def __init__(self, config: adict = None):
        assert isinstance(config, SharedFolderConfig)
        self.config = config
        self.local = LocalFolder(config.local_path)
        self.staging = LocalFolder(config.staging_path)
        self.remote = GoogleDriveFolder(config.remote_path)

    def fetch(self):
        with duration_report('fetch!'):
            mirror_fs_contents(self.remote.fs, self.staging.fs)

    def rewrite(self):
        with duration_report('rewrite!'):
            # are you sure...?
            mirror_fs_contents(self.staging.fs, self.local.fs)

    def pull(self):
        # are you sure...?
        self.fetch()
        self.rewrite()

    def stage(self):
        with duration_report('stage!'):
            mirror_fs_contents(self.local.fs, self.staging.fs)

    def push(self):
        with duration_report('push!'):
            mirror_fs_contents(self.staging.fs, self.remote.fs)

    def dump(self):
        self.stage()
        self.push()


class ArchivingSharedFolderManager(SharedFolderManager):
    archive_filename = '/folder.zip'  # hardcoded so far
    hashed_filename_template = '%s.dat'

    def __init__(self, config: adict = None):
        super().__init__(config)
        self.temp = LocalFolder(fs.path.join(config.temp_root_path, config.name))

    def compress_with_hash(self):
        """As part of push!: archive staging --> temp"""
        src_fs, dst_fs = self.staging.fs, self.temp.fs
        hash_alg_name = 'md5'  # hardcoded so far

        # # clear dir first ??
        # dst_fs.removetree('/')

        # 1. (re-)create archive without encryption
        plain_archive_filepath = dst_fs.getsyspath(self.archive_filename)
        compress_fs(src_fs, plain_archive_filepath)

        # calc archive hash
        file_hash = dst_fs.hash(self.archive_filename, hash_alg_name)

        # include the hash in the name of file to send
        new_filename = self.hashed_filename_template % file_hash

        if dst_fs.exists(new_filename):
            # archive with the same hash is already present, do not overwrite it.
            return new_filename

        # clear old versions first
        file_pattern = self.hashed_file_pattern()
        for path in dst_fs.walk.files(filter=[file_pattern]):
            dst_fs.remove(path)

        # 2. compress archive again, with encryption
        compress_files([plain_archive_filepath],
                       dst_fs.getsyspath(new_filename),
                       base_path=dst_fs.getsyspath('/'),
                       password=self.config.password_for_archive(),
                       compression_level=1)

        return new_filename

    def hashed_file_pattern(self):
        return self.hashed_filename_template % '*'

    def uncompress_hashed_file(self, filepath=None):
        """As part of fetch!: extract temp --> staging"""
        src_fs, dst_fs = self.temp.fs, self.staging.fs
        # clear dir (done by uncompress() internally)
        # dst_fs.removetree('/')

        if not filepath:
            filepath = self.find_hashed_file(src_fs)

        archive_syspath = src_fs.getsyspath(filepath)

        # 1. extract encrypted archive
        uncompress(
            archive_syspath,
            src_fs.getsyspath('/'),
            self.config.password_for_archive(),
            clear_target_contents=False  # required when unpacking to the same dir
        )

        assert src_fs.exists(self.archive_filename)

        # 2. extract plain archive containing user files
        uncompress(
            src_fs.getsyspath(self.archive_filename),
            dst_fs.getsyspath('/'))

        # # clear temp dir ?? No, keep cached download.
        # src_fs.removetree('/'))

    def find_hashed_file(self, src_fs: FS):
        # assume that exactly one file present
        file_pattern = self.hashed_file_pattern()
        files = list(src_fs.walk.files(filter=[file_pattern]))
        assert files
        assert len(files) == 1, ('Only one file expected, found:', files)
        return files[0]

    def mirror_hashed_file(self, src_fs: FS, dst_fs: FS, filepath: str = None) -> str:
        print(end=' mirroring file...')
        if not filepath:
            filepath = self.find_hashed_file(src_fs)

        if dst_fs.exists(filepath):
            # no point in copying the file again
            print(' already up-to-date.')
            return filepath

        # clear old versions first
        file_pattern = self.hashed_file_pattern()
        for path in dst_fs.walk.files(filter=[file_pattern]):
            dst_fs.remove(path)

        print(end=' transferring...')
        copy_file(src_fs, filepath, dst_fs, filepath, True)
        print(' done.')
        return filepath

    def fetch(self):
        with duration_report('fetch!'):
            filepath = self.mirror_hashed_file(self.remote.fs, self.temp.fs)
            self.uncompress_hashed_file(filepath)

    def push(self):
        with duration_report('push!'):
            target_filename = self.compress_with_hash()
            self.mirror_hashed_file(self.temp.fs, self.remote.fs, target_filename)


def get_shared_folder_manager_by_type(config_type: str) -> type:
    class_ = {
        'as-is': SharedFolderManager,
        'archive': ArchivingSharedFolderManager,

        # TODO: register new types here.
    }.get(config_type)
    assert class_, f'Unknown shared folder type: `{config_type}`.'
    return class_


def get_shared_folders_managers(config_file: str = './config/shared_folders.yml') -> list[SharedFolderManager]:
    configs = load_shared_folders_configuration(config_file)
    return [
        get_shared_folder_manager_by_type(cnf.type)(cnf)  # make an instance
        for cnf in configs
    ]


def main():
    # cnf = SharedFolderConfig(
    #     name='coursz',
    #     local_path=r'c:\Temp\11\cou-siz',
    # )
    # man = SharedFolderManager(cnf)
    # man.dump()

    # cnf = SharedFolderConfig(
    #     name='coursz',
    #     local_path=r'c:\Temp\11\cou-siz_2',
    # )
    #
    # man = SharedFolderManager(cnf)
    # # man.pull()
    # man.fetch()

    # print(load_shared_folders_configuration())
    # print(get_shared_folders_managers())

    mgrs = get_shared_folders_managers()
    mgrs[0].stage()
    mgrs[0].push()
    # mgrs[0].pull()  # !!
    ...


if __name__ == '__main__':
    main()
