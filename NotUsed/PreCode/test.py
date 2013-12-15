from collections import defaultdict, namedtuple
from itertools import izip

if __name__ == "__main__":
    names = ["abc", "def", "gef", "red", "blue", "yellow", "green", "red", "blue", "yellow", "green"]
    colors = ["red", "blue", "yellow", "green"]

    d = dict(izip(names, colors))
    print d

    group = {1: "def", 2: "trt", 3: "bgd", 4: "frg"}

    for key, value in group.iteritems():
        print key, value

    dd = defaultdict(int)
    for name in names:
        dd[name] += 1

    print dd

    #Grouping with dicts:
    d = defaultdict(list)
    for name in names:
        key = len(name)
        d[key].append(name)

    print d

    testTuple = namedtuple("TestTuple", ["a", "b"])

    a = testTuple(1, 1)
    print a

    print ", ".join(names)



