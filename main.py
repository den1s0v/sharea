import argparse

from control import get_shared_folders_managers
from helpers import duration_report


def run(command_name: str):
    mgrs = get_shared_folders_managers()

    with duration_report('all tasks'):
        for mgr in mgrs:
            getattr(mgr, command_name).__call__()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command',
                        choices=['fetch', 'rewrite', 'pull', 'stage', 'push', 'dump', ],
                        # required=True,
                        help="""Commands available:
 * fetch (from remote to staging area);
 * rewrite (from staging area to local area, Dangerous! May cause data loss!);
 * pull = fetch + rewrite;
---
 * stage (from local area to staging area);
 * push (from staging area to remote);
 * dump = stage + push.""")

    args = vars(parser.parse_args())
    run(args['command'])


if __name__ == "__main__":
    main()
