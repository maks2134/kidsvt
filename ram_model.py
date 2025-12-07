import numpy as np
from typing import Optional, List, Tuple
from enum import Enum

class RAMModel:
    """
    Цифровой двойник ОЗУ
    """
    
    def __init__(self, address_bits: int = 8, data_bits: int = 8):
        self.address_bits = address_bits
        self.data_bits = data_bits
        self.memory_size = 2 ** address_bits
        self.memory = np.zeros((self.memory_size, data_bits), dtype=np.uint8)
        self.faults = {} 
        
    def write(self, address: int, data: int) -> bool:
        if not self._validate_address(address):
            return False
        binary_data = self._int_to_binary(data, self.data_bits)
        self.memory[address] = binary_data
        return True
    
    def read(self, address: int) -> int:
        if not self._validate_address(address):
            return -1
        binary_data = self.memory[address]
        return self._binary_to_int(binary_data)
    
    def read_binary(self, address: int) -> np.ndarray:
        if not self._validate_address(address):
            return np.zeros(self.data_bits, dtype=np.uint8)
        return self.memory[address].copy()
    
    def clear(self):
        self.memory.fill(0)
        self.faults.clear()
    
    def reset(self):
        self.clear()
    
    def get_memory_state(self) -> np.ndarray:
        return self.memory.copy()
    
    def get_memory_size(self) -> int:
        return self.memory_size
    
    def _validate_address(self, address: int) -> bool:
        return 0 <= address < self.memory_size
    
    def _int_to_binary(self, value: int, bits: int) -> np.ndarray:
        binary_str = format(value & ((1 << bits) - 1), f'0{bits}b')
        return np.array([int(bit) for bit in binary_str], dtype=np.uint8)
    
    def _binary_to_int(self, binary: np.ndarray) -> int:
        result = 0
        for bit in binary:
            result = (result << 1) | int(bit)
        return result
    
    def inject_fault(self, address: int, fault_type: str, bit_position: int = 0):
        if not self._validate_address(address):
            return
        self.faults[(address, bit_position)] = fault_type
    
    def remove_fault(self, address: int, bit_position: int = 0):
        key = (address, bit_position)
        if key in self.faults:
            del self.faults[key]