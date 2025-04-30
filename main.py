import argparse
import threading

from control import get_shared_folders_managers
from helpers import duration_report


def run_command(mgr, command_name):
    getattr(mgr, command_name).__call__()

def run(command_name: str, use_threads: bool = True):
    mgrs = get_shared_folders_managers()

    if use_threads:
        threads = []
        with duration_report('all tasks'):
            for mgr in mgrs:
                thread = threading.Thread(target=run_command, args=(mgr, command_name))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()
    else:
        with duration_report('all tasks'):
            for mgr in mgrs:
                run_command(mgr, command_name)


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
    parser.add_argument('--noasync', action='store_true', help='Run commands synchronously')

    args = vars(parser.parse_args())
    run(args['command'], not args['noasync'])


if __name__ == "__main__":
    main()
