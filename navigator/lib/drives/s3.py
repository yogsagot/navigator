"""Amazon S3 -- and any endpoint that speaks its protocol (MinIO, Ceph, R2,
B2, Wasabi, Spaces) -- as a drive: ``s3://[key@]endpoint[:port]/bucket/key``.

Through `boto3 <https://boto3.amazonaws.com/>`_, one of Navigator's own
dependencies.

**A link is the four things every other is** (``Site``'s scheme, user,
host and port), so S3's own fit into them, as SMB's share fits into its path:

- the scheme is the transport: ``s3`` over HTTPS, ``s3+http`` over plain
  HTTP (a MinIO on the next machine), as ``ftp``/``ftps`` is FTP's;
- the host is the endpoint: ``s3.amazonaws.com`` (or ``s3.REGION.amazonaws.com``)
  is Amazon's, addressed as boto3 addresses it; any other host is an endpoint
  of its own, reached by URL and addressed path-style, which they all take;
- the user is who: empty for the AWS credential chain (the environment,
  ``~/.aws``, an instance's role), the name of a ``~/.aws`` profile for that
  profile, anything else an access key ID, its secret key asked for as a
  password is -- and kept, if asked, in the desktop's keyring, never here.

**The first name of a path is the bucket**, and the root lists the account's
buckets, with any reached by name besides (a key allowed into one bucket
cannot list them).  **Directories are prefixes**: a listing is
``list_objects_v2`` with ``/`` as its delimiter, the zero-byte ``dir/``
object a made directory leaves skipped.  An object is written whole or not
at all: a write is a multipart upload as the bytes come, completed on close
and abandoned on a failure.  A file renamed is copied on the server and the
old one deleted; a directory, having no object to rename, is ``EXDEV``, so
the copier copies it and deletes the old.  No modes, owners, links or times
to set: an object's time is its upload's.

Every request is HTTP of its own, so there is no connection to lose: botocore
retries, and an endpoint that cannot be reached after that is ``DriveGone``.
"""

from __future__ import annotations

import errno
import io
import re
import stat
import threading
from pathlib import PurePosixPath
from typing import IO, Any

from navigator.lib.drives.base import RENAME, WRITE, Child, Drive, DriveGone, FileStat
from navigator.lib.drives.location import Location, Site
from navigator.lib.drives.sessions import Answers, NeedPassword

#: Amazon's own endpoint: any other host is an endpoint of its own.
AWS_HOST = "s3.amazonaws.com"

#: ``s3.eu-west-1.amazonaws.com``, ``s3-eu-west-1.amazonaws.com``,
#: ``s3.dualstack.eu-west-1.amazonaws.com``: the region they name.
_AWS_REGIONAL = re.compile(r"^s3[.-](?:dualstack\.)?([a-z0-9-]+)\.amazonaws\.com$")

#: The size of each part a write uploads as it goes; S3's least is 5 MiB.
PART_SIZE = 8 * 1024 * 1024

#: The directories' mode, and the files': S3 keeps none.
DIR_MODE = stat.S_IFDIR | 0o755
FILE_MODE = stat.S_IFREG | 0o644

#: Error codes, and the errno each is.
_ERRNO = {
    "NoSuchKey": errno.ENOENT, "NoSuchBucket": errno.ENOENT, "NotFound": errno.ENOENT, "404": errno.ENOENT,
    "AccessDenied": errno.EACCES, "403": errno.EACCES, "AllAccessDisabled": errno.EACCES,
    "BucketAlreadyExists": errno.EEXIST, "BucketAlreadyOwnedByYou": errno.EEXIST,
    "BucketNotEmpty": errno.ENOTEMPTY, "InvalidBucketName": errno.EINVAL,
}

#: What an endpoint says of keys that will not do.
_BAD_KEYS = ("InvalidAccessKeyId", "SignatureDoesNotMatch", "InvalidClientTokenId", "InvalidToken",
             "ExpiredToken", "AuthorizationHeaderMalformed")


def available() -> str | None:
    """Always there: boto3 is one of Navigator's dependencies.  Every drive
    module answers this (``sessions.available``)."""
    return None


def is_aws(host: str) -> bool:
    return host == AWS_HOST or _AWS_REGIONAL.match(host) is not None


