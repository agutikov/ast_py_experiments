
import networkx as nx
import matplotlib.pyplot as plt
from pprint import pprint
from typing import List, Set, Dict, Tuple



# graph: dict node id -> list of linked node id
# + start node id

class blackbox:
    # state machine:
    # initialized with graph
    # store current node id
    # return size of links
    # if start node - return 0
    # after creation starts from start node
    # on invalid input - reset and return 0
    # step(int) -> int
    # show(): 

    def __init__(self, g: Dict[int, List[int]], start: int):
        if len(g[start]) > 1:
            raise Exception('Start node has more than one link')
        for k,v in g.items():
            if len(v) == 0:
                raise Exception(f'Node {k} has no links')
        self.g = g.deepcopy()
        self.start = start
        self.current = start

    def step(self, next: int) -> int:
        if next < 0 or next >= len(self.g[self.current]) or (next == 0 and self.current != self.start):
            self.current = self.start
        else:
            self.current = self.g[self.current][next]

        if self.current == self.start:
            return 0
        else:
            return len(self.g[self.current])

    def show(self):
        """
            convert dict to graph with marked start node and current node
            and draw it
        """
        pass




# navigation algorythm provided with interface
# step(int) -> int
# recevice number of links, return next move
# if return None - then finished

class navigator:
    def __init__(self):
        self.g = {}
        self.h = {}
    

    def step(self, current_size: int) -> int:
        return 0


    def show(self):
        pass



# external code that calls steps of state machine and navigation algorythm

b = blackbox({0: [1], 1: [0]}, 0)
n = navigator()

next = 0
size = 0
while True:
    next = n.step(size)
    if next is None:
        break
    size = b.step(next)
    b.show()

n.show()
