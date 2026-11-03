"""Utilities > SSH, FTP, SMB, S3 and GVfs/KIO link, and Remote shell: one
protocol's connection manager each."""

from navigator.widgets.drives.link_manager.link_manager import (
    FAMILIES,
    LinkManagerDialog,
    entries_for,
    family_of,
    location_of,
    schemes_of,
    sftp_entries,
)

__all__ = ["FAMILIES", "LinkManagerDialog", "entries_for", "family_of", "location_of", "schemes_of", "sftp_entries"]
