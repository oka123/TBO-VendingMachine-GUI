# -*- coding: utf-8 -*-
# Vending Machine Es Krim GUI dengan PyQt6
# Dibuat oleh seorang Software Engineer dengan pengalaman Python 10+ tahun.
# Arsitektur: Logika Backend terpisah dari Frontend (PyQt6)

import sys
import requests
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QLabel, QPushButton, QScrollArea, QFrame, QGroupBox)
from PyQt6.QtGui import QPixmap, QFont, QIcon, QPalette, QColor, QBrush, QPainter
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve

# =============================================================================
# BAGIAN 1: LOGIKA INTI VENDING MACHINE (BACKEND)
# =============================================================================
# Kelas ini tidak memiliki dependensi PyQt dan mengelola semua state mesin.
# Ini adalah evolusi dari kelas DFA Anda, diadaptasi untuk aplikasi berbasis event.

class VendingMachineLogic:
    """Mengelola state, stok, dan logika transaksi dari Vending Machine."""
    
    def __init__(self):
        self.menu_prices = {
            'Vanilla': 10000, 'Chocolate': 10000,
            'Caramel': 2000, 'Sprinkles': 2000
        }
        self.image_urls = {
            'Vanilla': 'https://placehold.co/150x150/FFF8DC/333333?text=Vanilla',
            'Chocolate': 'https://placehold.co/150x150/8B4513/FFFFFF?text=Chocolate',
            'Caramel': 'https://placehold.co/150x150/FFD700/333333?text=Caramel',
            'Sprinkles': 'https://placehold.co/150x150/FF69B4/FFFFFF?text=Sprinkles'
        }
        self.stock = {item: 10 for item in self.menu_prices}
        self.selected_items = []
        self.total_price = 0
        self.money_inserted = 0

    def select_item(self, item_name):
        if self.stock.get(item_name, 0) > 0:
            self.selected_items.append(item_name)
            self.total_price += self.menu_prices[item_name]
            return f"{item_name} ditambahkan ke keranjang."
        return f"Maaf, stok {item_name} habis."

    def insert_money(self, amount):
        self.money_inserted += amount
        return f"Uang Rp {amount:,} dimasukkan."

    def checkout(self):
        if not self.selected_items:
            return {'success': False, 'message': "Keranjang masih kosong."}
        if self.money_inserted < self.total_price:
            needed = self.total_price - self.money_inserted
            return {'success': False, 'message': f"Uang kurang Rp {needed:,}."}
        
        for item in self.selected_items: self.stock[item] -= 1
            
        change = self.money_inserted - self.total_price
        purchased_items = list(self.selected_items)
        self.money_inserted = 0
        self.selected_items.clear()
        self.total_price = 0
        
        return {'success': True, 'message': f"Berhasil! Kembalian Rp {change:,}.", 'change': change, 'items': purchased_items}
    
    def cancel_order(self):
        change_to_return = self.money_inserted
        self.selected_items.clear()
        self.total_price = 0
        self.money_inserted = 0
        if change_to_return > 0:
            return f"Pesanan dibatalkan. Uang Rp {change_to_return:,} dikembalikan."
        return "Pesanan dibatalkan."
            
    def take_change(self):
        change_to_return = self.money_inserted
        self.money_inserted = 0
        if change_to_return > 0:
            return f"Anda mengambil sisa uang Rp {change_to_return:,}."
        return "Tidak ada sisa uang untuk diambil."

# =============================================================================
# BAGIAN 2: ANTARMUKA PENGGUNA (FRONTEND - PYQT6)
# =============================================================================

