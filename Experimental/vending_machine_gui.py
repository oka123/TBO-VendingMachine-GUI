import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageTk
import time

# ==============================================================================
# BAGIAN 1: LOGIKA INTI (DFA VENDING MACHINE)
# Diadaptasi dari kode awal untuk integrasi dengan GUI
# ==============================================================================
class VendingMachineLogic:
    """
    Implementasi logika Vending Machine sebagai DFA.
    Kelas ini tidak tahu apa-apa tentang GUI, hanya mengelola state dan transisi.
    """
    def __init__(self, gui_callback):
        self.gui_callback = gui_callback # Fungsi untuk mengirim update ke GUI
        self.menu_prices = {
            'VanillaScoop': 10000, 'ChocolateScoop': 10000,
            'CaramelTopping': 2000, 'SprinklesTopping': 2000
        }
        self.stock = {item: 10 for item in self.menu_prices} # Stok awal
        self.reset_transaction()

    def reset_transaction(self):
        """Mengembalikan mesin ke state awal untuk transaksi baru."""
        self.current_state = 'Idle'
        self.selected_items = []
        self.total_price = 0
        self.money_inserted = 0
        return "Mesin Siap! Silakan pilih item."

    def delta(self, input_symbol):
        """Fungsi Transisi (δ). Menentukan state berikutnya dan memanggil callback GUI."""
        state = self.current_state

        # Logika untuk State 'Idle' atau 'WaitingForSelection'
        if state in ['Idle', 'WaitingForSelection']:
            if input_symbol in self.menu_prices:
                if self.stock[input_symbol] > 0:
                    self.selected_items.append(input_symbol)
                    self.total_price += self.menu_prices[input_symbol]
                    self.current_state = 'WaitingForSelection'
                    self.gui_callback('update_display', f"'{input_symbol}' ditambahkan.")
                else:
                    self.gui_callback('update_display', f"Maaf, '{input_symbol}' habis.")
            elif input_symbol == 'Checkout' and self.selected_items:
                self.current_state = 'WaitingForPayment'
                self.gui_callback('update_display', f"Total: Rp {self.total_price}. Silakan bayar.")
            elif input_symbol == 'Cancel':
                msg = self.reset_transaction()
                self.gui_callback('reset', msg)
            else:
                self.gui_callback('update_display', "Pilih item sebelum checkout.")

        # Logika untuk State 'WaitingForPayment'
        elif state == 'WaitingForPayment':
            if isinstance(input_symbol, int):
                self.money_inserted += input_symbol
                needed = self.total_price - self.money_inserted
                if self.money_inserted >= self.total_price:
                    self.current_state = 'DispensingItem'
                    self.gui_callback('update_display', "Pembayaran Lunas! Memproses...")
                    self.trigger_internal_transition('__dispense__')
                else:
                    self.gui_callback('update_display', f"Uang diterima. Kurang Rp {needed}.")
            elif input_symbol == 'Cancel':
                change_to_return = self.money_inserted
                msg = self.reset_transaction()
                self.gui_callback('reset', f"Dibatalkan. Uang Rp {change_to_return} dikembalikan.")
                self.gui_callback('return_change', change_to_return)

    def trigger_internal_transition(self, internal_symbol):
        """Fungsi untuk memicu transisi otomatis (dispensing, returning change)."""
        if internal_symbol == '__dispense__':
            # Kurangi stok
            for item in self.selected_items:
                self.stock[item] -= 1
            
            self.gui_callback('dispense_animation', self.selected_items)
            # Transisi ke returning change terjadi setelah animasi selesai

    def finalize_transaction(self):
        """Dipanggil setelah animasi dispensing selesai."""
        self.current_state = 'ReturningChange'
        change = self.money_inserted - self.total_price
        msg = self.reset_transaction()
        if change > 0:
            self.gui_callback('reset', f"Transaksi Selesai! Kembalian Anda Rp {change}.")
            self.gui_callback('return_change', change)
        else:
            self.gui_callback('reset', "Transaksi Selesai! Terima kasih.")


