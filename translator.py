from utils import IRNode, PrintNode, VarAssignNode, ForRangeNode, WhileNode, IfNode, FuncNode, RawCodeNode, guess_type

class BaseTranslator:
    def translate(self, nodes, indent=0):
        code = []
        for node in nodes:
            code.append(self.visit(node, indent))
        return "\n".join(code)

    def visit(self, node, indent):
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, indent)

    def generic_visit(self, node, indent):
        return ("    " * indent) + f"// Unhandled node: {type(node).__name__}"

class PythonGenerator(BaseTranslator):
    def visit_PrintNode(self, node, indent):
        return ("    " * indent) + f"print({node.value})"

    def visit_VarAssignNode(self, node, indent):
        return ("    " * indent) + f"{node.name} = {node.value}"

    def visit_ForRangeNode(self, node, indent):
        prefix = ("    " * indent)
        if node.start == "0":
            loop = prefix + f"for {node.var_name} in range({node.end}):"
        else:
            loop = prefix + f"for {node.var_name} in range({node.start}, {node.end}):"
        body = self.translate(node.body, indent + 1)
        if not body.strip():
            body = ("    " * (indent + 1)) + "pass"
        return loop + "\n" + body

    def visit_WhileNode(self, node, indent):
        prefix = ("    " * indent)
        loop = prefix + f"while {node.condition}:"
        body = self.translate(node.body, indent + 1)
        if not body.strip():
            body = ("    " * (indent + 1)) + "pass"
        return loop + "\n" + body

    def visit_IfNode(self, node, indent):
        prefix = ("    " * indent)
        stmt = prefix + f"if {node.condition}:"
        body = self.translate(node.body, indent + 1)
        if not body.strip():
            body = ("    " * (indent + 1)) + "pass"
        res = stmt + "\n" + body
        if node.orelse:
            res += "\n" + prefix + "else:\n" + self.translate(node.orelse, indent + 1)
        return res

    def visit_FuncNode(self, node, indent):
        prefix = ("    " * indent)
        args_str = ", ".join(node.args)
        stmt = prefix + f"def {node.name}({args_str}):"
        body = self.translate(node.body, indent + 1)
        if not body.strip():
            body = ("    " * (indent + 1)) + "pass"
        return stmt + "\n" + body

    def visit_RawCodeNode(self, node, indent):
        return ("    " * indent) + node.code

class JavaGenerator(BaseTranslator):
    def visit_PrintNode(self, node, indent):
        return ("    " * indent) + f"System.out.println({node.value});"

    def visit_VarAssignNode(self, node, indent):
        v_type = node.var_type if node.var_type != "auto" else guess_type(node.value)
        if v_type == "auto": v_type = "int"
        if v_type == "float": v_type = "double"
        return ("    " * indent) + f"{v_type} {node.name} = {node.value};"

    def visit_ForRangeNode(self, node, indent):
        prefix = ("    " * indent)
        loop = prefix + f"for (int {node.var_name} = {node.start}; {node.var_name} < {node.end}; {node.var_name}++) {{"
        body = self.translate(node.body, indent + 1)
        return loop + "\n" + body + "\n" + prefix + "}"

    def visit_WhileNode(self, node, indent):
        prefix = ("    " * indent)
        loop = prefix + f"while ({node.condition}) {{"
        body = self.translate(node.body, indent + 1)
        return loop + "\n" + body + "\n" + prefix + "}"

    def visit_IfNode(self, node, indent):
        prefix = ("    " * indent)
        stmt = prefix + f"if ({node.condition}) {{"
        body = self.translate(node.body, indent + 1)
        res = stmt + "\n" + body + "\n" + prefix + "}"
        if node.orelse:
            res += " else {\n" + self.translate(node.orelse, indent + 1) + "\n" + prefix + "}"
        return res

    def visit_FuncNode(self, node, indent):
        prefix = ("    " * indent)
        args_str = ", ".join([f"Object {a}" for a in node.args]) # Defaulting to Object for loosely typed to strongly typed
        stmt = prefix + f"public static void {node.name}({args_str}) {{"
        body = self.translate(node.body, indent + 1)
        return stmt + "\n" + body + "\n" + prefix + "}"

    def visit_RawCodeNode(self, node, indent):
        # We append a semicolon blindly if it looks like a statement, but better to just return it
        val = node.code.strip()
        if val and not val.endswith(';') and not val.endswith('}') and not val.endswith('{'):
            return ("    " * indent) + val + ";"
        return ("    " * indent) + node.code

class CppGenerator(BaseTranslator):
    def visit_PrintNode(self, node, indent):
        return ("    " * indent) + f"std::cout << {node.value} << std::endl;"

    def visit_VarAssignNode(self, node, indent):
        v_type = node.var_type if node.var_type != "auto" else guess_type(node.value)
        if v_type == "String": v_type = "std::string"
        if v_type == "auto": v_type = "auto"
        return ("    " * indent) + f"{v_type} {node.name} = {node.value};"

    def visit_ForRangeNode(self, node, indent):
        prefix = ("    " * indent)
        loop = prefix + f"for (int {node.var_name} = {node.start}; {node.var_name} < {node.end}; {node.var_name}++) {{"
        body = self.translate(node.body, indent + 1)
        return loop + "\n" + body + "\n" + prefix + "}"

    def visit_WhileNode(self, node, indent):
        prefix = ("    " * indent)
        loop = prefix + f"while ({node.condition}) {{"
        body = self.translate(node.body, indent + 1)
        return loop + "\n" + body + "\n" + prefix + "}"

    def visit_IfNode(self, node, indent):
        prefix = ("    " * indent)
        stmt = prefix + f"if ({node.condition}) {{"
        body = self.translate(node.body, indent + 1)
        res = stmt + "\n" + body + "\n" + prefix + "}"
        if node.orelse:
            res += " else {\n" + self.translate(node.orelse, indent + 1) + "\n" + prefix + "}"
        return res

    def visit_FuncNode(self, node, indent):
        prefix = ("    " * indent)
        args_str = ", ".join([f"auto {a}" for a in node.args])
        stmt = prefix + f"void {node.name}({args_str}) {{"
        body = self.translate(node.body, indent + 1)
        return stmt + "\n" + body + "\n" + prefix + "}"

    def visit_RawCodeNode(self, node, indent):
        val = node.code.strip()
        if val and not val.endswith(';') and not val.endswith('}') and not val.endswith('{'):
            return ("    " * indent) + val + ";"
        return ("    " * indent) + node.code

def translate_nodes(nodes, target_language):
    lang = target_language.lower()
    if lang == "python":
        return PythonGenerator().translate(nodes)
    elif lang == "java":
        return JavaGenerator().translate(nodes)
    elif lang == "c++" or lang == "cpp":
        return CppGenerator().translate(nodes)
    else:
        return "// Unsupported language"