def _code(error: Exception) -> str:
    response = getattr(error, "response", None) or {}
    code = str(response.get("Error", {}).get("Code", ""))
    return code or str(response.get("ResponseMetadata", {}).get("HTTPStatusCode", ""))


def _os_error(error: Exception, where: Any) -> OSError:
    code = _code(error)
    number = _ERRNO.get(code, errno.EIO)
    message = (getattr(error, "response", None) or {}).get("Error", {}).get("Message") or str(error)
    kind = {errno.ENOENT: FileNotFoundError, errno.EEXIST: FileExistsError,
            errno.EACCES: PermissionError}.get(number, OSError)
    return kind(number, message, str(where))


def _error(number: int, where: Any, message: str | None = None) -> OSError:
    import os

    kind = {errno.ENOENT: FileNotFoundError, errno.EEXIST: FileExistsError, errno.ENOTDIR: NotADirectoryError,
            errno.EISDIR: IsADirectoryError}.get(number, OSError)
    return kind(number, message or os.strerror(number), str(where))


def _split(location: Location) -> tuple[str, str]:
    """``(bucket, key)``: the first name, and the rest joined -- ``("", "")`` at the root."""
    parts = [part for part in location.path.parts if part not in ("/", ".")]
    if not parts:
        return "", ""
    return parts[0], "/".join(parts[1:])


