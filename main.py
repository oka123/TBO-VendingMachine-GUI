# main.py

import customtkinter as ctk
import tkinter as tk
from PIL import Image
from vending_machine_dfa import VendingMachineDFA
import simpleaudio as sa
from threading import Thread
from itertools import count

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.vm_dfa = VendingMachineDFA()
        self.title("Vending Machine Es Krim")
        self.geometry("1000x720")
        self.minsize(800, 600) # Menetapkan ukuran minimum jendela
        ctk.set_appearance_mode("dark")

        self.item_types = {
            'Vanilla Scoop': 'scoop', 'Chocolate Scoop': 'scoop',
            'Caramel': 'topping', 'Sprinkles': 'topping'
        }
        self.item_colors = {
            'Vanilla Scoop': '#FFFACD', # LemonChiffon
            'Chocolate Scoop': '#8B4513', # SaddleBrown
            'Caramel': '#D2691E', # Chocolate
            'Sprinkles': '#FF69B4'  # HotPink (sebagai representasi)
        }
        self.dispenser_item_queue = []

        # self.animation_frames = []
        # self.animation_job = None

        self.load_assets()
        self.setup_ui()
        self.update_gui("Selamat datang! Silakan pilih es krim.")

    def load_assets(self):
        try:
            self.product_images = {name: ctk.CTkImage(Image.open(f"assets/images/{name}.png"), size=(100, 80)) for name in self.vm_dfa.menu_prices}
            self.money_images = {val: ctk.CTkImage(Image.open(f"assets/images/{val}.png"), size=(120, 50)) for val in [2000, 5000, 10000, 20000]}
            self.clicked_sound = sa.WaveObject.from_wave_file("assets/sounds/clicked.wav")
            self.take_change_sound = sa.WaveObject.from_wave_file("assets/sounds/take_change.wav")
            self.ice_cream_sound = sa.WaveObject.from_wave_file("assets/sounds/ice_cream.wav")
        except Exception as e:
            print(f"Error loading assets: {e}")
            self.destroy() # Keluar jika aset gagal dimuat

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- FRAME KIRI (PRODUK & DISPENSER) ---
        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        left_frame.grid_rowconfigure(0, weight=1) 
        left_frame.grid_rowconfigure(1, weight=0) # Baris untuk judul dispenser
        left_frame.grid_rowconfigure(2, weight=0) # Baris untuk frame dispenser
        left_frame.grid_columnconfigure(0, weight=1)

        # Masalah 2: Menggunakan CTkScrollableFrame untuk produk
        self.products_scroll_frame = ctk.CTkScrollableFrame(left_frame, label_text="Pilih Item", label_font=("Arial", 20, "bold"))
        self.products_scroll_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        self.products_scroll_frame.grid_columnconfigure((0, 1), weight=1)

        self.product_buttons = {}
        for i, (name, price) in enumerate(self.vm_dfa.menu_prices.items()):
            image = self.product_images.get(name)
            button = ctk.CTkButton(self.products_scroll_frame, text=f"{name}\nRp{price}", image=image, compound="top", fg_color="#1E1E1E", hover_color="#4A4A4A", font=("Arial", 14), command=lambda p=name: self.handle_input(p))
            # button.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="ew", ipady=10)
            self.product_buttons[name] = button
        
        # PERUBAHAN PADA AREA DISPENSER
        dispenser_title = ctk.CTkLabel(left_frame, text="Area Dispenser", font=("Arial", 20, "bold"))
        dispenser_title.grid(row=1, column=0, padx=0, pady=(15, 5))

        # Menggunakan Tkinter Canvas di dalam CTkFrame
        self.dispenser_frame = ctk.CTkFrame(left_frame, fg_color="#1E1E1E")
        self.dispenser_frame.grid(row=2, column=0, padx=0, pady=(0,0), sticky="nsew")
        
        canvas_width = 400
        canvas_height = 250
        self.canvas_dispenser = tk.Canvas(self.dispenser_frame, width=canvas_width, height=canvas_height, bg="#1E1E1E", highlightthickness=0)
        self.canvas_dispenser.pack(expand=True, pady=10)

        # Variabel untuk posisi cone dan scoop
        self.cone_x_center = canvas_width / 2
        self.cone_y_bottom = canvas_height - 20
        self.cone_width = 80
        self.cone_height = 80
        self.last_scoop_y = self.cone_y_bottom - self.cone_height

        # --- FRAME KANAN (KONTROL) ---
        right_scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        right_scroll_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        
        # Area notifikasi yang bisa di-scroll
        notification_frame = ctk.CTkFrame(right_scroll_frame)
        notification_frame.pack(fill="both", expand=True, padx=5, pady=5)
        ctk.CTkLabel(notification_frame, height=0, text="Status", font=("Arial", 16, "bold")).pack(padx=10, pady=(10,0))
        self.notification_textbox = ctk.CTkTextbox(notification_frame, font=("Arial", 14), wrap="word", height=70)
        self.notification_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.notification_textbox.configure(state="disabled")

        # Frame untuk List Pesanan
        order_frame = ctk.CTkFrame(right_scroll_frame)
        order_frame.pack(fill="x", expand=True, padx=5, pady=5)
        ctk.CTkLabel(order_frame, height=0, text="List Pesanan", font=("Arial", 18, "bold")).pack(padx=10, pady=10)
        self.order_list_textbox = ctk.CTkTextbox(order_frame, height=70, font=("Arial", 14))
        self.order_list_textbox.pack(fill="x", expand=True, padx=10, pady=(0, 10))

        # Frame untuk Info Harga
        info_frame = ctk.CTkFrame(right_scroll_frame)
        info_frame.pack(fill="x", expand=True, padx=5, pady=5)
        info_frame.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(info_frame, text="Total Harga:", font=("Arial", 16)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.price_label = ctk.CTkLabel(info_frame, text="Rp0", font=("Arial", 20, "bold"))
        self.price_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        ctk.CTkLabel(info_frame, text="Uang Masuk:", font=("Arial", 16)).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.inserted_money_label = ctk.CTkLabel(info_frame, text="Rp0", font=("Arial", 20, "bold"), text_color="#33FF57")
        self.inserted_money_label.grid(row=1, column=1, padx=10, pady=5, sticky="e")

        # Frame untuk Pembayaran
        payment_frame = ctk.CTkFrame(right_scroll_frame)
        payment_frame.pack(fill="x", expand=True, padx=5, pady=5)
        payment_frame.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(payment_frame, height=0, text="Masukkan Uang", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        self.money_buttons = {}
        for i, val in enumerate([2000, 5000, 10000, 20000]):
            image = self.money_images.get(val)
            button = ctk.CTkButton(payment_frame, height=70, text="", image=image, fg_color="#1E1E1E", hover_color="#4A4A4A", command=lambda v=val: self.handle_input(v))
            button.grid(row=(i//2)+1, column=i%2, padx=5, pady=5, sticky="ew")
            self.money_buttons[val] = button

        # Frame untuk Tombol Aksi
        action_frame = ctk.CTkFrame(right_scroll_frame)
        action_frame.pack(fill="x", expand=True, padx=5, pady=5)
        action_frame.grid_columnconfigure((0, 1), weight=1)

        self.next_button = ctk.CTkButton(action_frame, height=50, text="Next", command=lambda: self.handle_input('Next'))
        self.next_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.cancel_button = ctk.CTkButton(action_frame, height=50, text="Cancel", fg_color="red", hover_color="#8B0000", command=lambda: self.handle_input('Cancel'))
        self.cancel_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.checkout_button = ctk.CTkButton(action_frame, height=50, text="Checkout", fg_color="green", hover_color="#006400", command=lambda: self.handle_input('Checkout'))
        self.checkout_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        money_slot = ctk.CTkFrame(action_frame, height=10, fg_color="black", border_width=2, border_color="grey")
        money_slot.grid(row=2, column=0, columnspan=2, padx=40, pady=10, sticky="ew")

        # Frame untuk Kembalian
        self.change_frame = ctk.CTkFrame(right_scroll_frame, height=0)
        self.change_frame.pack(fill="x", expand=True, padx=5, pady=5)
        self.take_change_button = ctk.CTkButton(right_scroll_frame, height=50, text="Ambil Kembalian & Selesai", command=self.take_change)
        self.take_change_button.pack(fill='x', padx=5, pady=10)

    def handle_input(self, input_symbol):
        # Mencegah input lain saat animasi sedang berjalan.
        if self.vm_dfa.current_state == 'DispensingItem':
            return
        
        # Putar suara jika item yang valid dan tersedia dipilih.
        # if input_symbol in self.vm_dfa.menu_prices:
        self.play_clicked_sound()

        # Kirim input ke logika DFA dan dapatkan output-nya.
        output = self.vm_dfa.delta(input_symbol)

        # Periksa state SETELAH input diproses
        if self.vm_dfa.current_state == 'DispensingItem':
            self.show_animation()
        else:
            # Perbarui GUI dengan pesan output
            self.update_gui(output)
            # panggil show_change() untuk menampilkan kembalian.
            if self.vm_dfa.current_state == 'ReturningChange':
                self.show_change()

    def update_gui(self, message):
        self.price_label.configure(text=f"Rp{self.vm_dfa.total_price}")
        self.inserted_money_label.configure(text=f"Rp{self.vm_dfa.money_inserted}")

        self.order_list_textbox.configure(state="normal")
        self.order_list_textbox.delete("1.0", "end")
        order_text = "\n".join(f"- {item}" for item in self.vm_dfa.selected_items) if self.vm_dfa.selected_items else "Belum ada pesanan..."
        self.order_list_textbox.insert("1.0", order_text)
        self.order_list_textbox.configure(state="disabled")

        self.notification_textbox.configure(state="normal")
        if message: # Hanya tambahkan jika ada pesan
            self.notification_textbox.insert("end", f"> {message}\n")
            self.notification_textbox.see("end")
        self.notification_textbox.configure(state="disabled")

        state = self.vm_dfa.current_state

        # PERBAIKAN: Logika untuk menampilkan tombol produk yang sesuai
        self._update_product_display(state)

        # PERBAIKAN: Logika untuk mengaktifkan/menonaktifkan tombol aksi
        for button in self.money_buttons.values():
            button.configure(state="normal" if state == 'WaitingForPayment' else "disabled")

        self.next_button.configure(state="normal" if state == 'IceCreamSelection' and self.vm_dfa.selected_items else "disabled")
        self.checkout_button.configure(state="normal" if state == 'ToppingSelection' else "disabled")
        self.cancel_button.configure(state="normal" if state not in ['Idle', 'ReturningChange', 'DispensingItem'] else "disabled")
        self.take_change_button.configure(state="normal" if state == 'ReturningChange' else "disabled")

    def _update_product_display(self, current_state):
        """Menampilkan/menyembunyikan tombol produk berdasarkan state."""
        scoop_count = 0
        topping_count = 0
        
        if current_state in ['Idle', 'IceCreamSelection']:
            self.products_scroll_frame.configure(label_text="Pilih Es Krim")
        elif current_state == 'ToppingSelection':
            self.products_scroll_frame.configure(label_text="Pilih Topping")
        else:
            # Judul default saat tidak dalam fase pemilihan
            self.products_scroll_frame.configure(label_text="Item Pilihan")
            
        for name, button in self.product_buttons.items():
            item_type = self.vm_dfa.item_types.get(name)
            
            if current_state in ['Idle', 'IceCreamSelection'] and item_type == 'scoop':
                row, col = divmod(scoop_count, 2)
                button.grid(row=row, column=col, padx=10, pady=10, sticky="ew", ipady=10)
                button.configure(state="normal")
                scoop_count += 1
            elif current_state == 'ToppingSelection' and item_type == 'topping':
                row, col = divmod(topping_count, 2)
                button.grid(row=row, column=col, padx=10, pady=10, sticky="ew", ipady=10)
                button.configure(state="normal")
                topping_count += 1
            else:
                button.grid_remove() 

    def play_clicked_sound(self):
        if self.clicked_sound:
            Thread(target=lambda: self.clicked_sound.play(), daemon=True).start()

    def play_take_change_sound(self):
        if self.take_change_sound:
            Thread(target=lambda: self.take_change_sound.play(), daemon=True).start()

    def play_ice_cream_sound(self):
        if self.ice_cream_sound:
            Thread(target=lambda: self.ice_cream_sound.play(), daemon=True).start()

    def show_animation(self):
        """Mempersiapkan dan memulai animasi dispenser."""
        # Nonaktifkan semua tombol
        for button in self.product_buttons.values(): button.configure(state="disabled")
        for button in self.money_buttons.values(): button.configure(state="disabled")
        self.checkout_button.configure(state="disabled")
        self.cancel_button.configure(state="disabled")
        
        self.update_gui("Pesanan sedang diproses...")
        self.play_ice_cream_sound()
        
        # Siapkan antrian item untuk dianimasikan
        self.dispenser_item_queue = self.vm_dfa.selected_items.copy()
        
        # Mulai animasi
        self.animate_dispenser_start()

    def draw_cone(self):
        """Menggambar cone es krim di canvas."""
        x_c, y_b = self.cone_x_center, self.cone_y_bottom
        w, h = self.cone_width, self.cone_height
        
        self.canvas_dispenser.create_polygon(
            x_c - w/2, y_b - h, x_c + w/2, y_b - h, x_c, y_b,
            fill="#FFA07A", outline="#CD853F", width=2
        )
        self.canvas_dispenser.create_oval(
            x_c - w/2, y_b - h - 10, x_c + w/2, y_b - h + 10,
            fill="#CD853F", outline="#CD853F", width=2
        )
        # Reset posisi Y untuk scoop pertama
        self.last_scoop_y = self.cone_y_bottom - self.cone_height + 5

    def animate_dispenser_start(self):
        """Membersihkan canvas dan memulai urutan animasi."""
        self.canvas_dispenser.delete("all")
        self.draw_cone()
        self.after(500, self._animate_next_item)

    def _animate_next_item(self):
        """Memproses item berikutnya dalam antrian untuk dianimasikan."""
        if not self.dispenser_item_queue:
            # Jika semua item sudah dianimasikan
            self.canvas_dispenser.create_text(
                self.cone_x_center, 50,
                text="✨ Siap Diambil! ✨", fill="#FFC107", font=("Arial", 24, "bold")
            )
            self.after(1000, self.finish_transaction) # Tunggu 1 detik sebelum selesai
            return
        
        item_name = self.dispenser_item_queue.pop(0)
        item_type = self.item_types.get(item_name)
        color = self.item_colors.get(item_name, 'gray')
        
        if item_type == 'scoop':
            self._animate_scoop(color)
        elif item_type == 'topping':
            self._animate_topping(color)

    def _animate_scoop(self, color):
        """Menganimasikan satu scoop es krim jatuh."""
        x_c = self.cone_x_center
        start_y = -30
        scoop_radius = 30
        
        item_id = self.canvas_dispenser.create_oval(
            x_c - scoop_radius, start_y, x_c + scoop_radius, start_y + 2 * scoop_radius,
            fill=color, outline=color
        )
        
        # Tentukan posisi target Y, menumpuk di atas scoop sebelumnya
        target_y_center = self.last_scoop_y - scoop_radius
        
        # Update posisi Y untuk scoop berikutnya
        self.last_scoop_y -= scoop_radius * 1.5

        def move_scoop():
            coords = self.canvas_dispenser.coords(item_id)
            if not coords: return
            
            current_y_center = coords[1] + scoop_radius
            if current_y_center < target_y_center:
                self.canvas_dispenser.move(item_id, 0, 8) # Kecepatan jatuh
                self.after(20, move_scoop)
            else:
                self.after(300, self._animate_next_item) # Jeda sebelum item berikutnya
        move_scoop()
        
    def _animate_topping(self, color):
        """Menganimasikan topping jatuh (sebagai titik-titik kecil)."""
        x_c, y_start = self.cone_x_center, -20
        # Buat beberapa partikel topping
        particles = [self.canvas_dispenser.create_oval(x_c-20+i*5, y_start, x_c-15+i*5, y_start+5, fill=color, outline=color) for i in range(10)]
        target_y = self.last_scoop_y

        def move_particles():
            all_done = True
            for p_id in particles:
                coords = self.canvas_dispenser.coords(p_id)
                if not coords: continue
                
                if coords[1] < target_y:
                    all_done = False
                    # Gerakan acak agar terlihat seperti taburan
                    self.canvas_dispenser.move(p_id, 0, 10 + (-1)**p_id)
            
            if not all_done:
                self.after(30, move_particles)
            else:
                self.after(300, self._animate_next_item)
        move_particles()

    def finish_transaction(self):
        """Dipanggil setelah semua animasi selesai."""
        output = self.vm_dfa.delta(None)
        self.update_gui(output)
        self.show_change()

    def _calculate_change(self, amount, denominations):
        """
        Menghitung kombinasi uang kembalian menggunakan rekursi dan backtracking.
        Fungsi ini akan menemukan kombinasi yang pas.
        """
        # Base case 1: Jika jumlahnya 0, kita berhasil.
        if amount == 0:
            return []
        # Base case 2: Jika tidak ada denominasi lagi tapi jumlah masih > 0, jalur ini gagal.
        if not denominations:
            return None

        # Ambil denominasi terbesar saat ini
        current_denom = denominations[0]
        # Sisa denominasi untuk rekursi berikutnya
        remaining_denoms = denominations[1:]

        # Coba gunakan denominasi saat ini sebanyak mungkin
        max_count = amount // current_denom
        for count in range(max_count, -1, -1):
            # Hitung sisa amount
            remainder = amount - count * current_denom
            
            # Panggil fungsi rekursif untuk sisa amount dan sisa denominasi
            result = self._calculate_change(remainder, remaining_denoms)
            
            # Jika rekursi berhasil (menemukan solusi untuk sisa)
            if result is not None:
                # Gabungkan hasilnya: (jumlah denom saat ini) + (hasil dari sisa)
                return [current_denom] * count + result
                
        # Jika tidak ada kombinasi yang berhasil dari loop di atas, jalur ini gagal.
        return None

    # Ganti fungsi show_change Anda dengan ini
    def show_change(self):
        """Menghitung dan menampilkan gambar uang kembalian."""
        # Hapus gambar kembalian dari transaksi sebelumnya
        for widget in self.change_frame.winfo_children():
            widget.destroy()

        amount = self.vm_dfa.change_to_return
        if amount <= 0:
            return
        
        denominations = sorted([k for k in self.money_images.keys()], reverse=True)
        
        # Tahap 1: Coba temukan kombinasi yang pas menggunakan backtracking
        bills_to_return = self._calculate_change(amount, denominations)
        
        change_images = []
        
        # Tahap 2: Jika tidak ada kombinasi pas, gunakan algoritma greedy sebagai fallback
        if bills_to_return is None:
            self.notification_textbox.configure(state="normal")
            self.notification_textbox.insert("end", f"> PERINGATAN: Tidak dapat memberikan kembalian pas.\n")
            self.notification_textbox.see("end")
            self.notification_textbox.configure(state="disabled")

            # Algoritma greedy untuk memberikan kembalian semaksimal mungkin
            temp_amount = amount
            for d in denominations:
                while temp_amount >= d:
                    change_images.append(self.money_images[d])
                    temp_amount -= d
        else:
            # Jika kombinasi pas ditemukan, gunakan hasilnya
            change_images = [self.money_images[bill] for bill in bills_to_return]

        # Tampilkan gambar-gambar uang yang berhasil dihitung
        max_items_per_row = 3
        for i, img in enumerate(change_images):
            row = i // max_items_per_row
            col = i % max_items_per_row
            label = ctk.CTkLabel(self.change_frame, image=img, text="")
            label.grid(row=row, column=col, padx=2, pady=2)

    def take_change(self):
        self.vm_dfa.reset()
        self.play_take_change_sound()
        for widget in self.change_frame.winfo_children(): widget.destroy()
        # 1. Hapus semua gambar dari canvas
        self.canvas_dispenser.delete("all")
        
        # 2. Gambar ulang teks default di tengah canvas
        canvas_width = self.canvas_dispenser.winfo_width()
        canvas_height = self.canvas_dispenser.winfo_height()
        self.canvas_dispenser.create_text(
            canvas_width / 2, canvas_height / 2,
            text="[Area Dispenser]", fill="white", font=("Arial", 16)
        )
        self.notification_textbox.configure(state="normal")
        self.notification_textbox.delete("1.0", "end")
        self.notification_textbox.configure(state="disabled")
        self.update_gui("Selamat datang! Silakan pilih es krim.")

        self.vm_dfa.current_state == 'Idle'

if __name__ == "__main__":
    app = App()
    app.mainloop()