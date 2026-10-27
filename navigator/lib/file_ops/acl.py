"""POSIX access control lists: the ACL page of Alt+E, with no I/O in it.

Not DN's -- DOS had no ACLs -- and a departure, asked for.  Linux keeps a
file's ACL in two extended attributes, :data:`ACCESS` and :data:`DEFAULT` (a
directory's, inherited by what is made in it), each in the kernel's own
binary form: a 32-bit version, 2, then an entry of ``tag, perm, id`` (16, 16
and 32 bits, little-endian) for each, sorted by tag and then id.  This module
reads and writes that form itself, so neither ``libacl`` nor ``setfacl`` is
needed.

**The owner, group and others entries are the mode's**: the kernel keeps them
equal to its bits, and the dialog's *Mode* page edits them.  What the ACL page
edits is the rest -- a user or group named, and the mask, which caps every
entry of the group class (named users, the owning group, named groups) and
which ``ls -l`` shows as the group bits.

**The mask is worked out, as ``setfacl`` works it out**, the union of the group
class, unless it was set explicitly; it is there whenever a named entry is,
and goes with the last one.  An ACL left with nothing but the three base
entries is *minimal*, and its attribute is removed rather than written
(``setfacl -b``).

**Edits are deltas** (:func:`apply_deltas`): entries to set, entries to
remove, keyed ``(kind, id)``, so the same edit goes to files whose ACLs
otherwise differ -- only what the user touched changes.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field, replace

#: The attributes an ACL lives in.
ACCESS = "system.posix_acl_access"
DEFAULT = "system.posix_acl_default"

#: The binary form's version, and its tags.
VERSION = 2
USER_OBJ, USER, GROUP_OBJ, GROUP, MASK, OTHER = 0x01, 0x02, 0x04, 0x08, 0x10, 0x20
#: The id of an entry that names no one.
UNDEFINED = 0xFFFFFFFF

#: A named entry's kind, as keys spell it.
KIND_USER, KIND_GROUP = "user", "group"
#: The mask's key, which names no one.
MASK_KEY = ("mask", None)

#: Read, write and execute, as an entry's perm holds them.
READ, WRITE, EXECUTE = 4, 2, 1
RWX = 7

_HEADER = struct.Struct("<I")
_ENTRY = struct.Struct("<HHI")


@dataclass
class Acl:
    """One access or default ACL."""

    owner: int = 0
    group: int = 0
    other: int = 0
    #: ``{("user" or "group", id): perms}``.
    named: dict[tuple[str, int], int] = field(default_factory=dict)
    #: The mask, or ``None`` where the ACL has none.
    mask: int | None = None

    @property
    def minimal(self) -> bool:
        """Nothing but the owner, group and others entries."""
        return not self.named and self.mask is None

    def entries(self) -> dict[tuple[str, int | None], int]:
        """What the ACL page lists: the named entries, and the mask."""
        found: dict[tuple[str, int | None], int] = dict(self.named)
        if self.mask is not None:
            found[MASK_KEY] = self.mask
        return found


def parse(data: bytes) -> Acl:
    """The kernel's binary form as an :class:`Acl`; ``ValueError`` for anything else."""
    if len(data) < _HEADER.size or (len(data) - _HEADER.size) % _ENTRY.size:
        raise ValueError("not an ACL")
    (version,) = _HEADER.unpack_from(data)
    if version != VERSION:
        raise ValueError(f"ACL version {version}")
    acl = Acl()
    for offset in range(_HEADER.size, len(data), _ENTRY.size):
        tag, perm, ident = _ENTRY.unpack_from(data, offset)
        perm &= RWX
        if tag == USER_OBJ:
            acl.owner = perm
        elif tag == GROUP_OBJ:
            acl.group = perm
        elif tag == OTHER:
            acl.other = perm
        elif tag == MASK:
            acl.mask = perm
        elif tag == USER:
            acl.named[(KIND_USER, ident)] = perm
        elif tag == GROUP:
            acl.named[(KIND_GROUP, ident)] = perm
        else:
            raise ValueError(f"ACL tag {tag:#x}")
    return acl


def pack(acl: Acl) -> bytes:
    """*acl* in the kernel's binary form, sorted as it requires."""
    entries = [(USER_OBJ, acl.owner, UNDEFINED), (GROUP_OBJ, acl.group, UNDEFINED), (OTHER, acl.other, UNDEFINED)]
    for (kind, ident), perm in acl.named.items():
        entries.append((USER if kind == KIND_USER else GROUP, perm, ident))
    if acl.mask is not None:
        entries.append((MASK, acl.mask, UNDEFINED))
    entries.sort(key=lambda entry: (entry[0], entry[2]))
    return _HEADER.pack(VERSION) + b"".join(_ENTRY.pack(tag, perm & RWX, ident) for tag, perm, ident in entries)


def from_mode(mode: int) -> Acl:
    """The minimal ACL a file without one has: its mode's three triplets."""
    return Acl(owner=(mode >> 6) & RWX, group=(mode >> 3) & RWX, other=mode & RWX)


def compute_mask(acl: Acl) -> int:
    """The union of the group class, ``setfacl``'s mask."""
    mask = acl.group
    for perm in acl.named.values():
        mask |= perm
    return mask


def apply_deltas(
    acl: Acl,
    set_entries: dict[tuple[str, int | None], int],
    remove: set[tuple[str, int | None]] | frozenset[tuple[str, int | None]],
) -> Acl:
    """*acl* with *set_entries* set and *remove* removed.

    The mask is one of the keys (:data:`MASK_KEY`): set, it is the user's;
    otherwise it is worked out again whenever a named entry changed.  It is
    there exactly when a named entry is, so removing it while one is left
    works it out again, and the last named entry gone takes it along.
    """
    new = replace(acl, named=dict(acl.named))
    touched_named = False
    for key in remove:
        if key != MASK_KEY and key in new.named:
            del new.named[key]
            touched_named = True
    for key, perm in set_entries.items():
        if key != MASK_KEY:
            new.named[key] = perm & RWX  # type: ignore[index]
            touched_named = True
    if not new.named:
        new.mask = None
    elif MASK_KEY in set_entries:
        new.mask = set_entries[MASK_KEY] & RWX
    elif touched_named or new.mask is None or MASK_KEY in remove:
        new.mask = compute_mask(new)
    return new


def seed_default(access: Acl) -> Acl:
    """A directory's first default ACL: its access ACL's base entries, as
    ``setfacl -d`` starts one."""
    return Acl(owner=access.owner, group=access.group, other=access.other)


def spell(perm: int | None) -> str:
    """``rw-``, or ``???`` for files that disagree."""
    if perm is None:
        return "???"
    return "".join(letter if perm & bit else "-" for letter, bit in (("r", READ), ("w", WRITE), ("x", EXECUTE)))


__all__ = [
    "ACCESS", "Acl", "DEFAULT", "KIND_GROUP", "KIND_USER", "MASK_KEY", "apply_deltas", "compute_mask",
    "from_mode", "pack", "parse", "seed_default", "spell",
]
