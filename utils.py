import time


class Timer:
    def __init__(self, tag):
        self.tag = tag

    def __enter__(self):
        self.start = time.clock()
        return self

    def __exit__(self, *args):
        self.end = time.clock()
        self.interval = self.end - self.start
        print(self.tag, self.interval)


def timeit(fun, args, repeat=100):
    start = time.time()
    for k in range(repeat):
        fun(*args)
    end = time.time()
    delta = (end - start) / repeat
    delta_unit = "s"
    for unit in ["ms", "μs", "ns"]:
        if delta > 1:
            break
        delta *= 1000
        delta_unit = unit
    print("Elapsed time {:.3f}{}".format(delta, delta_unit))