class S3Drive(Drive):
    """An endpoint's buckets, through boto3."""

    capabilities = frozenset((WRITE, RENAME))
    #: No endpoint says when a prefix changed: *Auto refresh* looks again.
    polled = True

    def __init__(self, site: Site, *, secret: str | None, start_bucket: str = "") -> None:
        self.site = site
        self.secure = site.scheme == "s3"
        self.aws = is_aws(site.host) and self.secure and not site.port
        regional = _AWS_REGIONAL.match(site.host)
        self.region = regional.group(1) if regional else None
        self.on_lost: Any = None
        self.home = PurePosixPath(f"/{start_bucket}") if start_bucket else PurePosixPath("/")
        #: The buckets reached by name, which the root lists with the account's.
        self.buckets: list[str] = [start_bucket] if start_bucket else []
        self._listed: list[str] | None = None
        self._lock = threading.Lock()
        #: A client per region (Amazon's) or the one (an endpoint's own), and
        #: each bucket's region once learnt.
        self._clients: dict[str | None, Any] = {}
        self._regions: dict[str, str | None] = {}
        self._session = self._make_session(secret)
        if not self.region:
            self.region = self._session.region_name or ("us-east-1" if not self.aws else None)

    # -- the session and its clients ----------------------------------------------------------

    def _make_session(self, secret: str | None) -> Any:
        import boto3

        user = self.site.user
        if not user:
            return boto3.Session()
        if user in boto3.Session().available_profiles:
            return boto3.Session(profile_name=user)
        return boto3.Session(aws_access_key_id=user, aws_secret_access_key=secret or "")

    @property
    def endpoint_url(self) -> str | None:
        """None for Amazon's (boto3 knows it); the URL of an endpoint of its own."""
        if self.aws:
            return None
        port = f":{self.site.port}" if self.site.port else ""
        host = f"[{self.site.host}]" if ":" in self.site.host else self.site.host
        return f"{'https' if self.secure else 'http'}://{host}{port}"

    def client(self, region: str | None = None) -> Any:
        """The client for *region* -- the drive's own when None."""
        from botocore.config import Config

        from navigator.settings import SETTINGS

        region = region or self.region
        with self._lock:
            found = self._clients.get(region)
            if found is None:
                timeout = max(1, SETTINGS.remote.timeout)
                config = Config(
                    signature_version="s3v4", connect_timeout=timeout, read_timeout=max(timeout, 60),
                    retries={"max_attempts": 3, "mode": "standard"},
                    s3={"addressing_style": "auto" if self.aws else "path"},
                )
                found = self._clients[region] = make_client(self._session, region, self.endpoint_url, config)
        return found

    def _bucket_client(self, bucket: str) -> Any:
        """The client for *bucket*: on Amazon, its own region's, learnt once."""
        if not self.aws or not bucket:
            return self.client()
        with self._lock:
            known = bucket in self._regions
            region = self._regions.get(bucket)
        if not known:
            region = self._learn_region(bucket)
            with self._lock:
                self._regions[bucket] = region
        return self.client(region)

    def _learn_region(self, bucket: str) -> str | None:
        """``x-amz-bucket-region``, which ``head_bucket`` answers with, even refused."""
        from botocore.exceptions import ClientError

        try:
            response = self.client().head_bucket(Bucket=bucket)
        except ClientError as error:
            response = error.response
        except Exception:
            return None
        headers = (response or {}).get("ResponseMetadata", {}).get("HTTPHeaders", {})
        return headers.get("x-amz-bucket-region") or self.region

    def _call(self, bucket: str, name: str, where: Any, **kwargs: Any) -> Any:
        """``client.name(**kwargs)`` on *bucket*'s client, its failures as ``OSError``."""
        from botocore.exceptions import BotoCoreError, ClientError, EndpointConnectionError, ConnectTimeoutError

        try:
            return getattr(self._bucket_client(bucket), name)(**kwargs)
        except ClientError as error:
            raise _os_error(error, where) from error
        except (EndpointConnectionError, ConnectTimeoutError) as error:
            self._lost()
            raise DriveGone(self.site.host, f"Cannot reach {self.site.host}: {error}") from error
        except BotoCoreError as error:
            raise _error(errno.EIO, where, str(error)) from error

    def _lost(self) -> None:
        lost = self.on_lost
        if lost is not None:
            threading.Thread(target=lost, daemon=True).start()

    # -- names ----------------------------------------------------------------------------------

    def get_dir(self, location: Location) -> str:
        from navigator.lib.drives.sessions import protocol_sign

        return f"{protocol_sign(self.site.scheme)}:{self.site.host}:{location.path}"

    def _note(self, bucket: str) -> None:
        if bucket:
            with self._lock:
                if bucket not in self.buckets:
                    self.buckets.append(bucket)

    # -- listing --------------------------------------------------------------------------------

    def _root(self) -> list[str]:
        """The account's buckets, asked once, and those reached by name."""
        with self._lock:
            listed = self._listed
        if listed is None:
            try:
                answer = self._call("", "list_buckets", Location(self.site, PurePosixPath("/")))
                listed = [bucket["Name"] for bucket in answer.get("Buckets", [])]
            except DriveGone:
                raise
            except OSError:
                listed = []  # a key that may not list them: those reached by name
            with self._lock:
                self._listed = listed
        with self._lock:
            known = list(self.buckets)
        return listed + [bucket for bucket in known if bucket not in listed]

    def _list(self, location: Location) -> list[Child]:
        """``(name, stat)`` for what is directly under *location*: its common
        prefixes as directories, its objects as files."""
        bucket, key = _split(location)
        self._note(bucket)
        prefix = f"{key}/" if key else ""
        found: dict[str, FileStat] = {}
        token = None
        while True:
            arguments: dict[str, Any] = {"Bucket": bucket, "Prefix": prefix, "Delimiter": "/"}
            if token:
                arguments["ContinuationToken"] = token
            page = self._call(bucket, "list_objects_v2", location, **arguments)
            for common in page.get("CommonPrefixes", []):
                name = common["Prefix"][len(prefix):].rstrip("/")
                if name:
                    found[name] = FileStat(DIR_MODE)
            for item in page.get("Contents", []):
                name = item["Key"][len(prefix):]
                if not name or "/" in name:
                    continue  # the directory's own marker
                moment = item["LastModified"].timestamp()
                found.setdefault(name, FileStat(FILE_MODE, item["Size"], moment, moment))
            if not page.get("IsTruncated"):
                break
            token = page.get("NextContinuationToken")
        if not found and key and not self._is_dir(bucket, key):
            raise _error(errno.ENOENT, location)
        return sorted(found.items())

    def _is_dir(self, bucket: str, key: str) -> bool:
        """Whether anything is under ``key/`` -- its marker, at least."""
        page = self._call(bucket, "list_objects_v2", key, Bucket=bucket, Prefix=f"{key}/", MaxKeys=1)
        return bool(page.get("KeyCount") or page.get("Contents"))

    def scan(self, location: Location, show_hidden: bool, sort: str, *, free: bool,
             **options: Any) -> tuple[list, str | None, tuple[int, str] | None]:
        from navigator.lib.appearance import filetypes
        from navigator.lib.drives.listing import DirEntry, order_entries

        if location.is_root:
            entries = [DirEntry(bucket, True, 0, DIR_MODE) for bucket in self._root()]
            return order_entries(entries, sort), None, None
        mask = options.get("mask", filetypes.ALL_FILES)
        filtered = mask.strip() not in ("", filetypes.ALL_FILES)
        entries = [DirEntry("..", True, 0, DIR_MODE)]
        try:
            listed = self._list(location)
        except DriveGone:
            raise
        except OSError as error:
            return entries, error.strerror or str(error), None
        for name, st in listed:
            if not show_hidden and name.startswith("."):
                continue
            is_dir = stat.S_ISDIR(st.st_mode)
            if filtered and not is_dir and not filetypes.in_filter(name, mask):
                continue
            entries.append(DirEntry(name, is_dir, st.st_size, st.st_mode, st.st_mtime))
        order = {key: options[key] for key in ("executables_first", "archives_first", "reverse")
                 if key in options}
        return order_entries(entries, sort, **order), None, None

    def children(self, location: Location) -> list[Child]:
        if location.is_root:
            return [(bucket, FileStat(DIR_MODE)) for bucket in self._root()]
        return self._list(location)

    def names(self, location: Location) -> list[str]:
        return [name for name, _ in self.children(location)]

    def stat(self, location: Location) -> FileStat:
        bucket, key = _split(location)
        if not bucket:
            return FileStat(DIR_MODE)
        self._note(bucket)
        if not key:
            self._call(bucket, "head_bucket", location, Bucket=bucket)
            return FileStat(DIR_MODE)
        try:
            head = self._call(bucket, "head_object", location, Bucket=bucket, Key=key)
        except FileNotFoundError:
            if self._is_dir(bucket, key):
                return FileStat(DIR_MODE)
            raise
        moment = head["LastModified"].timestamp()
        return FileStat(FILE_MODE, head["ContentLength"], moment, moment)

    def lstat(self, location: Location) -> FileStat:
        return self.stat(location)

    # -- reading --------------------------------------------------------------------------------

    def open_read(self, location: Location) -> IO[bytes]:
        bucket, key = _split(location)
        if not key:
            raise _error(errno.EISDIR, location)
        body = self._call(bucket, "get_object", location, Bucket=bucket, Key=key)["Body"]
        return io.BufferedReader(_Body(body), 1 << 16)  # type: ignore[return-value]

    def open_random(self, location: Location) -> Any:
        """Ranged ``GET``s: F3 reads an object a chunk at a time."""
        bucket, key = _split(location)
        if not key:
            raise _error(errno.EISDIR, location)
        return _RangeReader(self, bucket, key, location)

    # -- writing --------------------------------------------------------------------------------

    def open_write(self, location: Location, *, append: bool = False, mode: int = 0o666) -> IO[bytes]:
        bucket, key = _split(location)
        if not key:
            raise _error(errno.EISDIR, location)
        if append:
            raise _error(errno.ENOTSUP, location, "S3 cannot append to an object")
        return _Upload(self, bucket, key, location)  # type: ignore[return-value]

    def mkdir(self, location: Location, mode: int = 0o777) -> None:
        bucket, key = _split(location)
        if not bucket:
            raise _error(errno.EEXIST, location)
        if not key:
            # A bucket made at the root: in Amazon's region the drive is in.
            arguments: dict[str, Any] = {"Bucket": bucket}
            if self.aws and self.region and self.region != "us-east-1":
                arguments["CreateBucketConfiguration"] = {"LocationConstraint": self.region}
            self._call("", "create_bucket", location, **arguments)
            with self._lock:
                self._listed = None
            self._note(bucket)
            return
        if self.exists(location):
            raise _error(errno.EEXIST, location)
        self._call(bucket, "put_object", location, Bucket=bucket, Key=f"{key}/", Body=b"")

    def rmdir(self, location: Location) -> None:
        bucket, key = _split(location)
        if not key:
            self._call(bucket, "delete_bucket", location, Bucket=bucket)
            with self._lock:
                self._listed = None
                if bucket in self.buckets:
                    self.buckets.remove(bucket)
            return
        page = self._call(bucket, "list_objects_v2", location, Bucket=bucket, Prefix=f"{key}/", MaxKeys=2)
        keys = [item["Key"] for item in page.get("Contents", [])]
        if any(each != f"{key}/" for each in keys):
            raise _error(errno.ENOTEMPTY, location)
        if not keys:
            raise _error(errno.ENOENT, location)
        self._call(bucket, "delete_object", location, Bucket=bucket, Key=f"{key}/")

    def unlink(self, location: Location) -> None:
        bucket, key = _split(location)
        if not key:
            raise _error(errno.EISDIR, location)
        self._call(bucket, "head_object", location, Bucket=bucket, Key=key)
        self._call(bucket, "delete_object", location, Bucket=bucket, Key=key)

    def _move(self, source: Location, dest: Location, *, replace: bool) -> None:
        source_bucket, source_key = _split(source)
        dest_bucket, dest_key = _split(dest)
        if not source_key or not dest_key or stat.S_ISDIR(self.stat(source).st_mode):
            # No object to rename: the copier copies what is under it.
            raise _error(errno.EXDEV, source, "S3 renames objects, not prefixes")
        if not replace and self.lexists(dest):
            raise _error(errno.EEXIST, dest)
        # A managed copy, multipart past 5 GiB, then the old one deleted.
        self._call(dest_bucket, "copy", dest, CopySource={"Bucket": source_bucket, "Key": source_key},
                   Bucket=dest_bucket, Key=dest_key)
        self._call(source_bucket, "delete_object", source, Bucket=source_bucket, Key=source_key)

    def rename(self, source: Location, dest: Location) -> None:
        self._move(source, dest, replace=False)

    def replace(self, source: Location, dest: Location) -> None:
        self._move(source, dest, replace=True)

    # -- the rest -------------------------------------------------------------------------------

    def describe(self) -> list[tuple[str, str]]:
        lines = [("Server", self.endpoint_url or "Amazon S3")]
        if self.region:
            lines.append(("Region", self.region))
        lines.append(("Security", "TLS (HTTPS)" if self.secure else "none (plain HTTP)"))
        return lines

    def close(self) -> None:
        with self._lock:
            clients, self._clients = list(self._clients.values()), {}
        for client in clients:
            try:
                client.close()
            except Exception:
                pass


