# Navigator の起動

コマンドは `nav` です。

```sh
nav [LEFT] [RIGHT] [options]
```

`LEFT` と `RIGHT` は、2 枚のパネルが開くディレクトリです。1 つだけ指定すると両方のパネルがそこで開き、何も指定しなければ
両方とも現在のディレクトリで開きます。どちらにも、`sftp://user@host/dir`、`ftp://host/`、`smb://host/share`、
`s3://s3.amazonaws.com/bucket` のようなディスク以外の場所のアドレスを指定できます。[ディスク以外の場所](drives.md)を参照してください。

コマンドラインで指定したオプションは、そのセッションに限って有効です。[設定](settings.md)より優先され、設定に書き戻されることはありません。

## ファイルと場所

| オプション | 動作 |
|---|---|
| `-e FILE`, `--edit FILE` | 起動時にファイルを[エディタ](editor.md)で開く。複数のファイルを開くには複数回指定する。まだない名前は保存したときに作られる |
| `--config PATH` | 設定を `~/.config/navigator/navigator.ini` ではなく別のファイルで読み書きする |
| `--database PATH` | 履歴とブックマークを `~/.local/state/navigator/navigator.db` ではなく別のファイルに保存する |
| `--version` | バージョンと、インストールされている Navigator のコピーを表示して終了する |

`navigator.ini` の隣にあるファイル ([ユーザーメニューとファイルの関連付け](user-menu.md)、キー割り当て、パレット) は
`--config` では移動せず、`~/.config/navigator` に残ります。

## 色と文字

| オプション | 動作 |
|---|---|
| `--theme NAME` | 別の配色を使う |
| `--list-themes` | 配色の名前を表示して終了する |
| `--palette dos` | 端末自身の配色にかかわらず、各色を DOS Navigator の VGA カードが表示したとおりに表示する |
| `--palette terminal` | 16 色を端末自身の配色に任せる |
| `--reprogram-palette` | Navigator の実行中、端末の 16 色を DOS の色に設定する。他の方法では色を指定できない端末向け |
| `--colors DEPTH` | 端末が表示できる色数: `mono`、`8`、`16`、`256`、`truecolor`。`auto` は `$COLORTERM` と `$TERM` で判断する |
| `--glyphs SET` | 端末のフォントが描ける文字: `ascii` は枠を `+` と `-` で描き、`unicode` は罫線で描き、`nerd` は Nerd Font 用に各ファイル名の横にアイコンを加える。`auto` は推測する |
| `--marks LOOK` | チェックボックスとラジオボタンの見た目: `dos` は `[X]` と `(•)`、`brackets` は `[✓]` と `(●)`、`boxes` は括弧なし |
| `--charset NAME` | UTF-8 でない端末の文字セット。`koi8-r`、`cp866`、`iso8859-2` など。指定しなければロケールのものを使う |
| `--graphics HOW` | ビューアが画像を描く方法: `kitty`、`sixel`、またはバイトを表示する `none`。指定しなければ端末に問い合わせる |
| `--no-dim-modal` | ダイアログボックスの背後を薄くせず、そのままの色で表示する。`--dim-modal` で元に戻す |

テーマについては[キーと色](customizing.md#色)に詳しくあります。

## 言語と方向

| オプション | 動作 |
|---|---|
| `--language CODE` | 表示文字列とメッセージの言語。`lv`、`ru`、`ja`、`en` など。指定しなければ設定の *言語* を、それもなければ `$LANG` を使う |
| `--direction auto` | ヘブライ語やアラビア語のように右から左へ書く言語のとき、画面を左右反転する。オプションを指定しなければ設定の *文字の方向* を使い、その初期値はこれ |
| `--direction rtl` | 言語にかかわらず画面を左右反転し、右から左へ読めるようにする |
| `--direction ltr` | 画面を左右反転しない |
| `--bidi app` | 右から左へのテキストを Navigator 自身がレイアウトしてから送る。オプションを指定しなければ端末を判別して適切な方法を選ぶ |
| `--bidi words` | 右から左への各単語を逆順にして送る。kitty のように再び反転する端末向け |

同じ選択肢は設定の[インターフェース](settings.md#インターフェース)ページにもあります。

## 問題が起きたとき

| オプション | 動作 |
|---|---|
| `--on-error dialog` | 予期しないエラーが起きると詳細をボックスに表示し、そのまま続けられる |
| `--on-error crash` | 予期しないエラーが起きると Navigator を終了し、詳細を表示する |

いずれの場合も、エラーはデータベースの隣の `errors.log` に追記されます。場所は `~/.local/state/navigator`、または `--database` で
指定したディレクトリです。設定の[システム](settings.md#システム)ページにも同じ選択肢があります。

## Navigator の中で

Navigator 自身のコマンドラインで `nav` と入力しても、2 つ目のコピーは起動しません。Navigator がすでに実行中であることと、
`Ctrl+O` でそこへ戻れることを知らせます。
