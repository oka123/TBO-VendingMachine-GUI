import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                             QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtGui import QPixmap, QFont, QIcon, QColor
from PyQt6.QtCore import QObject, pyqtSignal, QPropertyAnimation, QRect, Qt

# ==============================================================================
# BAGIAN 1: LOGIKA INTI (DFA VENDING MACHINE DENGAN QT SIGNALS)
# ==============================================================================
class VendingMachineLogic(QObject):
    """
    Logika DFA Vending Machine.
    Menggunakan Qt Signals untuk berkomunikasi dengan GUI tanpa dependensi langsung.
    """
    # Signals untuk mengirim update ke GUI
    display_updated = pyqtSignal(str)
    transaction_reset = pyqtSignal(str)
    stock_updated = pyqtSignal(dict)
    dispense_triggered = pyqtSignal(list)
    change_returned = pyqtSignal(int)
    state_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.menu_prices = {
            'VanillaScoop': 10000, 'ChocolateScoop': 10000,
            'CaramelTopping': 2000, 'SprinklesTopping': 2000
        }
        self.stock = {item: 10 for item in self.menu_prices}
        self.reset_transaction()

    def reset_transaction(self):
        """Mengembalikan mesin ke state awal untuk transaksi baru."""
        self.current_state = 'Idle'
        self.selected_items = []
        self.total_price = 0
        self.money_inserted = 0
        self.state_changed.emit(self.current_state)
        # Emit sinyal untuk update stok ke GUI
        self.stock_updated.emit(self.stock.copy())
        self.transaction_reset.emit("Mesin Siap! Silakan pilih item.")

    def delta(self, input_symbol):
        """Fungsi Transisi (δ). Memproses input dan mengubah state."""
        state = self.current_state

        if state in ['Idle', 'WaitingForSelection']:
            if input_symbol in self.menu_prices:
                if self.stock[input_symbol] > 0:
                    self.selected_items.append(input_symbol)
                    self.total_price += self.menu_prices[input_symbol]
                    self.current_state = 'WaitingForSelection'
                    self.display_updated.emit(f"'{input_symbol}' ditambahkan.")
                else:
                    self.display_updated.emit(f"Maaf, '{input_symbol}' habis.")
            elif input_symbol == 'Checkout' and self.selected_items:
                self.current_state = 'WaitingForPayment'
                self.display_updated.emit(f"Total: Rp {self.total_price}. Silakan bayar.")
            elif input_symbol == 'Cancel':
                self.reset_transaction()
            else:
                self.display_updated.emit("Pilih item sebelum checkout.")

        elif state == 'WaitingForPayment':
            if isinstance(input_symbol, int):
                self.money_inserted += input_symbol
                needed = self.total_price - self.money_inserted
                if self.money_inserted >= self.total_price:
                    self.current_state = 'DispensingItem'
                    self.display_updated.emit("Pembayaran Lunas! Memproses...")
                    self.trigger_internal_transition('__dispense__')
                else:
                    self.display_updated.emit(f"Uang diterima. Kurang Rp {needed}.")
            elif input_symbol == 'Cancel':
                change_to_return = self.money_inserted
                self.reset_transaction()
                self.display_updated.emit(f"Dibatalkan. Uang dikembalikan.")
                self.change_returned.emit(change_to_return)

        self.state_changed.emit(self.current_state)

    def trigger_internal_transition(self, internal_symbol):
        """Memicu transisi otomatis (dispensing)."""
        if internal_symbol == '__dispense__':
            for item in self.selected_items:
                self.stock[item] -= 1
            self.dispense_triggered.emit(self.selected_items.copy())
            self.stock_updated.emit(self.stock.copy())

    def finalize_transaction(self):
        """Dipanggil oleh GUI setelah animasi dispensing selesai."""
        self.current_state = 'ReturningChange'
        self.state_changed.emit(self.current_state)
        change = self.money_inserted - self.total_price
        
        self.reset_transaction() # Reset untuk transaksi berikutnya
        if change > 0:
            self.display_updated.emit(f"Transaksi Selesai! Ambil kembalian Anda.")
            self.change_returned.emit(change)
        else:
            self.display_updated.emit("Transaksi Selesai! Terima kasih.")


