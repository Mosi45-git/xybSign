import sys

# 打印整个 argv 列表
print("All command line arguments:", sys.argv)

# 打印脚本名称
print("Script name:", sys.argv)

# 打印传递给脚本的第一个参数（如果存在）
if len(sys.argv) > 1:
    print("First argument:", sys.argv)
else:
    print("No arguments were provided.")

# 遍历并打印所有参数（除了脚本名称）
for i in range(1, len(sys.argv)):
    print(f"Argument {i}:", sys.argv[i])
  
