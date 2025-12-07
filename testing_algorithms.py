from typing import List, Tuple, Dict
import numpy as np

class TestResult:
    def __init__(self):
        self.passed = True
        self.detected_faults = []
        self.test_steps = []
        self.errors = []
        self.coverage = 0.0
    
    def add_step(self, step: str, address: int, operation: str, 
                 expected: int, actual: int, passed: bool):
        self.test_steps.append({
            'step': step,
            'address': address,
            'operation': operation,
            'expected': expected,
            'actual': actual,
            'passed': passed
        })
        if not passed:
            self.passed = False
            self.errors.append(f"Адрес {address}: ожидалось {expected}, получено {actual}")

class TestingAlgorithm:
    def __init__(self, ram_model, fault_model):
        self.ram = ram_model
        self.fault_model = fault_model
        self.result = TestResult()
    
    def run(self) -> TestResult:
        self.result = TestResult()
        return self.result
    
    def _read_and_verify(self, address: int, expected: int, step: str) -> bool:
        actual = self.fault_model.simulate_read(address)
        passed = (actual == expected)
        self.result.add_step(step, address, "READ", expected, actual, passed)
        return passed
    
    def _write(self, address: int, data: int, step: str):
        self.fault_model.simulate_write(address, data)
        self.result.add_step(step, address, "WRITE", data, data, True)

class MarchC(TestingAlgorithm):
    def run(self) -> TestResult:
        self.result = TestResult()
        mem_size = self.ram.get_memory_size()
        
        # 1. Write 0
        for addr in range(mem_size): self._write(addr, 0, "Init 0")
        # 2. Read 0, Write 1 (Up)
        for addr in range(mem_size):
            self._read_and_verify(addr, 0, "R0 W1 Up")
            self._write(addr, 1, "R0 W1 Up")
        # 3. Read 1, Write 0 (Up)
        for addr in range(mem_size):
            self._read_and_verify(addr, 1, "R1 W0 Up")
            self._write(addr, 0, "R1 W0 Up")
        # 4. Read 0, Write 1 (Down)
        for addr in range(mem_size - 1, -1, -1):
            self._read_and_verify(addr, 0, "R0 W1 Down")
            self._write(addr, 1, "R0 W1 Down")
        # 5. Read 1, Write 0 (Down)
        for addr in range(mem_size - 1, -1, -1):
            self._read_and_verify(addr, 1, "R1 W0 Down")
            self._write(addr, 0, "R1 W0 Down")
        # 6. Read 0
        for addr in range(mem_size): self._read_and_verify(addr, 0, "Final R0")
        
        return self.result

class MarchB(TestingAlgorithm):
    def run(self) -> TestResult:
        self.result = TestResult()
        mem_size = self.ram.get_memory_size()
        for addr in range(mem_size): self._write(addr, 0, "Init 0")
        for addr in range(mem_size):
            self._read_and_verify(addr, 0, "R0")
            self._write(addr, 1, "W1")
        for addr in range(mem_size):
            self._read_and_verify(addr, 1, "R1")
            self._write(addr, 0, "W0")
        for addr in range(mem_size - 1, -1, -1):
            self._read_and_verify(addr, 0, "R0")
            self._write(addr, 1, "W1")
        for addr in range(mem_size - 1, -1, -1):
            self._read_and_verify(addr, 1, "R1")
            self._write(addr, 0, "W0")
        return self.result

class Checkerboard(TestingAlgorithm):
    def run(self) -> TestResult:
        self.result = TestResult()
        mem_size = self.ram.get_memory_size()
        for addr in range(mem_size):
            pattern = 0xAA if addr % 2 == 0 else 0x55
            self._write(addr, pattern, "Write Pattern")
        for addr in range(mem_size):
            expected = 0xAA if addr % 2 == 0 else 0x55
            self._read_and_verify(addr, expected, "Read Pattern")
        return self.result

class WalkingOne(TestingAlgorithm):
    def run(self) -> TestResult:
        self.result = TestResult()
        mem_size = self.ram.get_memory_size()
        for addr in range(mem_size): self._write(addr, 0, "Clear")
        
        # Упрощенная версия для скорости (проверяет только первые 16 ячеек, если память большая)
        limit = min(mem_size, 32) 
        for test_addr in range(limit):
            self._write(test_addr, 1, f"Set bit {test_addr}")
            for addr in range(limit):
                expected = 1 if addr == test_addr else 0
                self._read_and_verify(addr, expected, f"Check {addr}")
            self._write(test_addr, 0, "Clear bit")
        return self.result

class GallopingPattern(TestingAlgorithm):
    def run(self) -> TestResult:
        self.result = TestResult()
        mem_size = self.ram.get_memory_size()
        base = 0x55
        for addr in range(mem_size): self._write(addr, base, "Init")
        
        limit = min(mem_size, 32) # Ограничиваем для производительности UI
        for test_addr in range(limit):
            self._write(test_addr, 0xAA, "Flip")
            for addr in range(limit):
                if addr != test_addr:
                    self._read_and_verify(addr, base, "Verify Others")
            self._write(test_addr, base, "Restore")
        return self.result