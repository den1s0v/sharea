from contextlib import contextmanager
import os.path
from pathlib import Path

import fs.path
from fs.googledrivefs import GoogleDriveFS
from fs import open_fs
import fs.mirror

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]  # all rights on my drive


def google_drive_credentials():
    """Obtain credentials for Google Drive.
      (full access rights to enable read & write operations, see SCOPES constant).

      @see https://developers.google.com/drive/api/quickstart/python
    """
    token_json_path = str(Path(__file__).parent.joinpath("token.json"))
    credentials_json_path = str(Path(__file__).parent.joinpath("credentials.json"))

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_json_path):
        creds = Credentials.from_authorized_user_file(token_json_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_json_path, SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_json_path, "w") as token:
            token.write(creds.to_json())

    return creds


class TempFileRemover:
    """
    class designed to:
    1) delete all files from previous session (stored in a file) on create
    2) gather paths of files to remove via cals to add() method for removal in next session.
    """

    def __init__(self):
        self.store_file = Path('./files_to_remove.txt')
        self.files = set()
        self.load()
        self.remove_all()

    def add(self, fullpath: str):
        if fullpath in self.files:
            return
        self.files.add(fullpath)
        self.save()

    def remove_all(self):
        count_ok = 0
        for fullpath in list(self.files):
            try:
                Path(fullpath).unlink(True)
                self.files.remove(fullpath)
                count_ok += 1
            except Exception as e:
                print('Error removing temp file:', repr(e))
                pass

        self.save()
        if count_ok > 0:
            print('Successfully removed {} temp file(s).'.format(count_ok))

    def save(self):
        self.store_file.write_text('\n'.join(self.files))

    def load(self):
        if self.store_file.exists():
            self.files = set(self.store_file.read_text().splitlines())
        else:
            self.files = set()


tempFileRemover = TempFileRemover()


@contextmanager
def handling_permission_error():
    try:
        yield
    except PermissionError as e:
        tempFileRemover.add(e.filename)


def decorate_for_permission_error(func):
    def proxy(*args, **kw):
        with handling_permission_error():
            return func.__call__(*args, **kw)

    return proxy


# def


class GoogleDriveFS_2(GoogleDriveFS):
    """
    upload() Copy a binary file to the filesystem.
    writebytes() Write a file as bytes.
    writefile() Write a file-like object to the filesystem.
    writetext() Write a file as text.
    """
    _base = GoogleDriveFS
    upload = decorate_for_permission_error(_base.upload)
    writebytes = decorate_for_permission_error(_base.writebytes)
    writefile = decorate_for_permission_error(_base.writefile)
    writetext = decorate_for_permission_error(_base.writetext)


def make_google_drive_fs(drive_path=None):
    credentials = google_drive_credentials()
    assert credentials
    drive_fs = GoogleDriveFS_2(credentials=credentials)

    if drive_path:
        drive_fs.makedirs(drive_path, recreate=True)
        drive_fs = drive_fs.opendir(drive_path)

    return drive_fs


def main():
    credentials = google_drive_credentials()
    assert credentials
    gfs = GoogleDriveFS_2(credentials=credentials)

    # drive_fs = gfs.opendir('Study/dev/shared/')
    drive_fs = gfs.opendir('Study/dev/shared/my-folder For Files')

    # play with uploading

    if 0:
        p = Path(r'c:\Temp2\Conf-link.txt')

        with handling_permission_error():
            gfs.writebytes('Study/dev/shared/' + p.name, p.read_bytes())
        # try:
        #     fs.writebytes('Study/dev/shared/' + p.name, p.read_bytes())
        # except PermissionError as e:
        #     tempFileRemover.add(e.filename)
        #     # print(vars(e))

    if 0:
        # local_fs = open_fs(r'c:\D\OpenServer\domains\moodle.loc\report\coursesize')
        local_fs = open_fs(r'c:\D\Нинь\Музыка\HPPav 2024\Rolling Stones')
        target_dir = 'Study/dev/shared/music24-RS'
        gfs.makedirs(target_dir, recreate=True)
        drive_fs = gfs.opendir(target_dir)
        print('mirroring the dir to Drive...')
        fs.mirror.mirror(local_fs, drive_fs, preserve_time=True)

        # # works, too. Use mirror instead :).
        # for step in local_fs.walk():
        #     print('ensuring dir:', step.path)
        #     drive_fs.makedirs(step.path, recreate=True)
        #     for file_info in step.files:
        #         filepath = file_info.make_path(step.path)
        #         print(' upload file:', filepath)
        #         with local_fs.openbin(filepath) as f:
        #             drive_fs.upload(filepath, f)

        # local_fs_dst = open_fs(r'c:\Temp\11\ttls')
        # print('mirroring Drive dir to local...')
        # fs.mirror.mirror(drive_fs, local_fs_dst, preserve_time=True)


if __name__ == '__main__':
    main()
    print('done.')
    print('end.')
