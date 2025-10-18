import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw

# =================================================================
# 1. LOGIKA INTI (Vending Machine DFA) - Tidak Berubah Signifikan
# =================================================================

class VendingMachineDFA:
    """
    Implementasi Vending Machine Es Krim sebagai Mealy Machine (DFA)
    dengan logika stok.
    """
    def __init__(self):
        self.menu_prices = {
            'Vanilla': 10000,
            'Chocolate': 10000,
            'Caramel': 2000,
            'Sprinkles': 2000
        }
        self.item_stocks = {
            'Vanilla': 10,
            'Chocolate': 9,
            'Caramel': 10,
            'Sprinkles': 10
        }
        self.item_types = {
            'Vanilla': 'scoop',
            'Chocolate': 'scoop',
            'Caramel': 'topping',
            'Sprinkles': 'topping'
        }
        self.money_denominations = [2000, 5000, 10000, 20000]
        self.reset()

    def reset(self):
        """Mengembalikan mesin ke state awal untuk transaksi baru."""
        self.current_state = 'Idle'
        self.selected_items = {}
        self.total_price = 0
        self.money_inserted = 0
        self.last_output = "🍦 Mesin Es Krim Siap! Silakan pilih item."

    def delta(self, input_symbol):
        """Fungsi Transisi (δ). Menentukan state berikutnya dan output."""
        state = self.current_state
        output = ""
        is_money_input = isinstance(input_symbol, int)

        # --- Logika Transisi ---
        
        if state in ['Idle', 'WaitingForSelection']:
            if input_symbol in self.menu_prices:
                item = input_symbol
                if self.item_stocks.get(item, 0) > 0:
                    self.selected_items[item] = self.selected_items.get(item, 0) + 1
                    self.total_price += self.menu_prices[item]
                    self.current_state = 'WaitingForSelection'
                    output = f"Item '{item}' ditambahkan. Total harga: Rp {self.total_price:,.0f}."
                else:
                    output = f"Maaf, stok {item} HABIS."
            elif input_symbol == 'Checkout' and self.selected_items:
                self.current_state = 'WaitingForPayment'
                output = f"Pesanan dikonfirmasi. Total: Rp {self.total_price:,.0f}. Silakan masukkan uang."
            elif input_symbol == 'Cancel':
                output = "Pesanan dibatalkan. Uang yang dimasukkan akan dikembalikan."
                self.trigger_internal_transition('_return_money_')
            elif is_money_input:
                output = "Silakan pilih item atau Checkout terlebih dahulu."
            else:
                output = "Pilihan tidak valid. Silakan pilih item, Checkout, atau Cancel."

        elif state == 'WaitingForPayment':
            if is_money_input and input_symbol in self.money_denominations:
                self.money_inserted += input_symbol
                output = f"Uang Rp {input_symbol:,.0f} diterima. Total dimasukkan: Rp {self.money_inserted:,.0f}."
                
                if self.money_inserted >= self.total_price:
                    self.current_state = 'DispensingItem'
                    output += "\nPembayaran cukup. Memproses pesanan..."
                    output += "\n" + self.trigger_internal_transition('_dispense_')
                else:
                    needed = self.total_price - self.money_inserted
                    output += f" Masih kurang Rp {needed:,.0f}."
            elif input_symbol == 'Cancel':
                self.current_state = 'ReturningChange'
                output = "Pembayaran dibatalkan."
                output += "\n" + self.trigger_internal_transition('_return_money_')
            else:
                output = "Input tidak valid. Silakan masukkan uang atau 'Cancel'."

        else:
             output = "Mohon tunggu. Transaksi sedang diproses."
        
        self.last_output = output
        return output

    def trigger_internal_transition(self, internal_symbol):
        """Fungsi untuk memicu transisi otomatis (dispensing, returning change)."""
        output = ""
        
        if internal_symbol == '_dispense_':
            for item, count in self.selected_items.items():
                if item in self.item_stocks:
                    self.item_stocks[item] -= count
            
            items_str = ", ".join([f"{item} ({count})" for item, count in self.selected_items.items()])
            output = f"✅ Mengeluarkan item: [{items_str}]."
            
            self.current_state = 'ReturningChange'
            output += "\n" + self.trigger_internal_transition('_return_money_')
        
        elif internal_symbol == '_return_money_':
            change = self.money_inserted - self.total_price
            
            if self.current_state == 'ReturningChange' and self.selected_items == {} and self.total_price == 0:
                 change = self.money_inserted

            self.money_inserted = 0 

            if change > 0:
                output = f"💰 Kembalian Anda: Rp {change:,.0f}."
            elif change == 0 and self.current_state == 'ReturningChange':
                output = "Tidak ada kembalian. Transaksi selesai."
            elif self.current_state == 'ReturningChange':
                output = "Transaksi selesai."

            self.current_state = 'Idle'
        
        return output

