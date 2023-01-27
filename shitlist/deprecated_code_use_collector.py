import ast
import collections
from _ast import AST
from collections import ChainMap
from types import MappingProxyType as readonlydict


class DeprecatedCodeUseCollector(ast.NodeVisitor):
    def __init__(self, deprecated_code: str, modulename, package=''):
        self.deprecated_code = deprecated_code
        self.modulename = modulename
        # used to resolve from ... import ... references
        self.package = package
        self.modulepackage, _, self.modulestem = modulename.rpartition('.')
        # track scope namespaces, with a mapping of imported names (bound name to original)
        # If a name references None it is used for a different purpose in that scope
        # and so masks a name in the global namespace.
        self.import_scopes = ChainMap()
        self.scope_names = collections.deque()
        self.used_at = []  # list of (name, alias, line) entries

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        prev_field, prev_value = None, None
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, AST):
                        self.visit(item)
            elif isinstance(value, AST):
                self.visit(value)
            elif field == "attr" and value == self.deprecated_code:
                self.visit_attr(value, prev_value)
            rev_field, prev_value = field, value

    def visit_FunctionDef(self, node):
        self.import_scopes = self.import_scopes.new_child()
        self.scope_names.append(node.name)
        self.generic_visit(node)
        self.import_scopes = self.import_scopes.parents
        self.scope_names.pop()

    def visit_Lambda(self, node):
        # lambdas are just functions, albeit with no statements
        # self.visit_Function(node)
        pass

    def visit_ClassDef(self, node):
        # class scope is a special local scope that is re-purposed to form
        # the class attributes. By using a read-only dict proxy here this code
        # we can expect an exception when a class body contains an import
        # statement or uses names that'd mask an imported name.
        self.import_scopes = self.import_scopes.new_child(readonlydict({}))
        self.scope_names.append(node.name)
        self.generic_visit(node)
        self.import_scopes = self.import_scopes.parents
        self.scope_names.pop()

    def visit_Import(self, node):
        self.import_scopes.update({
            a.asname or a.name: a.name
            for a in node.names
            if a.name == self.modulename
        })

    def visit_ImportFrom(self, node):
        # resolve relative imports; from . import <name>, from ..<name> import <name>
        source = node.module  # can be None
        if node.level:
            package = self.package
            if node.level > 1:
                # go up levels as needed
                package = '.'.join(self.package.split('.')[:-(node.level - 1)])
            source = f'{package}.{source}' if source else package
        if self.modulename == source:
            # names imported from our target module
            self.import_scopes.update({
                a.asname or a.name: f'{self.modulename}.{a.name}'
                for a in node.names
            })
        elif self.modulepackage and self.modulepackage == source:
            # from package import module import, where package.module is what we want
            self.import_scopes.update({
                a.asname or a.name: self.modulename
                for a in node.names
                if a.name == self.modulestem
            })

    def visit_Name(self, node):
        if not isinstance(node.ctx, ast.Load):
            # store or del operation, means the name is masked in the current scope
            try:
                self.import_scopes[node.id] = None
            except TypeError:
                # class scope, which we made read-only. These names can't mask
                # anything so just ignore these.
                pass
            return
        # find scope this name was defined in, starting at the current scope
        imported_name = self.import_scopes.get(node.id)
        if imported_name is None:
            return
        # pdb.set_trace()
        if self.deprecated_code == node.id:
            self.used_at.append(self.scope_names[0])

    def visit_attr(self, node, prev_node):
        imported_name = self.import_scopes.get(prev_node.id)
        if imported_name is None:
            return
            # pdb.set_trace()
        if self.deprecated_code == node:
            self.used_at.append(self.scope_names[0])
