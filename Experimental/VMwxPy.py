import wx
import wx.lib.scrolledpanel as scrolled

# ==============================================================================
# BAGIAN 1: LOGIKA INTI (DFA VENDING MACHINE)
# Diadaptasi untuk integrasi dengan GUI
# ==============================================================================
class VendingMachineLogic:
    """
    Implementasi logika Vending Machine sebagai DFA.
    Kelas ini terpisah dari GUI dan berkomunikasi melalui callback.
    """
    def __init__(self, gui_callback):
        self.gui_callback = gui_callback
        self.menu_prices = {
            'VanillaScoop': 10000, 'ChocolateScoop': 10000,
            'CaramelTopping': 2000, 'SprinklesTopping': 2000
        }
        self.stock = {item: 10 for item in self.menu_prices}
        self.reset_transaction()

    def reset_transaction(self):
        """Mengembalikan mesin ke state awal untuk transaksi baru."""
        self.current_state = 'Idle'
        self.selected_items = []
        self.total_price = 0
        self.money_inserted = 0
        return "Mesin Siap! Silakan pilih item."

    def delta(self, input_symbol):
        """Fungsi Transisi (δ)."""
        state = self.current_state

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
        if internal_symbol == '__dispense__':
            for item in self.selected_items:
                self.stock[item] -= 1
            self.gui_callback('dispense_animation', self.selected_items)

    def finalize_transaction(self):
        self.current_state = 'ReturningChange'
        change = self.money_inserted - self.total_price
        msg = self.reset_transaction()
        if change > 0:
            self.gui_callback('reset', f"Transaksi Selesai! Kembalian Anda Rp {change}.")
            self.gui_callback('return_change', change)
        else:
            self.gui_callback('reset', "Transaksi Selesai! Terima kasih.")

