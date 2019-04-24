#!/usr/bin/env python3

import time
import random
from pprint import pprint
import json
import networkx as nx
import matplotlib.pyplot as plt


def isomorph(g1, g2):
    G1 = nx.Graph({i:v for i,v in enumerate(g1)})
    G2 = nx.Graph({i:v for i,v in enumerate(g2)})
    return nx.is_isomorphic(G1, G2)


# система линейных алгебраических уравнений
# коэффициенты либо 0 либо 1/n, где n - количество ненулевых коэффициентов в строке
def calc_weight(g):
    w = [len(g[i]) for i in range(len(g))]
    #print(w)
    iter_count = 0
    diff = 1
    while diff > 0.00001:
        iter_count += 1
        diff = 0
        for i in range(len(g)):
            prev_w = w[i]
            w[i] = 1/len(g[i]) * sum([w[j] for j in g[i]])
            diff += abs(prev_w - w[i])
        #print(iter_count, diff, w)
        #time.sleep(1)
    return w[0], iter_count, diff

#calc_weight(g)

def gen_graph(n_nodes, m_links):
    assert(n_nodes < m_links)
    g = [set() for i in range(n_nodes)]

    for i in range(n_nodes):
        j = i
        while j == i:
            j = random.randint(0, len(g)-1)
        g[i].add(j)
        g[j].add(i)

    for i in range(random.randint(0, m_links-n_nodes)):
        node_1_i = random.randint(0, len(g)-1)
        node_2_i = node_1_i
        while node_2_i == node_1_i:
            node_2_i = random.randint(0, len(g)-1)
        g[node_1_i].add(node_2_i)
        g[node_2_i].add(node_1_i)

    return [list(node) for node in g]

def gen_graph2(n_nodes, m_links):
    g = gen_graph(n_nodes, m_links)
    return {i:v for i,v in enumerate(g)}

def groups(a):
    oc = {}
    for x in a:
        oc[x] = oc.get(x, 0) + 1
    return oc


#print(gen_graph(5, 6))

def fast_graph_compare(g1, g2):
    conns1 = [len(x) for x in g1]
    conns2 = [len(x) for x in g2]
    gg1 = groups(conns1)
    gg2 = groups(conns2)
    print(gg1, gg2)
    k1 = set(gg1.keys())
    k2 = set(gg2.keys())
    if 0 != len(k1.symmetric_difference(k2)):
        return False
    for k,v in gg1.items():
        if v != gg2[k]:
            return False
    return True


#############################################################################################################################

def exclude_node(g, node_id):
    q = {}
    for i,v in g.items():
        if i == node_id:
            continue
        q[i] = list(set(v) - set([node_id]))
    return q

def all_path_from_node(g, root_id):
    tree = []
    links = g[root_id]
    g = exclude_node(g, root_id)
    for i in links:
        tree.append(all_path_from_node(g, i))
    return tree

def all_path_from_all_nodes(g):
    tree = []
    for i in g.keys():
        tree.append(all_path_from_node(g, i))
    return tree

g = gen_graph2(4, 6)
print(g)

tree = all_path_from_all_nodes(g)
print(tree)





quit(0)



#############################################################################################################################



g = gen_graph(5, 6)

print(g)

w = [len(g[i]) for i in range(len(g))]

print(w)

for i in range(10):
    for i in range(len(g)):
        w[i] = sum([w[k] for k in g[i]])
    s = sum(w)
    for i in range(len(g)):
        w[i] /= s
    print(w)

quit(0)




#############################################################################################################################

gs = {}

for i in range(10000):
    g = gen_graph(5, 20)
    w, i, d = calc_weight(g)
    iw = int(w*1000)
    conns = [len(x) for x in g]
    cg = groups(conns)
    key = f'{iw} {json.dumps(cg, sort_keys=True)}'
    #g_str = json.dumps(g, sort_keys=True)
    if key not in gs:
        gs[key] = [g]
    else:
        do_add = True
        for gg in gs[key]:
            if isomorph(g, gg):
                do_add = False
        if do_add:
            gs[key].append(g)

pprint(gs, width=200)
print([len(item) for item in gs.values()])
print(len(gs))

for k,v in gs.items():
    if len(v) > 1:
        print(k, v)
        plt.subplot(121)
        nx.draw(nx.Graph({i:g for i,g in enumerate(v[0])}))
        plt.subplot(122)
        nx.draw(nx.Graph({i:g for i,g in enumerate(v[1])}))
        plt.show()

quit(0)



#############################################################################################################################


g = [
    [1, 2],
    [0, 2, 3],
    [0, 1, 3],
    [1, 2],
]

g = gen_graph(5, 6)

print(g)

w, i, d = calc_weight(g)

print(w, i, d)

dw = [abs(len(x) - w) for x in g]
print(dw)
diw = [int(x*100) for x in dw]
print(diw)
oc = groups(diw)
print(oc)

