# see https://pypi.org/project/drive/

"""
Работает только через Service account (не через OAuth2).
Не смог получить список файлов на диске.

"""


from drive.client import Client
from drive.files import File

# client = Client("../_pydrive/credentials.json")
client = Client("loginservice-225211-6f8a1ded54bc.json")

print('Client is prepared.')
print()

# print(client.files_shared_with_me())

# ok:
print(d := client.root())

print(d.is_directory)  # True
print(d.id, d.name)  # e.g. "My Drive"
print(d.human_type)

# Get a directory's content
for f in d.list():
    print(f.name)
    print(f)
    print()

print(repr(d.list()))


# print(d.get_child(r'RDF-storage-ER-Quetion & Template.drawio.svg') or 'nothing')
# print(client.get_file_by_name(r'/RDF-storage-ER-Quetion & Template.drawio.svg') or 'nothing')




