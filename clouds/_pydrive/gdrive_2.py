from pathlib import Path

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive, GoogleDriveFile

"""
@see: https://www.projectpro.io/recipes/upload-files-to-google-drive-using-python

@see: https://googlearchive.github.io/PyDrive/docs/build/html/index.html
"""

USEFUL_FILE_FIELDS = [
    'id',  # id на диске
    'title',  # имя файла (с расширением, без пути)
    'fileSize',  # размер файла в байтах (тип значения: строка)
    'modifiedDate',  # дата изменения, пример: '2024-01-30T23:37:44.161Z'
    'originalFilename',  # имя файла (м.б. другим, вероятно, если файл переименовывался)
    'alternateLink',  # ссылка на просмотр
    'embedLink',  # ссылка на просмотр в упрощённом интерфейсе, без кнопок
    'webContentLink',  # ссылка на скачивание
]

# My `Study/dev/shared` folder
root_folder_id = '1DeAhPLh8zHHkif58DBnIDmGZJWPHVwnn'


class GDriveClient:
    def __init__(self):
        self._gauth = None
        self._drive = None
        self.drive_folder = root_folder_id

    @property
    def gauth(self):
        if not self._gauth:
            self._gauth = GoogleAuth()
            # Create local webserver and auto handles authentication.
            self._gauth.LocalWebserverAuth()
        return self._gauth

    @property
    def drive(self):
        if not self._drive:
            self._drive = GoogleDrive(self.gauth)
        return self._drive

    def list_files(self, folder: str = None) -> dict[str, GoogleDriveFile]:
        folder = folder or self.drive_folder
        file_list = self.drive.ListFile(
            {'q': "'{}' in parents and trashed=false".format(folder)}).GetList()
        # for file in file_list:
        #     print('title: %s, id: %s' % (file['title'], file['id']))
        return {f['title']: f for f in file_list}

    def file_get_or_none(self, filename: str, folder: str = None) -> GoogleDriveFile | None:
        # folder = folder or self.drive_folder
        files = self.list_files(folder)
        return files.get(filename, None)

    def file_get_or_create(self, filename: str, folder: str = None) -> GoogleDriveFile | None:
        folder = folder or self.drive_folder
        file = self.file_get_or_none(filename, folder)
        if not file:
            file = self.drive.CreateFile({
                'parents': [{'id': folder}],
                'title': filename,
            })
        return file

    def upload(self, upload_file_list: list[str], folder: str = None):
        folder = folder or self.drive_folder
        # upload_file_list = ['1.jpg', '2.jpg']
        for upload_file in upload_file_list:
            gfile = self.drive.CreateFile({
                'parents': [{'id': folder}],
                'title': Path(upload_file).name,
            })
            # Read file and set it as the content of this instance.
            gfile.SetContentFile(upload_file)
            gfile.Upload()  # Upload the file.

    def download(self, file_list: list[GoogleDriveFile], local_dir: str = '.'):
        p = Path(local_dir)
        p.mkdir(parents=True, exist_ok=True)

        for i, file in enumerate(sorted(file_list, key=lambda x: x['title']), start=1):
            print('Downloading {} file from GDrive ({}/{})'.format(file['title'], i, len(file_list)))
            file.GetContentFile(str(Path(p, file['title'])))

    def read_text_content(self, filename: str, folder: str = None):
        folder = folder or self.drive_folder

        #
        # !! FIXmE: файл создаётся заново с новым ID, а не ищется по имени!
        #

        f = self.drive.CreateFile({
            'parents': [{'id': folder}],
            'title': filename,
        })
        f.FetchContent()
        return f.GetContentString()

    def write_text_content(self, filename: str, content: str, folder: str = None):
        folder = folder or self.drive_folder
        f = self.drive.CreateFile({
            'parents': [{'id': folder}],
            'title': filename,
        })
        f.SetContentString(content)
        f.Upload()

    ...


def file_to_dict(file: GoogleDriveFile) -> dict:
    return {
        k: v
        for k, v in file.items()
        if k in USEFUL_FILE_FIELDS
    }


def main():
    from pprint import pprint

    dc = GDriveClient()

    # play with uploading
    # p = Path(r'c:\Users\Olduser\Downloads\lk-main-draft.png')
    # dc.upload([str(p)])

    # dc.write_text_content('hello!user', 'Just a hello.')
    # print(dc.read_text_content('hello!user'))

    files = dc.list_files()
    pprint(files)


if __name__ == '__main__':
    main()
    print('done.')
