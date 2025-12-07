import random
import time
from ram_model import RAMModel
from fault_models import FaultModel, FaultType

class VerificationResult:
    def __init__(self):
        self.passed = True
        self.errors = []
        self.warnings = []
        self.tests_passed = 0
        self.tests_total = 0
        self.execution_time = 0.0

    def add_error(self, message: str):
        self.errors.append(message)
        self.passed = False

    def add_test_result(self, passed: bool):
        self.tests_total += 1
        if passed: self.tests_passed += 1
        else: self.passed = False

class Verifier:
    @staticmethod
    def verify_ram_model(ram: RAMModel) -> VerificationResult:
        result = VerificationResult()
        try:
            ram.write(0, 0xAA)
            if ram.read(0) == 0xAA: result.add_test_result(True)
            else: result.add_error("Ошибка чтения/записи")

            if not ram.write(ram.get_memory_size() - 1, 0x55): result.add_test_result(False)
            elif ram.write(ram.get_memory_size(), 0x00): result.add_test_result(False)
            else: result.add_test_result(True)
        except Exception as e:
            result.add_error(str(e))
        return result

    @staticmethod
    def verify_fault_model(fault_model: FaultModel) -> VerificationResult:
        result = VerificationResult()
        try:
            fault_model.ram.clear()
            fault_model.clear_all_faults()
            fault_model.apply_fault(0, FaultType.STUCK_AT_0, 7)
            fault_model.simulate_write(0, 0xFF)
            if (fault_model.simulate_read(0) & 1) == 0: result.add_test_result(True)
            else: result.add_error("Stuck-at-0 failed")
        except Exception as e:
            result.add_error(str(e))
        return result

    @staticmethod
    def validate_digital_twin(ram: RAMModel, fault_model: FaultModel) -> VerificationResult:
        result = VerificationResult()
        try:
            ram.clear()
            fault_model.clear_all_faults()
            fault_model.apply_fault(0, FaultType.STUCK_AT_1, 7)
            fault_model.simulate_write(0, 0x00)
            if (fault_model.simulate_read(0) & 1) == 1: result.add_test_result(True)
            else: result.add_error("Validation failed")
        except Exception as e:
            result.add_error(str(e))
        return result

class DynamicVerifier:
    @staticmethod
    def run_stress_test(ram: RAMModel, iterations: int = 1000) -> VerificationResult:
        result = VerificationResult()
        start_time = time.time()
        expected = {}
        mem_size = ram.get_memory_size()
        try:
            for _ in range(iterations):
                addr = random.randint(0, mem_size - 1)
                data = random.randint(0, 255)
                ram.write(addr, data)
                expected[addr] = data

            errors = 0
            for addr, val in expected.items():
                if ram.read(addr) != val: errors += 1

            if errors == 0: result.add_test_result(True)
            else: result.add_error(f"Errors found: {errors}")
        except Exception as e:
            result.add_error(str(e))
        result.execution_time = time.time() - start_time
        return result

    @staticmethod
    def run_integrity_over_time_test(ram: RAMModel) -> VerificationResult:
        result = VerificationResult()
        try:
            target = 0
            val = 0xAA
            ram.write(target, val)
            for i in range(1, min(50, ram.get_memory_size())):
                ram.write(i, 0xFF)
            if ram.read(target) == val: result.add_test_result(True)
            else: result.add_error("Integrity lost")
        except Exception as e:
            result.add_error(str(e))
        return result

    @staticmethod
    def run_pattern_stress(ram: RAMModel) -> VerificationResult:
        result = VerificationResult()
        addr = 0
        try:
            passed = True
            for _ in range(50):
                ram.write(addr, 0x00)
                if ram.read(addr) != 0: passed = False
                ram.write(addr, 0xFF)
                if ram.read(addr) != 0xFF: passed = False
            result.add_test_result(passed)
        except Exception as e:
            result.add_error(str(e))
        return result