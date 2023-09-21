import sys
import tools
import msvcrt
from interpreter import HFSyntaxError, Stack

# 类型
# 寄存器 跳跃字符 引用字符 一元运算符 二元运算符 命令 语句块
REG = 0; JMP = 1; REF = 2; UNOP = 3; BINOP = 4; CMD = 5; STMT = 6

# 解释器
class Compiler:
    def __init__(self, lines: list, ref_lines: list) -> None:
        # 忽略注释和空白 
        self.codes = ""
        for l in lines:
            if l[0] == "#":
                continue
            self.codes += l

        self.codes += "\0"
        self.position = -1
        self.head_code = """import msvcrt, sys, os
stack = []
q, w, e, r, t, y, u, i, res = 0, 0, 0, 0, 0, 0, 0, 0, 0
"""
        
        # 添加引用
        ref_chars = "ophjkl"
        ref_count = 0
        if ref_lines != None:
            for l in ref_lines:
                module, funcs_text = l.split(" ")
                functions = funcs_text.split(",")
                for f in functions:
                    if ref_count >= 5:
                        continue
                    self.head_code += f"{ref_chars[ref_count]} = __import__('{module}').{f}\n"
                    ref_count += 1
        
        # 主函数
        self.compiled_code = """def _main():
    global q, w, e, r, t, y, u, i, res
"""
        # 运行程序
        self.run_code = """\nif __name__ == "__main__":
    try:
        _main()
    except Exception as e:
        print("HyperFuck VM Compiled：错误")
        print("    错误类型：" + e.__class__.__name__)
        print("    错误描述：" + e.args[0])
        sys.exit(1)
"""
        
        # while的嵌套等级
        self.while_count = 0
        
        self.in_function = False # 是否在函数里
        # 当前函数名称
        self.now_function = 0
        # 选中的寄存器 注意：此处的结果寄存器仍然使用?来表示
        self.selected_register = ""
        # 选中的跳跃字符
        self.selected_jump = Stack(None)
        # 初始化过的跳跃字符
        self.inited_jump = ""
        # 选中的引用字符
        self.selected_ref = ""
    
    # 下一个
    def next(self, ignore = False) -> str:
        # 最后一个
        if self.codes[self.position + 1] == "\0":
            if ignore:
                return None
            raise SyntaxError()
        return self.codes[self.position + 1].lower()
    
    # 判断下一个
    # 如果指定了type，则遇到不对的就报错
    # 没有指定type，返回下一个的type
    def check_next(self, type = None) -> int:
        char = self.next()
        current_type = None
        if char in "qwertyui?":
            current_type = REG 
        elif char in "asdfzxcbnm":
            current_type = JMP
        elif char in "ophjkl":
            current_type = REF
        elif char in "^v]['.@!$:/*%":
            current_type = UNOP
        elif char in "+-~<>=&|":
            current_type = BINOP
        elif char in "\\0`;_":
            current_type = CMD
        elif char in "{}()":
            current_type = STMT
        if type == None:
            return current_type
        if current_type != type:
            self.syntax_error()
    
    def eat(self) -> str:
        # 最后一个
        if self.codes[self.position + 1] == "\0":
            raise HFSyntaxError()
        self.position += 1
        return self.codes[self.position].lower()
        
    # 报错（语法）
    def syntax_error(self) -> None:
        if self.position == -1:
            self.position += 1
        error = HFSyntaxError()
        error.error_exp = self.codes[
            tools.find_prev_char(self.codes, self.position, "\n") + 1: 
            tools.find_next_char(self.codes, self.position, "\n")
        ]
        raise error
    
    # 检查是否选中
    def check_selected(self, type: int) -> None:
        if type == REG:
            if self.selected_register == "":
                self.syntax_error()
        elif type == JMP:
            if self.selected_jump == "":
                self.syntax_error()
        elif type == REF:
            if self.selected_ref == "":
                self.syntax_error()
    
    def add_code(self, code: str) -> None:
        if self.while_count > 0:
            for i in range(self.while_count):
                code = self.add_tab(code)
        
        if self.in_function:
            self.head_code += self.add_tab(code) + "\n"
        else:
            self.compiled_code += self.add_tab(code) + "\n"
        
    def add_tab(self, code: str) -> str:
        return "    " + code
    
    # 开始编译
    # 返回编译后的Python代码
    def compile(self) -> str:
        while True:
            if self.codes[self.position + 1] == "\0":
                return self.head_code + self.compiled_code + self.run_code
            char = self.next()
            type = self.check_next()
            
            # 跳过空白
            if char in " \n\t\0":
                self.eat()
                continue
            
            # 选中寄存器
            if type == REG:
                self.eat()
                if char == "?":
                    self.selected_register = "res"
                else:
                    self.selected_register = char
                continue
            # 选中跳跃字符
            if type == JMP:
                self.eat()
                self.selected_jump.push(char)
                continue
            # 选中引用字符
            if type == REF:
                self.eat()
                self.selected_ref = char
                continue
            
            # 一元运算
            if type == UNOP:
                # 加减
                if char == "^" or char == "v":
                    self.check_selected(REG)
                    total = 0
                    while True:
                        char = self.next(True)
                        if char == "^":
                            total += 1
                        elif char == "v":
                            total -= 1
                        else:
                            break
                        self.eat()
                    self.add_code(f"{self.selected_register} += {total}")
                    continue
                # 归零
                if char == "*":
                    self.check_selected(REG)
                    self.eat()
                    self.add_code(f"{self.selected_register} = 0")
                    continue
                # 输出
                if char == ".":
                    self.check_selected(REG)
                    self.eat()
                    self.add_code(f"print(chr({self.selected_register}), end = '')")
                    continue
                # 输出数字
                if char == ":":
                    self.check_selected(REG)
                    self.eat()
                    self.add_code(f"print({self.selected_register}, end = '')")
                    continue
                # 输入
                if char == "@":
                    self.check_selected(REG)
                    self.eat()
                    self.add_code(f"{self.selected_register} = ord(msvcrt.getwch())")
                    self.add_code(f"print(chr({self.selected_register}), end = '')")
                    continue
                # 输入数字
                if char == "%":
                    self.check_selected(REG)
                    self.eat()
                    self.add_code(f"{self.selected_register} = int(input())")
                    continue
                # 入栈
                if char == "]":
                    self.check_selected(REG)
                    self.eat()
                    self.add_code(f"stack.append({self.selected_register})")
                    continue
                # 出栈
                if char == "[":
                    self.check_selected(REG)
                    self.eat()
                    self.add_code(f"{self.selected_register} = stack.pop()")
                    continue
                # 取反
                if char == "!":
                    self.check_selected(REG)
                    self.eat()
                    self.add_code(f"res = int(not {self.selected_register})")
                    continue
                # 记录此处语句块
                if char == "'":
                    self.check_selected(JMP)
                    self.eat()
                    self.head_code += f"def _{self.now_function}():\n"
                    self.in_function = True
                    self.add_code("global q, w, e, r, t, y, u, i, res")
                    continue
                # 跳到语句块
                if char == "/":
                    self.check_selected(JMP)
                    if not self.selected_jump.to_list()[-1] in self.inited_jump:
                        self.syntax_error()
                    self.eat()
                    self.add_code(f"{self.selected_jump.to_list()[-1]}()")
                    continue
                # 跳到引用
                if char == "$":
                    self.check_selected(REF)
                    self.eat()
                    # 寄存器字典
                    reg_dict = "_registers = {"
                    for reg_char in "qwertyui":
                        reg_dict += f"'{reg_char}': {reg_char}, "
                    reg_dict += "'?': res}"
                    self.add_code(reg_dict)
                    # 调用
                    self.add_code(f"{self.selected_ref}(_registers, stack)")
                    self.add_code("q, w, e, r, t, y, u, i, res = _registers.values()")
                    continue
                    
            # 二元运算
            if type == BINOP:
                if self.codes[self.position + 2] == "\0":
                    return self.head_code + self.compiled_code + self.run_code
                self.check_selected(REG)
                self.eat()
                self.check_next(REG)
                source = self.eat()
                if source == "?":
                    source = "res"
                
                # 加寄存器
                if char == "+":
                    self.add_code(f"{self.selected_register} += {source}")
                    self.selected_register = source
                    continue
                # 减寄存器
                if char == "-":
                    self.add_code(f"{self.selected_register} -= {source}")
                    self.selected_register = source
                    continue
                # 传送数据
                if char == "~":
                    self.add_code(f"{self.selected_register} = {source}")
                    self.selected_register = source
                    continue
                # 大于
                if char == ">":
                    self.add_code(f"res = int({self.selected_register} > {source})")
                    self.selected_register = source
                    continue
                # 小于
                if char == "<":
                    self.add_code(f"res = int({self.selected_register} < {source})")
                    self.selected_register = source
                    continue
                # 等于
                if char == "=":
                    self.add_code(f"res = int({self.selected_register} == {source})")
                    self.selected_register = source
                    continue
                # 与
                if char == "&":
                    self.add_code(f"res = int({self.selected_register} and {source})")
                    self.selected_register = source
                    continue
                # 或
                if char == "|":
                    self.add_code(f"res = int({self.selected_register} or {source})")
                    self.selected_register = source
                    continue
            
            # 语句块
            if type == STMT:
                # 语句
                if char == "{":
                    self.eat()
                    continue
                elif char == "}":
                    self.eat()
                    self.in_function = False
                    selected_jump = self.selected_jump.pop()
                    self.inited_jump += selected_jump
                    self.head_code += f"{selected_jump} = _{self.now_function}\n"
                    continue
            
                # 循环
                if char == "(":
                    self.check_selected(REG)
                    self.eat()
                    self.add_code(f"while {self.selected_register} != 0:")
                    self.while_count += 1
                    continue
                elif char == ")":
                    self.eat()
                    self.while_count -= 1
                    continue
            
            # 命令
            if type == CMD:
                if char == "\\":
                    self.eat()
                    self.add_code("print()")
                    continue
                if char == "0":
                    self.eat()
                    self.add_code("sys.exit(0)")
                    continue
                if char == "`":
                    self.check_selected(REG)
                    if self.while_count == 0:
                        self.syntax_error()
                    self.eat()
                    self.add_code(f"if {self.selected_register} != 0:")
                    self.add_code(f"    break")
                    continue
                if char == ";":
                    if self.while_count == 0:
                        self.syntax_error()
                    self.eat()
                    self.add_code(f"if {self.selected_register} != 0:")
                    self.add_code(f"    continue")
                    continue
                if char == "_":
                    self.eat()
                    self.add_code("os.system(\"cls\")")
                    continue
            
            # 没有任何一个匹配
            print(char)
            self.syntax_error()
