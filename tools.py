# 寻找上一个字符
import sys
Interpreter = None
HFSyntaxError = None
RuntimeException = None

def find_prev_char(string:str, position: int, char: str) -> int:
    current_char = ""
    if position == 0 or not char in string[:position - 1]:
        return -1
    while current_char != char:
        position -= 1
        current_char = string[position]
    return position

# 寻找下一个字符
def find_next_char(string:str, position: int, char: str) -> int:
    current_char = ""
    if not char in string[position:]:
        return -1
    while current_char != char:
        position += 1
        current_char = string[position]
    return position

# 图形化寄存器与堆栈
def diagram(registers: dict, stack: list) -> str:
    text = f""" 数据    Q={registers["q"]}   W={registers["w"]}   E={registers["e"]}   R={registers["r"]}
寄存器   T={registers["t"]}   Y={registers["y"]}   U={registers["u"]}   I={registers["i"]}
结果寄存器   ?={registers["?"]}
"""
    stack_text = [
        "┌──────┐",
        "│      │",
        "│  栈  │",
        "│      │",
        "└──────┘"
    ]
    if len(stack) == 0:
        stack_text[2] += "  无内容  "
    else:
        for x in stack:
            stack_text[2] += f" {x} "
            for i in range(5):
                if i == 2:
                    stack_text[i] += "│"
                elif i == 0:
                    stack_text[i] += " " * (2 + len(str(x))) + "┐"
                elif i == 4:
                    stack_text[i] += " " * (2 + len(str(x))) + "┘"
                else:
                    stack_text[i] += " " * (2 + len(str(x))) + "│"
    for line in stack_text:
        text += "\n" + line
    return text
            
# 获取引用
def get_references(ref_lines: list) -> dict:
    ref_functions = {
        "o": None, "p": None, "h": None, "j": None, "k": None, "l": None, 
    }
    keys = "ophjkl"
    key_index = 0
    # 读取信息
    for l in ref_lines:
        file, func_text = l.split(" ")
        functions = func_text.split(",")
        module = __import__(file)
        for f in functions:
            ref_functions[keys[key_index]] = eval(f"module.{f}")
            key_index += 1
            if key_index == 6:
                break
    return ref_functions

# 交互式
def run_interactive(ref_dict: dict) -> None:
    print("HyperFuck 1.2 交互式解释器 交互式工具")
    print("单独输入1来查看寄存器与堆栈使用。")
    
    code = get_input_code()
    interpreter = Interpreter([code])
    if ref_dict != None:
        interpreter.ref_functions = ref_dict
    if code == "1\n\0":
        print(diagram(interpreter.registers, interpreter.stack.to_list()))
    else:
        interpret_code(interpreter)
    print()
    
    while True:
        try:
            code = get_input_code()
            if "',`/" in code:
                print("警告：交互式解释器不能使用跳跃指令。")
            if code == "1\n\0":
                print(diagram(interpreter.registers, interpreter.stack.to_list()))
                continue
                
        except EOFError:
            return
        interpreter.codes = code
        interpreter.position = -1
        interpret_code(interpreter)
        print()
        
            
def get_input_code() -> str:
    try:
        return input(">>> ") + "\n\0"
    except EOFError:
        sys.exit(0)
        
def interpret_code(interpreter: Interpreter) -> None:
    try:
        interpreter.interpret()
    except EOFError:
        pass
    except HFSyntaxError as e:
        print("\nHyperFuck 1.2 解释器 语法错误")
        print(f"    位于：{e.error_exp}")
        print(diagram(interpreter.registers, interpreter.stack.to_list()))
    except RuntimeException as e:
        print(f"\nHyperFuck VM 1.2 错误：{e.error_type}")
        print(f"    位于：{e.error_exp}\n")
        print(diagram(interpreter.registers, interpreter.stack.to_list()))
        print(f"\n当前寄存器：{interpreter.selected_register.upper()}   ", end = "")
        print(f"当前跳跃字符：{interpreter.selected_jump.upper()}   ", end = "")
        print(f"当前引用字符：{interpreter.selected_ref.upper()}")