# 启动 Navigator

命令是 `nav`：

```sh
nav [LEFT] [RIGHT] [options]
```

`LEFT` 和 `RIGHT` 是两个面板打开时所在的目录。只给出一个时，两个面板都在那里打开；都不给出时，两个面板都在当前目录打开。二者都可以是磁盘以外某个位置的地址，例如 `sftp://user@host/dir`、`ftp://host/`、`smb://host/share` 或 `s3://s3.amazonaws.com/bucket`；参见[磁盘以外的位置](drives.md)。

命令行上给出的选项只对本次会话有效。它优先于[设置](settings.md)，并且永远不会写回设置。

## 文件和位置

| 选项 | 作用 |
|---|---|
| `-e FILE`、`--edit FILE` | 启动时在[编辑器](editor.md)中打开该文件。要打开多个文件就多次给出。尚不存在的名称在保存时创建 |
| `--config PATH` | 在 `~/.config/navigator/navigator.ini` 以外的另一个文件中读取和保存设置 |
| `--database PATH` | 把历史和书签保存在 `~/.local/state/navigator/navigator.db` 以外的另一个文件中 |
| `--version` | 显示版本以及安装的是哪一份 Navigator，然后退出 |

位于 `navigator.ini` 旁边的文件——[用户菜单和文件关联](user-menu.md)、键绑定、调色板——不会随 `--config` 移动：它们仍留在 `~/.config/navigator` 中。

## 颜色和字符

| 选项 | 作用 |
|---|---|
| `--theme NAME` | 使用另一种配色方案 |
| `--list-themes` | 显示所有配色方案的名称，然后退出 |
| `--palette dos` | 无论终端自身的配色方案如何，都按 DOS Navigator 的 VGA 显卡的样子显示每种颜色 |
| `--palette terminal` | 让十六种颜色使用终端自身的配色方案 |
| `--reprogram-palette` | 在 Navigator 运行期间把终端的十六种颜色设为 DOS 的颜色，适用于无法用其他方式设定颜色的终端 |
| `--colors DEPTH` | 终端能显示多少种颜色：`mono`、`8`、`16`、`256` 或 `truecolor`。`auto` 根据 `$COLORTERM` 和 `$TERM` 判断 |
| `--glyphs SET` | 终端字体能绘制哪些字符：`ascii` 用 `+` 和 `-` 绘制边框，`unicode` 绘制方框，`nerd` 为 Nerd Font 在每个文件名旁加上图标。`auto` 自动猜测 |
| `--marks LOOK` | 复选框和单选按钮的外观：`dos` 为 `[X]` 和 `(•)`，`brackets` 为 `[✓]` 和 `(●)`，`boxes` 不带括号 |
| `--charset NAME` | 非 UTF-8 终端的字符集，例如 `koi8-r`、`cp866` 或 `iso8859-2`。不给出时使用区域设置的字符集 |
| `--graphics HOW` | 查看器如何绘制图片：`kitty`、`sixel`，或 `none` 显示其字节。不给出时询问终端 |
| `--no-dim-modal` | 对话框后面的内容保持原色，而不是变暗；`--dim-modal` 重新打开变暗 |

[按键和颜色](customizing.md#颜色)中有关于主题的更多内容。

## 语言和方向

| 选项 | 作用 |
|---|---|
| `--language CODE` | 标题和消息的语言，例如 `lv`、`ru`、`ja` 或 `en`。不给出时使用设置中的 *语言*，否则使用 `$LANG` |
| `--direction auto` | 当语言从右向左书写（例如希伯来语或阿拉伯语）时镜像屏幕。不给出此选项时使用设置中的 *文字方向*，其初始值就是这一项 |
| `--direction rtl` | 无论何种语言都镜像屏幕，使其从右向左阅读 |
| `--direction ltr` | 从不镜像屏幕 |
| `--bidi app` | Navigator 在发送从右向左的文本之前自行排版。不给出此选项时会识别终端并选择正确的方式 |
| `--bidi words` | 每个从右向左的单词都反转后发送，适用于像 kitty 这样会再把它反转回来的终端 |

设置的[界面](settings.md#界面)页中有相同的选择。

## 出错时

| 选项 | 作用 |
|---|---|
| `--on-error dialog` | 意外错误会显示一个包含详细信息的对话框，可以继续使用 |
| `--on-error crash` | 意外错误会退出 Navigator 并显示详细信息 |

无论哪种方式，错误都会追加到数据库旁的 `errors.log` 中：即 `~/.local/state/navigator`，或 `--database` 指定的目录。设置的[系统](settings.md#系统)页中有相同的选择。

## 在 Navigator 内部

在 Navigator 自己的命令行上输入 `nav` 不会启动第二个副本：它会提示 Navigator 已在运行，并且按 `Ctrl+O` 即可回到其中。
