![Platform](https://img.shields.io/badge/platform-Linux-blue)
![License](https://img.shields.io/badge/license-MIT-green)


OpenVPN Desk

OpenVPN Desk is a lightweight, GTK-based OpenVPN client for Linux, designed for users who want a simple, reliable GUI without relying on NetworkManager or OpenVPN 3.

It is built on OpenVPN 2.x, a dedicated systemd unit, and polkit, and works especially well on Ubuntu and Pop!_OS.

-----------------------------------------------------------------

✨ Features

    ✅ Simple GTK desktop interface

    ✅ Import .ovpn profiles via GUI

    ✅ Secure credential handling (root-only auth files)

    ✅ systemd-managed connections (openvpn-desk@profile)

    ✅ One VPN active at a time (safe by design)

    ✅ Live connection status

    ✅ Upload / download speed indicator

    ✅ No tray clutter (v1 focus on stability)

    ✅ No NetworkManager dependency

-----------------------------------------------------------------

🚫 What This Is Not

    ❌ Not based on NetworkManager

    ❌ Not using OpenVPN 3

    ❌ Not a tray-only app

    ❌ Not storing credentials in user space

    ❌ Not affiliated with OpenVPN Inc.

This project exists because many Linux users need a simple OpenVPN GUI that works reliably with standard .ovpn profiles.

------------------------------------------------------------------------

🖥️ Supported Platforms

Ubuntu 22.04+

Ubuntu 24.04+

Pop!_OS 22.04+

(Other systemd-based distributions may work but are not officially tested yet.)

------------------------------------------------------------------------

🧱 Technical Overview

| Component       | Choice            |
| --------------- | ----------------- |
| Language        | Python 3          |
| GUI             | GTK 3 (PyGObject) |
| VPN Backend     | OpenVPN 2.x       |
| Privileges      | polkit / pkexec   |
| Service Manager | dedicated systemd unit |
| Packaging       | `.deb` (v1)       |

------------------------------------------------------------------------

🔐 Security Model

OpenVPN Desk follows a strict privilege separation model:

The GUI runs as an unprivileged user

A small root-only helper handles:

Installing profiles

Creating auth files

Managing the openvpn-desk systemd service

Credentials and generated configs are stored in: ` /etc/openvpn-desk/profiles/ `

with root-only permissions

No passwords are cached or logged by the GUI

------------------------------------------------------------------------

🚀 Installation (v1)
Prerequisites
sudo apt install openvpn policykit-1 pkexec python3 python3-gi gir1.2-gtk-3.0

Install the .deb
sudo dpkg -i openvpn-desk_1.0.0_all.deb


If dependencies are missing:

sudo apt -f install

----------------------------------------

🧭 Usage

Launch OpenVPN Desk from the application menu

Click Import

Select a .ovpn file

Enter:

Profile alias (safe name)

VPN username

VPN password

Click Connect

Monitor status and traffic in real time

Only one VPN connection can be active at a time.

--------------------------------------------

📸 Screenshots

Screenshots coming soon.

--------------------------------------------

🗺️ Roadmap
v1.0 (Current)

Import .ovpn profiles

Connect / disconnect

Live status & speed

Clean GTK UI

v1.1

Auto-refresh status toggle

v2.0

Export / import bundled profiles

Optional tray icon

Additional distro support

--------------------------------------------

🤝 Contributing

Contributions are welcome!

Ideas:

UI improvements

Packaging enhancements

Distro testing

Documentation

Bug reports

Please open an issue or submit a pull request.

--------------------------------------------    

📄 License

MIT License


--------------------------------------------

⚠️ Disclaimer

OpenVPN Desk is an independent, community-driven project and is not affiliated with or endorsed by OpenVPN Inc.

OpenVPN is a registered trademark of OpenVPN Inc.

--------------------------------------------    

⭐ Why OpenVPN Desk?

Because Linux users deserve a simple, reliable OpenVPN GUI that:

Respects system security

Works with existing .ovpn files

Doesn’t fight the OS

Doesn’t hide behind tray icons

Just works
If you install from source instead of the package:

sudo ./helper/install.sh

No extra group membership or re-login is required; local active users are allowed by polkit.
