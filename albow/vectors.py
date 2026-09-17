from __future__ import absolute_import
from six.moves import map
try:

    from Numeric import add, subtract, maximum

except ImportError:

    import operator

    def add(x, y):
        return list(map(operator.add, x, y))

    def subtract(x, y):
        return list(map(operator.sub, x, y))

    def maximum(*args):
        result = args[0]
        for x in args[1:]:
            result = list(map(max, result, x))
        return result
