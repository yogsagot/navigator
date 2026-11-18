# Connections

How a panel is put on a server, and how the connections you use are kept. What each kind of place is, and the
other ways to reach one, are in [Places other than the disk](drives.md).

## The link manager

Each entry of *Utilities > Link*, such as *SSH (SFTP)* (`Alt+F11`), opens the connections kept for that protocol
on the left and the lines of one connection on the right.

- The box opens with the lines empty. Fill them in and press *Connect* for a connection that is not kept.
- Choose a connection under *Saved* to put it in the lines. A double click connects to it.
- *New* makes a kept connection, under a name you can type over. *Save* keeps what you changed; a changed
  connection is marked `*`, and leaving it asks whether to save. *Delete* removes the connection.
- *Connect* sends the active panel there. From *Utilities > Remote shell* it opens a shell in a window instead.

The lines are those of [a connection](#a-connection). Each remembers what it held before; `Down` on a line opens
its history.

The SSH manager has three more:

- *ssh options* are passed to `ssh` when a remote shell is opened.
- *Forwards* sets the connection's [port forwards](#port-forwards).
- *Copy key* puts one of your public keys on the server, so that later connections need no password.

The rclone manager's *Configure* runs `rclone config` to set remotes up.

## A connection

| Line | What it is |
|---|---|
| *Host* | The server's name or address. For SSH, a `Host` name from `~/.ssh/config` works, and what the file says fills in a login and a port left empty |
| *Login* | The user to connect as |
| *Port* | The port, when it is not the protocol's usual one |
| *Directory* | Where the panel starts on the server |
| *Name* | The name the connection is kept under |

The lines differ a little between protocols: an FTP connection has *Encrypt with TLS*, which makes it FTPS, and a
GVfs/KIO place has only a *Name* and a *URI*.

*Keep in the Link list* saves the connection under its name, to connect again in one step.

## Passwords and passphrases

A server's password, or the passphrase of a private key, is asked for when the connection needs one. *Save in
keyring* remembers it in the desktop's keyring, so it is not asked again. It is shown only where there is a
keyring to keep it in.

## An unknown host key

The first time you connect to an SSH server, its host key is not in `~/.ssh/known_hosts`, and you are asked
whether to go on, as `ssh` asks.

- *Accept* trusts the key for this connection only.
- *Save* also writes it to `~/.ssh/known_hosts`, so you are not asked again.
- *Cancel* does not connect.

Compare the fingerprint shown with one you got from the server's administrator before accepting.

## Port forwards

*Forwards* in the SSH manager lists the port forwards of a connection. *Add*, *Edit* and *Delete* change the
list, which is kept with the connection when you save it.

| Kind | What it does |
|---|---|
| *Local (-L)* | A port on this machine leads to the destination, reached from the server |
| *Remote (-R)* | A port on the server leads to the destination, reached from this machine |
| *Dynamic, SOCKS (-D)* | A port on this machine is a SOCKS proxy through the server |

*Listen address* and *Listen port* are the end that waits for connections, and *Destination host* and
*Destination port* where they are sent. A dynamic forward has no destination.

## Saved links

*Utilities > Saved links* lists the kept connections of every protocol in one box. *Connect* opens the one under
the cursor, *Edit* changes it, *Add* makes a new one and *Delete* removes it. The changes are kept when you leave
with *OK*.

*Utilities > Disconnect*, `Alt+H`, closes a connection; a panel that was showing it goes back to the disk.
