from pathlib import Path
from typing import override

from archinstall.default_profiles.profile import ProfileType, GreeterType
from archinstall.default_profiles.xorg import XorgProfile
from archinstall.lib.disk.device_handler import device_handler
from archinstall.lib.disk.filesystem import FilesystemHandler
from archinstall.lib.installer import Installer
from archinstall.lib.models import Repository, LocaleConfiguration, Bootloader, CustomRepository, MirrorConfiguration, \
    FilesystemType, DeviceModification, PartitionModification, ModificationStatus, PartitionType, PartitionFlag, \
    DiskLayoutConfiguration, DiskLayoutType, Size, Unit, ProfileConfiguration
from archinstall.lib.models.mirrors import SignCheck, SignOption
from archinstall.lib.models.users import Password, User
from archinstall.lib.profile.profiles_handler import profile_handler

# we're creating a new ext4 filesystem installation
fs_type = FilesystemType('ext4')
device_path = Path('/dev/vda')
mountpoint = Path('/mnt/arch')

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

# create a new EFI system partition for systemd-boot
boot_partition = PartitionModification(
    status=ModificationStatus.Create,
    type=PartitionType.Primary,
    start=start_boot,
    length=length_boot,
    mountpoint=Path('/boot'),  # archinstall detects ESP here for systemd-boot
    fs_type=FilesystemType.Fat32,
    flags=[PartitionFlag.ESP, PartitionFlag.BOOT],
    #flags=[PartitionFlag.BOOT],  # for MBR (not used here; we're using GPT+ESP)
)

# root partition
root_partition = PartitionModification(
    status=ModificationStatus.Create,
    type=PartitionType.Primary,
    start=start_root,
    length=length_root,
    mountpoint=Path('/'),
    fs_type=FilesystemType.Ext4,
    mount_options=[],
)

device_modification.add_partition(boot_partition)
device_modification.add_partition(root_partition)

disk_config = DiskLayoutConfiguration(
    config_type=DiskLayoutType.Manual,
    device_modifications=[device_modification],
)

# initiate file handler with the disk config and the optional disk encryption config
fs_handler = FilesystemHandler(disk_config)

# perform all file operations
# WARNING: this will potentially format the filesystem and delete all data
fs_handler.perform_filesystem_operations(show_countdown=False)

custom_repo = CustomRepository(
    name='repo',
    url='https://repo.heili.eu/$arch',
    sign_check=SignCheck.Optional,
    sign_option=SignOption.TrustAll
)


