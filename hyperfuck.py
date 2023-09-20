# HyperFuck 主程序
import os
import shutil
import sys
from interpreter import *
from compiler import *

usage = """HyperFuck Release 1.2 解释器
用法：
    HyperFuck (-h | --help)
    HyperFuck [options] <主程序>

选项包括：
    -r | --reference <包含索引文件>
    -i | --interactive 交互式
    -c | -compile 编译到可执行文件
"""
    
if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.append("-h")
        
    # 帮助文档
    if sys.argv[1] == "-h" or sys.argv[1] == "--help":
        print(usage)
        sys.exit()
        
    # 引用索引
    ref_dict = None
    ref_lines = []
    if sys.argv[1] == "-r" or sys.argv[1] == "--reference":
        ref_file = sys.argv[2]
        try:
            with open(ref_file, "r") as f:
                ref_lines = f.readlines()
        except:
            print(f"错误：无法打开引用索引文件：{ref_file}")
            sys.exit(1)
        ref_dict = tools.get_references(ref_lines)
        
    # 交互式
    if "-i" in sys.argv or "--interactive" in sys.argv:
        tools.Interpreter = Interpreter
        tools.HFSyntaxError = HFSyntaxError
        tools.RuntimeException = RuntimeException
        tools.run_interactive(ref_dict)
        sys.exit(0)
    
    # 代码
    code_file = sys.argv[-1]
    try:
        with open(code_file, "r") as f:
            lines = f.readlines()
    except:
        print(f"错误：无法打开主程序文件：{code_file}")
        print("HyperFuck只支持GBK编码")
        sys.exit(1)
    
    # 编译
    if "-c" in sys.argv or "--compile" in sys.argv:
        compiler = Compiler(lines, ref_lines)
        compiled_code = compiler.compile()
        file_name = os.path.splitext(os.path.split(code_file)[-1])[0]
        
        if os.path.exists(".compile"):
            shutil.rmtree(".compile")
        os.mkdir(".compile")
        with open(f".compile\\{file_name}.py", "w", encoding = "utf-8") as f:
            f.write(compiled_code)
        
        print("Compilation finished.")
        
        sys.exit(0)

    try:
        interpreter = Interpreter(lines)
        if ref_dict != None:
            interpreter.ref_functions = ref_dict
        interpreter.interpret()
    except EOFError:
        pass
    except HFSyntaxError as e:
        print("\nHyperFuck 1.2 解释器 语法错误")
        print(f"    位于：{e.error_exp}")
        print(tools.diagram(interpreter.registers, interpreter.stack.to_list()))
    except RuntimeException as e:
        print(f"\nHyperFuck VM 1.2 错误：{e.error_type}")
        print(f"    位于：{e.error_exp}\n")
        print(tools.diagram(interpreter.registers, interpreter.stack.to_list()))
        print(f"\n当前寄存器：{interpreter.selected_register.upper()}   ", end = "")
        print(f"当前跳跃字符：{interpreter.selected_jump.upper()}   ", end = "")
        print(f"当前引用字符：{interpreter.selected_ref.upper()}")
        
    
    #print(tools.diagram(interpreter.registers, interpreter.stack.to_list()))
    