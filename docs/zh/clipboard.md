# 在 Navigator 中复制和粘贴

在终端程序中复制和粘贴，并不像看上去那么简单。Navigator 没有自己的窗口，因此不能像图形界面的编辑器那样直接与桌面的剪贴板交互。它有两种途径访问剪贴板：

- **计算机上安装的小型剪贴板工具**（X11 上是 `xclip` 或 `xsel`，Wayland 上是 `wl-clipboard`）。Navigator 把文本交给这个工具，由工具放到剪贴板上。这是可靠的方式。
- **你的终端。** Navigator 可以请终端把文本放到剪贴板上，或者把剪贴板内容读回来。有些终端会照做，有些会先询问你，有些则完全忽略这种请求。

此外，终端会为自己保留一些按键，所以在某个终端里能复制的键，在另一个终端里可能根本到不了 Navigator。本指南说明在什么情况下什么方法可用，以及如何设置才能让一切顺利工作。

## 快速入门

1. **安装剪贴板工具。** 先查看你运行的是哪种桌面会话：

   ```sh
   echo $XDG_SESSION_TYPE
   ```

   然后安装对应的工具：

   | 会话      | Debian、Ubuntu、Mint          | Fedora                         |
   |-----------|-------------------------------|--------------------------------|
   | `x11`     | `sudo apt install xclip`      | `sudo dnf install xclip`       |
   | `wayland` | `sudo apt install wl-clipboard` | `sudo dnf install wl-clipboard` |

   `xsel` 和 `xclip` 一样好用；只需安装其中一个。

2. **在编辑器中使用 Ctrl+C、Ctrl+X 和 Ctrl+V。** 在迄今测试过的所有终端中它们都能用。

3. **如果你使用 Ghostty**，把下面几行加到 `~/.config/ghostty/config`（或 `config.ghostty`）中，然后重启 Ghostty：

   ```
   keybind = ctrl+insert=unbind
   keybind = shift+insert=unbind
   ```