class CustomProfile(XorgProfile):
    def __init__(self):
        super().__init__('GNOME', ProfileType.DesktopEnv)

    def install(self, install_session: 'Installer') -> None:
        super().install(install_session)
        install_session.add_additional_packages(self.packages)
        self.post_install(install_session)

    def post_install(self, install_session: 'Installer') -> None:
        super().post_install(install_session)
        install_session.enable_service('NetworkManager.service')
        install_session.enable_service('gdm.service')

        # set git name+email
        install_session.arch_chroot('git config --global user.email "lukas.heiligenbrunner@gmail.com"', 'lukas')
        install_session.arch_chroot('git config --global user.name "Lukas Heiligenbrunner"', 'lukas')
        # setup rust toolchain
        install_session.arch_chroot('rustup default stable', 'lukas')

        # copy background
        local_background_path = Path('/root/rsc/background-hogwartslegacy.png')  # Adjust path if needed
        chroot_background_path = Path(f"{install_session.target}/home/lukas/Pictures/background.png")
        chroot_background_path.parent.mkdir(parents=True, exist_ok=True)
        chroot_background_path.write_bytes(local_background_path.read_bytes())
        install_session.arch_chroot('chown -R lukas:lukas /home/lukas/Pictures', 'root')

        # prepare gsettings commands (run for user 'lukas')
        gsettings_cmds = [
            'gsettings set org.gnome.desktop.background picture-uri "file:///home/lukas/Pictures/background.png"',
            'gsettings set org.gnome.desktop.background picture-uri-dark "file:///home/lukas/Pictures/background.png"',
            'gsettings set org.gnome.desktop.interface color-scheme "prefer-dark"',

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
            # https://extensions.gnome.org/extension-data/VitalsCoreCoding.com.v73.shell-extension.zip
            "gnome-extensions enable Vitals@CoreCoding.com",

            #"gsettings set org.gnome.shell.extensions.tiling-assistant enable-tiling-popup false",
        ]

        for cmd in gsettings_cmds:
            install_session.arch_chroot(f'dbus-launch --exit-with-session {cmd}', 'lukas')

    @property
    @override
    def packages(self) -> list[str]:
        return [
            'gnome-tweaks', self.default_greeter_type.value,

            # default gnome applications with some removed
            'baobab',
            'decibels',
            'papers',
            'gdm',
            'gnome-backgrounds',
            'gnome-calculator',
            'gnome-calendar',
            'gnome-characters',
            'gnome-clocks',
            'gnome-color-manager',
            'gnome-connections',
            'gnome-console',
            'gnome-contacts',
            'gnome-control-center',
            'gnome-disk-utility',
            'gnome-font-viewer',
            'gnome-keyring',
            'gnome-logs',
            'gnome-maps',
            'gnome-menus',
            'gnome-remote-desktop',
            'gnome-session',
            'gnome-settings-daemon',
            'gnome-shell',
            'gnome-shell-extensions',
            'gnome-text-editor',
            'gnome-user-docs',
            'gnome-user-share',
            'gnome-weather',
            'grilo-plugins',
            'gvfs',
            'gvfs-afc',
            'gvfs-dnssd',
            'gvfs-goa',
            'gvfs-mtp',
            'gvfs-nfs',
            'gvfs-smb',
            'gvfs-wsdd',
            'loupe',
            'nautilus',
            'orca',
            'rygel',
            'simple-scan',
            'snapshot',
            'sushi',
            'tecla',
            'totem',
            'xdg-desktop-portal-gnome',
            'xdg-user-dirs-gtk',
            # custom gnome stuff
            'gnome-shell-extensions', 'gnome-browser-connector','gnome-shell-extension-vitals',
            #'gnome-shell-extension-tiling-assistant',
            # custom additional ones
            'nano', 'wget', 'git', 'firefox', 'vlc', 'gnome-boxes', 'openscad', 'prusa-slicer', 'gimp',
            'zed', 'resources', 'steam', 'discord', 'blender', 'obs-studio', 'kicad', 'less',
            'rustup', 'rustrover', 'rustrover-jre', 'intellij-idea-ultimate-edition',
            'networkmanager', 'lib32-mesa', 'mesa', 'vulkan-radeon', 'lib32-vulkan-radeon',
            'htop', 'pycharm-professional', 'mangohud', 'lib32-mangohud', 'pipewire', 'pipewire-audio', 'wireplumber',
            'archiso', 'just',
            # todo sound stack
        ]

    @property
    @override
    def default_greeter_type(self) -> GreeterType:
        return GreeterType.Gdm

from archinstall.lib.general import SysCommand, run
from archinstall.lib.exceptions import DiskError, HardwareIncompatibilityError, RequirementError, ServiceException, SysCallError
from archinstall.lib.hardware import SysInfo
from archinstall.lib.models.device import (
    DiskEncryption,
    DiskLayoutConfiguration,
    EncryptionType,
    FilesystemType,
    LvmVolume,
    PartitionModification,
    SectorSize,
    Size,
    SnapshotType,
    SubvolumeModification,
    Unit,
)

