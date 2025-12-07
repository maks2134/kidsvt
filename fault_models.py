from typing import Dict, Tuple, List
from enum import Enum
import numpy as np

class FaultType(Enum):
    STUCK_AT_0 = "Stuck-at-0 (SA0)"
    STUCK_AT_1 = "Stuck-at-1 (SA1)"
    TRANSITION_0_TO_1 = "Transition 0→1 fault"
    TRANSITION_1_TO_0 = "Transition 1→0 fault"
    COUPLING = "Coupling fault"
    DATA_RETENTION = "Data retention fault"
    ADDRESS_DECODER = "Address decoder fault"
    BRIDGING = "Bridging fault"

class FaultModel:
    def __init__(self, ram_model):
        self.ram = ram_model
        self.active_faults = {}
    
    def apply_fault(self, address: int, fault_type: FaultType, 
                   bit_position: int = 0, **kwargs) -> bool:
        if not self.ram._validate_address(address):
            return False
        
        key = (address, bit_position)
        self.active_faults[key] = {
            'type': fault_type,
            'params': kwargs
        }
        self.ram.inject_fault(address, fault_type.value, bit_position)
        return True
    
    def simulate_read(self, address: int) -> int:
        if not self.ram._validate_address(address):
            return -1
        
        binary = self.ram.read_binary(address)
        
        for (fault_addr, bit_pos), fault_info in self.active_faults.items():
            if fault_addr == address:
                fault_type = fault_info['type']
                binary = self._apply_fault_to_binary(
                    binary, fault_type, bit_pos, fault_info['params']
                )
        
        return self.ram._binary_to_int(binary)
    
    def simulate_write(self, address: int, data: int) -> bool:
        if not self.ram._validate_address(address):
            return False
        
        success = self.ram.write(address, data)
        if not success: return False
        
        binary = self.ram.read_binary(address)
        
        for (fault_addr, bit_pos), fault_info in self.active_faults.items():
            if fault_addr == address:
                fault_type = fault_info['type']
                binary = self._apply_fault_to_binary(
                    binary, fault_type, bit_pos, fault_info['params']
                )
                self.ram.memory[address] = binary
        
        return True
    
    def _apply_fault_to_binary(self, binary: np.ndarray, fault_type: FaultType,
                              bit_pos: int, params: dict) -> np.ndarray:
        result = binary.copy()
        if bit_pos >= len(binary): return result
        
        if fault_type == FaultType.STUCK_AT_0:
            result[bit_pos] = 0
        elif fault_type == FaultType.STUCK_AT_1:
            result[bit_pos] = 1
        elif fault_type == FaultType.TRANSITION_0_TO_1:
            if result[bit_pos] == 0: result[bit_pos] = 0
        elif fault_type == FaultType.TRANSITION_1_TO_0:
            if result[bit_pos] == 1: result[bit_pos] = 1
        elif fault_type == FaultType.COUPLING:
            coupling_bit = params.get('coupling_bit', 0)
            if coupling_bit < len(binary):
                result[coupling_bit] = 1 - result[coupling_bit]
        elif fault_type == FaultType.BRIDGING:
            bridge_bit = params.get('bridge_bit', 0)
            if bridge_bit < len(binary):
                result[bridge_bit] = result[bit_pos]
        
        return result
    
    def remove_fault(self, address: int, bit_position: int = 0):
        key = (address, bit_position)
        if key in self.active_faults:
            del self.active_faults[key]
            self.ram.remove_fault(address, bit_position)
    
    def clear_all_faults(self):
        self.active_faults.clear()
        self.ram.faults.clear()
    
    def get_active_faults(self) -> Dict:
        return self.active_faults.copy()