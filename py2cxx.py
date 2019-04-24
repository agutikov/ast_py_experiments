#!/usr/bin/env python3

import os, sys
import json
import ast
import hashlib
from typing import List, Set, Dict, Tuple, Any, Callable
import argparse


def convert_cxx(filename):
    with open(filename) as f:
        code = f.read()
    ast_tree = ast.parse(code)

    test_vis().visit(ast_tree)


class test_vis(ast.NodeVisitor):
    def __init__(self):
        self.level = 0
        self.main_body = []

    def _tab(self):
        return '  ' * self.level;

    header = """/**************************************************
* This program was generated from Python code
*
**************************************************/

#include <variant>
#include <iostream>
#include <string>

using any = std::variant<int64_t, std::string, void*>;

std::ostream& operator<< (std::ostream& os, any const& v) {
    std::visit([&os](auto const& e){ os << e; }, v);
    return os;
}

"""

    def visit_Module(self, node):
        print(test_vis.header)
        self.generic_visit(node)
        print('int main()\n{')
        for s in self.main_body:
            print('  ' + s)
        print('  return 0;\n}\n')

    def visit_FunctionDef(self, node):
        args = ', '.join(['any ' + arg.arg for arg in node.args.args])
        print(self._tab() + f'void {node.name}({args})\n' + '{')
        self.level += 1
        self.generic_visit(node)
        self.level -= 1
        print(self._tab() + '}\n')

    def visit_Call(self, node):
        if node.func.id == 'print':
            s = self._call_print(node.args)
        else:
            s = self._tab() + f'{node.func.id}({self._call_args(node.args)});'

        if self.level == 0:
            self.main_body.append(s)
        else:
            print(s)

    def _call_args(self, args):
        a = []
        for arg in args:
            if isinstance(arg, ast.Name):
                a.append(arg.id)
            if isinstance(arg, ast.Str):
                s = arg.s
                s.replace('"', '\\"')
                a.append(f'"{s}"')
                #a.append(f'std::string("{s}")')
            if isinstance(arg, ast.Num):
                a.append(f'{arg.n}')
        return ', '.join(a)

    def _call_print(self, args):
        a = ' << " " << '.join([arg.id for arg in args])
        return self._tab() + 'std::cout << ' + a + ' << std::endl;'


def main():
    if len(sys.argv) > 1:
        convert_cxx(sys.argv[1])
        return

if __name__ == '__main__':
    main()
