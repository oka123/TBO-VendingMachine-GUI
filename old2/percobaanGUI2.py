import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw
from tkinter import messagebox
import os
import tkinter as tk

# Set appearance mode and default color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# =================================================================
# 1. LOGIKA INTI (Vending Machine DFA) - Sama seperti sebelumnya
# =================================================================

class VendingMachineDFA:
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
        self.current_state = 'Idle'
        self.selected_items = {}
        self.total_price = 0
        self.money_inserted = 0
        self.last_output = "🍦 Mesin Es Krim Siap! Silakan pilih item."

    def delta(self, input_symbol):
        state = self.current_state
        output = ""
        is_money_input = isinstance(input_symbol, int)

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
# 2. LOGIKA GUI (CustomTkinter) - Implementasi CTk
# =================================================================

class IceCreamVendingGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Vending Machine Es Krim Modern (CustomTkinter)")
        self.geometry("900x650") # Sedikit dilebarkan
        
        self.vm = VendingMachineDFA()
        self.item_buttons = {}
        self.item_stock_labels = {}
        self.dispenser_item_queue = []

        # Konfigurasi Grid Utama
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Inisialisasi Gambar
        self.image_references = {}
        self.load_images()
        
        # Inisialisasi Frame
        self.frame_products = self.create_product_frame(self)
        self.frame_status = self.create_status_frame(self)
        self.frame_dispenser = self.create_dispenser_frame(self)
        
        self.frame_products.grid(row=0, column=0, rowspan=2, padx=15, pady=15, sticky="nsew")
        self.frame_status.grid(row=0, column=1, padx=15, pady=15, sticky="n")
        self.frame_dispenser.grid(row=1, column=1, padx=15, pady=15, sticky="s")

        self.update_gui_data()
        
    def load_images(self):
        """Membuat gambar placeholder sederhana untuk uang menggunakan PIL/CTK."""
        self.money_images = {}
        for amount in self.vm.money_denominations:
            # Buat gambar PIL/Image untuk teks uang
            img = Image.new('RGB', (100, 50), color = '#28a745') 
            d = ImageDraw.Draw(img)
            d.text((10,15), f"Rp {amount:,.0f}", fill=(255,255,255), font=None, size=16) 
            
            # Konversi ke CTkImage
            self.money_images[amount] = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 50))

        # Warna untuk placeholder item
        self.item_colors = {
            'Vanilla': '#F3E5AB', 'Chocolate': '#6F4E37', 
            'Caramel': '#D2B48C', 'Sprinkles': '#F08080'
        }
        for item, color in self.item_colors.items():
            img = Image.new('RGB', (120, 100), color=color)
            self.image_references[item] = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 100))
            
    # --- Struktur GUI ---
    def create_product_frame(self, master):
        frame = ctk.CTkFrame(master, corner_radius=10)
        
        ctk.CTkLabel(frame, text="Pilih Es Krim Favorit Anda", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        
        products_frame = ctk.CTkFrame(frame, fg_color="transparent")
        products_frame.pack(padx=10, pady=5, fill="both", expand=True)
        products_frame.grid_columnconfigure((0, 1), weight=1)
        
        row, col = 0, 0
        for item, price in self.vm.menu_prices.items():
            item_frame = ctk.CTkFrame(products_frame, corner_radius=10)
            item_frame.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

            # Gambar Produk (Placeholder dengan CTkLabel)
            img_label = ctk.CTkLabel(item_frame, text="[Gambar]", image=self.image_references[item], fg_color=self.item_colors[item], text_color="black")
            img_label.pack(pady=10, padx=10)

            ctk.CTkLabel(item_frame, text=item, font=ctk.CTkFont(size=16, weight="bold")).pack()
            ctk.CTkLabel(item_frame, text=f"Rp {price:,.0f}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#FFD700").pack()
            
            stock_label = ctk.CTkLabel(item_frame, text=f"Stok: {self.vm.item_stocks.get(item, 0)}", font=ctk.CTkFont(size=12), text_color="#B0B0B0")
            stock_label.pack(pady=5)
            self.item_stock_labels[item] = stock_label
            
            btn = ctk.CTkButton(item_frame, text="Pilih", command=lambda i=item: self.handle_input(i), 
                            fg_color="#32CD32", hover_color="#228B22", font=ctk.CTkFont(size=14, weight="bold"))
            btn.pack(pady=(0, 10), padx=10, fill="x")
            self.item_buttons[item] = btn

            col += 1
            if col > 1:
                col = 0
                row += 1

        return frame

    def create_status_frame(self, master):
        frame = ctk.CTkFrame(master, corner_radius=10)
        
        # --- Status Pesanan ---
        ctk.CTkLabel(frame, text="Status Pesanan", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(10, 5))
        self.label_items = ctk.CTkLabel(frame, text="Keranjang: -", text_color="#ADD8E6", anchor="w", font=ctk.CTkFont(size=14))
        self.label_items.pack(fill='x', padx=15)
        self.label_total = ctk.CTkLabel(frame, text="Total: Rp 0", text_color="#FFD700", anchor="w", font=ctk.CTkFont(size=14))
        self.label_total.pack(fill='x', padx=15)
        self.label_money = ctk.CTkLabel(frame, text="Uang Masuk: Rp 0", text_color="#98FB98", anchor="w", font=ctk.CTkFont(size=14))
        self.label_money.pack(fill='x', padx=15, pady=(0, 10))
        
        ctk.CTkFrame(frame, height=2, fg_color="#4A4A4A").pack(fill='x', padx=10, pady=5)

        # --- Masukkan Uang ---
        ctk.CTkLabel(frame, text="Masukkan Uang", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        money_input_frame = ctk.CTkFrame(frame, fg_color="transparent")
        money_input_frame.pack(padx=10, pady=5)
        money_input_frame.grid_columnconfigure((0, 1), weight=1)
        
        col = 0
        for amount in self.vm.money_denominations:
            btn = ctk.CTkButton(money_input_frame, text="", image=self.money_images[amount], 
                            command=lambda a=amount: self.handle_input(a), 
                            fg_color="#28a745", hover_color="#218838", width=100, height=50)
            btn.grid(row=0 if col < 2 else 1, column=col % 2, padx=5, pady=5)
            col += 1

        ctk.CTkFrame(frame, height=2, fg_color="#4A4A4A").pack(fill='x', padx=10, pady=5)

        # --- Aksi ---
        ctk.CTkLabel(frame, text="Aksi", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        self.btn_checkout = ctk.CTkButton(frame, text="Checkout / Beli", command=lambda: self.handle_input('Checkout'), 
                                      fg_color="#007BFF", hover_color="#0056B3", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_checkout.pack(fill='x', padx=15, pady=5)
        
        self.btn_cancel = ctk.CTkButton(frame, text="Batalkan Pesanan", command=lambda: self.handle_input('Cancel'), 
                                    fg_color="#DC3545", hover_color="#C82333", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_cancel.pack(fill='x', padx=15, pady=5)
        
        self.btn_return = ctk.CTkButton(frame, text="Ambil Kembalian", command=lambda: self.collect_change(), 
                                    fg_color="#FFC107", text_color="black", hover_color="#E0A800", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_return.pack(fill='x', padx=15, pady=(5, 10))

        ctk.CTkFrame(frame, height=2, fg_color="#4A4A4A").pack(fill='x', padx=10, pady=5)

        # --- Area Notifikasi ---
        ctk.CTkLabel(frame, text="Notifikasi", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        self.label_notification = ctk.CTkLabel(frame, text=self.vm.last_output, text_color="white", 
                                           justify="left", wraplength=250, font=ctk.CTkFont(size=12),
                                           fg_color="#1E1E1E", corner_radius=5, height=60) # CTkLabel untuk notifikasi
        self.label_notification.pack(fill='x', padx=15, pady=(5, 15))

        return frame

    def create_dispenser_frame(self, master):
        frame = ctk.CTkFrame(master, corner_radius=10)
        ctk.CTkLabel(frame, text="Dispenser (Area Pengambilan)", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        # Canvas untuk Animasi Es Krim (tetap menggunakan Tkinter Canvas di dalam CTkFrame)
        self.canvas_dispenser = tk.Canvas(frame, width=300, height=200, bg="#1E1E1E", highlightthickness=0)
        self.canvas_dispenser.pack(padx=10, pady=10)
        
        self.cone_x_center = 300 // 2 
        self.cone_y_bottom = 180
        self.cone_width = 80
        self.cone_height = 80
        self.cone_y_top_fill = self.cone_y_bottom - self.cone_height + 5
        self.current_scoop_height = 0
        self.last_scoop_y = self.cone_y_top_fill 

        ctk.CTkLabel(frame, text="Uang Kembalian:", font=ctk.CTkFont(size=16)).pack()
        self.label_change = ctk.CTkLabel(frame, text="Rp 0", font=ctk.CTkFont(size=24, weight="bold"), text_color="#FFC107")
        self.label_change.pack(pady=(0, 10))
        
        return frame
        
    # --- Logika Interaksi & Update ---
    def handle_input(self, input_symbol):
        output = self.vm.delta(input_symbol)
        self.label_notification.configure(text=output)
        
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

        elif 'Pesanan dibatalkan' in output:
             self.canvas_dispenser.delete("all")
             self.vm.selected_items = {}
             self.vm.total_price = 0
             self.update_gui_data()

        self.update_gui_data()

    def collect_change(self):
        change_amount = self.vm.money_inserted - self.vm.total_price
        
        if self.vm.current_state == 'ReturningChange' and change_amount >= 0:
            if change_amount > 0:
                messagebox.showinfo("Kembalian", f"Anda mengambil kembalian Rp {change_amount:,.0f}.")
                self.label_notification.configure(text=f"Kembalian Rp {change_amount:,.0f} diambil.")
            else:
                messagebox.showinfo("Kembalian", "Tidak ada kembalian untuk diambil.")
                self.label_notification.configure(text="Tidak ada kembalian.")
            
            self.vm.reset()
            self.canvas_dispenser.delete("all")
            self.update_gui_data()
        elif self.vm.current_state == 'Idle' and self.vm.money_inserted > 0:
            messagebox.showinfo("Kembalian", f"Anda mengambil kembalian Rp {self.vm.money_inserted:,.0f}.")
            self.label_notification.configure(text=f"Uang Rp {self.vm.money_inserted:,.0f} dikembalikan.")
            self.vm.reset()
            self.canvas_dispenser.delete("all")
            self.update_gui_data()
        else:
            messagebox.showinfo("Informasi", "Tidak ada kembalian yang tersedia.")


    def update_gui_data(self):
        items_list = [f"{item} ({count})" for item, count in self.vm.selected_items.items()]
        items_str = ", ".join(items_list) if items_list else "-"
        self.label_items.configure(text=f"Keranjang: {items_str}")
        self.label_total.configure(text=f"Total: Rp {self.vm.total_price:,.0f}")
        self.label_money.configure(text=f"Uang Masuk: Rp {self.vm.money_inserted:,.0f}")

        change_display_amount = self.vm.money_inserted - self.vm.total_price
        if change_display_amount < 0:
            change_display_amount = 0
        self.label_change.configure(text=f"Rp {change_display_amount:,.0f}")

        for item, btn in self.item_buttons.items():
            stock = self.vm.item_stocks.get(item, 0)
            self.item_stock_labels[item].configure(text=f"Stok: {stock}")
            
            if stock <= 0:
                btn.configure(state="disabled", fg_color="#777777")
                self.item_stock_labels[item].configure(text_color="#DC3545")
            else:
                btn.configure(state="normal", fg_color="#32CD32")
                self.item_stock_labels[item].configure(text_color="#B0B0B0")

    # --- Animasi (Dipertahankan di Canvas Tkinter) ---
    def draw_cone(self):
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
        self.after(500, self._animate_next_item) # Menggunakan CTk method 'after'

    def _animate_next_item(self):
        if not self.dispenser_item_queue:
            self.after(1500, lambda: self.canvas_dispenser.delete("all"))
            self.canvas_dispenser.create_text(
                self.cone_x_center, self.cone_y_bottom - self.cone_height - 30,
                text="✨ Siap Diambil! ✨", fill="#FFC107", font=("Arial", 16, "bold")
            )
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
            self.after(500, self._animate_next_item)

    def _animate_scoop(self, item_name, color):
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
                self.after(20, move_scoop)
            else:
                self.after(200, self._animate_next_item)

        move_scoop()

    def _animate_topping(self, item_name, color):
        x_c = self.cone_x_center
        start_y = -30
        topping_radius = 10
        
        item_id = self.canvas_dispenser.create_oval(
            x_c - topping_radius, start_y, x_c + topping_radius, start_y + topping_radius*2,
            fill=color, outline=color, width=1, tags="topping"
        )
        
        target_y = self.last_scoop_y - 20

        def move_topping():
            current_coords = self.canvas_dispenser.coords(item_id)
            if not current_coords: return
            
            current_y_center = current_coords[1] + topping_radius
            
            if current_y_center < target_y:
                self.canvas_dispenser.move(item_id, 0, 5)
                self.after(20, move_topping)
            else:
                self.after(200, self._animate_next_item)

        move_topping()


# =================================================================
# 3. MAIN
# =================================================================

if __name__ == "__main__":
    # Ini diperlukan agar CTk berjalan sebagai root window
    app = IceCreamVendingGUI()
    app.mainloop()