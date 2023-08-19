To compile a OpenQASM file, use the Makefile in this folder. For a file named xx.qasm, use 'make xx'. This will produce an 'xx.ll' LLVM file and 'xx' executable. 

To run an executable, use '../test.sh xx'.

Use 'make clean' to clean up all *.ll files.

In the tests/ folder is a unittest, tests/test.py which runs sequences of GLI gates and checks if their outcomes are expected. To run test.py, first go into qcs/programs/qasm and run 'make' to compile all the test scripts in the tests/ folder. Then run 'python3 tests/test.py' to run the unittest.