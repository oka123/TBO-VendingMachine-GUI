# -*- coding: utf-8 -*-

class VendingMachineDFA:
    """
    Implementasi Vending Machine Es Krim sebagai Mealy Machine (DFA).
    Output dihasilkan selama transisi.
    """
    def __init__(self):
        # Daftar state yang mungkin
        self.states = {
            'Idle', 'WaitingForSelection', 'WaitingForPayment', 
            'DispensingItem', 'ReturningChange'
        }
        
        # Daftar input (alfabet) yang diterima
        self.alphabet = {
            'VanillaScoop', 'ChocolateScoop', 'CaramelTopping', 'SprinklesTopping',
            'Checkout', 'Cancel',
            2000, 5000, 10000, 20000
        }
        
        # Menu dan harga
        self.menu_prices = {
            'VanillaScoop': 10000,
            'ChocolateScoop': 10000,
            'CaramelTopping': 2000,
            'SprinklesTopping': 2000
        }
        
        # Inisialisasi kondisi awal mesin
        self.reset()

    def reset(self):
        """Mengembalikan mesin ke state awal untuk transaksi baru."""
        self.current_state = 'Idle'
        self.selected_items = []
        self.total_price = 0
        self.money_inserted = 0
        print("\n=============================================")
        print("🍦 Mesin Es Krim Siap! Silakan pilih item. 🍦")
        print("=============================================")

    def delta(self, input_symbol):
        """
        Fungsi Transisi (δ). Menentukan state berikutnya dan output
        berdasarkan state saat ini dan input.
        """
        state = self.current_state
        output = ""

        # Logika untuk State 'Idle' atau 'WaitingForSelection'
        if state in ['Idle', 'WaitingForSelection']:
            if input_symbol in self.menu_prices:
                self.selected_items.append(input_symbol)
                self.total_price += self.menu_prices[input_symbol]
                self.current_state = 'WaitingForSelection'
                output = f"Item '{input_symbol}' ditambahkan. Total harga: Rp {self.total_price}."
            elif input_symbol == 'Checkout' and self.selected_items:
                self.current_state = 'WaitingForPayment'
                output = f"Pesanan dikonfirmasi. Total: Rp {self.total_price}. Silakan masukkan uang."
            elif input_symbol == 'Cancel':
                output = "Pesanan dibatalkan."
                self.reset()
            elif input_symbol not in self.alphabet:
                 output = f"Input '{input_symbol}' tidak dikenali. Silakan coba lagi."
            else:
                output = "Input tidak valid pada state ini. Pilih item terlebih dahulu."

        # Logika untuk State 'WaitingForPayment'
        elif state == 'WaitingForPayment':
            if isinstance(input_symbol, int) and input_symbol in self.alphabet:
                self.money_inserted += input_symbol
                output = f"Uang Rp {input_symbol} diterima. Total dimasukkan: Rp {self.money_inserted}."
                
                if self.money_inserted >= self.total_price:
                    self.current_state = 'DispensingItem'
                    output += "\nPembayaran cukup. Memproses pesanan..."
                    output += "\n" + self.trigger_internal_transition('__dispense__') 
                else:
                    needed = self.total_price - self.money_inserted
                    output += f" Masih kurang Rp {needed}."
            elif input_symbol == 'Cancel':
                self.current_state = 'ReturningChange'
                output = "Pembayaran dibatalkan."
                output += "\n" + self.trigger_internal_transition('__return_money__')
            else:
                output = "Input tidak valid. Silakan masukkan uang (angka) atau 'Cancel'."

        return output

    def trigger_internal_transition(self, internal_symbol):
        """Fungsi untuk memicu transisi otomatis (dispensing, returning change)."""
        output = ""
        if internal_symbol == '__dispense__':
            items_str = ", ".join(self.selected_items)
            output = f"Mengeluarkan item: [{items_str}]."
            self.current_state = 'ReturningChange'
            output += "\n" + self.trigger_internal_transition('__return_money__') 
        
        elif internal_symbol == '__return_money__':
            change = self.money_inserted - self.total_price
            if change < 0: # Terjadi saat 'Cancel'
                change = self.money_inserted
            
            if change > 0:
                output = f"Silakan ambil kembalian Anda: Rp {change}."
            else:
                output = "Tidak ada kembalian."
            
            # Selesai, reset mesin
            self.reset()

        return output

# --- Simulasi INTERAKTIF DFA ---
if __name__ == "__main__":
    vm_dfa = VendingMachineDFA()
    
    print("\n--- Pilihan Input yang Tersedia ---")
    print("Item: VanillaScoop, ChocolateScoop, CaramelTopping, SprinklesTopping")
    print("Uang: 2000, 5000, 10000, 20000")
    print("Perintah: Checkout, Cancel, exit")
    print("------------------------------------")

    while True:
        # Menampilkan state saat ini sebelum meminta input
        prompt = f"\n[{vm_dfa.current_state}] Masukkan input: "
        user_input = input(prompt)

        if user_input.lower() in ['exit', 'keluar']:
            print("Terima kasih! Mesin berhenti.")
            break

        # Konversi input angka menjadi integer
        processed_input = user_input
        try:
            processed_input = int(user_input)
        except ValueError:
            pass # Biarkan sebagai string jika tidak bisa diubah jadi angka

        output = vm_dfa.delta(processed_input)
        print(f"==> OUTPUT: {output}")
