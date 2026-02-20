import sys
import os

print("Python Executable:", sys.executable)
print("System Path:")
for p in sys.path:
    print(p)

try:
    import dspy
    print("DSPy imported successfully:", dspy.__file__)
except ImportError as e:
    print("ImportError:", e)
