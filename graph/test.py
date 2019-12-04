
import networkx as nx
import matplotlib.pyplot as plt
from pprint import pprint
from typing import List, Set, Dict, Tuple

G = nx.random_lobster(6, 0.9, 0.9)
G = nx.barabasi_albert_graph(8, 5)
G = nx.watts_strogatz_graph(8, 3, 0.1)
G = nx.erdos_renyi_graph(10, 0.15)
G = nx.complete_bipartite_graph(3, 5)

G = nx.dorogovtsev_goltsev_mendes_graph(2)
G = nx.petersen_graph()
G = nx.tutte_graph()
G = nx.sedgewick_maze_graph() # cool
# G = nx.tetrahedral_graph() # not cool

G = nx.ladder_graph(8)
G = nx.barbell_graph(5, 2)
G = nx.turan_graph(10, 3)


def g2d(g):
    return {k:{k1 for k1 in v} for k,v in g.adj.items()}

#pprint(g2d(G))
#nx.draw_shell(G)
#plt.show()


# sorting nodes (with optional tails - additional strings for each node):
#   for each node - create "projection"
#     slice graph into levels by distance
#     append levels with subgraphs not connected to selected node
#       canonicalize each subgraph and sort them
#     sort not connected subgraphs 
#   sort nodes in each level as subgraph:
#       apply sorting algorithm recursively to levels
#       with added tail with uplinkes for sorting equivalent nodes on this level
#       e.g. sort by minimization of "projection" with additional information
#   for each level write each node as list of uplinks and list of siblings in sorted order
#   select lexicagraphically minimal string representation of sorted nodes representation

# canonicalized representaion solves next problems:
# 1 - serialize graph into string and build graph from this string
# 2 - serialize every isomorphic graph into same string
# 3 - produces order of nodes of this graph

# canonicalized graph = sorted list of canonicalized not-connected subgraphs, possibly added additional info for each node
# canonicalized linked graph = minimum of sliced order with each level canonicalized with additional info from upper level

# ++ no need to sort nodes if they all are symmetric
# like if g contains N nodes and every node has N-1 links - then it fully connected and thus symmetric
# if every node has equal number of links - is graph symmetric?


def serialize_can_graph(c_g: List[List[Tuple[Set[int], Set[int]]]]) -> str:
    """
        '@' - start isolated subgraph, head node
        '|' - separate levels
        ';' - separate nodes in level
        '/' - separate siblings and uplinks
        ',' - separate indexes
    """
    s = ''
    for level in c_g:
        if level == [([], [])]:
            s += '@'
            continue
        nodes = []
        for siblinks, uplinks in level:
            nodes.append(','.join(map(str, siblinks)) + '/' + ','.join(map(str, uplinks)))
        s += '|' + ';'.join(nodes)
    return s


def split_isolated_subgraphs(_g: Dict[int, Set[int]]) -> List[Dict[int, Set[int]]]:
    """
        Returns list of isolated subgraphs.
    """
    subgraphs = []

    if len(_g) == 0:
        return []

    g = _g.copy()

    while len(g) > 0:
        subgraph = {}
        links = set()

        # pick first node
        node = list(g.keys())[0]
        links.add(node)

        while len(links) != 0:
            # get first node linked to already collected subgraph
            node = list(links)[0]
            for link in g[node]:
                # add all links of this node
                if link not in subgraph:
                    # if linked node not collected yet
                    links.add(link)
            # move node to subgraph
            subgraph[node] = g[node]
            del g[node]
            # remove node (that is already in subgraph) from links
            links.remove(node)

        subgraphs.append(subgraph)

    return subgraphs


def subgraph(g: Dict[int, Set[int]], nodes: Set[int]) -> Dict[int, Set[int]]:
    """
        Return subgraph containing nodes from list.
    """
    # copy nodes
    subg = {node: g[node].copy() for node in nodes}
    
    # remove invalid links
    return {node: {link for link in links if link in s} for node,links in subg}


