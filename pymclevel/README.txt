Python library for reading Minecraft levels.

Simplified for the sake of this project to only support beta 1.7.3 levels

Includes a command-line client (mce.py)

Requires numpy and PyYaml.

Read mclevel.py to get started.

See LICENSE.txt for licensing terms.



mce.py is a command-line editor for SMP maps. It can be used interactively from a terminal, accept editing commands on standard input, or run a single editing command from the shell.

Sample usage:

$ python mce.py

    Usage:

    Block commands:
        clone <sourcePoint> <sourceSize> <destPoint>
        fill <blockType> [ <point> <size> ]
        replace <blockType> [with] <newBlockType> [ <point> <size> ]

        export <filename> <sourcePoint> <sourceSize>
        import <filename> <destPoint>

        analyze

    Player commands:
        player [ <player> [ <point> ] ]
        spawn [ <point> ]

    Entity commands:
        removeEntities [ <EntityID> ]

    Chunk commands:
        createChunks <point> <size>
        deleteChunks <point> <size>
        prune <point> <size>
        relight [ <point> <size> ]

    World commands:
        degrief

    Editor commands:
        save
        reload
        load <filename> | <world number>
        quit

    Informational:
        blocks [ <block name> | <block ID> ]
        help [ <command> ]

    Points and sizes are space-separated triplets of numbers ordered X Y Z.
    X is position north-south, increasing southward.
    Y is position up-down, increasing upward.
    Z is position east-west, increasing westward.

    A player's name can be used as a point - it will use the
    position of the player's head. Use the keyword 'delta' after
    the name to specify a point near the player.

    Example:
       codewarrior delta 0 5 0

    This refers to a point 5 blocks above codewarrior's head.

