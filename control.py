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
 2) manually compare and bring changes to local area (rewrite! may be used)
 3) update files in local area (do work)
 4) dump!
 5) go home
 6) repeat steps 1..4 at home

"""
import os
from pathlib import Path

from adict import adict
from fs import open_fs
from fs.base import FS
import fs.mirror

from clouds.gdrive import make_google_drive_fs


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


class RemoteFolder(Folder): pass


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
    print(end='mirroring fs contents...')
    fs.mirror.mirror(src_fs, dst_fs, preserve_time=True)
    print(' done.')


class SharedFolderConfig(DataClass):
    _init_defaults = dict(
        kind='as-is'
    )

    name: str
    local_path: str

    def __init__(self, data: dict = None, **kw):
        super().__init__(data, **kw)
        assert self.name  # must be unique!
        assert self.local_path  # should point to any existing location on local drive
        assert self.kind
        assert self.kind in ('as-is', 'archive')
        self.remote_kind = 'google-drive'
        # ignore_patterns: list
        # follow_gitignore: bool
        env = environment_defaults()
        self.remote_path = fs.path.join(env.remote_root_path, self.name)
        self.staging_path = fs.path.join(env.staging_root_path, self.name)


def environment_defaults():
    return adict(
        remote_root_path=r'Study/dev/shared/',
        staging_root_path=r'c:\Temp\11\staging',
    )


class SharedFolderManager:
    def __init__(self, config: adict = None):
        assert isinstance(config, SharedFolderConfig)
        self.config = config
        self.local = LocalFolder(config.local_path)
        self.staging = LocalFolder(config.staging_path)
        self.remote = GoogleDriveFolder(config.remote_path)

    """
     - fetch (from remote to staging area)
     - rewrite (from staging area to local area, Dangerous! May cause data loss!)
        - pull = fetch + rewrite
     - stage (from local area to staging area)
     - push (from staging area to remote)
         - dump = stage + push"""

    def fetch(self):
        print('fetch!')
        mirror_fs_contents(self.remote.fs, self.staging.fs)

    def rewrite(self):
        print('rewrite!')
        # are you sure...?
        mirror_fs_contents(self.staging.fs, self.local.fs)

    def pull(self):
        # are you sure...?
        self.fetch()
        self.rewrite()

    def stage(self):
        print('stage!')
        mirror_fs_contents(self.local.fs, self.staging.fs)

    def push(self):
        print('push!')
        mirror_fs_contents(self.staging.fs, self.remote.fs)

    def dump(self):
        self.stage()
        self.push()


def main():
    # cnf = SharedFolderConfig(
    #     name='coursz',
    #     local_path=r'c:\Temp\11\cou-siz',
    # )
    # man = SharedFolderManager(cnf)
    # man.dump()

    cnf = SharedFolderConfig(
        name='coursz',
        local_path=r'c:\Temp\11\cou-siz_2',
    )

    man = SharedFolderManager(cnf)
    man.pull()


if __name__ == '__main__':
    main()