# ==============================================================================
# BAGIAN 2: GUI (ANTARMUKA PENGGUNA) DENGAN TKINTER
# ==============================================================================
class VendingMachineGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Vending Machine Es Krim Cerdas")
        self.geometry("800x700")
        self.configure(bg="#F0F8FF") # AliceBlue background

        # Inisialisasi logika DFA
        self.logic = VendingMachineLogic(self.gui_callback)

        # Font Styles
        self.title_font = tkfont.Font(family="Helvetica", size=24, weight="bold")
        self.item_font = tkfont.Font(family="Arial", size=12, weight="bold")
        self.status_font = tkfont.Font(family="Arial", size=14)
        self.money_font = tkfont.Font(family="Arial", size=16, weight="bold")

        # Load images
        self.images = self.load_images()

        self.create_widgets()
        self.update_display_info()

    def load_images(self):
        """Memuat semua gambar yang dibutuhkan oleh GUI."""
        images = {}
        img_size = (100, 100)
        money_size = (120, 60)
        change_size = (80, 40)
        
        try:
            for item in self.logic.menu_prices.keys():
                images[item] = ImageTk.PhotoImage(Image.open(f"images/{item}.png").resize(img_size, Image.Resampling.LANCZOS))
            
            for value in [2000, 5000, 10000, 20000]:
                images[f'money_{value}'] = ImageTk.PhotoImage(Image.open(f"images/money_{value}.png").resize(money_size, Image.Resampling.LANCZOS))
                images[f'change_{value}'] = ImageTk.PhotoImage(Image.open(f"images/change_{value}.png").resize(change_size, Image.Resampling.LANCZOS))

            images['ice_cream_cone'] = ImageTk.PhotoImage(Image.open("images/ice_cream_cone.png").resize((80, 80), Image.Resampling.LANCZOS))

        except FileNotFoundError as e:
            print(f"Error: Pastikan file gambar ada di folder 'images'. File yang hilang: {e.filename}")
            self.destroy() # Keluar jika gambar tidak ditemukan
        return images

    def create_widgets(self):
        """Membuat dan menata semua elemen GUI."""
        main_frame = tk.Frame(self, bg="#F0F8FF", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Product Frame ---
        product_frame = tk.Frame(main_frame, bg="#FFFFFF", bd=2, relief=tk.GROOVE)
        product_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        tk.Label(product_frame, text="Pilih Es Krim Favoritmu!", font=self.title_font, bg="#FFFFFF", fg="#4682B4").pack(pady=10)

        self.product_buttons = {}
        product_grid = tk.Frame(product_frame, bg="#FFFFFF")
        product_grid.pack(pady=10, padx=10)
        
        items = list(self.logic.menu_prices.items())
        for i, (name, price) in enumerate(items):
            row, col = divmod(i, 2)
            item_frame = tk.Frame(product_grid, bg="#F0F8FF", bd=1, relief=tk.SOLID)
            item_frame.grid(row=row, column=col, padx=10, pady=10)
            
            img_label = tk.Label(item_frame, image=self.images[name], bg="#F0F8FF")
            img_label.pack(pady=5)
            
            info_label = tk.Label(item_frame, text=f"{name}\nRp {price}", font=self.item_font, bg="#F0F8FF")
            info_label.pack(pady=5)
            
            stock_label = tk.Label(item_frame, text=f"Stok: {self.logic.stock[name]}", bg="#F0F8FF")
            stock_label.pack()
            
            btn = tk.Button(item_frame, text="Pilih", command=lambda n=name: self.logic.delta(n),
                            bg="#5F9EA0", fg="white", font=self.item_font, relief=tk.RAISED,
                            activebackground="#4682B4")
            btn.pack(pady=10, padx=10, fill=tk.X)
            self.product_buttons[name] = {'button': btn, 'stock_label': stock_label}
        
        # --- Control & Payment Frame ---
        control_frame = tk.Frame(main_frame, bg="#B0E0E6", bd=2, relief=tk.GROOVE)
        control_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        tk.Label(control_frame, text="Pembayaran", font=self.title_font, bg="#B0E0E6", fg="#2F4F4F").pack(pady=10)

        # Display Info
        self.status_label = tk.Label(control_frame, text="Selamat Datang!", font=self.status_font, bg="#B0E0E6", wraplength=300)
        self.status_label.pack(pady=10)
        
        self.cart_label = tk.Label(control_frame, text="Keranjang: Kosong", font=self.item_font, bg="#B0E0E6")
        self.cart_label.pack(pady=5)

        self.total_price_label = tk.Label(control_frame, text="Total Harga: Rp 0", font=self.money_font, bg="#B0E0E6")
        self.total_price_label.pack(pady=5)
        
        self.money_inserted_label = tk.Label(control_frame, text="Uang Masuk: Rp 0", font=self.money_font, bg="#B0E0E6", fg="green")
        self.money_inserted_label.pack(pady=10)
        
        # Money Buttons
        money_frame = tk.Frame(control_frame, bg="#B0E0E6")
        money_frame.pack(pady=10)
        for value in [2000, 5000, 10000, 20000]:
            btn = tk.Button(money_frame, image=self.images[f'money_{value}'], command=lambda v=value: self.logic.delta(v),
                            bg="#B0E0E6", relief=tk.FLAT, bd=0)
            btn.pack(side=tk.LEFT, padx=5)

        # Action Buttons
        action_frame = tk.Frame(control_frame, bg="#B0E0E6")
        action_frame.pack(pady=20)
        tk.Button(action_frame, text="Checkout", command=lambda: self.logic.delta('Checkout'),
                  bg="#3CB371", fg="white", font=self.item_font, width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(action_frame, text="Cancel", command=lambda: self.logic.delta('Cancel'),
                  bg="#DC143C", fg="white", font=self.item_font, width=15).pack(side=tk.LEFT, padx=10)

        # --- Dispenser & Change Frame ---
        dispenser_frame = tk.Frame(main_frame, bg="#ADD8E6", height=150, bd=2, relief=tk.SUNKEN)
        dispenser_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        tk.Label(dispenser_frame, text="Area Pengambilan", font=self.item_font, bg="#ADD8E6").pack()
        self.dispenser_canvas = tk.Canvas(dispenser_frame, bg="#E0FFFF", width=760, height=100)
        self.dispenser_canvas.pack(pady=5)
        
        main_frame.grid_columnconfigure(0, weight=2)
        main_frame.grid_columnconfigure(1, weight=1)

    def gui_callback(self, action, data=None):
        """Fungsi yang dipanggil oleh logika DFA untuk mengupdate GUI."""
        if action == 'update_display':
            self.status_label.config(text=data)
            self.update_display_info()
        elif action == 'reset':
            self.status_label.config(text=data)
            self.update_display_info()
            self.dispenser_canvas.delete("all")
        elif action == 'dispense_animation':
            self.animate_dispense()
        elif action == 'return_change':
            self.display_change(data)

    def update_display_info(self):
        """Memperbarui semua label info di GUI."""
        self.cart_label.config(text=f"Keranjang: {', '.join(self.logic.selected_items) or 'Kosong'}")
        self.total_price_label.config(text=f"Total Harga: Rp {self.logic.total_price}")
        self.money_inserted_label.config(text=f"Uang Masuk: Rp {self.logic.money_inserted}")
        
        # Update stock and button state
        for name, widgets in self.product_buttons.items():
            stock = self.logic.stock[name]
            widgets['stock_label'].config(text=f"Stok: {stock}")
            if stock == 0:
                widgets['button'].config(state=tk.DISABLED, bg="grey")
            else:
                widgets['button'].config(state=tk.NORMAL, bg="#5F9EA0")
    
    def animate_dispense(self):
        """Animasi sederhana es krim jatuh ke area dispenser."""
        self.status_label.config(text="Membuat es krim Anda... Mohon tunggu!")
        
        # Disable all buttons during animation
        for widgets in self.product_buttons.values():
            widgets['button'].config(state=tk.DISABLED)

        x, y, end_y = 380, -40, 50
        item_id = self.dispenser_canvas.create_image(x, y, image=self.images['ice_cream_cone'])
        
        def move_down():
            nonlocal y
            if y < end_y:
                self.dispenser_canvas.move(item_id, 0, 5) # Pindahkan 5 pixel ke bawah
                y += 5
                self.after(15, move_down) # Ulangi setelah 15ms
            else:
                # Animasi selesai, finalisasi transaksi
                self.logic.finalize_transaction()

        move_down()

    def display_change(self, amount):
        """Menampilkan gambar uang kembalian di area dispenser."""
        self.dispenser_canvas.delete("all")
        denominations = [20000, 10000, 5000, 2000]
        x_pos = 50
        for value in denominations:
            while amount >= value:
                self.dispenser_canvas.create_image(x_pos, 50, image=self.images[f'change_{value}'])
                amount -= value
                x_pos += 90


# ==============================================================================
# BAGIAN 3: MENJALANKAN APLIKASI
# ==============================================================================
if __name__ == "__main__":
    app = VendingMachineGUI()
    app.mainloop()