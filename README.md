# Sharea: Sharing area
Yet another tool for syncing files via cloud (Google Drive so far)

## Features
- Sync folders/files you modify frequently between your workstations (e.g. home and office).
- Optionally encrypt contents of whole shared folder.
- Configure precisely which files are to sync and which are not within each shared folder by using filters.
- Staging area is used to mirror shared files locally, so you can merge any incoming changes into your local files manually or just replace everything (be careful, this canot be undone!).

## Status
Alpha, first experiments.

## Requirements

- Python 3.10.7+
- Google account
  - Developer app to access Drive on behalf of, see: https://developers.google.com/drive/api/quickstart/python
- Python requirements:
```
adict
fs
fs.googledrivefs
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
pyzipper
pyyaml
```

## Concepts
(TODO: picture)

High-level operations (using some terms of version control systems, e.g. Git):
 * local area : working tree, live files.
 * staging area : temporary area, mirroring remote area
 * remote area : cloud content.


### Commands:
 - fetch (from remote to staging area)
 - rewrite (from staging area to local area, Dangerous! May cause data loss!)
 - pull = fetch + rewrite
 - stage (from local area to staging area)
 - push (from staging area to remote)
 - dump = stage + push

The terminology is inspireg by common Git commands, but the semantics is a bit different.

#### Normal everyday workflow:
 0) come to office
 1) fetch!
 2) manually compare and bring changes to local area (rewrite! may be used if no local changes discovered)
 3) update files in local area (do work)
 4) dump!
 5) go home
 6) repeat steps 1..4 at home
    
