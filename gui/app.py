#!/usr/bin/env python3
import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk


from gui.backend import VpnBackend, VpnBackendError


class YangzLinuxVpnClient(Gtk.Window):

    def __init__(self):
        super().__init__(title="Yangz Linux VPN Client")
        # Force light theme (disable dark mode)
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property("gtk-application-prefer-dark-theme", False)
        
        self.get_style_context().add_class("openvpn-desk-window")

        self.load_css()
        self.set_border_width(12)
        self.set_default_size(420, 300)

        self.backend = VpnBackend()
        self.selected_profile = None
        self.active_profile = None


        self._build_ui()
        self.refresh_profiles()
        self.vpn_iface = None
        self.last_rx = None
        self.last_tx = None
        self.speed_timer_id = None



    # --------------------------------------------------
    # UI Construction
    # --------------------------------------------------

    def _build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(vbox)

        # Header bar
        header = Gtk.HeaderBar(title="OpenVPN Desk")
        header.set_show_close_button(True)
        self.set_titlebar(header)


        # Profile list
        # Columns: profile_name, status ("active"/"inactive")
        self.liststore = Gtk.ListStore(str, str)
        self.treeview = Gtk.TreeView(model=self.liststore)

        # renderer = Gtk.CellRendererText()
        # column = Gtk.TreeViewColumn("VPN Profiles", renderer, text=0)
        # self.treeview.append_column(column)

        # Status dot column
        status_renderer = Gtk.CellRendererText()
        status_column = Gtk.TreeViewColumn("#", status_renderer, text=0)
        status_column.set_cell_data_func(
            status_renderer, self.render_status_dot
        )
        status_column.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        self.treeview.append_column(status_column)
        status_column.set_fixed_width(32)
        status_column.set_expand(False)

        # Profile name column
        name_renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn("VPN Profiles", name_renderer, text=0)
        self.treeview.append_column(name_column)


        selection = self.treeview.get_selection()
        selection.connect("changed", self.on_profile_selected)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.add(self.treeview)

        vbox.pack_start(scrolled, True, True, 0)

        # Status label
        self.status_label = Gtk.Label(label="Status: Unknown")
        self.status_label.set_xalign(0)
        vbox.pack_start(self.status_label, False, False, 0)

        # Speed label
        self.speed_label = Gtk.Label(label="")
        self.speed_label.set_xalign(0)
        self.speed_label.set_visible(False)
        vbox.pack_start(self.speed_label, False, False, 0)

        # label Styles
        self.status_label.get_style_context().add_class("status-label")
        self.speed_label.get_style_context().add_class("speed-label")

        # Buttons row
        button_box = Gtk.Box(spacing=6)

        self.import_btn = self.create_icon_button(
            "document-open-symbolic", " Import"
        )

        self.connect_btn = self.create_icon_button(
            "network-vpn-symbolic", " Connect"
        )

        self.disconnect_btn = self.create_icon_button(
            "network-offline-symbolic", " Disconnect"
        )

        self.refresh_btn = self.create_icon_button(
            "view-refresh-symbolic", " Refresh"
        )   

        # Mark semantic button roles
        self.connect_btn.get_style_context().add_class("suggested-action")
        self.disconnect_btn.get_style_context().add_class("destructive-action")


        # button styles
        self.connect_btn.get_style_context().add_class("connect")
        self.disconnect_btn.get_style_context().add_class("disconnect")

        self.import_btn.connect("clicked", self.on_import_clicked)
        self.connect_btn.connect("clicked", self.on_connect_clicked)
        self.disconnect_btn.connect("clicked", self.on_disconnect_clicked)
        self.refresh_btn.connect("clicked", self.on_refresh_clicked)


        button_box.pack_start(self.import_btn, True, True, 0)
        button_box.pack_start(self.connect_btn, True, True, 0)
        button_box.pack_start(self.disconnect_btn, True, True, 0)
        button_box.pack_start(self.refresh_btn, True, True, 0)


        vbox.pack_start(button_box, False, False, 0)

        self._update_buttons()

    # --------------------------------------------------
    # UI Helpers
    # --------------------------------------------------

    def load_css(self):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(
            os.path.join(os.path.dirname(__file__), "style.css")
        )

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
    
    def create_icon_button(self, icon_name, label):
            btn = Gtk.Button(label=label)
            image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            btn.set_image(image)
            btn.set_always_show_image(True)
            return btn

    def detect_vpn_interface(self):
        for iface in os.listdir("/sys/class/net"):
            if iface.startswith("tun") or iface.startswith("tap"):
                return iface
        return None

    def render_status_dot(self, column, cell, model, iter, data=None):
        status = model.get_value(iter, 1)
        if status == "active":
            cell.set_property(
                "markup",
                "<span foreground='#16a34a' size='large'>●</span>"
            )
        else:
            cell.set_property(
                "markup",
                "<span foreground='#9ca3af' size='large'>●</span>"
            )

    def _update_buttons(self):
        if not self.selected_profile:
            self.connect_btn.set_sensitive(False)
            self.disconnect_btn.set_sensitive(False)
            return

        try:
            status = self.backend.get_status(self.selected_profile)
        except VpnBackendError:
            self.connect_btn.set_sensitive(False)
            self.disconnect_btn.set_sensitive(False)
            return

        if status.get("active"):
            self.connect_btn.set_sensitive(False)
            self.disconnect_btn.set_sensitive(True)
            self.status_label.set_text("Status: Connected to " + self.selected_profile)
        else:
            self.connect_btn.set_sensitive(True) 
            self.disconnect_btn.set_sensitive(False)
            self.status_label.set_text("Status: Disconnected")

    def show_error(self, title: str, message: str):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def choose_ovpn_file(self):
        dialog = Gtk.FileChooserDialog(
            title="Select OpenVPN Profile",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        ovpn_filter = Gtk.FileFilter()
        ovpn_filter.set_name("OpenVPN Profiles (*.ovpn)")
        ovpn_filter.add_pattern("*.ovpn")
        dialog.add_filter(ovpn_filter)

        response = dialog.run()
        filename = dialog.get_filename() if response == Gtk.ResponseType.OK else None
        dialog.destroy()

        return filename
    
    def prompt_credentials(self):
        dialog = Gtk.Dialog(
            title="VPN Profile Details",
            parent=self,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        content = dialog.get_content_area()
        grid = Gtk.Grid(column_spacing=10, row_spacing=10, margin=10)
        content.add(grid)

        alias_label = Gtk.Label(label="Profile Alias:")
        user_label = Gtk.Label(label="Username:")
        pass_label = Gtk.Label(label="Password:")

        alias_entry = Gtk.Entry()
        user_entry = Gtk.Entry()
        pass_entry = Gtk.Entry()
        pass_entry.set_visibility(False)

        alias_hint = Gtk.Label(
            label="Allowed: letters, numbers, - and _",
            xalign=0
        )
        alias_hint.get_style_context().add_class("dim-label")

        grid.attach(alias_label, 0, 0, 1, 1)
        grid.attach(alias_entry, 1, 0, 1, 1)
        grid.attach(alias_hint, 1, 1, 1, 1)

        grid.attach(user_label, 0, 2, 1, 1)
        grid.attach(user_entry, 1, 2, 1, 1)

        grid.attach(pass_label, 0, 3, 1, 1)
        grid.attach(pass_entry, 1, 3, 1, 1)

        dialog.show_all()
        response = dialog.run()

        alias = alias_entry.get_text().strip()
        username = user_entry.get_text().strip()
        password = pass_entry.get_text()

        dialog.destroy()

        if response != Gtk.ResponseType.OK:
            return None, None, None

        if not alias or not username or not password:
            self.show_error(
                "Invalid Input",
                "Profile alias, username and password are required."
            )
            return None, None, None

        # Client-side alias validation
        for ch in alias:
            if not (ch.isalnum() or ch in "-_"):
                self.show_error(
                    "Invalid Profile Alias",
                    "Alias may contain only letters, numbers, '-' and '_'."
                )
                return None, None, None

        return alias, username, password


    def on_import_clicked(self, button):
        ovpn_path = self.choose_ovpn_file()
        if not ovpn_path:
            return

        try:
            with open(ovpn_path, "r", encoding="utf-8") as f:
                ovpn_content = f.read()
        except Exception as e:
            self.show_error("Error", f"Failed to read profile: {e}")
            return

        alias, username, password = self.prompt_credentials()
        if not alias:
            return

        try:
            self.backend.install_profile(
                profile_name=alias,
                ovpn_content=ovpn_content,
                username=username,
                password=password
            )
            self.refresh_profiles()
        except VpnBackendError as e:
            self.show_error("Import Failed", e.message)
    
    def read_iface_bytes(self, iface):
        try:
            with open(f"/sys/class/net/{iface}/statistics/rx_bytes") as f:
                rx = int(f.read())
            with open(f"/sys/class/net/{iface}/statistics/tx_bytes") as f:
                tx = int(f.read())
            return rx, tx
        except Exception:
            return None, None

    def update_speed(self):
        if not self.vpn_iface:
            return True  # keep timer alive

        rx, tx = self.read_iface_bytes(self.vpn_iface)
        if rx is None:
            return True

        if not self.vpn_iface:
            self.speed_label.set_text("Detecting VPN interface…")
            return True

        if self.last_rx is not None:
            rx_rate = (rx - self.last_rx) * 8 / 1_000_000
            tx_rate = (tx - self.last_tx) * 8 / 1_000_000

            self.speed_label.set_text(
                f"↓ {rx_rate:.2f} Mbps   ↑ {tx_rate:.2f} Mbps"
            )

        self.last_rx = rx
        self.last_tx = tx
        return True


    # --------------------------------------------------
    # Backend Actions
    # --------------------------------------------------

    def refresh_profiles(self):
        self.liststore.clear()
        self.selected_profile = None
        self.active_profile = None
        self.status_label.set_text("Status: Unknown")

        try:
            profiles = self.backend.list_profiles()
            for p in profiles:
                # Default to inactive
                self.liststore.append([p, "inactive"])
        except VpnBackendError as e:
            self.show_error("Error", e.message)

        self._update_buttons()


    def refresh_status(self):
        if not self.selected_profile:
            return

        try:
            status = self.backend.get_status(self.selected_profile)
            active = status.get("active", False)

            # Update label
            if active:
                self.active_profile = self.selected_profile
                self.status_label.set_text(
                    f"Status: Connected to {self.active_profile}"
                )
                GLib.timeout_add_seconds(1, self._detect_iface_delayed)
                self.last_rx = None
                self.last_tx = None
                self.speed_label.set_visible(True)
                if self.speed_timer_id is None:
                    self.speed_timer_id = GLib.timeout_add_seconds(1, self.update_speed)

            else:
                self.active_profile = None
                self.status_label.set_text(f"Status: Disconnected ({self.selected_profile})")

                self.vpn_iface = None
                self.speed_label.set_visible(False)
                if self.speed_timer_id is not None:
                    GLib.source_remove(self.speed_timer_id)
                    self.speed_timer_id = None


            # Update list dots
            for row in self.liststore:
                if row[0] == self.selected_profile and active:
                    row[1] = "active"
                else:
                    row[1] = "inactive"
            self.treeview.queue_draw()


        except VpnBackendError as e:
            self.show_error("Error", e.message)

    def _detect_iface_delayed(self):
        iface = self.detect_vpn_interface()
        if iface:
            self.vpn_iface = iface
            self.last_rx = None
            self.last_tx = None
            return False  # stop retrying
        return True  # retry again in 1 second

    # --------------------------------------------------
    # Signal Handlers
    # --------------------------------------------------

    def on_profile_selected(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter:
            self.selected_profile = model[treeiter][0]
            self.refresh_status()
            self._update_buttons()
        else:
            self.selected_profile = None
            self.status_label.set_text("Status: Unknown")

        self._update_buttons()

    def on_connect_clicked(self, button):
        if not self.selected_profile:
            return

        try:
            self.backend.connect(self.selected_profile)
            self.refresh_status()
            self._update_buttons()
        except VpnBackendError as e:
            self.show_error("Connection Failed", e.message)

    def on_disconnect_clicked(self, button):
        if not self.selected_profile:
            return

        try:
            self.backend.disconnect(self.selected_profile)
            self.refresh_profiles()
        except VpnBackendError as e:
            self.show_error("Disconnection Failed", e.message)

    def on_refresh_clicked(self, button):
        self.refresh_profiles()


# --------------------------------------------------
# Application Entry Point
# --------------------------------------------------

def main():
    win = YangzLinuxVpnClient()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
