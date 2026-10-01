

try:
    try:
        from . import _nbt
        from ._nbt import *
        print("Accelerated NBT module loaded.")
    except ImportError:
        # TODO make the final release not rely on pyximport, it should only be needed for dev
        print("Could not load precompiled _nbt extension. Trying pyximport...")
        import numpy
        from pyximport import install; install(setup_args={'include_dirs':[numpy.get_include()]})
        from . import _nbt
        from ._nbt import *
        print("Accelerated NBT module loaded via pyximport")

except ImportError as e:
    print("Exception: ", repr(e))
    print(
        "Import error loading _nbt extension. NBT acceleration will not be available.\n" +
        "To take advantage of the accelerated NBT module, install both Cython and your system development tools. Use this\n" +
        "command to install Cython:\n" +
        "  pip install Cython")
    print("You must also install your system's development tools, i.e. gcc for nbt to load")
    from .pynbt import *
    print("Pure-python NBT module loaded.")