大多数人只需要这些。本指南的其余部分是背后的细节。在服务器上通过 ssh 运行 Navigator？请参见[通过 ssh 在远程服务器上](#通过-ssh-在远程服务器上)。

## 按键

按键取决于你在 Navigator 中所处的位置。

### 在编辑器中（F4）

| 操作                                       | 按键                                |
|--------------------------------------------|-------------------------------------|
| 复制                                       | **Ctrl+C**、Ctrl+Ins 或 Ctrl+Alt+C  |
| 剪切                                       | **Ctrl+X**、Shift+Del 或 Ctrl+Alt+X |
| 粘贴                                       | **Ctrl+V**、Shift+Ins 或 Ctrl+Alt+V |
| 删除标记的块而不复制                       | Ctrl+Del                            |

这四项也位于 **编辑器** 菜单的顶部（编辑器处于活动状态时，该菜单在菜单栏上）。

复制和剪切作用于标记的块。要标记块，可以按住 Shift 移动光标，或用鼠标拖动。

之所以有三组按键，是因为没有哪一组在所有地方都能用：

- **Ctrl+Ins / Shift+Del / Shift+Ins** 是 DOS Navigator 原来的按键。有些终端把 Ctrl+Ins 和 Shift+Ins 留给自己用（参见[终端说明](#终端说明)）。
- **Ctrl+C / Ctrl+X / Ctrl+V** 是其他所有程序都使用的按键。
- **Ctrl+Alt+C / Ctrl+Alt+X / Ctrl+Alt+V** 是备用的一组，以防你的终端或桌面占用了另外两组。

> **从 DOS Navigator 转过来？** 它的编辑器把 Ctrl+C、Ctrl+X 和 Ctrl+V 用作向下翻页、光标下移以及插入/改写切换（WordStar 按键）。Navigator 则把它们用于剪贴板。PgDn、Down 和 Ins 仍然执行那些功能。其他 WordStar 按键（Ctrl+K…、Ctrl+Q…、Ctrl+E、Ctrl+S 等）默认也没有绑定；从 选项 > 配置 > 按键绑定 > 加载 中加载 `keybindings_wordstar.ini` 可以找回它们，加载 `keybindings_dn151.ini` 还能连 DN 的 Ctrl+C/X/V 一起找回。

### 在对话框输入行和命令行中

| 操作  | 按键                                                                                                 |
|-------|------------------------------------------------------------------------------------------------------|
| 复制  | Ctrl+Ins：复制选中的内容，没有选中时复制整行。Ctrl+C 复制选中的内容。                               |
| 剪切  | Shift+Del                                                                                            |
| 粘贴  | Shift+Ins 或 Ctrl+V                                                                                  |

要在行中选择文字，可以按住 Shift 移动光标，或用鼠标拖动。

在面板下方的命令行上，**Ctrl+E 和 Ctrl+X 在命令历史中向后和向前翻阅**，所以在那里 Ctrl+X 不是剪切。

### 在控制台中（Ctrl+O）

用鼠标拖动选择文字，或双击一个词。然后：

| 操作  | 按键                                                                    |
|-------|-------------------------------------------------------------------------|
| 复制  | Ctrl+Ins，或者在没有程序运行时按 Ctrl+C                                 |
| 粘贴  | 终端自己的粘贴键（通常是 Ctrl+Shift+V），或者鼠标中键单击               |

控制台中有程序运行时，Ctrl+C 会如你所料地发给那个程序（通常是让它停止）。粘贴的文字也会发给正在运行的程序。

### 其他复制方式

- **计算器**：*复制* 按钮（经典界面）和 *计算器 > 复制*（所有界面）把结果放到剪贴板上。
- **屏幕抓取**（Alt+Shift+Ins）：用方向键和 Shift+方向键移动区域、调整大小，然后按 Enter 把屏幕的那一部分作为文本复制——或者用鼠标拖出区域，松开时就会复制。Esc 或右键单击则不复制而离开。
- **列求和**（在编辑器中按 Alt+Ins，需开启纵向块）：把标记的列中的数字加起来，并把总和放到剪贴板上。

## 鼠标与主选区

在 Linux 上实际有两个剪贴板：

- **剪贴板**，由“复制”填入，由“粘贴”读取；
- **主选区**，只要选中文字就会填入，用鼠标中键粘贴。

Navigator 遵循同样的约定。在编辑器、控制台或输入行中拖过文字时，这些文字就成为主选区，**鼠标中键单击** 粘贴主选区。**双击** 选中一个词。

由于 Navigator 自己使用鼠标，在 Navigator 运行时无法使用终端自身的鼠标选择。如果仍想使用它（以终端的方式选择文字，或打开终端的右键菜单），请在拖动或单击时 **按住 Shift**。这在大多数终端中有效。

## 终端自身的粘贴

你的终端有自己的粘贴键，通常是 **Ctrl+Shift+V**，菜单中也有“粘贴”一项。这种粘贴由终端完成：它把桌面剪贴板的内容像你亲手键入一样输入 Navigator。无论 Navigator 如何设置、是否安装了剪贴板工具，它都能用。

这就是为什么粘贴在其他程序中复制的文字可能一切正常，而从 Navigator *向外* 复制却不行：前一个方向是终端的事，后一个方向是 Navigator 的事。

## “使用系统剪贴板”设置

**选项 > 配置 > 系统设置 > 使用系统剪贴板**

- **开启**（默认）：复制把文字放到桌面的剪贴板上，其他程序可以粘贴；粘贴读取桌面的剪贴板。
- **关闭**：Navigator 像 DOS Navigator 那样使用自己私有的剪贴板。复制的内容不会离开 Navigator。终端自身的粘贴（Ctrl+Shift+V）仍会把桌面剪贴板中的内容带进来。

无论如何设置，Navigator 总会保留你最后一次复制内容的副本。

## 终端说明

有些终端会在 Navigator 收到之前把某些按键留给自己，而且它们在是否允许程序使用剪贴板这一点上也各不相同。

| 终端                                      | 自己占用的按键                                | 是否允许 Navigator 使用剪贴板    | 怎么办                                   |
|-------------------------------------------|-----------------------------------------------|----------------------------------|------------------------------------------|
| **Ghostty**                               | Ctrl+Ins、Shift+Ins、Shift+PgUp/PgDn/Home/End | 复制：允许。粘贴：先询问你       | 解除这些键的绑定（见下文）               |
| **xfce4-terminal、GNOME Terminal、Tilix** | Ctrl+Ins、Shift+Ins（无法更改）               | 否                               | 安装剪贴板工具；使用 Ctrl+C/X/V          |
| **PyCharm 及其他 JetBrains 终端**         | –                                             | 否                               | 安装剪贴板工具                           |

### Ghostty

默认情况下，Ghostty 用 **Ctrl+Ins** 复制它自己的选区，用 **Shift+Ins** 粘贴主选区，因此这两个键永远到不了 Navigator。它还用 Shift+PgUp、Shift+PgDn、Shift+Home 和 Shift+End 滚动，而编辑器需要这些键来标记文字。把下面几行加到 Ghostty 的配置文件中，然后重启 Ghostty（关闭所有窗口；只开新标签页不够）：

```
keybind = ctrl+insert=unbind
keybind = shift+insert=unbind
keybind = shift+page_up=unbind
keybind = shift+page_down=unbind
keybind = shift+home=unbind
keybind = shift+end=unbind
```

在 Ghostty 本身中，仍可以用 Ctrl+Shift+C 和 Ctrl+Shift+V 复制和粘贴。

在程序 *读取* 剪贴板之前，Ghostty 会请求许可。如果你没有安装剪贴板工具，Navigator 不会等待你的回答，而是粘贴它自己最后一次复制的内容。要让 Navigator 不经询问就能读取剪贴板，请添加：

```
clipboard-read = allow
```

要查看 Ghostty 绑定了哪些键，请运行 `ghostty +list-keybinds --default`。

### xfce4-terminal、GNOME Terminal、Tilix

这些终端都基于同一个库（VTE），它自己处理 **Ctrl+Ins**（复制）和 **Shift+Ins**（粘贴主选区）。没有任何设置能把这两个键交还给程序，所以请改用 **Ctrl+C / Ctrl+X / Ctrl+V**（或 Ctrl+Alt+C / X / V）。

它们还会忽略程序使用剪贴板的请求，因此要从 Navigator 向外复制，**必须安装剪贴板工具**。

在 **xfce4-terminal** 中，还要打开 *Edit > Preferences > Advanced*，开启 **Disable all menu access keys** 和 **Disable menu shortcut key**。否则终端会在 Alt+E、Alt+F、Alt+V、Alt+T、Alt+B、Alt+H 和 F10 上打开它自己的菜单，而这些键 Navigator 都要用。这与剪贴板无关，但却是你接下来会碰到的问题。

### PyCharm 及其他 JetBrains IDE

内置终端会忽略程序使用剪贴板的请求，所以请安装剪贴板工具。关闭 *使用系统剪贴板* 时，在 Navigator 内部复制和粘贴不需要剪贴板工具也能工作。

## 没有剪贴板工具时

没有安装剪贴板工具时，Navigator 仍然可以工作：

- **在 Navigator 内部** 复制和粘贴可以正常使用。无法读取桌面剪贴板时，Navigator 粘贴它自己最后一次复制的内容。第一次出现这种情况时，会有一条消息建议安装剪贴板工具。
- 从 **Navigator 向外** 复制到其他程序，只有在终端接受请求时才能成功（Ghostty 接受；xfce4-terminal、GNOME Terminal 和 PyCharm 不接受）。
- 从其他程序 **向 Navigator 内** 粘贴，用终端自己的粘贴键（Ctrl+Shift+V）总能成功。

问题在于，这时 Navigator 的粘贴可能粘贴的是 *你最后在 Navigator 中复制的内容*，而不是此后在其他程序中复制的内容。

## 通过 ssh 在远程服务器上

通过 ssh 在另一台机器上运行 Navigator 时，Navigator 运行在 *那台机器* 上，但你想用的剪贴板在 *你自己的* 计算机上。服务器上的剪贴板工具本身帮不上忙：服务器没有桌面，那里的 `xclip` 无处存放文字。有三种方式可以弥合这个差距，并且可以同时使用多种。

**在 Navigator 内部复制和粘贴总能工作**，无论你如何设置。无法访问你计算机上的剪贴板时，Navigator 粘贴它自己最后一次复制的内容。

### 粘贴进来：终端的粘贴键

终端自己的粘贴（通常是 **Ctrl+Shift+V**，或其菜单）把你本地的剪贴板内容输入 ssh 会话。它不需要任何设置，是从你的计算机带入文字的最快方式，因为不需要往回传送任何东西去获取内容。只有在 Navigator 内部复制的文字才需要用 Navigator 自己的粘贴键。

### 复制出去：终端（OSC 52）

Navigator 请你的本地终端把复制的文字放到你的剪贴板上，所用的终端功能叫做 OSC 52。这个请求像其他输出一样沿着 ssh 连接传过来，因此在服务器上什么都不需要。它能否工作取决于你的 **本地** 终端：

| 终端                                      | 向外复制                                         |
|-------------------------------------------|--------------------------------------------------|
| Ghostty、WezTerm、foot                    | 可用                                             |
| kitty                                     | 可用（`clipboard_control` 必须允许 `write-clipboard`，默认即如此） |
| Alacritty                                 | 可用（`[terminal]` 中的 `osc52` 不能为 `Disabled`） |
| xfce4-terminal、GNOME Terminal、Tilix     | 不支持；请使用 X11 转发（见下文）                |
| PyCharm 及其他 JetBrains 终端             | 不支持                                           |

要在不运行 Navigator 的情况下测试你的终端，请在服务器上运行下面的命令，然后在你的计算机上粘贴：

```sh
printf '\e]52;c;%s\a' "$(printf hello | base64)"
```

如果粘贴出 `hello`，那么从 Navigator 向外复制也能工作。如果没有，说明你的终端忽略 OSC 52。

OSC 52 也能 *读取* 剪贴板，但大多数终端会拒绝或先询问你，所以要粘贴进来，请使用终端的粘贴键。

### 双向：X11 转发

ssh 可以把服务器上的 X11 连接转发回你的计算机。这样服务器会得到一个通向你桌面的 `DISPLAY`，服务器上 Navigator 的剪贴板工具就能访问 **你的** 剪贴板，复制和粘贴都可以，不论你的终端支持什么。

你需要：

- **在你的计算机上**：一个 X 服务器。任何 X11 桌面都有；在 Wayland 上，XWayland 可以胜任，并且与 Wayland 程序共享剪贴板。
- **在服务器上**：`xclip`（或 `xsel`）和 `xauth`（`sudo apt install xclip xauth`，或 `sudo dnf install xclip
  xorg-x11-xauth`），以及 `/etc/ssh/sshd_config` 中的 `X11Forwarding yes`，大多数发行版已经设置好了。可以用 `sudo sshd -T | grep -i x11forwarding` 检查。

然后用 **`-Y`** 连接：

```sh
ssh -Y user@server
```

第一次连接时，你可能会看到 `/usr/bin/xauth: file /home/user/.Xauthority does not exist`。这无关紧要：`xauth` 会创建该文件，这条消息不会再出现。要检查是否生效：

```sh
echo $DISPLAY                            # something like localhost:10.0
echo hello | xclip -selection clipboard  # then paste on your computer
```

在同一个会话中启动 Navigator，并开启 *使用系统剪贴板*。要在每次连接该服务器时都转发 X11，请把下面的内容加到你计算机上的 `~/.ssh/config` 中：

```
Host server
    ForwardX11 yes
    ForwardX11Trusted yes
```

需要注意的事项：

- **安全。** `-Y` 让服务器信任你的 X 会话：在你连接期间，服务器上的程序，或那里任何拥有 root 权限的人，都能读取你的按键、屏幕和剪贴板。只对你信任的服务器使用它。普通的 `-X` 会限制服务器，但这种限制也可能使 `xclip` 无法读取你的剪贴板，从而导致粘贴失败。
- **粘贴有短暂延迟。** Navigator 每次粘贴都会在服务器上启动 `xclip`，它通过网络获取你的剪贴板内容。经由互联网时，几百毫秒是正常的。终端的粘贴键可以避免这一往返。如果获取超过 2 秒，Navigator 会放弃，改为粘贴它自己最后一次复制的内容。
- **断开连接后，复制的内容可能消失。** `xclip` 是从服务器上提供复制的文字的，所以如果断开后还需要，请在退出登录前把它粘贴到你计算机上的某个地方。

### 在 tmux 或 screen 中

在 **tmux** 中，要让 tmux 把 OSC 52 复制请求转给你的终端，请把下面一行加到 `~/.tmux.conf` 中：

```
set -g set-clipboard on
```

只要 tmux 会话是从开启了转发的 ssh 会话中启动的，X11 转发在 tmux 中就能工作。更早创建的会话，或从新连接重新接入的会话，会保留旧的 `DISPLAY`。在那里用新值运行 `export DISPLAY=...`，或在新的 tmux 窗口中启动 Navigator。

如果某个终端在你复制时打印出乱码，可以用 `NAVKIT_CLIPBOARD=off nav` 启动 Navigator，关闭经由终端的途径。

## 故障排除

**复制没有反应，或者文字没有到达其他程序。**
没有安装剪贴板工具，而你的终端又忽略了 Navigator 的请求。请安装 `xclip` 或 `wl-clipboard`（参见[快速入门](#快速入门)）。

**粘贴出来的是旧文字，而不是我刚在其他程序中复制的内容。**
Navigator 无法读取桌面剪贴板，于是使用了它自己最后一次复制的内容。请安装剪贴板工具。在 Ghostty 中也可以设置 `clipboard-read = allow`。在此之前，请使用终端的粘贴键（Ctrl+Shift+V）。

**Shift+Ins 粘贴的内容与 Ctrl+V 不同。**
你的终端截获了 Shift+Ins，粘贴的是 *主选区*（你在任何地方最后高亮选中的文字），而不是剪贴板。在 Ghostty 中，按上文所示解除绑定。在 xfce4-terminal 和 GNOME Terminal 中，请使用 Ctrl+V。

**某个键完全没有反应。**
很可能是你的终端或桌面占用了这个键。在 Navigator 的源码检出目录中，可以查看实际收到的是什么：

```sh
./venv/bin/python tools/keyprobe.py
```

按下这个键。如果什么都没打印，说明终端把它占用了。按两次 `q` 退出。请使用上面列出的其他按键，或绑定你自己的按键（见下一节）。

**通过 ssh 时，复制的文字始终到不了我的计算机。**
服务器没有桌面，而你的本地终端忽略 OSC 52。请使用 X11 转发（`ssh -Y`），或使用支持 OSC 52 的终端；参见[通过 ssh 在远程服务器上](#通过-ssh-在远程服务器上)。

**通过 ssh 时，粘贴要等一会儿。**
使用 X11 转发时，每次粘贴都要通过网络获取你的剪贴板内容。对于来自你计算机的文字，请使用终端的粘贴键（Ctrl+Shift+V）；它不需要往返。

**在一个终端里能用，在另一个终端里却不行。**
这在意料之中。请在[终端说明](#终端说明)中查看那个终端。

## 更改按键

每个按键都可以在 **选项 > 配置 > 按键绑定** 中，或在 `~/.config/navigator/keybindings.ini` 中自行更改。一个命令可以有多个键，用逗号分隔：

```ini
clipboard_cut = shift+delete, ctrl+x, ctrl+alt+x
clipboard_copy = ctrl+insert, ctrl+c, ctrl+alt+c
clipboard_paste = shift+insert, ctrl+v, ctrl+alt+v
```

在同一个位置，一个键只能属于一个命令。要在编辑器中把 Ctrl+C 分给别的命令，请先把它从 `clipboard_copy` 中去掉。

Navigator 第一次启动时会把所有默认值写入该文件，此后保留其中所写的内容。如果你的文件比某次默认值的更改还旧，它会保留你原来的按键。在按键绑定对话框中选中该命令，按 **默认** 即可采用新的按键。
