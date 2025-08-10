from pathlib import Path
from typing import override

from archinstall.default_profiles.desktops.gnome import GnomeProfile
from archinstall.default_profiles.profile import ProfileType, GreeterType
from archinstall.default_profiles.xorg import XorgProfile
from archinstall.lib.disk.device_handler import device_handler
from archinstall.lib.disk.filesystem import FilesystemHandler
from archinstall.lib.installer import Installer
from archinstall.lib.models import Repository, LocaleConfiguration, Bootloader, CustomRepository, MirrorConfiguration
from archinstall.lib.models.device_model import (
    DeviceModification,
    DiskLayoutConfiguration,
    DiskLayoutType,
    FilesystemType,
    ModificationStatus,
    PartitionFlag,
    PartitionModification,
    PartitionType,
    Size,
    Unit,
)
from archinstall.lib.models.mirrors import SignCheck, SignOption
from archinstall.lib.models.profile_model import ProfileConfiguration
from archinstall.lib.models.users import Password, User
from archinstall.lib.profile.profiles_handler import profile_handler

# we're creating a new ext4 filesystem installation
fs_type = FilesystemType('ext4')
device_path = Path('/dev/vda')

# get the physical disk device
device = device_handler.get_device(device_path)

if not device:
    raise ValueError('No device found for given path')

# create a new modification for the specific device
device_modification = DeviceModification(device, wipe=True)

start_boot = Size(1, Unit.MiB, device.device_info.sector_size)
length_boot = Size(1024, Unit.MiB, device.device_info.sector_size)
start_root = start_boot + length_boot
length_root = device.device_info.total_size - start_root - start_boot # todo -start_boot shouldnt be required actually

# create a new boot partition
boot_partition = PartitionModification(
    status=ModificationStatus.Create,
    type=PartitionType.Primary,
    start=start_boot,
    length=length_boot,
    mountpoint=Path('/boot'),
    fs_type=FilesystemType.Fat32,
    flags=[PartitionFlag.ESP],
    #flags=[PartitionFlag.BOOT], # for mbr
)

root_partition = PartitionModification(
    status=ModificationStatus.Create,
    type=PartitionType.Primary,
    start=start_root,
    length=length_root,
    mountpoint=Path('/'),
    fs_type=fs_type,
    mount_options=[],
)

device_modification.add_partition(boot_partition)
device_modification.add_partition(root_partition)

disk_config = DiskLayoutConfiguration(
    config_type=DiskLayoutType.Default,
    device_modifications=[device_modification],
)

# initiate file handler with the disk config and the optional disk encryption config
fs_handler = FilesystemHandler(disk_config)

# perform all file operations
# WARNING: this will potentially format the filesystem and delete all data
fs_handler.perform_filesystem_operations(show_countdown=False)

mountpoint = Path('/tmp')

custom_repo = CustomRepository(
    name='repo',
    url='https://repo.heili.eu/$arch',
    sign_check=SignCheck.Optional,
    sign_option=SignOption.TrustAll
)