# =================================================================
# 2. LOGIKA GUI (Tkinter) - Modifikasi Ukuran Font & Posisi Tengah
# =================================================================

class IceCreamVendingGUI:
    def __init__(self, master):
        self.master = master
        master.title("Vending Machine Es Krim Modern")
        master.configure(bg="#1E1E1E")
        master.geometry("800x650")
        
        self.vm = VendingMachineDFA()
        self.item_buttons = {}
        self.item_stock_labels = {}
        self.dispenser_item_queue = []

        # Tentukan Ukuran Font Baru
        self.FONT_HEADER = ("Arial", 18, "bold")
        self.FONT_TITLE = ("Arial", 16, "bold")
        self.FONT_SUBTITLE = ("Arial", 14)
        self.FONT_PRICE = ("Arial", 14, "bold")
        self.FONT_STOCK = ("Arial", 12)
        self.FONT_BUTTON = ("Arial", 12, "bold")
        self.FONT_NOTIFICATION = ("Arial", 12)

        self.image_references = {}
        self.load_images()
        
        self.frame_products = self.create_product_frame(master)
        self.frame_status = self.create_status_frame(master)
        self.frame_dispenser = self.create_dispenser_frame(master)
        
        self.frame_products.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="nsew")
        self.frame_status.grid(row=0, column=1, padx=10, pady=10, sticky="n")
        self.frame_dispenser.grid(row=1, column=1, padx=10, pady=10, sticky="s")

        master.grid_columnconfigure(0, weight=3)
        master.grid_columnconfigure(1, weight=2)
        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=1)

        self.update_gui_data()

    def load_images(self):
        # ... (Kode load_images sama, hanya perlu ukuran font yang lebih besar untuk label di GUI)
        self.money_images = {}
        for amount in self.vm.money_denominations:
            img = Image.new('RGB', (100, 50), color = '#28a745') # Ukuran tombol uang diperbesar
            d = ImageDraw.Draw(img)
            d.text((10,15), f"Rp {amount:,.0f}", fill=(255,255,255), font_size=16) # Ukuran font teks uang
            self.money_images[amount] = ImageTk.PhotoImage(img)

        self.item_colors = {
            'Vanilla': '#F3E5AB', 'Chocolate': '#6F4E37', 
            'Caramel': '#D2B48C', 'Sprinkles': '#F08080'
        }
        for item, color in self.item_colors.items():
            img = Image.new('RGB', (100, 100), color=color)
            self.image_references[item] = ImageTk.PhotoImage(img)

    def create_product_frame(self, master):
        frame = tk.Frame(master, bg="#2E2E2E", bd=5, relief="groove")
        tk.Label(frame, text="Pilih Es Krim Favorit Anda", font=self.FONT_HEADER, fg="white", bg="#2E2E2E").pack(pady=10)
        
        products_frame = tk.Frame(frame, bg="#2E2E2E")
        products_frame.pack(padx=10, pady=5)
        
        row, col = 0, 0
        for item, price in self.vm.menu_prices.items():
            item_frame = tk.Frame(products_frame, bg="#1E1E1E", width=200, height=220, padx=5, pady=5, bd=2, relief="raised")
            item_frame.grid(row=row, column=col, padx=15, pady=15, sticky="n") # Jarak diperlebar
            item_frame.grid_propagate(False)

            color = self.item_colors.get(item, 'grey')
            # Gambar produk placeholder
            img_label = tk.Label(item_frame, bg=color, text="[Gambar]", fg="black", font=self.FONT_STOCK)
            img_label.pack(pady=5, fill="x", expand=True)

            tk.Label(item_frame, text=item, font=self.FONT_TITLE, fg="white", bg="#1E1E1E").pack()
            tk.Label(item_frame, text=f"Rp {price:,.0f}", font=self.FONT_PRICE, fg="#FFD700", bg="#1E1E1E").pack()
            
            stock_label = tk.Label(item_frame, text=f"Stok: {self.vm.item_stocks.get(item, 0)}", font=self.FONT_STOCK, fg="#B0B0B0", bg="#1E1E1E")
            stock_label.pack()
            self.item_stock_labels[item] = stock_label
            
            btn = tk.Button(item_frame, text="Pilih", command=lambda i=item: self.handle_input(i), 
                            bg="#32CD32", fg="white", font=self.FONT_BUTTON, 
                            activebackground="#228B22", relief="flat")
            btn.pack(pady=5, fill="x")
            self.item_buttons[item] = btn

            col += 1
            if col > 1:
                col = 0
                row += 1

        return frame

    def create_status_frame(self, master):
        frame = tk.Frame(master, bg="#2E2E2E", bd=5, relief="groove")
        
        # --- Status Pesanan ---
        tk.Label(frame, text="Status Pesanan", font=self.FONT_TITLE, fg="white", bg="#2E2E2E").pack(pady=5)
        self.label_items = tk.Label(frame, text="Keranjang: -", fg="#ADD8E6", bg="#2E2E2E", anchor="w", font=self.FONT_SUBTITLE)
        self.label_items.pack(fill='x', padx=10)
        self.label_total = tk.Label(frame, text="Total: Rp 0", fg="#FFD700", bg="#2E2E2E", anchor="w", font=self.FONT_SUBTITLE)
        self.label_total.pack(fill='x', padx=10)
        self.label_money = tk.Label(frame, text="Uang Masuk: Rp 0", fg="#98FB98", bg="#2E2E2E", anchor="w", font=self.FONT_SUBTITLE)
        self.label_money.pack(fill='x', padx=10)
        
        tk.Frame(frame, height=2, bg="#4A4A4A").pack(fill='x', padx=10, pady=5)

        # --- Masukkan Uang ---
        tk.Label(frame, text="Masukkan Uang", font=self.FONT_SUBTITLE, fg="white", bg="#2E2E2E").pack(pady=5)
        money_input_frame = tk.Frame(frame, bg="#2E2E2E")
        money_input_frame.pack(padx=10, pady=5)
        
        col = 0
        for amount in self.vm.money_denominations:
            btn = tk.Button(money_input_frame, image=self.money_images[amount], 
                            command=lambda a=amount: self.handle_input(a), 
                            bg="#28a745", activebackground="#218838", relief="flat", bd=0)
            btn.grid(row=0 if col < 2 else 1, column=col % 2, padx=5, pady=5)
            col += 1

        tk.Frame(frame, height=2, bg="#4A4A4A").pack(fill='x', padx=10, pady=5)

        # --- Aksi ---
        tk.Label(frame, text="Aksi", font=self.FONT_SUBTITLE, fg="white", bg="#2E2E2E").pack(pady=5)
        
        self.btn_checkout = tk.Button(frame, text="Checkout / Beli", command=lambda: self.handle_input('Checkout'), 
                                      bg="#007BFF", fg="white", font=self.FONT_BUTTON, activebackground="#0056B3", relief="flat")
        self.btn_checkout.pack(fill='x', padx=10, pady=5)
        
        self.btn_cancel = tk.Button(frame, text="Batalkan Pesanan", command=lambda: self.handle_input('Cancel'), 
                                    bg="#DC3545", fg="white", font=self.FONT_BUTTON, activebackground="#C82333", relief="flat")
        self.btn_cancel.pack(fill='x', padx=10, pady=5)
        
        self.btn_return = tk.Button(frame, text="Ambil Kembalian", command=lambda: self.collect_change(), 
                                    bg="#FFC107", fg="black", font=self.FONT_BUTTON, activebackground="#E0A800", relief="flat")
        self.btn_return.pack(fill='x', padx=10, pady=5)

        tk.Frame(frame, height=2, bg="#4A4A4A").pack(fill='x', padx=10, pady=5)

        # --- Area Notifikasi ---
        tk.Label(frame, text="Notifikasi", font=self.FONT_SUBTITLE, fg="white", bg="#2E2E2E").pack(pady=5)
        self.label_notification = tk.Label(frame, text=self.vm.last_output, fg="white", bg="#1E1E1E", anchor="w", 
                                           justify=tk.LEFT, wraplength=250, bd=1, relief="sunken", font=self.FONT_NOTIFICATION)
        self.label_notification.pack(fill='x', padx=10, pady=5, ipady=10)

        return frame

    def create_dispenser_frame(self, master):
        frame = tk.Frame(master, bg="#2E2E2E", bd=5, relief="groove")
        tk.Label(frame, text="Dispenser (Area Pengambilan)", font=self.FONT_TITLE, fg="white", bg="#2E2E2E").pack(pady=5)
        
        # Canvas untuk Animasi Es Krim
        self.canvas_dispenser = tk.Canvas(frame, width=300, height=200, bg="#1E1E1E", highlightthickness=0)
        self.canvas_dispenser.pack(padx=10, pady=10)
        
        # PENTING: Tentukan posisi tengah berdasarkan ukuran canvas
        self.cone_x_center = 300 // 2  # Set posisi X di tengah
        self.cone_y_bottom = 180       # Posisi Y bawah cone
        self.cone_width = 80
        self.cone_height = 80
        self.cone_y_top_fill = self.cone_y_bottom - self.cone_height + 5 # Posisi Y awal es krim
        self.current_scoop_height = 0
        self.last_scoop_y = self.cone_y_top_fill 

        tk.Label(frame, text="Uang Kembalian:", font=self.FONT_SUBTITLE, fg="white", bg="#2E2E2E").pack()
        self.label_change = tk.Label(frame, text="Rp 0", font=("Arial", 20, "bold"), fg="#FFC107", bg="#2E2E2E") # Ukuran kembalian lebih besar
        self.label_change.pack()
        
        return frame

    # --- Logika Interaksi & Update (Tidak Berubah) ---
    def handle_input(self, input_symbol):
        output = self.vm.delta(input_symbol)
        self.label_notification.config(text=output)
        
        if 'Mengeluarkan item' in output:
            ordered_items = []
            for item in self.vm.menu_prices.keys():
                if item in self.vm.selected_items:
                    for _ in range(self.vm.selected_items[item]):
                        ordered_items.append(item)
            
            scoops_to_animate = [item for item in ordered_items if self.vm.item_types.get(item) == 'scoop']
            toppings_to_animate = [item for item in ordered_items if self.vm.item_types.get(item) == 'topping']

            self.dispenser_item_queue = scoops_to_animate + toppings_to_animate
            self.animate_dispenser_start()

        elif 'Pesanan dibatalkan' in output or 'Kembalian Anda' in output:
             self.canvas_dispenser.delete("all")
             self.vm.selected_items = {}
             self.vm.total_price = 0
             self.vm.money_inserted = 0
             self.update_gui_data()

    def collect_change(self):
        change_amount = self.vm.money_inserted - self.vm.total_price
        
        if self.vm.current_state == 'ReturningChange' and change_amount >= 0:
            if change_amount > 0:
                messagebox.showinfo("Kembalian", f"Anda mengambil kembalian Rp {change_amount:,.0f}.")
                self.label_notification.config(text=f"Kembalian Rp {change_amount:,.0f} diambil.")
            else:
                messagebox.showinfo("Kembalian", "Tidak ada kembalian untuk diambil.")
                self.label_notification.config(text="Tidak ada kembalian.")
            
            self.vm.reset()
            self.canvas_dispenser.delete("all")
            self.update_gui_data()
        elif self.vm.current_state == 'Idle' and self.vm.money_inserted > 0:
            messagebox.showinfo("Kembalian", f"Anda mengambil kembalian Rp {self.vm.money_inserted:,.0f}.")
            self.label_notification.config(text=f"Uang Rp {self.vm.money_inserted:,.0f} dikembalikan.")
            self.vm.reset()
            self.canvas_dispenser.delete("all")
            self.update_gui_data()
        else:
            messagebox.showinfo("Informasi", "Tidak ada kembalian yang tersedia.")


    def update_gui_data(self):
        # ... (Kode update_gui_data sama, hanya label yang menggunakan font baru)
        items_list = [f"{item} ({count})" for item, count in self.vm.selected_items.items()]
        items_str = ", ".join(items_list) if items_list else "-"
        self.label_items.config(text=f"Keranjang: {items_str}")
        self.label_total.config(text=f"Total: Rp {self.vm.total_price:,.0f}")
        self.label_money.config(text=f"Uang Masuk: Rp {self.vm.money_inserted:,.0f}")

        change_display_amount = self.vm.money_inserted - self.vm.total_price
        if change_display_amount < 0:
            change_display_amount = 0
        self.label_change.config(text=f"Rp {change_display_amount:,.0f}")

        for item, btn in self.item_buttons.items():
            stock = self.vm.item_stocks.get(item, 0)
            self.item_stock_labels[item].config(text=f"Stok: {stock}")
            
            if stock <= 0:
                btn.config(state=tk.DISABLED, bg="#777777")
                self.item_stock_labels[item].config(fg="#DC3545")
            else:
                btn.config(state=tk.NORMAL, bg="#32CD32")
                self.item_stock_labels[item].config(fg="#B0B0B0")

    # --- Animasi (Diperbaiki Posisi Tengah) ---
    def draw_cone(self):
        """Menggambar bentuk cone di canvas."""
        x_c, y_b = self.cone_x_center, self.cone_y_bottom
        w, h = self.cone_width, self.cone_height
        
        # Segitiga cone
        self.canvas_dispenser.create_polygon(
            x_c - w/2, y_b - h,
            x_c + w/2, y_b - h,
            x_c, y_b,
            fill="#FFA07A", outline="#CD853F", width=2, tags="cone"
        )
        # Oval di bagian atas cone
        self.canvas_dispenser.create_oval(
            x_c - w/2, y_b - h - 10,
            x_c + w/2, y_b - h + 10,
            fill="#CD853F", outline="#CD853F", width=2, tags="cone_top"
        )
        self.current_scoop_height = 0 
        self.last_scoop_y = self.cone_y_top_fill

    def animate_dispenser_start(self):
        self.canvas_dispenser.delete("all")
        self.draw_cone()
        self.master.after(500, self._animate_next_item)

    def _animate_next_item(self):
        if not self.dispenser_item_queue:
            self.master.after(1500, lambda: self.canvas_dispenser.delete("all"))
            self.canvas_dispenser.create_text(
                self.cone_x_center, self.cone_y_bottom - self.cone_height - 30,
                text="✨ Siap Diambil! ✨", fill="#FFC107", font=self.FONT_TITLE
            )
            # Reset setelah animasi selesai
            self.vm.total_price = 0
            self.vm.selected_items = {} 
            self.update_gui_data()
            return
        
        item_name = self.dispenser_item_queue.pop(0)
        item_type = self.vm.item_types.get(item_name, 'unknown')
        color = self.item_colors.get(item_name, 'gray')
        
        if item_type == 'scoop':
            self._animate_scoop(item_name, color)
        elif item_type == 'topping':
            self._animate_topping(item_name, color)
        else:
            self.master.after(500, self._animate_next_item)

    def _animate_scoop(self, item_name, color):
        """Animasi es krim scoop jatuh ke cone."""
        x_c = self.cone_x_center
        start_y = -30
        scoop_radius = 25
        
        item_id = self.canvas_dispenser.create_oval(
            x_c - scoop_radius, start_y, x_c + scoop_radius, start_y + scoop_radius*2,
            fill=color, outline=color, width=1, tags="scoop"
        )
        
        target_y = self.last_scoop_y - scoop_radius * 2 + 5
        
        self.current_scoop_height += scoop_radius * 1.5
        self.last_scoop_y = target_y + scoop_radius

        def move_scoop():
            current_coords = self.canvas_dispenser.coords(item_id)
            if not current_coords: return
            
            current_y_center = current_coords[1] + scoop_radius
            
            if current_y_center < target_y:
                self.canvas_dispenser.move(item_id, 0, 5)
                self.master.after(20, move_scoop)
            else:
                self.master.after(200, self._animate_next_item)

        move_scoop()

    def _animate_topping(self, item_name, color):
        """Animasi topping jatuh ke atas es krim."""
        x_c = self.cone_x_center
        start_y = -30
        topping_radius = 10
        
        item_id = self.canvas_dispenser.create_oval(
            x_c - topping_radius, start_y, x_c + topping_radius, start_y + topping_radius*2,
            fill=color, outline=color, width=1, tags="topping"
        )
        
        # Target Y adalah di atas scoop terakhir (atau di atas cone jika tidak ada scoop)
        target_y = self.last_scoop_y - 20

        def move_topping():
            current_coords = self.canvas_dispenser.coords(item_id)
            if not current_coords: return
            
            current_y_center = current_coords[1] + topping_radius
            
            if current_y_center < target_y:
                self.canvas_dispenser.move(item_id, 0, 5)
                self.master.after(20, move_topping)
            else:
                self.master.after(200, self._animate_next_item)

        move_topping()


# =================================================================
# 3. MAIN
# =================================================================

if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
        
    root = tk.Tk()
    app = IceCreamVendingGUI(root)
    root.mainloop()