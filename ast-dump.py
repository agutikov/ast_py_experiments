#!/usr/bin/env python3

import os, sys
import json
import ast
import hashlib
from typing import List, Set, Dict, Tuple, Any, Callable
import argparse

node_id_counter = 0

def node_to_dict(node, level=0, parent_id=None):
    global node_id_counter
    node_id = str(node_id_counter)
    node_id_counter += 1
    tree_node = {
        '__type': type(node).__name__,
        '_id': node_id,
        '_loc': {},
        '_val_hash': None,
        '_tree_hash': None,
        '_weight': None,
        '_max_depth': None,
        '_level': level,
        '_parent_id': parent_id,
    }
    weight = 1
    max_depth = 0
    for k,v in node.__dict__.items():
        if k == 'col_offset' or k == 'lineno':
            tree_node['_loc'][k] = v
            continue
        weight += 1
        if isinstance(v, str) or isinstance(v, int) or isinstance(v, float) or v is None:
            tree_node[k] = v
        elif isinstance(v, list):
            if len(v) > 0 and isinstance(v[0], str):
                tree_node[k] = v
            else:
                children = []
                for item in v:
                    child_node = node_to_dict(item, level+1, node_id)
                    weight += child_node['_weight']
                    max_depth = max([max_depth, child_node['_max_depth'] + 1])
                    children.append(child_node)
                tree_node[k] = children
        else:
            attr_node = node_to_dict(v, level+1, node_id)
            weight += attr_node['_weight']
            max_depth = max([max_depth, attr_node['_max_depth'] + 1])
            tree_node[k] = attr_node

    tree_node['_weight'] = weight
    tree_node['_max_depth'] = max_depth

    tree_value = filter_meta(tree_node)
    canonical_value = json.dumps(tree_value, sort_keys=True)

    tree_structure = filter_tree_structure(tree_node)
    canonical_tree = json.dumps(tree_structure, sort_keys=True)

    #print('canonical_value', canonical_value)
    #print('canonical_tree', canonical_tree)

    tree_node['_val_hash'] = hashlib.md5(canonical_value.encode('utf-8')).hexdigest()
    tree_node['_tree_hash'] = hashlib.md5(canonical_tree.encode('utf-8')).hexdigest()

    return tree_node

def filter_meta(node):
    obj = {}
    for k,v in node.items():
        if k[0] == '_' and k != '__type':
            continue
        if isinstance(v, str) or isinstance(v, int) or isinstance(v, float) or v is None:
            obj[k] = v
        elif isinstance(v, list):
            if len(v) > 0 and isinstance(v[0], str):
                obj[k] = v
            else:
                children = []
                for item in v:
                    child_node = filter_meta(item)
                    children.append(child_node)
                obj[k] = children
        else:
            obj[k] = filter_meta(v)
    return obj

def filter_tree_structure(node):
    obj = {}
    for k,v in node.items():
        if k == '__type':
            obj[k] = v
        if k[0] == '_':
            continue
        if isinstance(v, str) or isinstance(v, int) or isinstance(v, float) or v is None:
            continue
        elif isinstance(v, list):
            if len(v) > 0 and isinstance(v[0], str):
                continue
            else:
                children = []
                for item in v:
                    child_node = filter_tree_structure(item)
                    children.append(child_node)
                obj[k] = children
        else:
            obj[k] = filter_tree_structure(v)
    return obj

def parse_file(filename):
    with open(filename) as f:
        code = f.read()
    ast_tree = ast.parse(code)
    return node_to_dict(ast_tree)



# TODO: walk tree and visitors (add/update attrs): tree -> tree
# TODO: tree filter (remove children or attrs): tree -> tree
# TODO: subtree selector (select multiple subtrees): tree -> forest
# TODO: library with utility functions like filters, hash
# TODO: two-way convertions code<->ast<->tree<->tables

