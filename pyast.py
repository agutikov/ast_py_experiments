#!/usr/bin/env python3

import os, sys
import json
import ast
from pprint import pprint
from typing import List, Set, Dict, Tuple, Any, Callable
from enum import Enum
from copy import copy, deepcopy

def node_to_dict(node):
    type_name = type(node).__name__
    node_id = id(node)
    tree_node = {'_id':node_id, '_type':type_name}
    for k,v in node.__dict__.items():
        if isinstance(v, str) or isinstance(v, int) or isinstance(v, float) or v is None:
            tree_node[k] = v
        elif isinstance(v, list):
            res = []
            for item in v:
                res.append(node_to_dict(item))
            tree_node[k] = res
        else:
            tree_node[k] = node_to_dict(v)
    return tree_node

def parse_file(filename):
    with open(filename) as f:
        code = f.read()
    ast_tree = ast.parse(code)
    return node_to_dict(ast_tree)


# TODO:
# - compare items of same type
#   - recursively
#   - separate element structure (without names, with or without types)
#   - compare lists
#     - detect inserts, appends, prepends, removes, reorders, updates
#     - detect wrapping with nodes, like foo(x) ----> a = foo(x)
# - parse entire project
# - diff between git revisions
# - construct scopes for body where required
#   - link folded scopes and parent scopes
#   - each scope has table of variables, functions, classes
#   - each object of related type has link to item in scope table
#   - detect changes of usage of variables, functions and classes
#   - detect change of variable class in assignment
#   - detect renames
#   - detect replaces of used variable, function, operator, ...
# - summarize types of possible changes for each type of objects: variables, functions, classes, ...
# - detect incomplete changes, for example partial rename (can be valid change or mistake)
# - detect combined changes, for example function move and rename, or function move and changes of body
# - allow see related changes as single change (e.g. function rename with all usages)
# - allow see all changes related to specific object, for example class
# - allow see logically non-related changes separated (e.g. function move and body changes)
# - find code affected by change, i.e. usage contexts
#
# Additional:
# - build data flow graph


#
# AST node type includes:
# - set of keys
# - data types of values:
#   - simple: int, float, string, None)
#   - scalar object
#   - sequence of objects
#     - here can't be sequence of data types because it is already AST, only types of AST nodes
#
# AST node instance includes:
# - values of simple attributes (int, float, string, None)
# - types of nodes of scalar attributes
# - sequence of types of nodes of sequence attributes
#


# TODO:
# 1. AST node canonical format: _type, _id, _loc, _weight, sorted, ...
# 2. AST node hash
#    - with all logical values, excepting style (lineno, etc...)
#    - with types only (structure)
# 3. AST node weight:
#    - atomic value (string, int, float, None) weight=1
#    - node weight = sum of weights
# 4. Code distance between two trees - number of modifications
#    - replace value, i.e. node update (None -> Any, Any -> None, Any -> Any) - 1 modification
#    - change node type (of cause with change of values) = remove node + insert node = sum of weights of removed and inserted nodes
# 5. Difference of two nodes - distance(node1, node2) / sum(node1._weight, node2._weight)
#    - maximum difference = 1.0
# 6. Path distance between two nodes in one tree - used to find where entire code or pattern was copied
# 7. Patterns
#    - complete tree structure (with types) matching
#    - partial tree matching - without implementation of leaf nodes
#
# 20. Semantic rules to generate tables/indexes/trees/graphs for particular semantic concepts (variables, functions, types, data flow, ...)
#
# 30. Code Style Sheet (while XPath available)
# 40. Conversion RBNF <-> JSON Schema of AST


# TODO: rewrite with numpy or pandas?

# TODO: Tools
# - print formatted ast with all attrs calculated _type, _loc, _id, _val_hash, _weight, _max_depth, _level, _struct_hash
# - diff two ast files

# Change representation:
# - for each node with _id and _type add _changed key
# - for each keys except starting from underline, lineno, col_offset
#   - list:
#     - compare list of elements and save result into _changed[key]
#       - compare each element in new list with each element in old
#       - updated element will have it's own _changed dict
#   - object:
#     - compare objects recursively and save result into _changed[key]
#        - types of changes:
#          - replaced: changed isinstance or _type => _changed[key] = (before, after)
#          - updated: changed keys or body => changes will appear inside that object
#     - possibility to define score of similarity of objects that depends on similarity of internal structure and values
#   - string or number
#     - simply compare values and set _changed[key] = (before, after)


def jprint(x):
    if callable(getattr(x, "to_dict", None)):
        d = x.to_dict()
    else:
        d = x
    print(json.dumps(d, indent=4))

def print_modification(mod):
    _mod_type = {
        0: "copy from {}",
        1: "update from {}",
        2: "replace {}",
        3: "insert new"
    }
    return _mod_type[mod[0]].format(mod[1])


