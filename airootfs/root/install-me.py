from pathlib import Path

from archinstall.default_profiles.desktops.gnome import GnomeProfile
from archinstall.lib.disk.device_handler import device_handler
from archinstall.lib.disk.filesystem import FilesystemHandler
from archinstall.lib.installer import Installer
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
from archinstall.lib.models.profile_model import ProfileConfiguration
from archinstall.lib.models.users import Password, User
from archinstall.lib.profile.profiles_handler import profile_handler

# we're creating a new ext4 filesystem installation
fs_type = FilesystemType('ext4')
device_path = Path('/dev/sda')

# get the physical disk device
device = device_handler.get_device(device_path)

if not device:
	raise ValueError('No device found for given path')

# create a new modification for the specific device
device_modification = DeviceModification(device, wipe=True)

start_boot = Size(1, Unit.MiB, device.device_info.sector_size)
length_boot = Size(512, Unit.MiB, device.device_info.sector_size)
start_root = start_boot + length_boot
length_root = device.device_info.total_size - start_root

# create a new boot partition
boot_partition = PartitionModification(
	status=ModificationStatus.Create,
	type=PartitionType.Primary,
	start=start_boot,
	length=length_boot,
	mountpoint=Path('/boot'),
	fs_type=FilesystemType.Fat32,
	flags=[PartitionFlag.BOOT],
)

root_partition = PartitionModification(
	status=ModificationStatus.Create,
	type=PartitionType.Primary,
	start=start_root,
	length=length_root,
	mountpoint=None,
	fs_type=fs_type,
	mount_options=[],
)

device_modification.add_partition(boot_partition)
device_modification.add_partition(root_partition)

disk_config = DiskLayoutConfiguration(
	config_type=DiskLayoutType.Default,
	device_modifications=[device_modification],
)

# disk encryption configuration (Optional)
#disk_encryption = DiskEncryption(
#	encryption_password=Password(plaintext='enc_password'),
#	encryption_type=EncryptionType.Luks,
##	partitions=[home_partition],
#	hsm_device=None,
#)

#disk_config.disk_encryption = disk_encryption

# initiate file handler with the disk config and the optional disk encryption config
fs_handler = FilesystemHandler(disk_config)

# perform all file operations
# WARNING: this will potentially format the filesystem and delete all data
fs_handler.perform_filesystem_operations(show_countdown=False)

mountpoint = Path('/tmp')

with Installer(
	mountpoint,
	disk_config,
	kernels=['linux'],
) as installation:
	installation.mount_ordered_layout()
	installation.minimal_installation(hostname='minimal-arch')
	installation.add_additional_packages(['nano', 'wget', 'git'])

# Optionally, install a profile of choice.
# In this case, we install a minimal profile that is empty
profile_config = ProfileConfiguration(GnomeProfile())
profile_handler.install_profile_config(installation, profile_config)

user = User('lukas', Password(plaintext='1qayxsw2'), True)
installation.create_users(user)
