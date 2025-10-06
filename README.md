# Custom Arch Linux ISO

A customized Arch Linux live ISO with an automated installer that sets up a complete GNOME desktop environment tailored for development and creative work.

## Overview

This project creates a bootable Arch Linux ISO (`archlinux-baseline`) with:
- GNOME desktop environment with custom configurations
- Comprehensive development tools (Rust, Python, Java IDEs)
- Creative applications (Blender, GIMP, KiCad, OBS Studio)
- Gaming support (Steam, Mangohud)
- AMD GPU drivers pre-configured
- Automated installation script

## Prerequisites

To build this ISO, you need:
- An Arch Linux system (or Arch-based distribution)
- `archiso` package installed: `sudo pacman -S archiso`
- `just` command runner (optional, for using Justfile): `sudo pacman -S just`
- Sufficient disk space (~10GB for build artifacts)
- Root/sudo privileges

## Building the ISO

### Method 1: Using the build script

```bash
./build.sh
```

This will:
1. Remove previous `work` and `out` directories
2. Build the ISO using `mkarchiso`
3. Output the ISO to the `out/` directory

### Method 2: Using Just

```bash
just build
```

This uses the Justfile to build with a different work directory (`../work`).

### Build Output

After building, you'll find the ISO file in the `out/` directory:
```
out/archlinux-baseline-YYYY.MM.DD-x86_64.iso
```

## Installing from the ISO

1. **Boot from the ISO** - Boot the generated ISO on your target machine (requires UEFI boot mode)

2. **Run the installer** - Once booted, run the automated installer as root:
   ```bash
   sudo /root/install-me.py
   ```

3. **Disk Selection** - The installer will automatically detect and select the best disk:
   - Priority: NVMe > SSD > Largest disk
   - **WARNING**: The installer will WIPE the selected disk completely

4. **Confirmation** - Confirm the installation when prompted

5. **Reboot** - After installation completes, reboot into your new system

## What the Installer Configures

### Partitioning Scheme

- **ESP (EFI System Partition)**: 1024 MiB, FAT32, mounted at `/boot`
- **Root Partition**: Remaining disk space, ext4, mounted at `/`

### System Configuration

- **Hostname**: `arch-lukas`
- **Bootloader**: systemd-boot (UEFI only)
- **Locale**: German (`de_DE.UTF-8`) with English fallback (`en_US.UTF-8`)
- **Kernel**: Linux kernel
- **Init System**: systemd
- **Display Server**: Xorg
- **Desktop Environment**: GNOME with GDM display manager

### User Accounts

| User | Password | Privileges |
|------|----------|------------|
| `lukas` | `lukas` | Administrator (sudo) |
| `root` | `root` | Root access |

**⚠️ SECURITY NOTE**: Change these default passwords immediately after installation!

### Installed Packages

#### Desktop Environment
- **GNOME**: Full GNOME desktop with most default applications
- **GDM**: GNOME Display Manager
- **Extensions**: Vitals, Tiling Assistant, Browser Connector

#### Development Tools
- **Languages & Runtimes**: Rust (rustup), Python, Git
- **IDEs**: RustRover, IntelliJ IDEA Ultimate, PyCharm Professional, Zed
- **Build Tools**: Just, archiso

#### Creative Applications
- **3D Modeling**: Blender, OpenSCAD
- **2D Graphics**: GIMP
- **Video**: OBS Studio, VLC
- **CAD/Electronics**: KiCad, Prusa Slicer
- **3D Printing**: UVTools

#### Gaming
- **Platforms**: Steam (with 32-bit library support)
- **Performance**: MangoHud (with 32-bit support)
- **GPU**: AMD Radeon drivers (Mesa, Vulkan)

#### Communication
- Discord

#### System Utilities
- **Package Management**: Multilib repository enabled
- **Network**: NetworkManager
- **Audio**: PipeWire with WirePlumber
- **File System**: gvfs (with SMB, NFS, MTP support)
- **Virtualization**: GNOME Boxes
- **Monitoring**: htop, Resources
- **Archive Manager**: Included with GNOME
- **Text Editors**: nano, GNOME Text Editor

