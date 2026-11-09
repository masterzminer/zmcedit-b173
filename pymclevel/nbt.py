import log

try:
    try:
        from . import _nbt
        from ._nbt import *
        log.info("Accelerated NBT module loaded.")
    except ImportError:
        log.info("Could not load precompiled _nbt extension. Trying pyximport...")
        import numpy
        from pyximport import install; install(setup_args={'include_dirs':[numpy.get_include()]})
        from . import _nbt
        from ._nbt import *
        log.info("Accelerated NBT module loaded via pyximport")

except ImportError as e:
    log.info("Exception: ", repr(e))
    log.info(
        "Import error loading _nbt extension. NBT acceleration will not be available.\n"
        "To take advantage of the accelerated NBT module, install both Cython and your system development tools. Use this\n"
        "command to install Cython:\n"
        "  pip install Cython")
    log.info("You must also install your system's development tools, i.e. gcc for nbt to load")
    from .pynbt import *
    log.info("Pure-python NBT module loaded.")
