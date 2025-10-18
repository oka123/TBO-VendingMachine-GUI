# -*- coding: utf-8 -*-
# Vending Machine Es Krim GUI
# Dibuat oleh seorang Software Engineer dengan pengalaman Python 10+ tahun.

import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageTk
import os
import random

# =============================================================================
# BAGIAN 1: LOGIKA INTI VENDING MACHINE (BACKEND)
# =============================================================================
# Kelas ini mengelola semua state dan aturan bisnis mesin, terpisah dari GUI.
# Ini adalah evolusi dari kelas DFA Anda, diadaptasi untuk aplikasi berbasis event.

class VendingMachineLogic:
    """Mengelola state, stok, dan logika transaksi dari Vending Machine."""
    
    def __init__(self):
        self.menu_prices = {
            'Vanilla': 10000,
            'Chocolate': 10000,
            'Caramel': 2000,
            'Sprinkles': 2000
        }
        self.stock = {item: 10 for item in self.menu_prices}
        self.selected_items = []
        self.total_price = 0
        self.money_inserted = 0

    def select_item(self, item_name):
        """Menambahkan item ke keranjang jika stok tersedia."""
        if self.stock.get(item_name, 0) > 0:
            self.selected_items.append(item_name)
            self.total_price += self.menu_prices[item_name]
            return f"{item_name} ditambahkan."
        return f"Maaf, stok {item_name} habis."

    def insert_money(self, amount):
        """Menambahkan uang ke saldo saat ini."""
        self.money_inserted += amount
        return f"Uang Rp {amount:,} dimasukkan."

    def checkout(self):
        """Memproses pembelian, memvalidasi pembayaran dan stok."""
        if not self.selected_items:
            return {'success': False, 'message': "Pilih item terlebih dahulu."}
            
        if self.money_inserted < self.total_price:
            needed = self.total_price - self.money_inserted
            return {'success': False, 'message': f"Uang tidak cukup. Kurang Rp {needed:,}."}
        
        # Cek stok sekali lagi sebelum finalisasi
        for item in self.selected_items:
            if self.stock[item] <= 0:
                # Seharusnya tidak terjadi jika tombol dinonaktifkan, tapi sebagai pengaman
                return {'success': False, 'message': f"Stok {item} habis saat checkout."}

        # Kurangi stok
        for item in self.selected_items:
            self.stock[item] -= 1
            
        change = self.money_inserted - self.total_price
        purchased_items = list(self.selected_items)
        
        # Reset untuk transaksi berikutnya
        self.money_inserted = 0 # Saldo dipakai untuk bayar
        self.selected_items.clear()
        self.total_price = 0
        
        return {
            'success': True,
            'message': f"Pembelian berhasil! Kembalian Anda Rp {change:,}.",
            'change': change,
            'items': purchased_items
        }
    
    def cancel_order(self):
        """Membatalkan pesanan saat ini dan mengembalikan uang."""
        change_to_return = self.money_inserted
        self.selected_items.clear()
        self.total_price = 0
        self.money_inserted = 0
        if change_to_return > 0:
            return f"Pesanan dibatalkan. Uang Rp {change_to_return:,} dikembalikan."
        else:
            return "Pesanan dibatalkan."
            
    def take_change(self):
        """Mengambil sisa uang (jika ada) tanpa membeli."""
        change_to_return = self.money_inserted
        self.money_inserted = 0
        if change_to_return > 0:
            return f"Anda mengambil Rp {change_to_return:,}."
        return "Tidak ada uang untuk diambil."


# =============================================================================
# BAGIAN 2: ANTARMUKA PENGGUNA (FRONTEND - TKINTER)
# =============================================================================
# Kelas ini bertanggung jawab untuk semua elemen visual dan interaksi pengguna.