# ==============================================================================
# BAGIAN 2: GUI (ANTARMUKA PENGGUNA) DENGAN PYQT6
# ==============================================================================
class VendingMachineGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vending Machine Es Krim Cerdas")
        self.setWindowIcon(QIcon("images/app_icon.png"))
        self.setGeometry(100, 100, 1000, 750)

        # Inisialisasi logika DFA
        self.logic = VendingMachineLogic()

        # Koneksi sinyal dari logika ke slot di GUI
        self.logic.display_updated.connect(self.update_status_display)
        self.logic.transaction_reset.connect(self.reset_ui)
        self.logic.stock_updated.connect(self.update_stock_display)
        self.logic.dispense_triggered.connect(self.run_dispense_animation)
        self.logic.change_returned.connect(self.display_change)
        self.logic.state_changed.connect(self.update_main_display)

        self.init_ui()
        self.logic.reset_transaction() # Inisialisasi tampilan awal

    def init_ui(self):
        """Membuat dan menata semua elemen GUI."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F0F8FF;
            }
            QLabel {
                font-family: 'Segoe UI';
            }
            QPushButton {
                font-family: 'Segoe UI';
                font-size: 14px;
                font-weight: bold;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            #ProductButton {
                background-color: #5F9EA0;
            }
            #ProductButton:hover {
                background-color: #4682B4;
            }
            #ProductButton:disabled {
                background-color: #A9A9A9;
            }
            #ControlButton {
                background-color: #3CB371;
            }
            #ControlButton:hover {
                background-color: #2E8B57;
            }
            #CancelButton {
                background-color: #DC143C;
            }
            #CancelButton:hover {
                background-color: #B22222;
            }
            #Panel {
                background-color: white;
                border-radius: 15px;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- Panel Kiri: Produk ---
        product_panel = QWidget()
        product_panel.setObjectName("Panel")
        product_panel_layout = QVBoxLayout(product_panel)
        main_layout.addWidget(product_panel, 2) # Lebar 2/3

        title_label = QLabel("Pilih Es Krim Favoritmu!")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        product_panel_layout.addWidget(title_label)
        
        self.product_grid = QGridLayout()
        product_panel_layout.addLayout(self.product_grid)
        self.product_widgets = {}
        items = list(self.logic.menu_prices.items())
        for i, (name, price) in enumerate(items):
            self.create_product_widget(i, name, price)

        # --- Panel Kanan: Kontrol & Display ---
        control_panel = QWidget()
        control_panel.setObjectName("Panel")
        control_panel_layout = QVBoxLayout(control_panel)
        main_layout.addWidget(control_panel, 1) # Lebar 1/3
        
        # Display Utama
        self.status_display = QLabel("Selamat Datang!")
        self.status_display.setFont(QFont("Segoe UI", 16))
        self.status_display.setWordWrap(True)
        self.status_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_display.setStyleSheet("padding: 15px; background-color: #E6E6FA; border-radius: 10px;")
        control_panel_layout.addWidget(self.status_display)

        self.cart_display = QLabel("Keranjang: Kosong")
        self.cart_display.setFont(QFont("Segoe UI", 12))
        self.cart_display.setWordWrap(True)
        control_panel_layout.addWidget(self.cart_display)
        
        self.total_price_display = QLabel("Total: Rp 0")
        self.total_price_display.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        control_panel_layout.addWidget(self.total_price_display)

        self.money_inserted_display = QLabel("Uang Masuk: Rp 0")
        self.money_inserted_display.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.money_inserted_display.setStyleSheet("color: green;")
        control_panel_layout.addWidget(self.money_inserted_display)
        
        control_panel_layout.addWidget(self.create_separator())
        
        # Tombol Uang
        control_panel_layout.addWidget(QLabel("Masukkan Uang:"))
        money_layout = QGridLayout()
        denominations = [2000, 5000, 10000, 20000]
        for i, value in enumerate(denominations):
            btn = QPushButton()
            btn.setIcon(QIcon(f"images/money_{value}.png"))
            btn.setIconSize(btn.sizeHint() * 2) # Ukuran ikon
            btn.setFixedSize(140, 70)
            btn.clicked.connect(lambda _, v=value: self.logic.delta(v))
            money_layout.addWidget(btn, i // 2, i % 2)
        control_panel_layout.addLayout(money_layout)
        
        control_panel_layout.addWidget(self.create_separator())

        # Tombol Aksi
        action_layout = QHBoxLayout()
        checkout_btn = QPushButton("Checkout")
        checkout_btn.setObjectName("ControlButton")
        checkout_btn.clicked.connect(lambda: self.logic.delta('Checkout'))
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("CancelButton")
        cancel_btn.clicked.connect(lambda: self.logic.delta('Cancel'))
        action_layout.addWidget(checkout_btn)
        action_layout.addWidget(cancel_btn)
        control_panel_layout.addLayout(action_layout)
        
        control_panel_layout.addStretch()

        # --- Area Dispenser & Kembalian (di bawah) ---
        self.dispenser_area = QFrame()
        self.dispenser_area.setFrameShape(QFrame.Shape.StyledPanel)
        self.dispenser_area.setMinimumHeight(150)
        self.dispenser_area_layout = QHBoxLayout(self.dispenser_area)
        product_panel_layout.addWidget(self.dispenser_area)
        
    def create_product_widget(self, index, name, price):
        """Membuat widget untuk satu produk."""
        row, col = divmod(index, 2)
        
        container = QFrame()
        container.setStyleSheet("background-color: #F0F8FF; border-radius: 10px;")
        container_layout = QVBoxLayout(container)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        container.setGraphicsEffect(shadow)

        img_label = QLabel()
        pixmap = QPixmap(f"images/{name}.png")
        img_label.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(img_label)

        name_label = QLabel(f"{name}\nRp {price}")
        name_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(name_label)
        
        stock_label = QLabel(f"Stok: {self.logic.stock[name]}")
        stock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(stock_label)
        
        btn = QPushButton("Pilih")
        btn.setObjectName("ProductButton")
        btn.clicked.connect(lambda: self.logic.delta(name))
        container_layout.addWidget(btn)

        self.product_grid.addWidget(container, row, col)
        self.product_widgets[name] = {'button': btn, 'stock_label': stock_label}

    def create_separator(self):
        """Membuat garis pemisah."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    # --- Slot untuk menangani sinyal dari Logika ---
    def update_status_display(self, message):
        self.status_display.setText(message)

    def update_main_display(self, state):
        self.cart_display.setText(f"Keranjang: {', '.join(self.logic.selected_items) or 'Kosong'}")
        self.total_price_display.setText(f"Total: Rp {self.logic.total_price}")
        self.money_inserted_display.setText(f"Uang Masuk: Rp {self.logic.money_inserted}")

    def reset_ui(self, message):
        self.update_status_display(message)
        self.update_main_display(self.logic.current_state)
        self.clear_layout(self.dispenser_area_layout)

    def update_stock_display(self, stock_data):
        for name, widgets in self.product_widgets.items():
            stock = stock_data[name]
            widgets['stock_label'].setText(f"Stok: {stock}")
            widgets['button'].setEnabled(stock > 0)

    def run_dispense_animation(self, items):
        """Animasi es krim jatuh ke area dispenser."""
        self.clear_layout(self.dispenser_area_layout)
        
        self.animated_widget = QLabel(self.dispenser_area)
        self.animated_widget.setPixmap(QPixmap("images/ice_cream_cone.png").scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
        self.animated_widget.show()
        
        self.animation = QPropertyAnimation(self.animated_widget, b"geometry")
        self.animation.setDuration(1500) # 1.5 detik
        start_pos = QRect(self.dispenser_area.width() // 2 - 50, -100, 100, 100)
        end_pos = QRect(self.dispenser_area.width() // 2 - 50, 20, 100, 100)
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(end_pos)
        
        # Panggil finalize_transaction setelah animasi selesai
        self.animation.finished.connect(self.logic.finalize_transaction)
        self.animation.start()
        
    def display_change(self, amount):
        """Menampilkan gambar uang kembalian."""
        self.clear_layout(self.dispenser_area_layout)
        denominations = [20000, 10000, 5000, 2000]
        
        if amount == 0: return

        for value in denominations:
            while amount >= value:
                change_label = QLabel()
                change_label.setPixmap(QPixmap(f"images/money_{value}.png").scaled(120, 60, Qt.AspectRatioMode.KeepAspectRatio))
                self.dispenser_area_layout.addWidget(change_label)
                amount -= value
        self.dispenser_area_layout.addStretch()

    def clear_layout(self, layout):
        """Menghapus semua widget dari sebuah layout."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

# ==============================================================================
# BAGIAN 3: MENJALANKAN APLIKASI
# ==============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VendingMachineGUI()
    window.show()
    sys.exit(app.exec())