#TODO: Possible required different behaviour for different types of objects
# for example modification function body can be compared that way
# while modifications of array initializer, or argument list may require different set of allowed modifications
#TODO: Consider compare structure of objects and return 3-tuple of bool flags
def compare_lists(before: List[Any], after: List[Any], compare_object_callback: Callable[[Any, Any], Tuple[bool, bool]]
    )-> Tuple[List[List[int]], List[Tuple[int, int]]]:
    """
    compare_object_callback - return tuple of bool flags: (same_type, same_values)
                              (True, True) => equal objects
                              (True, False) => updated object
                              (False, None) => replaced object

    Types of changes in order of priority:
        - reorder (same type anv value):
            - copy into multiple places
        - update (same type, but not value)
            - reorder + update, only if src element not copied before or in-place
        - replace element in-place:
        - change structure:
            - insert new, append, prepend
            - remove
    """
    m = []

    for dst_el in after:
        n = []
        for src_el in before:
            n.append(compare_object_callback(src_el, dst_el))
        m.append(n)

    #print(m)

    return calculate_list_diff(m, len(before), len(after))


def calculate_list_diff(m: List[List[Tuple[int, int]]], src_count=None, dst_count=None):
    if dst_count != len(m):
        dst_count = len(m)
    if dst_count > 0:
        if src_count != len(m[0]):
            src_count = len(m[0])

    src = [[] for i in range(src_count)]
    dst = [(-1, -1) for i in range(dst_count)]

    # Find closest equal object from where it was taken
    for dst_i, potential_src in enumerate(m):
        #print(dst_i, potential_src)

        # Look for copy from source
        #TODO: restrict copy of single-level nodes (for example of _type=Num), required additional info in m
        min_distance = max(dst_count, src_count)
        source_index = -1
        for src_i, src_el in enumerate(potential_src):
            distance = abs(dst_i - src_i)
            #print(src_el[0], src_el[1], min_distance, distance)
            if src_el[0] and src_el[1] and distance < min_distance:
                min_distance = distance
                source_index = src_i
        if source_index >= 0:
            dst[dst_i] = (source_index, 0)
            src[source_index].append(dst_i)

    for dst_i, potential_src in enumerate(m):
        if dst[dst_i][0] >= 0:
            continue
        # Look for updated copy from source
        min_distance = max(dst_count, src_count)
        source_index = -1
        for src_i, src_el in enumerate(potential_src):
            distance = abs(dst_i - src_i)
            if src_el[0] and distance < min_distance:
                min_distance = distance
                source_index = src_i
        if source_index >= 0 and ((len(src) > dst_i and len(src[dst_i]) == 0) or source_index == dst_i):
            dst[dst_i] = (source_index, 1)
            src[source_index].append(dst_i)

    for dst_i, potential_src in enumerate(m):
        if dst[dst_i][0] >= 0:
            continue
        # Check for replace
        if len(src) > dst_i and len(src[dst_i]) == 0:
            dst[dst_i] = (dst_i, 2)
            src[dst_i].append(dst_i)
            continue

        # Fallback to insert
        dst[dst_i] = (-1, 3)

    for src_i, src_el in enumerate(src):
        src[src_i] = sorted(src_el)

    return src, dst


def test_compare_lists(verbose: bool = False):
    def simple_cmp(x, y):
        return type(x) == type(y), x == y

    tests = [
        (([0], [0]),       ([[0]], [(0, 0)])), # copy
        (([0], [1]),       ([[0]], [(0, 1)])), # update
        (([0], ['0']),     ([[0]], [(0, 2)])), # replace
        (([0], [None]),    ([[0]], [(0, 2)])), # replace

        (([0], []),        ([[]], [])), # delete
        (([0, 1], []),     ([[], []], [])), # delete
        (([0, 1], [0]),    ([[0], []], [(0, 0)])), # delete
        (([0, 1], [1]),    ([[], [0]], [(1, 0)])), # delete

        (([], [0]),        ([], [(-1, 3)])), # insert
        (([], [0, 1]),     ([], [(-1, 3), (-1, 3)])), # insert

        (([0], [0, 0]),    ([[0, 1]], [(0, 0), (0, 0)])), # copy
        (([0], [0, 1]),    ([[0]], [(0, 0), (-1, 3)])), # append
        (([0], [0, '0']),  ([[0]], [(0, 0), (-1, 3)])), # append
        (([0], [1, 0]),    ([[0, 1]], [(0, 1), (0, 0)])), # update
        (([0], ['0', 0]),  ([[1]], [(-1, 3), (0, 0)])), # prepend

        (([0, 1], [0, 1]), ([[0], [1]], [(0, 0), (1, 0)])), # copy
        (([1, 0], [0, 1]), ([[1], [0]], [(1, 0), (0, 0)])), # copy

        (([0, 1, 2, 3],       [1, 2, 3, 4]),      ([[], [0], [1], [2, 3]],          [(1, 0), (2, 0), (3, 0), (3, 1)])),
        (([0, 1, 2, 3],       [1, '2', 4, 2, 5]), ([[], [0], [2, 3], []],           [(1, 0), (-1, 3), (2, 1), (2, 0), (-1, 3)])),
        (([1, '2', 4, 2, 5],  [0, 1, 2, 3]),      ([[0, 1], [], [], [2, 3], []],    [(0, 1), (0, 0), (3, 0), (3, 1)])),
        (([0, 1, 2, 3, 4, 5], [5, '2', 3, 5, 0]), ([[4], [1], [], [2], [], [0, 3]], [(5, 0), (1, 2), (3, 0), (5, 0), (0, 0)])),
    ]

    for test in tests:
        args = test[0]
        expected_output = test[1]

        output = compare_lists(args[0], args[1], simple_cmp)

        if verbose or output != expected_output:
            print(f'input: arg1={args[0]}, arg2={args[1]}')
            print(f'output: {output}')
            if output != expected_output:
                print(f'expected output: {expected_output}')
        assert output == expected_output