class VendingMachineGUI(tk.Tk):
    """Kelas utama untuk GUI Vending Machine."""

    def __init__(self):
        super().__init__()
        
        self.logic = VendingMachineLogic()
        self.images = {}
        self.product_buttons = {}

        self.title("Vending Machine Es Krim Inovatif")
        self.geometry("800x600")
        self.configure(bg="#F0F8FF") # AliceBlue background

        # Font-font profesional
        self.title_font = tkfont.Font(family="Helvetica", size=18, weight="bold")
        self.item_font = tkfont.Font(family="Helvetica", size=11, weight="bold")
        self.status_font = tkfont.Font(family="Helvetica", size=12)
        
        self._load_images()
        self._create_widgets()
        self.update_display()

    def _load_images(self):
        """Memuat semua gambar yang dibutuhkan oleh GUI."""
        # CATATAN: Pastikan Anda memiliki folder 'img' di direktori yang sama
        # dengan script ini, atau ganti path berikut.
        image_paths = {
            'Vanilla': 'https://placehold.co/100x100/FFF8DC/333333?text=Vanilla',
            'Chocolate': 'https://placehold.co/100x100/8B4513/FFFFFF?text=Chocolate',
            'Caramel': 'https://placehold.co/100x100/FFD700/333333?text=Caramel',
            'Sprinkles': 'https://placehold.co/100x100/FF69B4/FFFFFF?text=Sprinkles',
            'money_2000': 'https://placehold.co/100x50/C0C0C0/333333?text=Rp2.000',
            'money_5000': 'https://placehold.co/100x50/FFD700/333333?text=Rp5.000',
            'money_10000': 'https://placehold.co/100x50/EE82EE/333333?text=Rp10.000',
            'money_20000': 'https://placehold.co/100x50/87CEEB/333333?text=Rp20.000'
        }
        
        # Placeholder jika gambar tidak ditemukan
        import requests
        from io import BytesIO

        for name, url_or_path in image_paths.items():
            try:
                # Coba muat dari URL
                response = requests.get(url_or_path)
                response.raise_for_status() # Cek jika ada error http
                img_data = Image.open(BytesIO(response.content))
                if name.startswith('money'):
                    img_data = img_data.resize((100, 50), Image.Resampling.LANCZOS)
                else:
                    img_data = img_data.resize((100, 100), Image.Resampling.LANCZOS)
                self.images[name] = ImageTk.PhotoImage(img_data)
            except Exception as e:
                print(f"Gagal memuat gambar {name}: {e}. Menggunakan placeholder.")
                # Buat gambar placeholder sederhana jika gagal
                ph_img = Image.new('RGB', (100, 100 if not name.startswith('money') else 50), color = 'grey')
                self.images[name] = ImageTk.PhotoImage(ph_img)

    def _create_widgets(self):
        """Membuat dan menata semua widget di jendela utama."""
        # --- Layout Utama ---
        main_frame = tk.Frame(self, bg="#F0F8FF", padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        product_frame = tk.Frame(main_frame, bg="#E6E6FA", relief=tk.GROOVE, borderwidth=2)
        product_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        control_frame = tk.Frame(main_frame, bg="#F0F8FF")
        control_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(0, weight=1)

        # --- Panel Produk ---
        tk.Label(product_frame, text="Pilih Es Krim Anda", font=self.title_font, bg="#E6E6FA").pack(pady=10)
        
        items_canvas = tk.Frame(product_frame, bg="#E6E6FA")
        items_canvas.pack(pady=5)

        row, col = 0, 0
        for name, price in self.logic.menu_prices.items():
            item_frame = tk.Frame(items_canvas, bg="#FFFFFF", relief=tk.RAISED, borderwidth=2)
            item_frame.grid(row=row, column=col, padx=10, pady=10)

            tk.Label(item_frame, image=self.images.get(name)).pack(padx=5, pady=5)
            tk.Label(item_frame, text=f"{name}\nRp {price:,}", font=self.item_font, bg="#FFFFFF").pack()
            
            stock_label = tk.Label(item_frame, text=f"Stok: {self.logic.stock[name]}", bg="#FFFFFF")
            stock_label.pack()
            
            btn = tk.Button(item_frame, text="Pilih", command=lambda n=name: self.on_select_item(n))
            btn.pack(pady=5)
            self.product_buttons[name] = {'button': btn, 'stock_label': stock_label}
            
            col += 1
            if col > 1:
                col = 0
                row += 1

        # --- Panel Kontrol (Kanan) ---
        # Status Pesanan
        status_frame = tk.Frame(control_frame, bg="#FFFFFF", relief=tk.GROOVE, borderwidth=2)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.cart_label = tk.Label(status_frame, text="Keranjang: Kosong", font=self.status_font, wraplength=250, justify=tk.LEFT, bg="#FFFFFF")
        self.cart_label.pack(anchor="w", padx=10, pady=5)
        self.total_label = tk.Label(status_frame, text="Total: Rp 0", font=self.status_font, bg="#FFFFFF")
        self.total_label.pack(anchor="w", padx=10, pady=5)

        # Status Uang
        money_frame = tk.Frame(control_frame, bg="#FFFFFF", relief=tk.GROOVE, borderwidth=2)
        money_frame.pack(fill=tk.X, pady=5)
        
        self.money_label = tk.Label(money_frame, text="Uang Masuk: Rp 0", font=self.status_font, bg="#FFFFFF")
        self.money_label.pack(anchor="w", padx=10, pady=5)
        
        # Input Uang
        payment_frame = tk.Frame(control_frame, bg="#F0F8FF")
        payment_frame.pack(pady=10)
        tk.Label(payment_frame, text="Masukkan Uang:", font=self.item_font, bg="#F0F8FF").pack()
        
        money_buttons_frame = tk.Frame(payment_frame, bg="#F0F8FF")
        money_buttons_frame.pack()
        for amount in [2000, 5000, 10000, 20000]:
            btn = tk.Button(money_buttons_frame, image=self.images.get(f'money_{amount}'),
                             command=lambda a=amount: self.on_insert_money(a))
            btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Tombol Aksi
        action_frame = tk.Frame(control_frame, bg="#F0F8FF")
        action_frame.pack(pady=10)
        
        tk.Button(action_frame, text="Checkout", bg="#90EE90", command=self.on_checkout, font=self.item_font).pack(fill=tk.X, pady=5)
        tk.Button(action_frame, text="Batal", bg="#FFB6C1", command=self.on_cancel, font=self.item_font).pack(fill=tk.X, pady=5)
        tk.Button(action_frame, text="Ambil Uang", bg="#ADD8E6", command=self.on_take_change, font=self.item_font).pack(fill=tk.X, pady=5)
        
        # Area Notifikasi & Dispenser
        dispenser_frame = tk.Frame(control_frame, bg="#333333", height=150, relief=tk.SUNKEN, borderwidth=2)
        dispenser_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        dispenser_frame.pack_propagate(False)
        
        self.notification_label = tk.Label(dispenser_frame, text="Selamat Datang!", font=self.status_font,
                                           bg="#333333", fg="white", wraplength=280)
        self.notification_label.pack(pady=10)
        
        self.dispenser_canvas = tk.Canvas(dispenser_frame, bg="#333333", highlightthickness=0)
        self.dispenser_canvas.pack(fill=tk.BOTH, expand=True)

    def on_select_item(self, item_name):
        """Handler saat tombol 'Pilih' item ditekan."""
        message = self.logic.select_item(item_name)
        self.show_notification(message)
        self.update_display()
        
    def on_insert_money(self, amount):
        """Handler saat tombol uang ditekan."""
        message = self.logic.insert_money(amount)
        self.show_notification(message)
        self.update_display()

    def on_checkout(self):
        """Handler untuk tombol Checkout."""
        result = self.logic.checkout()
        self.show_notification(result['message'])
        if result['success']:
            self.run_dispense_animation(result['items'])
            # Tunda reset display agar animasi selesai
            self.after(2000, self.update_display)
        else:
            self.update_display()
    
    def on_cancel(self):
        """Handler untuk tombol Batal."""
        message = self.logic.cancel_order()
        self.show_notification(message)
        self.update_display()
        
    def on_take_change(self):
        """Handler untuk tombol Ambil Uang."""
        message = self.logic.take_change()
        self.show_notification(message)
        self.update_display()

    def update_display(self):
        """Memperbarui semua label di GUI sesuai state terbaru dari logic."""
        # Update keranjang
        if self.logic.selected_items:
            cart_text = "Keranjang: " + ", ".join(self.logic.selected_items)
            self.cart_label.config(text=cart_text)
        else:
            self.cart_label.config(text="Keranjang: Kosong")
            
        # Update total harga
        self.total_label.config(text=f"Total: Rp {self.logic.total_price:,}")
        
        # Update uang masuk
        self.money_label.config(text=f"Uang Masuk: Rp {self.logic.money_inserted:,}")
        
        # Update stok dan status tombol produk
        for name, widgets in self.product_buttons.items():
            stock = self.logic.stock[name]
            widgets['stock_label'].config(text=f"Stok: {stock}")
            if stock > 0:
                widgets['button'].config(state=tk.NORMAL)
            else:
                widgets['button'].config(state=tk.DISABLED)

    def show_notification(self, message):
        """Menampilkan pesan di area notifikasi."""
        self.notification_label.config(text=message)
        # Hapus pesan setelah beberapa detik
        self.after(5000, lambda: self.notification_label.config(text=""))

    def run_dispense_animation(self, items):
        """Menjalankan animasi sederhana untuk item yang dikeluarkan."""
        self.dispenser_canvas.delete("all")
        colors = {'Vanilla': 'ivory', 'Chocolate': '#6B4226', 'Caramel': 'goldenrod', 'Sprinkles': 'pink'}
        
        x_pos = 50
        for item in items:
            color = colors.get(item, 'grey')
            if 'Scoop' in item or item in ['Vanilla', 'Chocolate']: # Es Krim
                shape = self.dispenser_canvas.create_oval(x_pos, -40, x_pos + 40, 0, fill=color, outline=color)
            else: # Topping
                shape = self.dispenser_canvas.create_rectangle(x_pos, -40, x_pos + 40, -20, fill=color, outline=color)
            
            self._animate_fall(shape, 0)
            x_pos += 60

    def _animate_fall(self, shape, step):
        """Langkah rekursif untuk animasi jatuh."""
        if step < 70: # Jatuh hingga posisi y=70
            self.dispenser_canvas.move(shape, 0, 2)
            self.after(15, self._animate_fall, shape, step + 1)
        else:
            # Setelah selesai jatuh, hapus setelah beberapa saat
            self.after(1000, lambda: self.dispenser_canvas.delete(shape))

# =============================================================================
# BAGIAN 3: EKSEKUSI PROGRAM
# =============================================================================
if __name__ == "__main__":
    # Pastikan Anda menginstal library Pillow
    # Buka terminal/cmd dan ketik: pip install Pillow requests
    app = VendingMachineGUI()
    app.mainloop()
