class IRNode:
    pass

class PrintNode(IRNode):
    def __init__(self, value):
        self.value = value

class VarAssignNode(IRNode):
    def __init__(self, name, value, var_type="auto"):
        self.name = name
        self.value = value
        self.var_type = var_type

class ForRangeNode(IRNode):
    def __init__(self, var_name, start, end, body):
        self.var_name = var_name
        self.start = start
        self.end = end
        self.body = body

class WhileNode(IRNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class IfNode(IRNode):
    def __init__(self, condition, body, orelse=None):
        self.condition = condition
        self.body = body
        self.orelse = orelse or []

class FuncNode(IRNode):
    def __init__(self, name, args, body):
        self.name = name
        self.args = args
        self.body = body

class RawCodeNode(IRNode):
    def __init__(self, code):
        self.code = code

def guess_type(value_str):
    value_str = value_str.strip()
    if value_str.isdigit():
        return "int"
    try:
        float(value_str)
        return "float"
    except ValueError:
        pass
    if value_str.startswith('"') or value_str.startswith("'"):
        return "String"
    if value_str in ["True", "False", "true", "false"]:
        return "bool"
    return "auto"
