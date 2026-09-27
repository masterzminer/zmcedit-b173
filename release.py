
import os.path


VERSION_NAME = 'zMCEdit-b173'

VERSION_PATH = 'zmcedit-b173-version.txt'


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

release = get_version()
