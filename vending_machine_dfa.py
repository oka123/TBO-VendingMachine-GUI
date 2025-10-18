# vending_machine_dfa.py

class VendingMachineDFA:
    def __init__(self):
        self.states = {
            'Idle', 'IceCreamSelection', 'ToppingSelection', 'WaitingForPayment',
            'DispensingItem', 'ReturningChange'
        }
        self.item_types = {
            'Vanilla Scoop': 'scoop', 'Chocolate Scoop': 'scoop',
            'Caramel': 'topping', 'Sprinkles': 'topping'
        }
        self.menu_prices = {
            'Vanilla Scoop': 10000,
            'Chocolate Scoop': 10000,
            'Caramel': 2000,
            'Sprinkles': 2000
        }
        self.alphabet = set(self.menu_prices.keys()) | {'Next', 'Checkout', 'Cancel'} | {2000, 5000, 10000, 20000}
        
        self.reset()

    def reset(self):
        """Mengembalikan mesin ke kondisi awal untuk transaksi baru."""
        self.current_state = 'Idle'
        self.selected_items = []
        self.total_price = 0
        self.money_inserted = 0
        self.change_to_return = 0

    def delta(self, input_symbol):
        state = self.current_state
        output = ""

        # PERBAIKAN: Logika untuk state 'Idle'
        if state == 'Idle':
            if self.item_types.get(input_symbol) == 'scoop':
                self.selected_items.append(input_symbol)
                self.total_price += self.menu_prices[input_symbol]
                self.current_state = 'IceCreamSelection'
                output = f"'{input_symbol}' ditambahkan. Pilih scoop lagi atau tekan 'Next'."
            else:
                output = "Silakan pilih es krim terlebih dahulu."

        # PERBAIKAN: Logika untuk state 'IceCreamSelection'
        elif state == 'IceCreamSelection':
            if self.item_types.get(input_symbol) == 'scoop':
                self.selected_items.append(input_symbol)
                self.total_price += self.menu_prices[input_symbol]
                output = f"'{input_symbol}' ditambahkan. Total: Rp {self.total_price}."
            elif input_symbol == 'Next':
                self.current_state = 'ToppingSelection'
                output = "Pilih topping atau langsung 'Checkout'."
            elif input_symbol == 'Cancel':
                output = "Pesanan dibatalkan."
                self.reset()
            else:
                output = "Input tidak valid. Pilih scoop, 'Next', atau 'Cancel'."

        # PERBAIKAN: Logika untuk state 'ToppingSelection'
        elif state == 'ToppingSelection':
            if self.item_types.get(input_symbol) == 'topping':
                self.selected_items.append(input_symbol)
                self.total_price += self.menu_prices[input_symbol]
                output = f"'{input_symbol}' ditambahkan. Total: Rp {self.total_price}."
            elif input_symbol == 'Checkout':
                if not self.selected_items:
                    output = "Keranjang kosong. Pesanan dibatalkan."
                    self.reset()
                else:
                    self.current_state = 'WaitingForPayment'
                    output = f"Pesanan dikonfirmasi. Total: Rp {self.total_price}. Silakan masukkan uang."
            elif input_symbol == 'Cancel':
                output = "Pesanan dibatalkan."
                self.reset()
            else:
                output = "Input tidak valid. Pilih topping, 'Checkout', atau 'Cancel'."

        # PERBAIKAN: Logika untuk state 'WaitingForPayment'
        elif state == 'WaitingForPayment':
            if isinstance(input_symbol, int):
                self.money_inserted += input_symbol
                output = f"Uang Rp {input_symbol} diterima. Total dimasukkan: Rp {self.money_inserted}."
                if self.money_inserted >= self.total_price:
                    self.current_state = 'DispensingItem'
                    output += "\nPembayaran cukup. Memproses pesanan..."
                else:
                    needed = self.total_price - self.money_inserted
                    output += f" Masih kurang Rp {needed}."
            elif input_symbol == 'Cancel':
                self.change_to_return = self.money_inserted
                self.current_state = 'ReturningChange' # Langsung ke state pengembalian
                output = f"Pembayaran dibatalkan. Uang Anda sebesar Rp {self.change_to_return} dikembalikan."

        # PERBAIKAN: Logika untuk state 'DispensingItem' (transisi otomatis)
        if state == 'DispensingItem':
            self.change_to_return = self.money_inserted - self.total_price
            self.current_state = 'ReturningChange' # Langsung ke state pengembalian
            items_str = ", ".join(self.selected_items)
            output = f"Mengeluarkan [{items_str}].\n"
            if self.change_to_return > 0:
                output += f"Silakan ambil kembalian Anda: Rp {self.change_to_return}.\nTerima Kasih"
            else:
                output += "Tidak ada kembalian."
        
        return output