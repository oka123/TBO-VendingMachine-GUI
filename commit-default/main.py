import customtkinter as ctk
from PIL import Image, ImageTk
from vending_machine_dfa2 import VendingMachineDFA
import simpleaudio as sa
from threading import Thread
from itertools import count

class App(ctk.CTk):
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
        self.update_gui("Selamat datang! Silakan pilih es krim.")

    def load_assets(self):
        try:
            self.product_images = {name: ctk.CTkImage(Image.open(f"assets/images/{name}.png"), size=(100, 80)) for name in self.vm_dfa.menu_prices}
            self.money_images = {val: ctk.CTkImage(Image.open(f"assets/images/{val}.png"), size=(120, 50)) for val in [2000, 5000, 10000, 20000]}
            self.notification_sound = sa.WaveObject.from_wave_file("assets/sounds/notification.wav")
            # Muat frame GIF untuk animasi
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
        # ... (Kode setup UI sama persis dengan versi final sebelumnya) ...
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left_frame = ctk.CTkFrame(self, fg_color="#2B2B2B")
        left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        products_frame = ctk.CTkFrame(left_frame)
        products_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        products_frame.grid_columnconfigure((0, 1), weight=1)

        self.product_buttons = {}
        for i, (name, price) in enumerate(self.vm_dfa.menu_prices.items()):
            image = self.product_images.get(name)
            button = ctk.CTkButton(products_frame, text=f"Rp {price}", image=image, compound="top", command=lambda p=name: self.handle_input(p))
            button.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="ew", ipady=10)
            self.product_buttons[name] = button

        self.dispenser_frame = ctk.CTkFrame(left_frame, height=150, fg_color="#1E1E1E")
        self.dispenser_frame.grid(row=1, column=0, padx=15, pady=100, sticky="nsew")
        self.dispenser_label = ctk.CTkLabel(self.dispenser_frame, text="[Area Dispenser]", font=("Arial", 16))
        self.dispenser_label.pack(expand=True)

        right_frame = ctk.CTkFrame(self, fg_color="#2B2B2B")
        right_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)

        order_frame = ctk.CTkFrame(right_frame)
        order_frame.grid(row=0, column=0, padx=15, pady=15, sticky="new")
        order_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(order_frame, text="List Pesanan", font=("Arial", 18, "bold")).grid(row=0, column=0, padx=10, pady=10)
        self.order_list_textbox = ctk.CTkTextbox(order_frame, height=120, font=("Arial", 14))
        self.order_list_textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        info_frame = ctk.CTkFrame(right_frame)
        info_frame.grid(row=1, column=0, padx=15, pady=(0,15), sticky="new")
        info_frame.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(info_frame, text="Total Harga:", font=("Arial", 16)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.price_label = ctk.CTkLabel(info_frame, text="Rp 0", font=("Arial", 16, "bold"))
        self.price_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        ctk.CTkLabel(info_frame, text="Uang Masuk:", font=("Arial", 16)).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.inserted_money_label = ctk.CTkLabel(info_frame, text="Rp 0", font=("Arial", 16, "bold"))
        self.inserted_money_label.grid(row=1, column=1, padx=10, pady=5, sticky="e")

        payment_frame = ctk.CTkFrame(right_frame)
        payment_frame.grid(row=2, column=0, padx=15, pady=(0,15), sticky="new")
        payment_frame.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(payment_frame, text="Masukkan Uang", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        self.money_buttons = {}
        for i, val in enumerate([2000, 5000, 10000, 20000]):
            image = self.money_images.get(val)
            button = ctk.CTkButton(payment_frame, text="", image=image, command=lambda v=val: self.handle_input(v))
            button.grid(row=(i//2)+1, column=i%2, padx=5, pady=5, sticky="ew")
            self.money_buttons[val] = button

        action_frame = ctk.CTkFrame(right_frame)
        action_frame.grid(row=3, column=0, padx=15, pady=(0,15), sticky="new")
        action_frame.grid_columnconfigure(0, weight=1)
        self.checkout_button = ctk.CTkButton(action_frame, text="Checkout", fg_color="green", command=lambda: self.handle_input('Checkout'))
        self.checkout_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.cancel_button = ctk.CTkButton(action_frame, text="Cancel", fg_color="red", command=lambda: self.handle_input('Cancel'))
        self.cancel_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.change_frame = ctk.CTkFrame(right_frame)
        self.change_frame.grid(row=4, column=0, padx=15, pady=(0,15), sticky="new")
        self.change_frame.grid_columnconfigure(0, weight=1)
        self.take_change_button = ctk.CTkButton(right_frame, text="Ambil Kembalian & Selesai", fg_color="blue", command=self.take_change)
        self.take_change_button.grid(row=5, column=0, padx=15, pady=0, sticky="ew")

        self.notification_label = ctk.CTkLabel(right_frame, text="", font=("Arial", 14), wraplength=280, justify="left")
        self.notification_label.grid(row=6, column=0, padx=15, pady=15, sticky="sew")
        right_frame.grid_rowconfigure(6, weight=1)


    def handle_input(self, input_symbol):
        if self.vm_dfa.current_state == 'DispensingItem': return
        if input_symbol in self.vm_dfa.menu_prices and self.vm_dfa.stock.get(input_symbol, 0) > 0: self.play_sound()
        output = self.vm_dfa.delta(input_symbol)
        if self.vm_dfa.current_state == 'DispensingItem': self.show_animation(output)
        else: self.update_gui(output)

    def update_gui(self, message):
        self.notification_label.configure(text=message)
        self.price_label.configure(text=f"Rp {self.vm_dfa.total_price}")
        self.inserted_money_label.configure(text=f"Rp {self.vm_dfa.money_inserted}")

        self.order_list_textbox.configure(state="normal")
        self.order_list_textbox.delete("0.0", "end")
        self.order_list_textbox.insert("0.0", "\n".join(f"- {item}" for item in self.vm_dfa.selected_items) if self.vm_dfa.selected_items else "Belum ada pesanan...")
        self.order_list_textbox.configure(state="disabled")

        state = self.vm_dfa.current_state
        is_interactive = state not in ['DispensingItem', 'TransactionComplete']

        for name, button in self.product_buttons.items():
            button.configure(state="normal" if state in ['Idle', 'WaitingForSelection'] and self.vm_dfa.stock.get(name, 0) > 0 else "disabled")
        for button in self.money_buttons.values():
            button.configure(state="normal" if state == 'WaitingForPayment' else "disabled")

        self.checkout_button.configure(state="normal" if self.vm_dfa.selected_items and state == 'WaitingForSelection' else "disabled")
        self.cancel_button.configure(state="normal" if is_interactive and state != 'Idle' else "disabled")
        self.take_change_button.configure(state="normal" if state == 'TransactionComplete' else "disabled")

    def play_sound(self):
        if self.notification_sound: Thread(target=lambda: self.notification_sound.play(), daemon=True).start()

    def show_animation(self, final_message):
        self.set_all_buttons_state("disabled")
        self.notification_label.configure(text="Pesanan sedang diproses...")
        self.dispenser_label.configure(text="") # Hapus teks, siapkan untuk gambar
        self.animate_gif(0, final_message)

    def animate_gif(self, frame_index, final_message):
        if self.animation_job: self.after_cancel(self.animation_job)
        if self.vm_dfa.current_state != 'DispensingItem': # Berhenti jika state berubah
             self.finish_transaction(final_message)
             return
        frame = self.animation_frames[frame_index]
        self.dispenser_label.configure(image=frame)
        next_frame_index = (frame_index + 1) % len(self.animation_frames)
        if next_frame_index == 0: # Selesaikan setelah satu putaran
            self.after(200, lambda: self.finish_transaction(final_message))
        else:
            self.animation_job = self.after(100, self.animate_gif, next_frame_index, final_message)

    def finish_transaction(self, final_message):
        if self.animation_job: self.after_cancel(self.animation_job)
        self.animation_job = None
        self.dispenser_label.configure(image=None, text="PESANAN SIAP!")
        output = self.vm_dfa.delta(None) # Pemicu transisi internal
        self.update_gui(output)
        self.show_change()

    def show_change(self):
        # Hapus gambar kembalian lama
        for widget in self.change_frame.winfo_children(): widget.destroy()

        amount = self.vm_dfa.change_to_return
        if amount <= 0: return

        denominations = sorted([k for k in self.money_images.keys()], reverse=True)
        change_images = []
        for d in denominations:
            while amount >= d:
                change_images.append(self.money_images[d])
                amount -= d

        # Tampilkan gambar kembalian baru
        for i, img in enumerate(change_images):
             label = ctk.CTkLabel(self.change_frame, image=img, text="")
             label.grid(row=i//2, column=i%2, padx=2, pady=2)

    def take_change(self):
        self.vm_dfa.reset()
        for widget in self.change_frame.winfo_children(): widget.destroy()
        self.dispenser_label.configure(image=None, text="[Area Dispenser]")
        self.update_gui("Terima kasih! Silakan pilih item baru.")

    def set_all_buttons_state(self, state):
        # ... (sama seperti sebelumnya) ...
        for button in self.product_buttons.values(): button.configure(state=state)
        for button in self.money_buttons.values(): button.configure(state=state)
        self.checkout_button.configure(state=state)
        self.cancel_button.configure(state=state)


if __name__ == "__main__":
    app = App()
    app.mainloop()