# ==============================================================================
# BAGIAN 2: GUI (ANTARMUKA PENGGUNA) DENGAN WXPYTHON
# ==============================================================================
class VendingMachineFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Vending Machine Es Krim Cerdas", size=(850, 750))
        self.SetBackgroundColour("#F0F8FF") # AliceBlue

        self.logic = VendingMachineLogic(self.gui_callback)
        self.product_widgets = {}
        self.animation_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_animation_timer, self.animation_timer)

        self.init_ui()
        self.Centre()
        self.Show()

    def init_ui(self):
        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # --- Top Banner ---
        banner_font = wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        banner_label = wx.StaticText(main_panel, label="🍦 Vending Machine Es Krim Cerdas 🍦")
        banner_label.SetFont(banner_font)
        banner_label.SetForegroundColour("#4682B4") # SteelBlue
        main_sizer.Add(banner_label, 0, wx.ALL | wx.CENTER, 20)

        # --- Main Content Sizer (Produk | Kontrol) ---
        content_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # --- Product Panel (Left) ---
        product_panel = self.create_product_panel(main_panel)
        content_sizer.Add(product_panel, 2, wx.EXPAND | wx.ALL, 10)

        # --- Control Panel (Right) ---
        control_panel = self.create_control_panel(main_panel)
        content_sizer.Add(control_panel, 1, wx.EXPAND | wx.ALL, 10)

        main_sizer.Add(content_sizer, 1, wx.EXPAND)
        
        # --- Dispenser Panel (Bottom) ---
        dispenser_panel_container = self.create_dispenser_panel(main_panel)
        main_sizer.Add(dispenser_panel_container, 0, wx.EXPAND | wx.ALL, 10)

        main_panel.SetSizerAndFit(main_sizer)
        self.Layout()
    
    def create_product_panel(self, parent):
        panel = wx.Panel(parent, style=wx.BORDER_RAISED)
        panel.SetBackgroundColour("#FFFFFF")
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title = wx.StaticText(panel, label="Pilih Es Krim Favoritmu!")
        title.SetFont(title_font)
        sizer.Add(title, 0, wx.ALL | wx.CENTER, 15)

        grid = wx.GridSizer(2, 2, 10, 10)
        items = self.logic.menu_prices.items()

        for name, price in items:
            item_panel = wx.Panel(panel, style=wx.BORDER_SIMPLE)
            item_panel.SetBackgroundColour("#F0F8FF")
            item_sizer = wx.BoxSizer(wx.VERTICAL)

            # Image
            try:
                img = wx.Image(f"images/{name}.png", wx.BITMAP_TYPE_PNG).Scale(100, 100, wx.IMAGE_QUALITY_HIGH)
                bmp = wx.StaticBitmap(item_panel, bitmap=wx.Bitmap(img))
                item_sizer.Add(bmp, 0, wx.ALL | wx.CENTER, 10)
            except Exception as e:
                print(f"Gagal memuat gambar {name}.png: {e}")

            # Info
            info_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            info_label = wx.StaticText(item_panel, label=f"{name}\nRp {price}")
            info_label.SetFont(info_font)
            info_label.SetForegroundColour("#2F4F4F")
            item_sizer.Add(info_label, 0, wx.CENTER | wx.BOTTOM, 5)

            # Stock
            stock_label = wx.StaticText(item_panel, label=f"Stok: {self.logic.stock[name]}")
            item_sizer.Add(stock_label, 0, wx.CENTER | wx.BOTTOM, 5)
            
            # Button
            btn = wx.Button(item_panel, label="Pilih")
            btn.Bind(wx.EVT_BUTTON, lambda evt, n=name: self.logic.delta(n))
            item_sizer.Add(btn, 0, wx.EXPAND | wx.ALL, 10)

            item_panel.SetSizer(item_sizer)
            grid.Add(item_panel, 1, wx.EXPAND)
            self.product_widgets[name] = {'button': btn, 'stock_label': stock_label}

        sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 10)
        panel.SetSizer(sizer)
        return panel

    def create_control_panel(self, parent):
        panel = wx.Panel(parent, style=wx.BORDER_RAISED)
        panel.SetBackgroundColour("#B0E0E6") # PowderBlue
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Title
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title = wx.StaticText(panel, label="Pembayaran")
        title.SetFont(title_font)
        sizer.Add(title, 0, wx.ALL | wx.CENTER, 15)

        # Status Display
        self.status_label = wx.StaticText(panel, label="Selamat Datang!", style=wx.ALIGN_CENTER)
        self.status_label.Wrap(250)
        sizer.Add(self.status_label, 0, wx.EXPAND | wx.ALL, 10)

        self.cart_label = wx.StaticText(panel, label="Keranjang: Kosong")
        sizer.Add(self.cart_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        money_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.total_price_label = wx.StaticText(panel, label="Total Harga: Rp 0")
        self.total_price_label.SetFont(money_font)
        sizer.Add(self.total_price_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        self.money_inserted_label = wx.StaticText(panel, label="Uang Masuk: Rp 0")
        self.money_inserted_label.SetFont(money_font)
        self.money_inserted_label.SetForegroundColour("green")
        sizer.Add(self.money_inserted_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 10)
        
        # Money Buttons
        money_grid = wx.GridSizer(2, 2, 5, 5)
        for value in [2000, 5000, 10000, 20000]:
            img = wx.Image(f"images/money_{value}.png", wx.BITMAP_TYPE_PNG).Scale(120, 60, wx.IMAGE_QUALITY_HIGH)
            btn = wx.BitmapButton(panel, bitmap=wx.Bitmap(img))
            btn.Bind(wx.EVT_BUTTON, lambda evt, v=value: self.logic.delta(v))
            money_grid.Add(btn, 1, wx.CENTER)
        sizer.Add(money_grid, 0, wx.EXPAND | wx.ALL, 10)
        
        # Action Buttons
        action_sizer = wx.BoxSizer(wx.HORIZONTAL)
        checkout_btn = wx.Button(panel, label="Checkout")
        checkout_btn.SetBackgroundColour("#3CB371")
        checkout_btn.SetForegroundColour("white")
        checkout_btn.Bind(wx.EVT_BUTTON, lambda evt: self.logic.delta('Checkout'))
        
        cancel_btn = wx.Button(panel, label="Cancel")
        cancel_btn.SetBackgroundColour("#DC143C")
        cancel_btn.SetForegroundColour("white")
        cancel_btn.Bind(wx.EVT_BUTTON, lambda evt: self.logic.delta('Cancel'))

        action_sizer.Add(checkout_btn, 1, wx.EXPAND | wx.ALL, 5)
        action_sizer.Add(cancel_btn, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(action_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        return panel

    def create_dispenser_panel(self, parent):
        panel = wx.Panel(parent, style=wx.BORDER_SUNKEN)
        panel.SetBackgroundColour("#ADD8E6")
        sizer = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label="Area Pengambilan")
        sizer.Add(title, 0, wx.TOP | wx.LEFT, 5)

        self.dispenser_panel = wx.Panel(panel, size=(-1, 100))
        self.dispenser_panel.SetBackgroundColour("#E0FFFF")
        sizer.Add(self.dispenser_panel, 1, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(sizer)
        return panel

    def gui_callback(self, action, data=None):
        if action == 'update_display':
            self.status_label.SetLabel(data)
            self.update_info_labels()
        elif action == 'reset':
            self.status_label.SetLabel(data)
            self.update_info_labels()
            self.dispenser_panel.DestroyChildren()
        elif action == 'dispense_animation':
            wx.CallAfter(self.animate_dispense)
        elif action == 'return_change':
            wx.CallAfter(self.display_change, data)

    def update_info_labels(self):
        self.cart_label.SetLabel(f"Keranjang: {', '.join(self.logic.selected_items) or 'Kosong'}")
        self.total_price_label.SetLabel(f"Total Harga: Rp {self.logic.total_price}")
        self.money_inserted_label.SetLabel(f"Uang Masuk: Rp {self.logic.money_inserted}")
        for name, widgets in self.product_widgets.items():
            stock = self.logic.stock[name]
            widgets['stock_label'].SetLabel(f"Stok: {stock}")
            widgets['button'].Enable(stock > 0)
        self.Layout()

    def animate_dispense(self):
        self.status_label.SetLabel("Membuat es krim Anda... Mohon tunggu!")
        self.toggle_ui_elements(False)

        img = wx.Image("images/ice_cream_cone.png", wx.BITMAP_TYPE_PNG).Scale(80, 80, wx.IMAGE_QUALITY_HIGH)
        self.animation_item = wx.StaticBitmap(self.dispenser_panel, bitmap=wx.Bitmap(img))
        self.animation_pos_y = -80
        self.animation_item.Move((self.dispenser_panel.GetSize().width // 2 - 40, self.animation_pos_y))
        
        self.animation_timer.Start(15)

    def on_animation_timer(self, event):
        target_y = (self.dispenser_panel.GetSize().height // 2) - 40
        if self.animation_pos_y < target_y:
            self.animation_pos_y += 5
            self.animation_item.Move((self.dispenser_panel.GetSize().width // 2 - 40, self.animation_pos_y))
        else:
            self.animation_timer.Stop()
            self.toggle_ui_elements(True)
            self.logic.finalize_transaction()

    def display_change(self, amount):
        self.dispenser_panel.DestroyChildren()
        denominations = [20000, 10000, 5000, 2000]
        x_pos = 10
        for value in denominations:
            while amount >= value:
                img = wx.Image(f"images/change_{value}.png", wx.BITMAP_TYPE_PNG).Scale(80, 40, wx.IMAGE_QUALITY_HIGH)
                wx.StaticBitmap(self.dispenser_panel, bitmap=wx.Bitmap(img), pos=(x_pos, 30))
                amount -= value
                x_pos += 90
        self.Layout()

    def toggle_ui_elements(self, enabled):
        for widgets in self.product_widgets.values():
            widgets['button'].Enable(enabled and self.logic.stock[widgets['button'].GetLabel()] > 0)
        # Tambahkan tombol lain yang perlu di-disable/enable di sini
        # Contoh: self.checkout_btn.Enable(enabled)

# ==============================================================================
# BAGIAN 3: MENJALANKAN APLIKASI
# ==============================================================================
if __name__ == "__main__":
    app = wx.App(False)
    frame = VendingMachineFrame()
    app.MainLoop()