from operator import itemgetter
from heapq import nlargest


def mostcommon(iterable,n=None):
    """Return a sorted list of the most common to least common elements and
    their counts.  If n is specified, return only the n most common elements.
    """

    # http://code.activestate.com/recipes/347615/ (Raymond
    # Hettinger)

    bag = {}
    for elem in iterable:
        bag[elem] = bag.get(elem, 0) + 1
    if n is None:
        return sorted(bag.iteritems(), key=itemgetter(1), reverse=True)
    it = enumerate(bag.iteritems())
    nl = nlargest(n, ((cnt, i, elem) for (i, (elem, cnt)) in it))
    return [(elem,cnt) for cnt, i, elem in nl]

