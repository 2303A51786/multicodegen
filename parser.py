import ast
import re
from utils import IRNode, PrintNode, VarAssignNode, ForRangeNode, WhileNode, IfNode, FuncNode, RawCodeNode, guess_type

class PythonParser:
    def parse(self, code_str):
        try:
            tree = ast.parse(code_str)
            return self._parse_block(tree.body)
        except Exception as e:
            return [RawCodeNode(code_str)]

    def _parse_block(self, body):
        nodes = []
        for stmt in body:
            if isinstance(stmt, ast.Assign):
                # Simple single target assignment: x = 5
                if len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                    name = stmt.targets[0].id
                    # Just get the source string of the value
                    value = ast.unparse(stmt.value)
                    nodes.append(VarAssignNode(name, value))
                else:
                    nodes.append(RawCodeNode(ast.unparse(stmt)))
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if isinstance(call.func, ast.Name) and call.func.id == "print":
                    if call.args:
                        val = ast.unparse(call.args[0])
                        nodes.append(PrintNode(val))
                    else:
                        nodes.append(PrintNode('""'))
                else:
                    nodes.append(RawCodeNode(ast.unparse(stmt)))
            elif isinstance(stmt, ast.For):
                if isinstance(stmt.target, ast.Name) and isinstance(stmt.iter, ast.Call) and isinstance(stmt.iter.func, ast.Name) and stmt.iter.func.id == "range":
                    var_name = stmt.target.id
                    args = stmt.iter.args
                    start = "0"
                    end = "0"
                    if len(args) == 1:
                        end = ast.unparse(args[0])
                    elif len(args) == 2:
                        start = ast.unparse(args[0])
                        end = ast.unparse(args[1])
                    body_nodes = self._parse_block(stmt.body)
                    nodes.append(ForRangeNode(var_name, start, end, body_nodes))
                else:
                    nodes.append(RawCodeNode(ast.unparse(stmt)))
            elif isinstance(stmt, ast.While):
                condition = ast.unparse(stmt.test)
                body_nodes = self._parse_block(stmt.body)
                nodes.append(WhileNode(condition, body_nodes))
            elif isinstance(stmt, ast.If):
                condition = ast.unparse(stmt.test)
                body_nodes = self._parse_block(stmt.body)
                orelse_nodes = self._parse_block(stmt.orelse)
                nodes.append(IfNode(condition, body_nodes, orelse_nodes))
            elif isinstance(stmt, ast.FunctionDef):
                name = stmt.name
                args = [arg.arg for arg in stmt.args.args]
                body_nodes = self._parse_block(stmt.body)
                nodes.append(FuncNode(name, args, body_nodes))
            else:
                nodes.append(RawCodeNode(ast.unparse(stmt)))
        return nodes

class RegexParser:
    def parse(self, code_str):
        # A very simplified regex-based line parser for C++/Java
        lines = code_str.split('\n')
        nodes = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # Print
            if "System.out.print" in line or "cout" in line:
                val = self._extract_print_val(line)
                nodes.append(PrintNode(val))
            
            # Variables
            elif re.match(r'^(int|float|double|String|boolean|bool|auto)\s+([a-zA-Z_]\w*)\s*=\s*(.+);$', line):
                m = re.match(r'^(int|float|double|String|boolean|bool|auto)\s+([a-zA-Z_]\w*)\s*=\s*(.+);$', line)
                var_type, name, val = m.groups()
                nodes.append(VarAssignNode(name, val, var_type))
            
            # While loop
            elif line.startswith("while"):
                m = re.search(r'while\s*\((.+)\)', line)
                if m:
                    condition = m.group(1)
                    body_str, next_i = self._extract_block(lines, i)
                    body_nodes = self.parse(body_str)
                    nodes.append(WhileNode(condition, body_nodes))
                    i = next_i
                    continue

            # If statement
            elif line.startswith("if"):
                m = re.search(r'if\s*\((.+)\)', line)
                if m:
                    condition = m.group(1)
                    body_str, next_i = self._extract_block(lines, i)
                    body_nodes = self.parse(body_str)
                    
                    orelse_nodes = []
                    if next_i < len(lines) and lines[next_i].strip().startswith("else"):
                        else_body_str, next_i = self._extract_block(lines, next_i)
                        orelse_nodes = self.parse(else_body_str)

                    nodes.append(IfNode(condition, body_nodes, orelse_nodes))
                    i = next_i
                    continue

            # For loop (simple)
            elif line.startswith("for"):
                # roughly match for(int i=0; i<10; i++)
                m = re.search(r'for\s*\([^;]+;\s*([^;]+);[^\)]+\)', line)
                if m:
                    # just extract the end condition loosely for translation purposes
                    cond = m.group(1).strip()
                    end_val = cond.split('<')[-1].strip() if '<' in cond else "n"
                    body_str, next_i = self._extract_block(lines, i)
                    body_nodes = self.parse(body_str)
                    nodes.append(ForRangeNode("i", "0", end_val, body_nodes)) # naive assumption
                    i = next_i
                    continue
            
            # Function def
            elif re.match(r'^(public\s+|static\s+|private\s+)*(\w+)\s+(\w+)\s*\((.*?)\)\s*\{?$', line):
                m = re.match(r'^(public\s+|static\s+|private\s+)*(\w+)\s+(\w+)\s*\((.*?)\)\s*\{?$', line)
                ret_type, name, args_str = m.group(2), m.group(3), m.group(4)
                args = [a.strip().split()[-1] for a in args_str.split(',')] if args_str else []
                body_str, next_i = self._extract_block(lines, i)
                body_nodes = self.parse(body_str)
                nodes.append(FuncNode(name, args, body_nodes))
                i = next_i
                continue

            else:
                nodes.append(RawCodeNode(line))
            i += 1
        return nodes

    def _extract_print_val(self, line):
        # Extract string inside println() or cout <<
        if "println" in line or "print" in line:
            m = re.search(r'\((.*)\)', line)
            return m.group(1) if m else '""'
        elif "cout" in line:
            m = re.search(r'cout\s*<<\s*(.+?)\s*(?:<<|;)', line)
            return m.group(1) if m else '""'
        return '""'

    def _extract_block(self, lines, start_idx):
        # rudimentary bracket matcher
        block_lines = []
        open_brackets = 0
        i = start_idx
        started = False
        while i < len(lines):
            line = lines[i]
            if '{' in line:
                open_brackets += line.count('{')
                started = True
            if started:
                block_lines.append(line)
            if '}' in line:
                open_brackets -= line.count('}')
            if started and open_brackets <= 0:
                break
            i += 1
        
        # remove the first and last brackets for the body
        body_str = "\n".join(block_lines)
        body_str = re.sub(r'^.*?\{', '', body_str, count=1)
        body_str = re.sub(r'\}[^}]*$', '', body_str)
        return body_str, i + 1

def parse_code(code_str, language):
    if language.lower() == "python":
        return PythonParser().parse(code_str)
    else:
        return RegexParser().parse(code_str)