def make_client(session: Any, region: str | None, endpoint_url: str | None, config: Any) -> Any:
    """``session.client("s3", ...)``: a test puts a stand-in here."""
    return session.client("s3", region_name=region, endpoint_url=endpoint_url, config=config)


class _Body(io.RawIOBase):
    """An object's streaming body as a raw file."""

    def __init__(self, body: Any) -> None:
        super().__init__()
        self._body = body

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Any) -> int:
        data = self._body.read(len(buffer))
        buffer[: len(data)] = data
        return len(data)

    def close(self) -> None:
        if not self.closed:
            try:
                self._body.close()
            except Exception:
                pass
        super().close()


class _RangeReader:
    """``read_at`` as a ranged ``GET``."""

    def __init__(self, drive: S3Drive, bucket: str, key: str, where: Location) -> None:
        self._drive, self._bucket, self._key, self._where = drive, bucket, key, where

    def read_at(self, offset: int, count: int) -> bytes:
        if count <= 0:
            return b""
        answer = self._drive._call(self._bucket, "get_object", self._where, Bucket=self._bucket, Key=self._key,
                                   Range=f"bytes={offset}-{offset + count - 1}")
        with answer["Body"] as body:
            return body.read()

    def close(self) -> None:
        pass


class _Upload(io.RawIOBase):
    """An object being written: a multipart upload as its parts fill, one
    ``put_object`` if it never grows to one; completed on close, abandoned if
    the ``with`` it is written in ends in an exception (a failure, Stop)."""

    def __init__(self, drive: S3Drive, bucket: str, key: str, where: Location) -> None:
        super().__init__()
        self._drive, self._bucket, self._key, self._where = drive, bucket, key, where
        self._buffer = bytearray()
        self._upload: str | None = None
        self._parts: list[dict[str, Any]] = []
        self._failed = False

    def writable(self) -> bool:
        return True

    def write(self, data: Any) -> int:
        if self.closed:
            raise ValueError("write to a closed upload")
        self._buffer += data
        while len(self._buffer) >= PART_SIZE:
            part, self._buffer = bytes(self._buffer[:PART_SIZE]), self._buffer[PART_SIZE:]
            self._send(part)
        return len(data)

    def _send(self, part: bytes) -> None:
        drive, bucket, key = self._drive, self._bucket, self._key
        try:
            if self._upload is None:
                self._upload = drive._call(bucket, "create_multipart_upload", self._where,
                                           Bucket=bucket, Key=key)["UploadId"]
            number = len(self._parts) + 1
            answer = drive._call(bucket, "upload_part", self._where, Bucket=bucket, Key=key,
                                 UploadId=self._upload, PartNumber=number, Body=part)
        except BaseException:
            self._failed = True
            raise
        self._parts.append({"PartNumber": number, "ETag": answer["ETag"]})

    def abort(self) -> None:
        """Nothing written: the parts sent so far thrown away."""
        self._failed = True
        if self._upload is not None:
            try:
                self._drive._call(self._bucket, "abort_multipart_upload", self._where, Bucket=self._bucket,
                                  Key=self._key, UploadId=self._upload)
            except OSError:
                pass
            self._upload = None
        super().close()

    def close(self) -> None:
        if self.closed:
            return
        if self._failed:
            self.abort()
            return
        drive, bucket, key = self._drive, self._bucket, self._key
        try:
            if self._upload is None:
                drive._call(bucket, "put_object", self._where, Bucket=bucket, Key=key, Body=bytes(self._buffer))
            else:
                if self._buffer or not self._parts:
                    self._send(bytes(self._buffer))
                drive._call(bucket, "complete_multipart_upload", self._where, Bucket=bucket, Key=key,
                            UploadId=self._upload, MultipartUpload={"Parts": self._parts})
        except BaseException:
            self.abort()
            raise
        self._buffer = bytearray()
        super().close()

    def __exit__(self, kind: Any, value: Any, traceback: Any) -> None:
        if kind is not None:
            self.abort()
        else:
            self.close()


