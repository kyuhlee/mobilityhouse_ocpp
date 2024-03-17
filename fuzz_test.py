from argparse import Namespace
from pyjfuzz.lib import *

#config = PJFConfiguration(Namespace(json={"test": ["1", 2, True]}, nologo=True, level=3, debug=True))
# Heartbeat: '[2,"3f2409f0-85a7-426c-982d-77e0e6412356","Heartbeat",{}]'
#fuzz_config = PJFConfiguration(Namespace(json={"test": ["1", 2, True]}, nologo=True, level=6))
config = PJFConfiguration(Namespace(json=[1, "1", "Heartbeat", 1], nologo=True, level=3, debug=True))
fuzzer = PJFFactory(config)
#while True:
for i in range(0, 10):
    print(fuzzer.fuzzed)