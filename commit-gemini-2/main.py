import customtkinter as ctk
from PIL import Image
from vending_machine_dfa2 import VendingMachineDFA
import simpleaudio as sa
from threading import Thread
from itertools import count

class VendingMachineApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.vm_dfa = VendingMachineDFA()
        self.title("Vending Machine Es Krim")
        self.geometry("1000x720")
        self.resizable(True, True)
        ctk.set_appearance_mode("dark")

        self.animation_frames = []
        self.animation_job = None
        
        self.load_assets()
        self.setup_ui()
        # PERBAIKAN 1: Pesan awal sekarang akan tetap terlihat.
        self.log_message("Selamat datang! Silakan pilih es krim.")
        self.update_gui() # Lakukan update awal untuk menonaktifkan tombol yang tidak relevan

    def load_assets(self):
        try:
            self.product_images = {name: ctk.CTkImage(Image.open(f"assets/images/{name}.png"), size=(100, 80)) for name in self.vm_dfa.menu_prices}
            self.money_images = {val: ctk.CTkImage(Image.open(f"assets/images/{val}.png"), size=(120, 50)) for val in [2000, 5000, 10000, 20000]}
            self.notification_sound = sa.WaveObject.from_wave_file("assets/sounds/notification.wav")
            
            gif_path = "assets/images/dispensing.gif"
            with Image.open(gif_path) as im:
                for i in count(1):
                    try:
                        frame = ctk.CTkImage(im.copy().convert("RGBA"), size=(100, 100))
                        self.animation_frames.append(frame)
                        im.seek(i)
                    except EOFError:
                        break
        except Exception as e:
            print(f"Error loading assets: {e}")

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Panel Kiri (Produk & Dispenser) ---
        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        # PERBAIKAN 2 & 3: Gunakan CTkScrollableFrame agar produk bisa di-scroll
        products_scroll_frame = ctk.CTkScrollableFrame(left_frame, label_text="Menu Produk", label_font=("Arial", 16, "bold"))
        products_scroll_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        products_scroll_frame.grid_columnconfigure((0, 1), weight=1)

        self.product_buttons = {}
        for i, (name, price) in enumerate(self.vm_dfa.menu_prices.items()):
            image = self.product_images.get(name)
            button = ctk.CTkButton(products_scroll_frame, text=f"Rp {price:,}", image=image, compound="top", font=("Arial", 14), command=lambda p=name: self.handle_input(p))
            button.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="ew", ipady=10)
            self.product_buttons[name] = button

        self.dispenser_frame = ctk.CTkFrame(left_frame, height=150, fg_color="#1E1E1E")
        self.dispenser_frame.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")
        self.dispenser_label = ctk.CTkLabel(self.dispenser_frame, text="[Area Dispenser]", font=("Arial", 16))
        self.dispenser_label.pack(expand=True)

        # --- Panel Kanan (Kontrol) ---
        # PERBAIKAN 2 & 3: Seluruh panel kanan dibuat scrollable
        right_scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#2B2B2B", label_text="")
        right_scroll_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        right_scroll_frame.grid_columnconfigure(0, weight=1)
        
        # --- Di dalam right_scroll_frame ---
        order_frame = ctk.CTkFrame(right_scroll_frame)
        order_frame.grid(row=0, column=0, padx=15, pady=15, sticky="new")
        order_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(order_frame, text="List Pesanan", font=("Arial", 18, "bold")).grid(row=0, column=0, padx=10, pady=10)
        self.order_list_textbox = ctk.CTkTextbox(order_frame, height=120, font=("Arial", 14), state="disabled")
        self.order_list_textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        info_frame = ctk.CTkFrame(right_scroll_frame)
        info_frame.grid(row=1, column=0, padx=15, pady=(0,15), sticky="new")
        info_frame.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(info_frame, text="Total Harga:", font=("Arial", 16)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.price_label = ctk.CTkLabel(info_frame, text="Rp 0", font=("Arial", 16, "bold"))
        self.price_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        ctk.CTkLabel(info_frame, text="Uang Masuk:", font=("Arial", 16)).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.inserted_money_label = ctk.CTkLabel(info_frame, text="Rp 0", font=("Arial", 16, "bold"))
        self.inserted_money_label.grid(row=1, column=1, padx=10, pady=5, sticky="e")

        payment_frame = ctk.CTkFrame(right_scroll_frame)
        payment_frame.grid(row=2, column=0, padx=15, pady=(0,15), sticky="new")
        payment_frame.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(payment_frame, text="Masukkan Uang", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        self.money_buttons = {}
        for i, val in enumerate([2000, 5000, 10000, 20000]):
            image = self.money_images.get(val)
            button = ctk.CTkButton(payment_frame, text="", image=image, command=lambda v=val: self.handle_input(v))
            button.grid(row=(i//2)+1, column=i%2, padx=5, pady=5, sticky="ew")
            self.money_buttons[val] = button

        action_frame = ctk.CTkFrame(right_scroll_frame)
        action_frame.grid(row=3, column=0, padx=15, pady=(0,15), sticky="new")
        action_frame.grid_columnconfigure(0, weight=1)
        self.checkout_button = ctk.CTkButton(action_frame, text="Checkout", fg_color="green", command=lambda: self.handle_input('Checkout'))
        self.checkout_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.cancel_button = ctk.CTkButton(action_frame, text="Cancel", fg_color="red", command=lambda: self.handle_input('Cancel'))
        self.cancel_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        # PERBAIKAN 4: Menambahkan slot uang sebagai hiasan
        money_slot = ctk.CTkFrame(action_frame, height=10, fg_color="#1A1A1A", border_color="#555", border_width=2, corner_radius=5)
        money_slot.grid(row=2, column=0, padx=50, pady=(10,5), sticky="ew")

        # PERBAIKAN 5: Frame untuk kembalian dengan layout "flex-wrap"
        self.change_frame = ctk.CTkFrame(right_scroll_frame, fg_color="transparent")
        self.change_frame.grid(row=4, column=0, padx=15, pady=(0,15), sticky="new")
        self.take_change_button = ctk.CTkButton(right_scroll_frame, text="Ambil Kembalian & Selesai", command=self.take_change)
        self.take_change_button.grid(row=5, column=0, padx=15, pady=10, sticky="ew")

        # PERBAIKAN 6: Area notifikasi yang bisa di-scroll
        message_frame = ctk.CTkFrame(right_scroll_frame)
        message_frame.grid(row=6, column=0, padx=15, pady=15, sticky="nsew")
        message_frame.grid_rowconfigure(0, weight=1)
        message_frame.grid_columnconfigure(0, weight=1)
        right_scroll_frame.grid_rowconfigure(6, weight=1) # Agar bisa memuai
        self.message_log = ctk.CTkTextbox(message_frame, font=("Arial", 14), state="disabled", wrap="word")
        self.message_log.grid(row=0, column=0, sticky="nsew")

    def log_message(self, message):
        """Menambahkan pesan baru ke area log yang bisa di-scroll."""
        if not message: return # Jangan log pesan kosong
        self.message_log.configure(state="normal")
        self.message_log.insert("end", f"- {message}\n\n") # Tambah spasi antar pesan
        self.message_log.see("end") # Auto-scroll ke bawah
        self.message_log.configure(state="disabled")

    def handle_input(self, input_symbol):
        if self.vm_dfa.current_state == 'DispensingItem': return
        if input_symbol in self.vm_dfa.menu_prices and self.vm_dfa.stock.get(input_symbol, 0) > 0: self.play_sound()
        
        output = self.vm_dfa.delta(input_symbol)
        self.log_message(output)
        
        if self.vm_dfa.current_state == 'DispensingItem':
            self.show_animation()
        else:
            self.update_gui()

    def update_gui(self):
        self.price_label.configure(text=f"Rp {self.vm_dfa.total_price:,}")
        self.inserted_money_label.configure(text=f"Rp {self.vm_dfa.money_inserted:,}")

        self.order_list_textbox.configure(state="normal")
        self.order_list_textbox.delete("0.0", "end")
        self.order_list_textbox.insert("0.0", "\n".join(f"- {item}" for item in self.vm_dfa.selected_items) if self.vm_dfa.selected_items else "Belum ada pesanan...")
        self.order_list_textbox.configure(state="disabled")

        state = self.vm_dfa.current_state
        for name, button in self.product_buttons.items():
            button.configure(state="normal" if state in ['Idle', 'WaitingForSelection'] and self.vm_dfa.stock.get(name, 0) > 0 else "disabled")
        for button in self.money_buttons.values():
            button.configure(state="normal" if state == 'WaitingForPayment' else "disabled")

        self.checkout_button.configure(state="normal" if self.vm_dfa.selected_items and state == 'WaitingForSelection' else "disabled")
        self.cancel_button.configure(state="normal" if state != 'Idle' and state not in ['DispensingItem', 'TransactionComplete'] else "disabled")
        # PERBAIKAN 2: Pastikan tombol ini aktif meskipun kembaliannya 0
        self.take_change_button.configure(state="normal" if state == 'TransactionComplete' else "disabled")

    def play_sound(self):
        if hasattr(self, 'notification_sound'): Thread(target=lambda: self.notification_sound.play(), daemon=True).start()

    def show_animation(self):
        self.update_gui() # Nonaktifkan tombol
        self.log_message("Pesanan sedang diproses...")
        self.dispenser_label.configure(text="")
        self.animate_gif(0)

    def animate_gif(self, frame_index):
        if self.animation_job: self.after_cancel(self.animation_job)
        if self.vm_dfa.current_state != 'DispensingItem':
            self.finish_transaction()
            return
            
        frame = self.animation_frames[frame_index]
        self.dispenser_label.configure(image=frame)
        next_frame_index = (frame_index + 1) % len(self.animation_frames)
        
        self.animation_job = self.after(100, self.animate_gif, next_frame_index)

    def finish_transaction(self):
        if self.animation_job: self.after_cancel(self.animation_job)
        self.animation_job = None
        self.dispenser_label.configure(image=None, text="PESANAN SIAP!")
        
        output = self.vm_dfa.delta(None)
        
        self.log_message(output)
        self.show_change()
        self.update_gui() # Update terakhir untuk mengaktifkan tombol "Ambil Kembalian"

    def show_change(self):
        for widget in self.change_frame.winfo_children(): widget.destroy()
        amount = self.vm_dfa.change_to_return
        # Tidak perlu `if amount <= 0` karena kita ingin tombol "Selesai" tetap muncul

        denominations = sorted([k for k in self.money_images.keys()], reverse=True)
        change_images_to_display = []
        temp_amount = amount
        for d in denominations:
            while temp_amount >= d:
                change_images_to_display.append(self.money_images[d])
                temp_amount -= d

        # PERBAIKAN 4 & 5: Logika "flex-wrap" untuk kembalian
        self.change_frame.update_idletasks() # Pastikan frame punya ukuran yang benar
        container_width = self.change_frame.winfo_width()
        if container_width < 100: container_width = 280 # Fallback
        x_pos, y_pos = 5, 5
        for img in change_images_to_display:
            img_width, img_height = img.cget("size")
            if x_pos + img_width + 5 > container_width and x_pos > 5:
                x_pos = 5
                y_pos += img_height + 5
            
            label = ctk.CTkLabel(self.change_frame, image=img, text="")
            label.place(x=x_pos, y=y_pos)
            x_pos += img_width + 5

    def take_change(self):
        self.vm_dfa.reset()
        for widget in self.change_frame.winfo_children(): widget.destroy()
        self.dispenser_label.configure(image=None, text="[Area Dispenser]")
        self.log_message("Terima kasih! Silakan pilih item baru.")
        self.update_gui()

if __name__ == "__main__":
    app = VendingMachineApp()
    def on_closing():
        if app.animation_job:
            app.after_cancel(app.animation_job)
        app.destroy()
    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()

