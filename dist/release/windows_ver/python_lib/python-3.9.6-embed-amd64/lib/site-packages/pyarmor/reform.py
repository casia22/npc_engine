import ast


class ReformNodeTransformer(ast.NodeTransformer):

    def _has_docstring(self, node):
        try:
            return ast.get_docstring(node) is not None
        except TypeError:
            pass

    def _reform_node(self, node):
        # Ignore docstring
        start = 1 if self._has_docstring(node) else 0

        # Ignore any statement "from __future__ import xxx"
        for x in node.body[start:]:
            if isinstance(x, ast.ImportFrom) and x.module == '__future__':
                start += 1
                continue
            break

        body = node.body[:start]

        np = ast.parse('lambda : None').body[0]
        ast.copy_location(np, node)
        ast.fix_missing_locations(np)
        body.append(np)

        if self.wrap:
            np = ast.Try(node.body[start:], [], [], ast.parse('lambda : None').body)
            ast.copy_location(np, node)
            ast.fix_missing_locations(np)
            body.append(np)
        else:
            body.extend(node.body[start:])

        node.body = body

    def reform_node(self, node):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.Module)):
            self._reform_node(node)

    def visit(self, node):
        self.reform_node(node)
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                [self.visit(x) for x in value]
            elif isinstance(value, ast.AST):
                self.visit(value)


def ast_reform(mtree, **kwargs):
    # Modify attribute "body" of the following nodes:
    #     ast.Module
    #     ast.FunctionDef
    #     ast.ClassDef
    #
    # Normal mode:
    #    insert "lambda : None" at the beginning of node.body
    #
    # Wrap mode:
    #    change node.body as
    #        lambda : None
    #        try:
    #            original node.body
    #        finally:
    #            lambda : None
    #
    snt = ReformNodeTransformer()
    snt.wrap = kwargs.get('wrap')
    snt.visit(mtree)


if __name__ == '__main__':
    with open('foo.py') as f:
        source = f.read()

    mtree = ast.parse(source, 'foo')
    ast_reform(mtree, wrap=True)
    print(ast.dump(mtree, indent=2))