### Automated Customizations

The installer automatically configures:

#### Git Configuration (for user `lukas`)
- User name: Lukas Heiligenbrunner
- Email: lukas.heiligenbrunner@gmail.com

#### Rust Setup
- Default toolchain: stable

#### GNOME Settings
- **Theme**: Dark mode enabled
- **Desktop Background**: Custom Hogwarts Legacy background
- **Clock**: Show seconds in top bar
- **Power Management**: Automatic suspend disabled
- **Keybindings**: Screenshot UI on Ctrl+F12
- **Favorite Apps**: Firefox, Console, Nautilus, Steam, Resources
- **Experimental Features**: Variable refresh rate, Scale monitor framebuffer

#### Nautilus (File Manager)
- Default view: List view (small, tree view enabled)
- Show "Create Link" option
- Show "Delete Permanently" option

#### GNOME Extensions
- **Tiling Assistant**: Auto-enabled (popup and tile groups disabled)
- **Vitals**: Auto-enabled for system monitoring
- **Launch New Instance**: Auto-enabled

#### Enabled Services
- NetworkManager (for network connectivity)
- GDM (for graphical login)

### Custom Repository

The system is configured with a custom package repository:
- URL: `https://repo.heili.eu/$arch`
- Contains additional packages not in official Arch repos

## Boot Process

The ISO boots with:
- **Boot Mode**: UEFI with systemd-boot
- **Boot Timeout**: 15 seconds
- **Architecture**: x86_64 only

## File Structure

```
.
├── airootfs/              # Files copied to the live ISO root filesystem
│   └── root/
│       ├── install-me.py  # Automated installer script
│       └── rsc/           # Resources (backgrounds, etc.)
├── build.sh               # Build script
├── Justfile               # Just build recipe
├── profiledef.sh          # ISO profile definition
├── packages.x86_64        # Packages included in live ISO
├── pacman.conf            # Pacman configuration for building
├── bootstrap_packages.x86_64  # Bootstrap packages
├── efiboot/               # UEFI boot configuration
├── grub/                  # GRUB configuration (if used)
└── syslinux/              # Syslinux configuration
```

## Post-Installation Steps

After installation, you should:

1. **Change default passwords**:
   ```bash
   passwd          # Change root password
   passwd lukas    # Change user password
   ```

2. **Update the system**:
   ```bash
   sudo pacman -Syu
   ```

3. **Configure git** (if needed):
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

4. **Install additional software** as needed:
   ```bash
   sudo pacman -S <package-name>
   ```

## Customization

To customize this ISO for your needs:

1. **Modify packages**: Edit `packages.x86_64` for live ISO packages, or modify the `packages` property in `airootfs/root/install-me.py` for installed system packages

2. **Change installer behavior**: Edit `airootfs/root/install-me.py` to modify:
   - User credentials
   - Hostname
   - Partitioning scheme
   - Desktop settings
   - Installed packages

3. **Update profile settings**: Edit `profiledef.sh` to change:
   - ISO name and label
   - Publisher information
   - Boot modes

4. **Rebuild**: After making changes, rebuild with `./build.sh` or `just build`

## Notes

- The installer is **destructive** and will wipe the selected disk
- BIOS/Legacy boot is not supported (UEFI only)
- The system is optimized for AMD Radeon GPUs (but should work with other GPUs)
- Some packages (RustRover, IntelliJ IDEA Ultimate, PyCharm Professional) require licenses

## License

This is a custom Arch Linux configuration. Arch Linux itself is under various open source licenses. Check individual package licenses for details.

## Credits

- Built on [Arch Linux](https://archlinux.org)
- Uses [archiso](https://gitlab.archlinux.org/archlinux/archiso) for ISO creation
- Uses [archinstall](https://github.com/archlinux/archinstall) library for installation
