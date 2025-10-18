class VendingMachineDFA:
    def __init__(self):
        self.states = {
            'Idle', 'WaitingForSelection', 'WaitingForPayment',
            'DispensingItem', 'ReturningChange', 'TransactionComplete'
        }
        self.alphabet = {
            'VanillaScoop', 'ChocolateScoop', 'CaramelTopping', 'SprinklesTopping',
            'Checkout', 'Cancel',
            2000, 5000, 10000, 20000
        }
        self.menu_prices = {
            'VanillaScoop': 10000,
            'ChocolateScoop': 10000,
            'CaramelTopping': 2000,
            'SprinklesTopping': 2000
        }
        self.stock = {
            'VanillaScoop': 10,
            'ChocolateScoop': 10,
            'CaramelTopping': 10,
            'SprinklesTopping': 10
        }
        self.current_state = 'Idle'
        self.selected_items = []
        self.total_price = 0
        self.money_inserted = 0
        self.change_to_return = 0

    def reset(self):
        """Mengembalikan mesin ke state awal untuk transaksi baru."""
        self.current_state = 'Idle'
        self.selected_items = []
        self.total_price = 0
        self.money_inserted = 0
        self.change_to_return = 0
        print("\n--- Mesin Di-reset ---")

    def delta(self, input_symbol):
        state = self.current_state
        output = ""

        if state in ['Idle', 'WaitingForSelection']:
            if input_symbol in self.menu_prices:
                if self.stock.get(input_symbol, 0) > 0:
                    self.selected_items.append(input_symbol)
                    self.total_price += self.menu_prices[input_symbol]
                    self.current_state = 'WaitingForSelection'
                    output = f"'{input_symbol}' ditambahkan. Total: Rp {self.total_price}."
                else:
                    output = f"Maaf, '{input_symbol}' sudah habis."
            elif input_symbol == 'Checkout' and self.selected_items:
                self.current_state = 'WaitingForPayment'
                output = f"Pesanan dikonfirmasi. Total: Rp {self.total_price}. Silakan masukkan uang."
            elif input_symbol == 'Cancel':
                output = "Pesanan dibatalkan."
                self.reset()
            # ... (logika lainnya tetap sama) ...

        elif state == 'WaitingForPayment':
            if isinstance(input_symbol, int) and input_symbol in self.alphabet:
                self.money_inserted += input_symbol
                output = f"Uang Rp {input_symbol} diterima. Total dimasukkan: Rp {self.money_inserted}."
                if self.money_inserted >= self.total_price:
                    self.current_state = 'DispensingItem'
                    output = "Pembayaran cukup. Memproses pesanan..."
                else:
                    needed = self.total_price - self.money_inserted
                    output += f" Masih kurang Rp {needed}."
            elif input_symbol == 'Cancel':
                self.change_to_return = self.money_inserted
                self.current_state = 'TransactionComplete'
                output = f"Pembayaran dibatalkan. Ambil uang Anda: Rp {self.change_to_return}."

        # Transisi internal tidak lagi memanggil reset secara otomatis
        if state == 'DispensingItem':
            for item in self.selected_items:
                if item in self.stock: self.stock[item] -= 1

            self.change_to_return = self.money_inserted - self.total_price
            self.current_state = 'TransactionComplete'
            items_str = ", ".join(self.selected_items)
            output = f"Mengeluarkan [{items_str}].\n"
            if self.change_to_return > 0:
                output += f"Silakan ambil kembalian Anda: Rp {self.change_to_return}."
            else:
                output += "Tidak ada kembalian."

        return output