with Installer(
    mountpoint,
    disk_config,
    kernels=['linux'],
) as installation:
    # Let Installer handle partitioning, formatting, and mounting under /mnt/arch
    installation.mount_ordered_layout()

    installation.minimal_installation(
        hostname='arch-lukas',
        optional_repositories=[Repository.Multilib],
        locale_config=LocaleConfiguration('de', 'en_US.UTF-8', 'UTF-8')
    )
    installation.set_mirrors(MirrorConfiguration(custom_repositories=[custom_repo]))

    # Install systemd-boot (requires UEFI boot mode and ESP mounted at /mnt/arch/boot)
    #installation.add_bootloader(Bootloader.Systemd)
    # debug('Installing systemd bootloader')

    efi_partition = installation._get_efi_partition()
    boot_partition = installation._get_boot_partition()
    root = installation._get_root()
    installation.pacman.strap('efibootmgr')

    if not SysInfo.has_uefi():
        raise HardwareIncompatibilityError

    if not efi_partition:
        raise ValueError('Could not detect EFI system partition')
    elif not efi_partition.mountpoint:
        raise ValueError('EFI system partition is not mounted')

    # TODO: Ideally we would want to check if another config
    # points towards the same disk and/or partition.
    # And in which case we should do some clean up.
    bootctl_options = []

    if boot_partition != efi_partition:
        bootctl_options.append(f'--esp-path={efi_partition.mountpoint}')
        bootctl_options.append(f'--boot-path={boot_partition.mountpoint}')

    systemd_version = '257'  # This works as a safety workaround for this hot-fix

    # Install the boot loader
    try:
        # Force EFI variables since bootctl detects arch-chroot
        # as a container environemnt since v257 and skips them silently.
        # https://github.com/systemd/systemd/issues/36174
        if systemd_version >= '258':
            SysCommand(f'arch-chroot {installation.target} bootctl --variables=yes {" ".join(bootctl_options)} install')
        else:
            SysCommand(f'arch-chroot {installation.target} bootctl {" ".join(bootctl_options)} install')
    except SysCallError:
        if systemd_version >= '258':
            # Fallback, try creating the boot loader without touching the EFI variables
            SysCommand(f'arch-chroot {installation.target} bootctl --variables=no {" ".join(bootctl_options)} install')
        else:
            SysCommand(f'arch-chroot {installation.target} bootctl --no-variables {" ".join(bootctl_options)} install')

    # Loader configuration is stored in ESP/loader:
    # https://man.archlinux.org/man/loader.conf.5
    loader_conf = installation.target / efi_partition.relative_mountpoint / 'loader/loader.conf'
    # Ensure that the ESP/loader/ directory exists before trying to create a file in it
    loader_conf.parent.mkdir(parents=True, exist_ok=True)

    default_kernel = installation.kernels[0]

    entry_name = installation.init_time + '_{kernel}{variant}.conf'
    default_entry = entry_name.format(kernel=default_kernel, variant='')
    installation._create_bls_entries(boot_partition, root, entry_name)

    default = f'default {default_entry}'

    # Modify or create a loader.conf
    try:
        loader_data = loader_conf.read_text().splitlines()
    except FileNotFoundError:
        loader_data = [
            default,
            'timeout 15',
        ]
    else:
        for index, line in enumerate(loader_data):
            if line.startswith('default'):
                loader_data[index] = default
            elif line.startswith('#timeout'):
                # We add in the default timeout to support dual-boot
                loader_data[index] = line.removeprefix('#')

    loader_conf.write_text('\n'.join(loader_data) + '\n')

    installation._helper_flags['bootloader'] = 'systemd'

    user = User('lukas', Password(enc_password='$6$73CpxYtM7XJpkM1/$j0EDtT7VGzpTsgBhtrhzfMPId2PC9JnSvUMXwhnW0y2RWfyEspQwlsCSIA53qatk10zKuOg/GAMWVjHUoUE.r/'), True)
    installation.create_users(user)
    installation.set_user_password(User('root', Password(enc_password='$6$krcop.s33vKrd/Nh$rO/toJMTBfowFx5hdg9t3vTri0.Ienr.uhm5MnO3xi4KHja8eO/kxeXrK/Z/z..rw3lz63qzSiDlTMwMIW1bh/'), False))

    profile_config = ProfileConfiguration(CustomProfile())
    profile_handler.install_profile_config(installation, profile_config)