# --- Widget Kustom untuk Produk ---
class ProductWidget(QFrame):
    def __init__(self, item_name, price, image_url, stock, select_callback):
        super().__init__()
        self.setObjectName("ProductCard")
        layout = QVBoxLayout(self)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_image_from_url(image_url)
        
        self.name_label = QLabel(f"{item_name}\nRp {price:,}")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stock_label = QLabel(f"Stok: {stock}")
        self.stock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stock_label.setObjectName("StockLabel")
        
        self.select_button = QPushButton("Pilih")
        self.select_button.clicked.connect(lambda: select_callback(item_name))

        layout.addWidget(self.image_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.stock_label)
        layout.addWidget(self.select_button)

    def load_image_from_url(self, url):
        try:
            response = requests.get(url, timeout=5)
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            self.image_label.setPixmap(pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio))
        except requests.RequestException:
            # Fallback jika gagal load gambar
            self.image_label.setText(f"[Gambar\n{self.name_label.text().splitlines()[0]}]")

# --- Jendela Utama Aplikasi ---
class VendingMachineGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.logic = VendingMachineLogic()
        self.product_widgets = {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Vending Machine Es Krim Modern")
        self.setGeometry(100, 100, 900, 650)
        self.setStyleSheet(self.get_stylesheet())

        # Layout Utama
        main_layout = QHBoxLayout(self)

        # Panel Kiri (Produk)
        product_panel = self.create_product_panel()
        main_layout.addWidget(product_panel, 65) # 65% width

        # Panel Kanan (Kontrol)
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel, 35) # 35% width

        self.update_ui()

    def create_product_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        title = QLabel("Pilih Es Krim Favorit Anda")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.product_grid = QGridLayout(scroll_content)
        self.product_grid.setSpacing(15)
        
        row, col = 0, 0
        for name, price in self.logic.menu_prices.items():
            widget = ProductWidget(name, price, self.logic.image_urls[name], self.logic.stock[name], self.on_select_item)
            self.product_widgets[name] = widget
            self.product_grid.addWidget(widget, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

        scroll_area.setWidget(scroll_content)
        layout.addWidget(title)
        layout.addWidget(scroll_area)
        return container

    def create_control_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)

        # Grup Status
        status_group = QGroupBox("Status Pesanan")
        status_layout = QVBoxLayout(status_group)
        self.cart_label = QLabel("Keranjang: Kosong")
        self.total_label = QLabel("Total: Rp 0")
        self.money_label = QLabel("Uang Masuk: Rp 0")
        self.money_label.setObjectName("MoneyLabel")
        status_layout.addWidget(self.cart_label)
        status_layout.addWidget(self.total_label)
        status_layout.addWidget(self.money_label)

        # Grup Pembayaran
        payment_group = QGroupBox("Masukkan Uang")
        payment_layout = QGridLayout(payment_group)
        amounts = [2000, 5000, 10000, 20000]
        for i, amount in enumerate(amounts):
            btn = QPushButton(f"Rp {amount:,}")
            btn.clicked.connect(lambda _, a=amount: self.on_insert_money(a))
            payment_layout.addWidget(btn, i // 2, i % 2)

        # Grup Aksi
        action_group = QGroupBox("Aksi")
        action_layout = QVBoxLayout(action_group)
        checkout_btn = QPushButton("Checkout / Beli")
        checkout_btn.setObjectName("CheckoutButton")
        checkout_btn.clicked.connect(self.on_checkout)
        cancel_btn = QPushButton("Batalkan Pesanan")
        cancel_btn.setObjectName("CancelButton")
        cancel_btn.clicked.connect(self.on_cancel)
        take_change_btn = QPushButton("Ambil Sisa Uang")
        take_change_btn.clicked.connect(self.on_take_change)
        action_layout.addWidget(checkout_btn)
        action_layout.addWidget(cancel_btn)
        action_layout.addWidget(take_change_btn)

        # Grup Dispenser & Notifikasi
        self.dispenser_group = QGroupBox("Dispenser")
        dispenser_layout = QVBoxLayout(self.dispenser_group)
        self.notification_label = QLabel("Selamat Datang!")
        self.notification_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.notification_label.setWordWrap(True)
        self.animation_area = QWidget()
        dispenser_layout.addWidget(self.notification_label, 1)
        dispenser_layout.addWidget(self.animation_area, 4)

        layout.addWidget(status_group)
        layout.addWidget(payment_group)
        layout.addWidget(action_group)
        layout.addWidget(self.dispenser_group)
        return container

    # --- Event Handlers (Slots) ---
    def on_select_item(self, item_name):
        msg = self.logic.select_item(item_name)
        self.show_notification(msg)
        self.update_ui()
    
    def on_insert_money(self, amount):
        msg = self.logic.insert_money(amount)
        self.show_notification(msg)
        self.update_ui()

    def on_checkout(self):
        result = self.logic.checkout()
        self.show_notification(result['message'])
        if result['success']:
            self.run_dispense_animation(result['items'])
        self.update_ui()

    def on_cancel(self):
        msg = self.logic.cancel_order()
        self.show_notification(msg)
        self.update_ui()

    def on_take_change(self):
        msg = self.logic.take_change()
        self.show_notification(msg)
        self.update_ui()

    # --- UI Update and Animation ---
    def update_ui(self):
        if self.logic.selected_items:
            self.cart_label.setText("Keranjang: " + ", ".join(self.logic.selected_items))
        else:
            self.cart_label.setText("Keranjang: Kosong")
        self.total_label.setText(f"Total: Rp {self.logic.total_price:,}")
        self.money_label.setText(f"Uang Masuk: Rp {self.logic.money_inserted:,}")

        for name, widget in self.product_widgets.items():
            stock = self.logic.stock[name]
            widget.stock_label.setText(f"Stok: {stock}")
            widget.select_button.setEnabled(stock > 0)

    def show_notification(self, message):
        self.notification_label.setText(message)
        # Hapus notifikasi setelah 5 detik
        QTimer.singleShot(5000, lambda: self.notification_label.setText(""))

    def run_dispense_animation(self, items):
        for i, item_name in enumerate(items):
            # Buat label gambar untuk animasi di dalam area animasi
            anim_label = QLabel(self.animation_area)
            pixmap = QPixmap()
            try:
                response = requests.get(self.logic.image_urls[item_name], timeout=5)
                pixmap.loadFromData(response.content)
                anim_label.setPixmap(pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio))
            except requests.RequestException:
                anim_label.setText(item_name) # Fallback teks
            
            anim_label.show()
            
            start_x = self.animation_area.width() // (len(items) + 1) * (i + 1) - 30
            end_y = self.animation_area.height() - 70
            
            # Buat animasi properti geometri
            self.animation = QPropertyAnimation(anim_label, b"geometry")
            self.animation.setDuration(1500)
            self.animation.setStartValue(QRect(start_x, -60, 60, 60))
            self.animation.setEndValue(QRect(start_x, end_y, 60, 60))
            self.animation.setEasingCurve(QEasingCurve.Type.OutBounce)
            
            # Hapus label setelah animasi selesai
            self.animation.finished.connect(anim_label.deleteLater)
            self.animation.start()

    def get_stylesheet(self):
        return """
            QWidget {
                font-family: 'Segoe UI', 'Calibri', 'Arial';
                font-size: 11pt;
            }
            #ProductCard {
                background-color: white;
                border: 1px solid #DDD;
                border-radius: 8px;
            }
            #StockLabel {
                color: #888;
                font-size: 9pt;
            }
            #TitleLabel {
                font-size: 18pt;
                font-weight: bold;
                color: #2c3e50;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #CCC;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f618d;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            #CheckoutButton {
                background-color: #2ecc71; /* Green */
            }
            #CheckoutButton:hover {
                background-color: #27ae60;
            }
            #CancelButton {
                background-color: #e74c3c; /* Red */
            }
            #CancelButton:hover {
                background-color: #c0392b;
            }
            #MoneyLabel {
                font-size: 14pt;
                font-weight: bold;
                color: #27ae60; /* Green */
            }
        """
# =============================================================================
# BAGIAN 3: EKSEKUSI PROGRAM
# =============================================================================
if __name__ == '__main__':
    # Pastikan Anda menginstal library PyQt6 dan requests
    # Buka terminal/cmd dan ketik: pip install PyQt6 requests
    app = QApplication(sys.argv)
    ex = VendingMachineGUI()
    ex.show()
    sys.exit(app.exec())

    