# TODO: add _scope object attr for objects with scopes (FunctionDef, Lambda, what else)
# - scope itself contains:
#   - id of object it belongs to
#   - id of ast node it belongs to
#   - id of parent scope
#   - list of named objects in this scope
# - list of scopes
# - list of objects
# - types of named objects in scope:
#   - variable
#   - function
#   - class
#     - scope of class (static)
#     - public scope of object of class
#     - private scope of self of object of class
#     - scope inside each method
# - named object itself contains:
#   - id of scope
#   - id of to ast node with definition in this scope
#   - type (variable, function, ...)
#   - list of usages
#     - by scope
#     - by ast node
#     - by usage type:
#       - load - to the right of assign
#       - store - to the left of assign
#       - modification (for example: a[0] = 1)
#       - pass as function arg - is always load, but internal object can be modified inside function
#         - infer modified or not from function content

# TODO: semantic of named object usages:
# - link to named object definition in this or any of parent scopes
# - type of usage: store or load
# - next usage, previous usage in this scope

# TODO: data flow graph for each scope
# TODO: variable type inference

def walk_tree(
    node: Dict[str, Any],
    visitor_pre: Callable[[Dict[str, Any]], None] = None,
    visitor_post: Callable[[Dict[str, Any]], None] = None
    ):
    if visitor_pre is not None:
        visitor_pre(node)
    for k,v in node.items():
        if k == '__type':
            continue
        if k[0] == '_':
            continue
        if isinstance(v, str) or isinstance(v, int) or isinstance(v, float) or v is None:
            continue
        elif isinstance(v, list):
            if len(v) > 0 and isinstance(v[0], str):
                continue
            else:
                for item in v:
                    walk_tree(item, visitor_pre, visitor_post)
        else:
            walk_tree(v, visitor_pre, visitor_post)
    if visitor_post is not None:
        visitor_post(node)

def get_flat_node(node):
    """
    Replace child nodes by stubs with only _id attr
    """
    flat_node = {}
    for k,v in node.items():
        if k[0] == '-' or k[0] == '_':
            flat_node[k] = v
        elif isinstance(v, str) or isinstance(v, int) or isinstance(v, float) or v is None:
            flat_node[k] = v
        elif isinstance(v, list):
            if len(v) > 0 and isinstance(v[0], str):
                flat_node[k] = v
            else:
                flat_node[k] = [{'_id':item['_id']} for item in v]
        else:
            flat_node[k] = {'_id':v['_id']}
    return flat_node

class tables:
    def __init__(self):
        self.node_by_id = {}
        self.node_id_by_type = {}

        # list of nodes by tree hash (nodes of identical structure)
        self.node_id_by_tree = {}

        # list of nodes by value hash (identical nodes)
        self.node_id_by_value = {}

        self.node_id_by_type_depth_weight = {}

    def to_dict(self):
        return {
            'nodes' : self.node_by_id,
            'trees' : self.node_id_by_tree,
            'types' : self.node_id_by_type,
            'type_depth_weight' : self.node_id_by_type_depth_weight,
            'values' : self.node_id_by_value,
        }

    def __call__(self, node):
        node_id = node['_id']
        node_type = node['__type']
        node_val_hash = node['_val_hash']
        node_tree_hash = node['_tree_hash']
        tdw = f"{node_type}_{node['_max_depth']}_{node['_weight']}"
        self.node_by_id[node_id] = get_flat_node(node)
        self.node_id_by_type[node_type] = self.node_id_by_type.get(node_type, []) + [node_id]
        if node['_max_depth'] > 0:
            self.node_id_by_tree[node_tree_hash] = self.node_id_by_tree.get(node_tree_hash, []) + [node_id]
            self.node_id_by_value[node_val_hash] = self.node_id_by_value.get(node_val_hash, []) + [node_id]
            self.node_id_by_type_depth_weight[tdw] = self.node_id_by_type_depth_weight.get(tdw, []) + [node_id]



def main():
    parser = argparse.ArgumentParser(description='Dump AST (Abstract Syntax Tree) for Python code.')
    parser.add_argument('filepath', metavar='file.py',
                        help='*.py file to parse')
    parser.add_argument('--tree', action='store_true',
                        help='dump tree instead of list of tables')
    args = parser.parse_args(sys.argv[1:])

    tree = parse_file(args.filepath)

    if args.tree:
        print(json.dumps(tree, indent=4, sort_keys=True))
        return

    ic = tables()
    walk_tree(tree, ic)
    print(json.dumps(ic.to_dict(), indent=4, sort_keys=True))


if __name__ == '__main__':
    main()

