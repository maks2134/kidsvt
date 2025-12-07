#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QComboBox, 
                             QSpinBox, QTextEdit, QTableWidget, QTableWidgetItem,
                             QGroupBox, QTabWidget, QMessageBox, QProgressBar,
                             QSplitter)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor

# Импорт локальных модулей
from ram_model import RAMModel
from fault_models import FaultModel, FaultType
from testing_algorithms import (MarchC, MarchB, Checkerboard, WalkingOne, 
                                GallopingPattern, TestingAlgorithm)
from verification import Verifier, DynamicVerifier

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ram = RAMModel(address_bits=8, data_bits=8)
        self.fault_model = FaultModel(self.ram)
        self.current_test_result = None
        self.init_ui()
        self.run_verification()
    
    def init_ui(self):
        self.setWindowTitle("Цифровой двойник ОЗУ")
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)
        
        right_panel = self.create_results_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
    
    def create_control_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Faults
        fault_group = QGroupBox("Неисправности")
        fault_layout = QVBoxLayout()
        self.fault_type_combo = QComboBox()
        for fault_type in FaultType:
            self.fault_type_combo.addItem(fault_type.value, fault_type)
        fault_layout.addWidget(self.fault_type_combo)
        
        self.fault_address_spin = QSpinBox()
        self.fault_address_spin.setRange(0, 255)
        self.fault_address_spin.setPrefix("Addr: ")
        fault_layout.addWidget(self.fault_address_spin)
        
        self.fault_bit_spin = QSpinBox()
        self.fault_bit_spin.setRange(0, 7)
        self.fault_bit_spin.setPrefix("Bit: ")
        fault_layout.addWidget(self.fault_bit_spin)
        
        self.inject_fault_btn = QPushButton("Внедрить")
        self.inject_fault_btn.clicked.connect(self.inject_fault)
        fault_layout.addWidget(self.inject_fault_btn)
        
        self.remove_fault_btn = QPushButton("Удалить")
        self.remove_fault_btn.clicked.connect(self.remove_fault)
        fault_layout.addWidget(self.remove_fault_btn)

        self.clear_faults_btn = QPushButton("Очистить все")
        self.clear_faults_btn.clicked.connect(self.clear_all_faults)
        fault_layout.addWidget(self.clear_faults_btn)

        fault_group.setLayout(fault_layout)
        layout.addWidget(fault_group)

        # Tests
        test_group = QGroupBox("Тестирование")
        test_layout = QVBoxLayout()
        self.test_algorithm_combo = QComboBox()
        self.test_algorithm_combo.addItem("March C-", "march_c")
        self.test_algorithm_combo.addItem("March B", "march_b")
        self.test_algorithm_combo.addItem("Checkerboard", "checkerboard")
        self.test_algorithm_combo.addItem("Walking One (Lite)", "walking_one")
        self.test_algorithm_combo.addItem("Galloping (Lite)", "galloping")
        test_layout.addWidget(self.test_algorithm_combo)

        self.run_test_btn = QPushButton("Запустить тест")
        self.run_test_btn.clicked.connect(self.run_test)
        test_layout.addWidget(self.run_test_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        test_layout.addWidget(self.progress_bar)
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)

        # Verification
        ver_group = QGroupBox("Верификация")
        ver_layout = QVBoxLayout()
        self.verify_btn = QPushButton("Статическая верификация")
        self.verify_btn.clicked.connect(self.run_verification)
        ver_layout.addWidget(self.verify_btn)

        self.dynamic_test_btn = QPushButton("Динамические тесты")
        self.dynamic_test_btn.clicked.connect(self.run_dynamic_tests)
        ver_layout.addWidget(self.dynamic_test_btn)
        ver_group.setLayout(ver_layout)
        layout.addWidget(ver_group)

        # Memory Control
        mem_group = QGroupBox("Память")
        mem_layout = QVBoxLayout()
        self.clear_mem_btn = QPushButton("Сброс (Reset)")
        self.clear_mem_btn.clicked.connect(self.reset_all)
        mem_layout.addWidget(self.clear_mem_btn)
        mem_group.setLayout(mem_layout)
        layout.addWidget(mem_group)

        # Info
        self.faults_info_label = QLabel("Нет активных неисправностей")
        layout.addWidget(self.faults_info_label)

        layout.addStretch()
        return panel

    def create_results_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.tabs = QTabWidget()

        # Tab 1: Steps
        viz_tab = QWidget()
        viz_layout = QVBoxLayout(viz_tab)
        self.test_steps_table = QTableWidget()
        self.test_steps_table.setColumnCount(6)
        self.test_steps_table.setHorizontalHeaderLabels(["Шаг", "Адр", "Оп", "Ожид", "Факт", "Рез"])
        viz_layout.addWidget(self.test_steps_table)
        self.tabs.addTab(viz_tab, "Шаги")

        # Tab 2: Memory
        mem_tab = QWidget()
        mem_layout = QVBoxLayout(mem_tab)
        self.memory_table = QTableWidget()
        self.memory_table.setColumnCount(9)
        self.memory_table.setHorizontalHeaderLabels(["Адр"] + [f"B{i}" for i in range(8)])
        mem_layout.addWidget(self.memory_table)
        self.update_memory_table_btn = QPushButton("Обновить")
        self.update_memory_table_btn.clicked.connect(self.update_memory_table)
        mem_layout.addWidget(self.update_memory_table_btn)
        self.tabs.addTab(mem_tab, "Память")

        # Tab 3: Reports
        rep_tab = QWidget()
        rep_layout = QVBoxLayout(rep_tab)
        self.verification_text = QTextEdit()
        self.verification_text.setReadOnly(True)
        rep_layout.addWidget(self.verification_text)
        self.tabs.addTab(rep_tab, "Отчеты")

        layout.addWidget(self.tabs)
        return panel

    def inject_fault(self):
        ft = self.fault_type_combo.currentData()
        addr = self.fault_address_spin.value()
        bit = self.fault_bit_spin.value()

        params = {}
        if ft == FaultType.COUPLING:
            params['coupling_bit'] = (bit + 1) % 8
        elif ft == FaultType.BRIDGING:
            params['bridge_bit'] = (bit + 1) % 8

        if self.fault_model.apply_fault(addr, ft, bit, **params):
            self.update_faults_info()
            self.update_memory_table()

    def remove_fault(self):
        self.fault_model.remove_fault(self.fault_address_spin.value(), self.fault_bit_spin.value())
        self.update_faults_info()
        self.update_memory_table()

    def clear_all_faults(self):
        self.fault_model.clear_all_faults()
        self.update_faults_info()
        self.update_memory_table()

    def reset_all(self):
        self.ram.reset()
        self.fault_model.clear_all_faults()
        self.update_faults_info()
        self.update_memory_table()
        self.verification_text.setText("Система сброшена")
        self.test_steps_table.setRowCount(0)

    def run_test(self):
        algo_name = self.test_algorithm_combo.currentData()
        algos = {
            "march_c": MarchC, "march_b": MarchB,
            "checkerboard": Checkerboard, "walking_one": WalkingOne,
            "galloping": GallopingPattern
        }

        if algo_name not in algos: return

        self.run_test_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.tabs.setCurrentIndex(0)
        QApplication.processEvents()

        algo = algos[algo_name](self.ram, self.fault_model)
        try:
            res = algo.run()
            self.display_results(res)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

        self.run_test_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

    def display_results(self, result):
        self.test_steps_table.setRowCount(len(result.test_steps))
        for i, step in enumerate(result.test_steps):
            self.test_steps_table.setItem(i, 0, QTableWidgetItem(step['step']))
            self.test_steps_table.setItem(i, 1, QTableWidgetItem(str(step['address'])))
            self.test_steps_table.setItem(i, 2, QTableWidgetItem(step['operation']))
            self.test_steps_table.setItem(i, 3, QTableWidgetItem(hex(step['expected'])))
            self.test_steps_table.setItem(i, 4, QTableWidgetItem(hex(step['actual'])))
            res_item = QTableWidgetItem("OK" if step['passed'] else "FAIL")
            res_item.setForeground(QColor("green") if step['passed'] else QColor("red"))
            self.test_steps_table.setItem(i, 5, res_item)

        txt = f"Результат: {'PASSED' if result.passed else 'FAILED'}\n"
        txt += f"Ошибок: {len(result.errors)}\n"
        if result.errors:
            txt += "Первые 5 ошибок:\n" + "\n".join(result.errors[:5])
        self.verification_text.setText(txt)
        self.tabs.setCurrentIndex(2) # Switch to Report

    def run_verification(self):
        self.tabs.setCurrentIndex(2)
        log = "ЗАПУСК ВЕРИФИКАЦИИ...\n"

        r1 = Verifier.verify_ram_model(self.ram)
        log += f"RAM Model: {'OK' if r1.passed else 'FAIL'}\n"

        r2 = Verifier.verify_fault_model(self.fault_model)
        log += f"Fault Model: {'OK' if r2.passed else 'FAIL'}\n"

        r3 = Verifier.validate_digital_twin(self.ram, self.fault_model)
        log += f"Integration: {'OK' if r3.passed else 'FAIL'}\n"

        self.verification_text.setText(log)

    def run_dynamic_tests(self):
        self.tabs.setCurrentIndex(2)
        self.progress_bar.setVisible(True)
        QApplication.processEvents()

        log = self.verification_text.toPlainText() + "\nЗАПУСК ДИНАМИЧЕСКИХ ТЕСТОВ...\n"

        d1 = DynamicVerifier.run_stress_test(self.ram)
        log += f"Stress Test: {'OK' if d1.passed else 'FAIL'} ({d1.execution_time:.3f}s)\n"

        d2 = DynamicVerifier.run_integrity_over_time_test(self.ram)
        log += f"Integrity: {'OK' if d2.passed else 'FAIL'}\n"

        d3 = DynamicVerifier.run_pattern_stress(self.ram)
        log += f"Pattern Stress: {'OK' if d3.passed else 'FAIL'}\n"

        self.verification_text.setText(log)
        self.progress_bar.setVisible(False)

    def update_faults_info(self):
        cnt = len(self.fault_model.active_faults)
        self.faults_info_label.setText(f"Активных неисправностей: {cnt}")

    def update_memory_table(self):
        state = self.ram.get_memory_state()
        rows = min(256, len(state))
        self.memory_table.setRowCount(rows)
        faults = self.fault_model.active_faults

        for i in range(rows):
            self.memory_table.setItem(i, 0, QTableWidgetItem(str(i)))
            for j in range(8):
                val = state[i][j]
                item = QTableWidgetItem(str(val))
                if (i, j) in faults:
                    item.setBackground(QColor(255, 200, 200))
                self.memory_table.setItem(i, j+1, item)

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()