def compare_can_graphs(
        g1: List[List[Tuple[Set[int], Set[int]]]],
        g2: List[List[Tuple[Set[int], Set[int]]]],
        g1_x: List[List[str]] = None,
        g2_x: List[List[str]] = None
    ) -> bool:
    """
        True - if g1 goes first in sorted order.
        False - if g2 goes first in sorted order.
    """
    return True


def sort_graph_levels_from_node(_g: Dict[int, Set[int]], node: int) -> List[Set[int]]:
    """
        Returns order of original graph nodes.
    """
    g = _g.copy()

    # first iteration with known node
    levels = [set([node])]
    lvl = {node: g[node]}
    del g[node]

    # for every next level
    while len(g) > 0:
        next_lvl = {}
        
        for n in lvl:
            for k in lvl[n]:
                if k in g and k not in lvl:
                    # collect next lvl
                    next_lvl[k] = g[k]
                    # remove next lvl nodes from g
                    del g[k]

        # push level
        levels.append(set(next_lvl.keys()))
        lvl = next_lvl

    return levels





def canonicalize(
        g: Dict[int, Set[int]],
        suffixes: Dict[int, str] = None
    ) -> Tuple[Dict[int, Tuple[int, int]], List[List[int]], List[List[Tuple[Set[int], Set[int]]]]]:
    """
        Returns canonicalized graph representaion:
         - conversion from original graph into canoniclized:
           map of node id to pair of level and index in level
         - conversion from canonocalized into oroginal graph:
           list of levels where level is list of node ids
         - original caconicalized representation:
           list of levels where level is list of nodes where node is pair of list of up links indexes and list of sibling link indexes
           graph = [levels]
           level = [nodes]
           node = (siblings, uplinks)
           siblings = {index from this level}
           uplinks = {index from upper level}
    """
    if len(g) == 0:
        return {}, [], []
    if len(g) == 1:
        return {k:(0, 0) for k in g}, [[k for k in g]], [[([], [])]]


exit()


#######################################################################################################


def print_as_dag(g, node):
    lvl = [node]
    next_level = []
    uplinks = []
    siblings = []
    g1 = g.copy()
    while len(g1) > 0:
        # collect next lvl
        for n in lvl:
            for k in g1[n]:
                if k not in lvl:
                    if k not in next_level:
                        next_level.append(k)
        
        # calc uplinks
        siblings_links = False
        for k in next_level:
            uplinks.append([])
            siblings.append([])
            for i,n in enumerate(lvl):
                if n in g1[k]:
                    uplinks[-1].append(i)
            for i,n in enumerate(next_level):
                if n in g1[k]:
                    siblings[-1].append(i)
                    siblings_links = True

        if siblings_links:
            g_next_lvl = g1.subgraph(next_level)
            pprint(g2d(g_next_lvl))
            nx.draw_shell(g_next_lvl)
            plt.show()

        # remove level from g1
        for n in lvl:
            g1.remove_node(n)

        # push level
        #print(lvl, len(lvl))
        next_lvl_a = []
        if len(uplinks) > 0:
            #print(uplinks)
            #print(siblings)
            for u,s in zip(uplinks, siblings):
                next_lvl_a.append(','.join(map(str, u)) + '/' + ','.join(map(str, s)))
        next_lvl_s = '; '.join(next_lvl_a)
        print(next_lvl_s)
        lvl = next_level
        next_level = []
        uplinks = []
        siblings = []

    print()

for node in G:
    print(node)
    print_as_dag(G, node)


def print_all_paths(g, tab=0):
    for node in g.adj:
        print('(', end='')
        # remove node
        g1 = g.copy()
        g1.remove_node(node)
        # print all paths to all other nodes
        print_all_paths(g1, tab+1)
        print(')', end='')
        if tab == 0:
            print()

#print_all_paths(G)
print()