def connect(site: Site, answers: Answers) -> S3Drive:
    """*site*'s endpoint, its credentials proved: blocks, and raises what the user must answer.

    The account's buckets are listed to prove them; a key that may not list
    them is proved on the bucket asked for (``answers.start``'s first name).
    """
    from botocore.exceptions import NoCredentialsError, PartialCredentialsError

    from navigator.lib.drives import credentials

    parts = [part for part in PurePosixPath(answers.start or "/").parts if part not in ("/", ".")]
    bucket = parts[0] if parts else ""
    user = site.user
    profile = False
    if user:
        import boto3

        profile = user in boto3.Session().available_profiles
    if user and not profile:
        if answers.password is None and not answers.tried_keyring:
            answers.tried_keyring = True
            answers.password = credentials.saved_password(site)
        if not answers.password:
            raise NeedPassword(site, user, site.host)
    drive = S3Drive(site, secret=answers.password, start_bucket=bucket)
    root = Location(site, PurePosixPath("/"))
    try:
        try:
            drive._call("", "list_buckets", root)
        except PermissionError:
            if not bucket:
                raise
            drive._call(bucket, "head_bucket", Location(site, PurePosixPath(f"/{bucket}")), Bucket=bucket)
    except (NoCredentialsError, PartialCredentialsError) as error:
        drive.close()
        raise OSError(errno.EACCES, "No AWS credentials: give an access key as the login, "
                      "or set them up in ~/.aws", site.host) from error
    except OSError as error:
        drive.close()
        cause = error.__cause__
        if cause is not None and _code(cause) in _BAD_KEYS:
            if user and not profile:
                raise NeedPassword(site, user, site.host, wrong=True) from error
            raise OSError(errno.EACCES, f"{site.host} refused the AWS credentials: {error.strerror}",
                          site.host) from error
        raise
    if answers.save_password and answers.password and user and not profile:
        credentials.save_password(site, answers.password)
    return drive


__all__ = ["AWS_HOST", "EXTRA", "PART_SIZE", "S3Drive", "available", "connect", "is_aws", "make_client"]
