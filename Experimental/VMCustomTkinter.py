# -*- coding: utf-8 -*-
# Vending Machine Es Krim GUI dengan CustomTkinter (Versi Diperbaiki & Disempurnakan)
# Dibuat oleh seorang Software Engineer dengan pengalaman Python 10+ tahun.

import customtkinter as ctk
from PIL import Image
import requests
from io import BytesIO
import threading

# =============================================================================
# BAGIAN 1: LOGIKA INTI VENDING MACHINE (BACKEND)
# =============================================================================
class VendingMachineLogic:
    """Mengelola state, stok, dan logika transaksi dari Vending Machine."""
    
    def __init__(self):
        self.menu = {
            'Vanilla': {'price': 10000, 'image': 'https://placehold.co/150x150/FFF8DC/333333?text=Vanilla'},
            'Chocolate': {'price': 10000, 'image': 'https://placehold.co/150x150/8B4513/FFFFFF?text=Chocolate'},
            'Caramel': {'price': 2000, 'image': 'https://placehold.co/150x150/FFD700/333333?text=Caramel'},
            'Sprinkles': {'price': 2000, 'image': 'https://placehold.co/150x150/FF69B4/FFFFFF?text=Sprinkles'}
        }
        self.money_denominations = {
            2000: 'https://placehold.co/120x60/A2D8B1/333333?text=Rp2.000',
            5000: 'https://placehold.co/120x60/F9C59A/333333?text=Rp5.000',
            10000: 'https://placehold.co/120x60/D6A2D8/333333?text=Rp10.000',
            20000: 'https://placehold.co/120x60/A2B1D8/333333?text=Rp20.000'
        }
        self.stock = {item: 10 for item in self.menu}
        self.current_state = 'Idle' # State: Idle, Payment
        self.selected_items = []
        self.total_price = 0
        self.money_inserted = 0

    def select_item(self, item_name):
        if self.current_state != 'Idle':
            return {'success': False, 'message': "Selesaikan pesanan saat ini terlebih dahulu."}
        if self.stock.get(item_name, 0) > 0:
            self.selected_items.append(item_name)
            self.total_price += self.menu[item_name]['price']
            return {'success': True, 'message': f"{item_name} ditambahkan."}
        return {'success': False, 'message': f"Maaf, stok {item_name} habis."}

    def go_to_payment(self):
        if not self.selected_items:
            return {'success': False, 'message': "Keranjang masih kosong."}
        self.current_state = 'Payment'
        return {'success': True, 'message': f"Total: Rp {self.total_price:,}. Silakan bayar."}

    def insert_money(self, amount):
        if self.current_state != 'Payment':
            return {'success': False, 'message': "Harus checkout terlebih dahulu."}
        self.money_inserted += amount
        return {'success': True, 'message': f"Uang Rp {amount:,} dimasukkan."}

    def process_purchase(self):
        if self.current_state != 'Payment':
            return {'success': False, 'message': "Tidak ada yang perlu dibayar."}
        if self.money_inserted < self.total_price:
            needed = self.total_price - self.money_inserted
            return {'success': False, 'message': f"Uang kurang Rp {needed:,}."}
        
        for item in self.selected_items: self.stock[item] -= 1
            
        change = self.money_inserted - self.total_price
        purchased_items = list(self.selected_items)
        
        return {'success': True, 'message': f"Berhasil! Kembalian Rp {change:,}.", 'change': change, 'items': purchased_items}

    def reset_transaction(self):
        change_to_return = self.money_inserted - self.total_price if self.total_price > 0 else self.money_inserted
        self.current_state = 'Idle'
        self.selected_items.clear()
        self.total_price = 0
        self.money_inserted = 0
        return {'change': change_to_return}
        
    def calculate_change_denominations(self, amount):
        denominations = sorted(self.money_denominations.keys(), reverse=True)
        change_breakdown = []
        remaining = amount
        for d in denominations:
            while remaining >= d:
                change_breakdown.append(d)
                remaining -= d
        return change_breakdown

# =============================================================================
# BAGIAN 2: ANTARMUKA PENGGUNA (FRONTEND - CUSTOMTKINTER)
# =============================================================================

class VendingMachineApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.logic = VendingMachineLogic()
        self.images = {}
        self.product_buttons = {}

        self.title("Vending Machine Es Krim Modern")
        self.geometry("1000x720")
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self._load_images_threaded()
        self._create_widgets()

    def _load_images_threaded(self):
        threading.Thread(target=self._load_images, daemon=True).start()

    def _load_images(self):
        # FIX: Tambahkan header User-Agent untuk menghindari masalah dengan layanan placeholder
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        
        all_images = {**{name: data['image'] for name, data in self.logic.menu.items()},
                      **{f"money_{d}": url for d, url in self.logic.money_denominations.items()}}
        
        for name, url in all_images.items():
            try:
                response = requests.get(url, headers=headers, timeout=10)
                # Pastikan request berhasil dan content-type adalah gambar
                if response.status_code == 200 and 'image' in response.headers['Content-Type']:
                    img_data = Image.open(BytesIO(response.content))
                    size = (150, 150) if not name.startswith('money') else (120, 60)
                    ctk_image = ctk.CTkImage(light_image=img_data, size=size)
                    self.images[name] = ctk_image
                else:
                    raise ValueError(f"URL tidak mengembalikan gambar valid. Status: {response.status_code}")
            except Exception as e:
                print(f"Gagal memuat gambar {name}: {e}")
        
        # Setelah semua gambar dimuat, panggil populate_products dari main thread
        self.after(0, self.populate_products)

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.product_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.product_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.product_frame.grid_columnconfigure((0,1), weight=1)
        
        title = ctk.CTkLabel(self.product_frame, text="Pilih Es Krim & Topping", font=("Arial", 24, "bold"))
        title.grid(row=0, column=0, columnspan=2, pady=10)
        
        self.control_frame = ctk.CTkFrame(self, fg_color="#EAEAEA")
        self.control_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        self.control_frame.grid_rowconfigure(2, weight=1)

        order_frame = ctk.CTkFrame(self.control_frame)
        order_frame.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        order_frame.grid_columnconfigure(0, weight=1)
        
        self.order_title = ctk.CTkLabel(order_frame, text="Pesanan Anda (0 item)", font=("Arial", 16, "bold"))
        self.order_title.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.order_list_frame = ctk.CTkScrollableFrame(order_frame, label_text="")
        self.order_list_frame.grid(row=1, column=0, sticky="ew")

        self.total_price_label = ctk.CTkLabel(order_frame, text="Total Harga: Rp 0", font=("Arial", 16, "bold"))
        self.total_price_label.grid(row=2, column=0, sticky="e", padx=10, pady=10)
        
        self.action_frame = ctk.CTkFrame(self.control_frame)
        self.action_frame.grid(row=1, column=0, padx=15, pady=0, sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=1)
        
        self.checkout_button = ctk.CTkButton(self.action_frame, text="Checkout & Bayar", command=self.on_checkout)
        self.checkout_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.dispenser_frame = ctk.CTkFrame(self.control_frame, fg_color="#333333")
        self.dispenser_frame.grid(row=2, column=0, padx=15, pady=15, sticky="nsew")
        self.dispenser_frame.grid_rowconfigure(1, weight=1)
        self.dispenser_frame.grid_columnconfigure(0, weight=1)
        
        self.notification_label = ctk.CTkLabel(self.dispenser_frame, text="Selamat Datang! Silakan pilih item.", font=("Arial", 14), text_color="white", wraplength=250)
        self.notification_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.output_area = ctk.CTkFrame(self.dispenser_frame, fg_color="transparent")
        self.output_area.grid(row=1, column=0, sticky="nsew")

    def populate_products(self):
        # FIX: Menggunakan .configure pada tombol, bukan membuat label baru
        row, col = 1, 0
        for name, data in self.logic.menu.items():
            card_text = f"{name}\nRp {data['price']:,}"
            card = ctk.CTkButton(self.product_frame, 
                                 text=card_text, 
                                 fg_color="white", 
                                 text_color="black",
                                 hover_color="#F0F0F0",
                                 image=self.images.get(name, None), 
                                 compound="top",
                                 font=("Arial", 14),
                                 command=lambda n=name: self.on_select_item(n))
            
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.product_buttons[name] = card # Simpan referensi tombol
            
            col += 1
            if col > 1:
                col = 0
                row += 1

    def on_select_item(self, item_name):
        result = self.logic.select_item(item_name)
        if result['success']:
            self.update_order_list()
        self.show_notification(result['message'])

    def on_checkout(self):
        result = self.logic.go_to_payment()
        if result['success']:
            self.show_payment_view()
        self.show_notification(result['message'])
        
    def show_payment_view(self):
        for widget in self.action_frame.winfo_children(): widget.destroy()
            
        self.money_inserted_label = ctk.CTkLabel(self.action_frame, text="Uang Masuk: Rp 0", font=("Arial", 16, "bold"), text_color="#27ae60")
        self.money_inserted_label.grid(row=0, column=0, pady=5)
        
        money_buttons_frame = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        money_buttons_frame.grid(row=1, column=0, pady=5)
        
        for i, (amount, url) in enumerate(self.logic.money_denominations.items()):
            btn = ctk.CTkButton(money_buttons_frame, text="", image=self.images.get(f"money_{amount}"),
                                width=120, height=60, fg_color="transparent", hover=False,
                                command=lambda a=amount: self.on_insert_money(a))
            btn.grid(row=i//2, column=i%2, padx=5, pady=5)

        self.purchase_button = ctk.CTkButton(self.action_frame, text="Bayar Sekarang", command=self.on_purchase)
        self.purchase_button.grid(row=2, column=0, pady=10, sticky="ew")
        self.cancel_button = ctk.CTkButton(self.action_frame, text="Batalkan", fg_color="#e74c3c", hover_color="#c0392b", command=self.on_cancel)
        self.cancel_button.grid(row=3, column=0, pady=5, sticky="ew")

    def on_insert_money(self, amount):
        result = self.logic.insert_money(amount)
        if result['success']:
            self.money_inserted_label.configure(text=f"Uang Masuk: Rp {self.logic.money_inserted:,}")
        self.show_notification(result['message'])
        
    def on_purchase(self):
        result = self.logic.process_purchase()
        self.show_notification(result['message'])
        if result['success']:
            self.run_dispense_animation(result['items'], result['change'])
            self.update_stock_display()

    def on_cancel(self):
        result = self.logic.reset_transaction()
        self.show_notification("Pesanan dibatalkan.", 5)
        self.show_change(result['change'])
        # Tidak perlu reset view di sini, show_change akan menanganinya

    def update_order_list(self):
        for widget in self.order_list_frame.winfo_children(): widget.destroy()
        self.order_title.configure(text=f"Pesanan Anda ({len(self.logic.selected_items)} item)")
        for item in self.logic.selected_items:
            price = self.logic.menu[item]['price']
            item_label = ctk.CTkLabel(self.order_list_frame, text=f"- {item} (Rp {price:,})")
            item_label.pack(anchor="w", padx=5)
        self.total_price_label.configure(text=f"Total Harga: Rp {self.logic.total_price:,}")
    
    def update_stock_display(self):
        # Fungsi baru untuk update stok setelah pembelian
        for name, button in self.product_buttons.items():
            if self.logic.stock[name] == 0:
                button.configure(state="disabled", fg_color="#AAAAAA")
        
    def show_notification(self, message, duration=3):
        self.notification_label.configure(text=message)
        self.after(duration * 1000, lambda: self.notification_label.configure(text=""))
        
    def run_dispense_animation(self, items, change):
        for widget in self.action_frame.winfo_children(): widget.destroy()
        self.show_notification("Membuat es krim...", 5)
        
        canvas = ctk.CTkCanvas(self.output_area, bg="#333333", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        colors = {'Vanilla': 'ivory', 'Chocolate': '#6B4226', 'Caramel': 'goldenrod', 'Sprinkles': 'pink'}
        shapes = [canvas.create_oval(50 + i*60, -50, 100 + i*60, 0, fill=colors.get(item, 'grey'), outline=colors.get(item, 'grey')) for i, item in enumerate(items)]

        def animate_fall(step=0):
            if step < 100:
                for shape in shapes: canvas.move(shape, 0, 1.5)
                self.after(15, animate_fall, step + 1)
            else:
                self.show_notification("Silakan ambil pesanan Anda.", 5)
                self.after(1000, lambda: self.show_change(change))
                self.after(2000, lambda: canvas.destroy())
        animate_fall()
        
    def show_change(self, change_amount):
        if change_amount <= 0:
            self.after(2000, self.reset_to_idle_view)
            return
            
        self.show_notification(f"Kembalian Anda Rp {change_amount:,}.", 10)
        change_breakdown = self.logic.calculate_change_denominations(change_amount)
        
        change_frame = ctk.CTkFrame(self.output_area, fg_color="transparent")
        change_frame.pack(pady=10)
        
        for i, amount in enumerate(change_breakdown):
            img_label = ctk.CTkLabel(change_frame, text="", image=self.images.get(f"money_{amount}"))
            img_label.grid(row=i//2, column=i%2, padx=2, pady=2)
            
        take_change_btn = ctk.CTkButton(self.output_area, text="Ambil Kembalian & Selesai", command=lambda: self.reset_to_idle_view(frame=change_frame))
        take_change_btn.pack(pady=10)

    def reset_to_idle_view(self, frame=None):
        if frame: frame.destroy()
        for widget in self.output_area.winfo_children(): widget.destroy()
        for widget in self.action_frame.winfo_children(): widget.destroy()
            
        self.checkout_button = ctk.CTkButton(self.action_frame, text="Checkout & Bayar", command=self.on_checkout)
        self.checkout_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.logic.reset_transaction()
        self.update_order_list()
        self.show_notification("Selamat Datang! Silakan pilih item.", 5)

if __name__ == "__main__":
    app = VendingMachineApp()
    app.mainloop()