class CustomProfile(XorgProfile):
    def __init__(self):
        super().__init__('GNOME', ProfileType.DesktopEnv)

    def install(self, install_session:'Installer') -> None:
        super().install(install_session)
        install_session.add_additional_packages(self.packages)

        self.post_install(install_session)

    def post_install(self, install_session:'Installer') -> None:
        super().post_install(install_session)
        installation.enable_service('NetworkManager.service')
        installation.enable_service('gdm.service')

        # set git name+email
        installation.arch_chroot(f'git config --global user.email "lukas.heiligenbrunner@gmail.com"','lukas')
        installation.arch_chroot(f'git config --global user.name "Lukas Heiligenbrunner"','lukas')
        # setup rust toolchain
        installation.arch_chroot(f'rustup default stable','lukas')

        local_background_path = Path('/root/rsc/background-hogwartslegacy.png')  # Adjust path
        chroot_background_path = Path(f"{installation.mountpoint}/home/lukas/Pictures/background.png")
        chroot_background_path.parent.mkdir(parents=True, exist_ok=True)
        chroot_background_path.write_bytes(local_background_path.read_bytes())
        installation.arch_chroot(f'chown -R lukas:lukas /home/lukas/Pictures', 'root')

        # prepare gsettings commands
        gsettings_cmds = [
            'gsettings set org.gnome.desktop.background picture-uri "file:///home/lukas/Pictures/background.jpg"',
            'gsettings set org.gnome.desktop.background picture-uri-dark "file:///home/lukas/Pictures/background.jpg"',
            'gsettings set org.gnome.desktop.interface color-scheme "prefer-dark"'

            # Screenshot UI: keep Print and add Ctrl+F12
            'gsettings set org.gnome.shell.keybindings show-screenshot-ui "[\'<Ctrl>F12\']"',

            # Enable extensions globally
            'gsettings set org.gnome.shell disable-user-extensions false',

            # Show seconds in top bar clock
            'gsettings set org.gnome.desktop.interface clock-show-seconds true',

            # Disable automatic suspend (on AC and battery)
            "gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'",
            "gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'",

            "gnome-extensions enable tiling-assistant@leleat-on-github",

            "gsettings set org.gnome.shell.extensions.tiling-assistant enable-tiling-popup false"
        ]

        for cmd in gsettings_cmds:
            installation.arch_chroot(f'dbus-launch --exit-with-session {cmd}', 'lukas')

    @property
    @override
    def packages(self) -> list[str]:
        return [
           'gnome-tweaks', self.default_greeter_type.value,

            # default gnome applications with some removed
            'baobab', # 	A graphical directory tree analyzer', #
            'decibels', # 	Audio player for GNOME', #
            'papers',
            'gdm', # 	Display manager and login screen', #
            'gnome-backgrounds', # 	Background images and data for GNOME', # 	
            'gnome-calculator', # 	GNOME Scientific calculator', #
            'gnome-calendar', # 	Simple and beautiful calendar application designed to perfectly fit the GNOME desktop', # 	
            'gnome-characters', # 	A character map application', # 	
            'gnome-clocks', # 	Clocks applications for GNOME', # 	
            'gnome-color-manager', # 	GNOME Color Profile Tools', # 	
            'gnome-connections', # 	Remote desktop client for the GNOME desktop environment', # 	
            'gnome-console', # 	A simple user-friendly terminal emulator for the GNOME desktop', # 	
            'gnome-contacts', # 	Contacts Manager for GNOME', #
            'gnome-control-center', # 	GNOME's main interface to configure various aspects of the desktop', # 	
            'gnome-disk-utility', # 	Disk Management Utility for GNOME', # 	
            'gnome-font-viewer', # 	A font viewer utility for GNOME', # 	
            'gnome-keyring', # 	Stores passwords and encryption keys', # 	
            'gnome-logs', # 	A log viewer for the systemd journal', #
            'gnome-maps', # 	Find places around the world', # 	
            'gnome-menus', # 	GNOME menu specifications', #
            'gnome-remote-desktop', # 	GNOME Remote Desktop server', # 	
            'gnome-session', # 	The GNOME Session Handler', #
            'gnome-settings-daemon', # 	GNOME Settings Daemon', #
            'gnome-shell', # 	Next generation desktop shell', #
            'gnome-shell-extensions', # 	Extensions for GNOME shell, including classic mode', #
            'gnome-text-editor', # 	A simple text editor for the GNOME desktop', #
            'gnome-user-docs', # 	User documentation for GNOME', # 	
            'gnome-user-share', # 	Easy to use user-level file sharing for GNOME', # 	
            'gnome-weather', # 	Access current weather conditions and forecasts', # 	
            'grilo-plugins', # 	A collection of plugins for the Grilo framework', # 	
            'gvfs', # 	Virtual filesystem implementation for GIO', # 	
            'gvfs-afc', # 	Virtual filesystem implementation for GIO - AFC backend (Apple mobile devices)', # 	
            'gvfs-dnssd', # 	Virtual filesystem implementation for GIO - DNS-SD and WebDAV backend (macOS file sharing)', # 	
            'gvfs-goa', # 	Virtual filesystem implementation for GIO - Gnome Online Accounts backend (e.g. OwnCloud)', #
            'gvfs-mtp', # 	Virtual filesystem implementation for GIO - MTP backend (Android, media player)', # 	
            'gvfs-nfs', # 	Virtual filesystem implementation for GIO - NFS backend', #
            'gvfs-smb', # 	Virtual filesystem implementation for GIO - SMB/CIFS backend (Windows file sharing)', # 	
            'gvfs-wsdd', # 	Virtual filesystem implementation for GIO - Web Services Dynamic Discovery backend (Windows discovery)', # 	
            'loupe', # 	A simple image viewer for GNOME', #
            'nautilus', # 	Default file manager for GNOME', #
            'orca', # 	Screen reader for individuals who are blind or visually impaired', # 	
            'rygel', # 	UPnP AV MediaServer and MediaRenderer', #
            'simple-scan', # 	Simple scanning utility', # 	
            'snapshot', # 	Take pictures and videos', #
            'sushi', # 	A quick previewer for Nautilus', # 	
            'tecla', # 	Keyboard layout viewer', # 	
            'totem', # 	Movie player for the GNOME desktop based on GStreamer', #
            'xdg-desktop-portal-gnome', # 	Backend implementation for xdg-desktop-portal for the GNOME desktop environment', # 	
            'xdg-user-dirs-gtk', # 	Creates user dirs and asks to relocalize them', #
            # custom gnome stuff
            'gnome-shell-extensions', 'gnome-browser-connector'
            # custom additional ones
           'nano','wget','git', 'firefox', 'vlc', 'gnome-boxes', 'openscad', 'prusa-slicer', 'gimp',
           'zed','resources', 'steam','discord', 'blender', 'obs-studio', 'kicad','less',
           'rustup','rustrover','rustrover-jre','intellij-idea-ultimate-edition',
           'networkmanager','lib32-mesa','mesa','vulkan-radeon','lib32-vulkan-radeon',
            'htop', 'pycharm-professional', 'mangohud', 'lib32-mangohud', 'pipewire', 'pipewire-audio', 'wireplumber',
            "archiso",
            # todo sound stack
        ]

    @property
    @override
    def default_greeter_type(self) -> GreeterType:
        return GreeterType.Gdm


with Installer(
        mountpoint,
        disk_config,
        kernels=['linux'],
) as installation:
    installation.mount_ordered_layout()
    installation.minimal_installation(hostname='arch-lukas', optional_repositories=[Repository.Multilib],
                                      locale_config=LocaleConfiguration('de','en_US.UTF-8','UTF-8'))
    installation.set_mirrors(MirrorConfiguration(custom_repositories=[custom_repo]))
    installation.add_bootloader(Bootloader.Systemd)

    user = User('lukas', Password(plaintext='$y$j9T$V3.bK9ivKqOVLw6FP3vZd/$I/74DMIysyyqUNHYeh/SEcHEDnNApy8UhL5Ane3VsK8'), True)
    installation.create_users(user)
    installation.set_user_password(User('root', Password(enc_password='$y$j9T$9WdI/dqHMFJnw0S2I51qV0$putBFyE2kORmJs9bWcRBjhax3yFoo0A/yk3hRtQzeL.'), False))

    profile_config = ProfileConfiguration(CustomProfile())
    profile_handler.install_profile_config(installation, profile_config)
