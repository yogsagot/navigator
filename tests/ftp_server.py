"""An FTP server for ``tests/test_ftp.py``, run as a process of its own:
pyftpdlib keeps timers on one loop per process, and two servers in one --
one stopped, the next started -- trip over each other.

``python tests/ftp_server.py ROOT PORT [list]``: serves ROOT on 127.0.0.1:PORT
(0 for any), user ``tester`` with password ``secret`` and anonymous; with
``list``, a server of the older kind that answers neither MLSD nor MLST.  It
prints the port it took, and serves until it is killed.
"""

from __future__ import annotations

import sys

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer


def main() -> None:
    root, port = sys.argv[1], int(sys.argv[2])
    authorizer = DummyAuthorizer()
    authorizer.add_user("tester", "secret", root, perm="elradfmwMT")
    authorizer.add_anonymous(root)

    class Handler(FTPHandler):
        banner = "test"
        auth_failed_timeout = 0

    Handler.authorizer = authorizer
    if len(sys.argv) > 3 and sys.argv[3] == "list":
        def refuse(self, path):
            self.respond("500 Command not understood.")
        Handler.ftp_MLSD = Handler.ftp_MLST = refuse
    server = FTPServer(("127.0.0.1", port), Handler)
    print(server.address[1], flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
