
import os.path
import directories


NAME = 'zMCEdit-b173'

VERSION_PATH = directories.ASSETS / 'zmcedit-b173-version.txt'


def get_version():
    """
    Loads the build version from the bundled version file, if available.
    """
    if not os.path.exists(VERSION_PATH):
        return 'unknown'

    fin = open(VERSION_PATH, 'r')
    v = fin.read().strip()
    fin.close()

    return v

VERSION = get_version()