def ast_list_compare(seq1: List[Dict[str, Any]], seq2: List[Dict[str, Any]]):
    """

    """
    modified = False
    comparators = []
    m = []
    for dst_el in seq2:
        comp = []
        n = []
        for src_el in seq1:
            c = ast_node_comparator()
            comp.append(c)
            n.append(c(src_el, dst_el))
        m.append(n)
        comparators.append(comp)

    #jprint(seq1)
    #jprint(seq2)
    #jprint(m)

    src, dst = calculate_list_diff(m, len(seq1), len(seq2))
    # store changes summary in any case
    changed = (src, dst)

    # select where store deepcopy and where comparator
    src_attr = [None]*len(src)
    dst_attr = [None]*len(dst)
    for dst_i, dst_el in enumerate(dst):
        if dst_el[1] == 0: # copied
            #TODO: store value that was copied or not? store hash will be useful for checking appliability of patch?
            pass
        if dst_el[1] == 1: # updated
            # store comparator
            dst_attr[dst_i] = comparators[dst_i][dst_el[0]]
            modified = True
        if dst_el[1] == 2: # replaced
            # store both values
            src_attr[dst_el[0]] = deepcopy(seq1[dst_el[0]])
            dst_attr[dst_i] = deepcopy(seq2[dst_i])
            modified = True
        if dst_el[1] == 3: # inserted
            # store only new value
            dst_attr[dst_i] = deepcopy(seq2[dst_i])
            modified = True

    for src_i, src_el in enumerate(src):
        if len(src_el) == 0: # removed
            # store only removed value
            src_attr[src_i] = deepcopy(seq1[src_i])
            modified = True

    return changed, (src_attr, dst_attr), modified


class ast_node_comparator:

    def __init__(self):
        self.changed = {}
        self.type = ''
        self.attrs = {}

    def to_dict(self):
        d = {
            '_type': self.type,
            '_changed': self.changed,
        }
        attrs = {}
        for k,v in self.attrs.items():
            if isinstance(v, list):
                assert False
            elif isinstance(v, ast_node_comparator):
                attrs[k] = v.to_dict()
            elif isinstance(v, tuple) and len(v) == 2 and isinstance(v[0], list) and isinstance(v[1], list):
                attrs[k] = (
                    [el.to_dict() if isinstance(el, ast_node_comparator) else el for el in v[0]],
                    [el.to_dict() if isinstance(el, ast_node_comparator) else el for el in v[1]]
                )
            else:
                attrs[k] = v
        d['_attrs'] = attrs
        return d

    def __repr__(self):
        return json.dumps(self.to_dict())


    def __call__(self, before: Dict[str, Any], after: Dict[str, Any]):
        if before['_type'] != after['_type']:
            return (False, None)

        self.type = after['_type']

        keys1 = set(before.keys())
        keys2 = set(after.keys())

        exclude = set(['lineno', 'col_offset'])
        keys1 = [key for key in keys1 if key not in exclude and key[0] != '_']
        keys2 = [key for key in keys2 if key not in exclude and key[0] != '_']

        assert keys1 == keys2

        for key in keys1:
            value1 = before[key]
            value2 = after[key]

            assert type(value1) == type(value2)

            if isinstance(value1, str) or isinstance(value1, int) or isinstance(value1, float) or value1 is None:
                if not value1 == value2:
                    self.changed[key] = (copy(value1), copy(value2))

            elif isinstance(value1, list):
                changed, attr, modified = ast_list_compare(value1, value2)
                if modified:
                    self.changed[key] = changed
                    self.attrs[key] = attr

            else:
                c = ast_node_comparator()
                same_type, same_val = c(value1, value2)
                if not same_type:
                    self.changed[key] = (deepcopy(value1), deepcopy(value2))
                elif not same_val:
                    self.attrs[key] = c

        return (True, len(self.changed) == 0 and len(self.attrs) == 0)







def main():
    test_compare_lists()

    if len(sys.argv) == 1:
        jprint(parse_file(sys.argv[0]))
        exit(0)

    if len(sys.argv) == 2:
        jprint(parse_file(sys.argv[1]))
        exit(0)

    if len(sys.argv) == 3:
        tree1 = parse_file(sys.argv[1])
        tree2 = parse_file(sys.argv[2])

        c = ast_node_comparator()
        c(tree1, tree2)

        #jprint(tree1), "\n"*10)
        #jprint(tree2), "\n"*10)
        print(c)


if __name__ == '__main__':
    main()
