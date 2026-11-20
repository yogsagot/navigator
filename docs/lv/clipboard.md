# Kopēšana un ielīmēšana Navigator

Kopēšana un ielīmēšana termināļa programmā nav tik vienkārša, kā izskatās. Navigator nepieder savs logs, tāpēc tas
nevar sazināties ar darbvirsmas starpliktuvi tieši, kā to var grafisks redaktors. Tam ir divi ceļi, kā to sasniegt:

- **Neliels starpliktuves rīks**, kas instalēts jūsu datorā (`xclip` vai `xsel` X11 vidē, `wl-clipboard` Wayland
  vidē). Navigator nodod tekstu rīkam, un rīks to ieliek starpliktuvē. Tas ir uzticamais ceļš.
- **Jūsu terminālis.** Navigator var palūgt terminālim ielikt tekstu starpliktuvē vai nolasīt to atpakaļ. Daži
  termināļi to dara, daži vispirms pajautā jums, bet daži šo pieprasījumu pilnībā ignorē.

Turklāt termināļi dažus taustiņus patur sev, tāpēc taustiņš, kas vienā terminālī kopē, citā var nekad nenonākt līdz
Navigator. Šī rokasgrāmata izskaidro, kas kur darbojas un kā visu iestatīt, lai viss vienkārši darbotos.

## Ātrais sākums

1. **Instalējiet starpliktuves rīku.** Noskaidrojiet, kāda veida darbvirsmas sesija jums darbojas:

   ```sh
   echo $XDG_SESSION_TYPE
   ```

   Tad instalējiet tai atbilstošo rīku:

   | Sesija    | Debian, Ubuntu, Mint          | Fedora                         |
   |-----------|-------------------------------|--------------------------------|
   | `x11`     | `sudo apt install xclip`      | `sudo dnf install xclip`       |
   | `wayland` | `sudo apt install wl-clipboard` | `sudo dnf install wl-clipboard` |

   `xsel` der tikpat labi kā `xclip`; vajag tikai vienu no tiem.

2. **Redaktorā lietojiet Ctrl+C, Ctrl+X un Ctrl+V.** Tie darbojas visos līdz šim pārbaudītajos termināļos.

3. **Ja lietojat Ghostty**, pievienojiet šīs rindas failam `~/.config/ghostty/config` (vai `config.ghostty`) un
   palaidiet Ghostty no jauna:

   ```
   keybind = ctrl+insert=unbind
   keybind = shift+insert=unbind
   ```

Ar to pietiek lielākajai daļai lietotāju. Pārējā rokasgrāmatas daļa ir sīkāka informācija par to, kas aiz tā slēpjas.
Darbināt Navigator serverī caur ssh? Skatiet [Attālā serverī caur ssh](#attālā-serverī-caur-ssh).

## Taustiņi

Taustiņi ir atkarīgi no tā, kur Navigator atrodaties.

### Redaktorā (F4)

| Lai                                        | Spiediet                            |
|--------------------------------------------|-------------------------------------|
| Kopētu                                     | **Ctrl+C**, Ctrl+Ins vai Ctrl+Alt+C |
| Izgrieztu                                  | **Ctrl+X**, Shift+Del vai Ctrl+Alt+X |
| Ielīmētu                                   | **Ctrl+V**, Shift+Ins vai Ctrl+Alt+V |
| Dzēstu iezīmēto bloku, to nenokopējot      | Ctrl+Del                            |

Visi četri ir arī izvēlnes **Redaktors** augšā (izvēlņu joslā, kamēr redaktors ir aktīvs).

Kopēšana un izgriešana darbojas ar iezīmēto bloku. Lai iezīmētu bloku, turiet nospiestu Shift, pārvietojot kursoru,
vai velciet ar peli.

Taustiņu komplekti ir trīs, jo neviens komplekts nedarbojas visur:

- **Ctrl+Ins / Shift+Del / Shift+Ins** ir oriģinālie DOS Navigator taustiņi. Daži termināļi Ctrl+Ins un Shift+Ins
  patur sev (skatiet [Piezīmes par termināļiem](#piezīmes-par-termināļiem)).
- **Ctrl+C / Ctrl+X / Ctrl+V** ir taustiņi, ko lieto visas pārējās programmas.
- **Ctrl+Alt+C / Ctrl+Alt+X / Ctrl+Alt+V** ir rezerves komplekts gadījumam, ja jūsu terminālis vai darbvirsma
  aizņem abus pārējos.

> **Nākat no DOS Navigator?** Tā redaktors lietoja Ctrl+C, Ctrl+X un Ctrl+V, lai pārvietotos lapu uz leju, kursoru
> uz leju un pārslēgtu ievietošanas/pārrakstīšanas režīmu (WordStar taustiņi). Navigator tos tā vietā lieto
> starpliktuvei. PgDn, Down un Ins joprojām dara šos darbus. Arī pārējie WordStar taustiņi (Ctrl+K…, Ctrl+Q…, Ctrl+E,
> Ctrl+S un tā tālāk) pēc noklusējuma nav piesaistīti; ielādējiet `keybindings_wordstar.ini` no Iestatījumi >
> Konfigurācija > Taustiņu piesaiste > Ielādēt, lai tos atgūtu, vai `keybindings_dn151.ini`, lai atgūtu arī DN
> Ctrl+C/X/V.

### Dialogu ievades rindās un komandrindā

| Lai      | Spiediet                                                                                                  |
|----------|-----------------------------------------------------------------------------------------------------------|
| Kopētu   | Ctrl+Ins: kopē atlasi vai visu rindu, ja nekas nav atlasīts. Ctrl+C kopē atlasi.                           |
| Izgrieztu | Shift+Del                                                                                                |
| Ielīmētu | Shift+Ins vai Ctrl+V                                                                                      |

Lai atlasītu tekstu rindā, turiet nospiestu Shift un pārvietojiet kursoru vai velciet ar peli.

Komandrindā zem paneļiem **Ctrl+E un Ctrl+X pārvietojas atpakaļ un uz priekšu pa komandu vēsturi**, tāpēc tur
Ctrl+X neizgriež.

### Konsolē (Ctrl+O)

Atlasiet tekstu, velkot ar peli, vai veiciet dubultklikšķi uz vārda. Tad:

| Lai      | Spiediet                                                                        |
|----------|---------------------------------------------------------------------------------|
| Kopētu   | Ctrl+Ins vai Ctrl+C, kad nedarbojas neviena programma                           |
| Ielīmētu | Jūsu termināļa paša ielīmēšanas taustiņš (parasti Ctrl+Shift+V) vai vidējais klikšķis |

Kad konsolē darbojas programma, Ctrl+C nonāk pie šīs programmas (parasti, lai to apturētu), kā jau gaidāms. Arī
ielīmētais teksts nonāk pie darbojošās programmas.

### Citi kopēšanas veidi

- **Kalkulators**: poga *Kopēt* (Classic) un *Kalkulators > Kopēt* (visos veidos) ieliek rezultātu starpliktuvē.
- **Ekrāna tvērējs** (Alt+Shift+Ins): pārvietojiet apgabalu un mainiet tā izmēru ar bultiņām un Shift+bultiņām, tad
  nospiediet Enter, lai nokopētu šo ekrāna daļu kā tekstu -- vai izvelciet apgabalu ar peli, un tas tiek nokopēts,
  kad pogu atlaižat. Esc vai labais klikšķis iziet, neko nenokopējot.
- **Kolonnas summa** (Alt+Ins redaktorā, ar ieslēgtiem vertikālajiem blokiem): saskaita iezīmētās kolonnas skaitļus
  un ieliek kopsummu starpliktuvē.

## Pele un primārā atlase

Linux sistēmā patiesībā ir divas starpliktuves:

- **starpliktuve**, ko aizpilda kopēšana un nolasa ielīmēšana;
- **primārā atlase**, ko aizpilda jau pati teksta atlasīšana un ielīmē ar peles vidējo pogu.

Navigator ievēro to pašu konvenciju. Kad velkat pāri tekstam redaktorā, konsolē vai ievades rindā, tas kļūst par
primāro atlasi, un **vidējais klikšķis** ielīmē primāro atlasi. **Dubultklikšķis** atlasa vārdu.

Tā kā Navigator peli lieto pats, jūsu termināļa paša peles atlase, kamēr Navigator darbojas, nav pieejama. Lai to
tomēr izmantotu (lai atlasītu tekstu termināļa veidā vai piekļūtu tā labā klikšķa izvēlnei), velkot vai klikšķinot
**turiet nospiestu Shift**. Tas darbojas vairumā termināļu.

## Termināļa paša ielīmēšana

Jūsu terminālim ir savs ielīmēšanas taustiņš, parasti **Ctrl+Shift+V**, un vienums Paste tā izvēlnē. Šo ielīmēšanu
veic terminālis: tas ieraksta darbvirsmas starpliktuves saturu Navigator tā, it kā jūs to būtu ierakstījis. Tas
darbojas neatkarīgi no Navigator iestatījumiem un no tā, vai starpliktuves rīks ir instalēts.

Tāpēc citā programmā nokopēta teksta ielīmēšana var darboties lieliski, kamēr kopēšana *no* Navigator nedarbojas:
pirmais virziens ir termināļa darbs, otrais ir Navigator darbs.

## Iestatījums "Sistēmas starpliktuve"

**Iestatījumi > Konfigurācija > Sistēmas iestatīšana > Sistēmas starpliktuve**

- **Ieslēgts** (pēc noklusējuma): kopēšana ieliek tekstu jūsu darbvirsmas starpliktuvē, lai citas programmas to
  varētu ielīmēt, un ielīmēšana nolasa darbvirsmas starpliktuvi.
- **Izslēgts**: Navigator tur savu privātu starpliktuvi, kā to darīja DOS Navigator. Nekas no nokopētā neatstāj
  Navigator. Jūsu termināļa paša ielīmēšana (Ctrl+Shift+V) joprojām ienes visu, kas ir darbvirsmas starpliktuvē.

Navigator vienmēr patur pats savu kopiju no pēdējā, ko nokopējāt, lai kā šis iestatījums būtu iestatīts.

## Piezīmes par termināļiem

Daži termināļi patur taustiņus sev, pirms Navigator tos vispār ierauga, un tie atšķiras ar to, vai ļauj programmai
lietot starpliktuvi.

| Terminālis                                | Patur sev                                     | Ļauj Navigator lietot starpliktuvi | Ko darīt                                  |
|-------------------------------------------|-----------------------------------------------|------------------------------------|-------------------------------------------|
| **Ghostty**                               | Ctrl+Ins, Shift+Ins, Shift+PgUp/PgDn/Home/End | Kopēt: jā. Ielīmēt: vispirms jautā | Atsaistiet taustiņus (zemāk)              |
| **xfce4-terminal, GNOME Terminal, Tilix** | Ctrl+Ins, Shift+Ins (nevar mainīt)            | Nē                                 | Instalējiet starpliktuves rīku; lietojiet Ctrl+C/X/V |
| **PyCharm un citi JetBrains termināļi**   | –                                             | Nē                                 | Instalējiet starpliktuves rīku            |

### Ghostty

Pēc noklusējuma Ghostty lieto **Ctrl+Ins**, lai kopētu savu atlasi, un **Shift+Ins**, lai ielīmētu primāro
atlasi, tāpēc šie taustiņi nekad nenonāk līdz Navigator. Tas arī lieto Shift+PgUp, Shift+PgDn, Shift+Home un
Shift+End ritināšanai, bet redaktoram tie vajadzīgi teksta iezīmēšanai. Pievienojiet šo Ghostty konfigurācijas
failam un palaidiet Ghostty no jauna (aizveriet visus logus; ar jaunu cilni nepietiek):

```
keybind = ctrl+insert=unbind
keybind = shift+insert=unbind
keybind = shift+page_up=unbind
keybind = shift+page_down=unbind
keybind = shift+home=unbind
keybind = shift+end=unbind
```

Pašā Ghostty joprojām var kopēt un ielīmēt ar Ctrl+Shift+C un Ctrl+Shift+V.

Ghostty prasa atļauju, pirms programma drīkst *nolasīt* starpliktuvi. Ja jums nav instalēts starpliktuves rīks,
Navigator negaida jūsu atbildi, bet tā vietā ielīmē savu pēdējo kopiju. Lai ļautu Navigator nolasīt starpliktuvi
bez jautāšanas, pievienojiet:

```
clipboard-read = allow
```

Lai redzētu, kurus taustiņus Ghostty piesaista, palaidiet `ghostty +list-keybinds --default`.

### xfce4-terminal, GNOME Terminal, Tilix

Visi šie termināļi ir veidoti uz vienas un tās pašas bibliotēkas (VTE), kas pati apstrādā **Ctrl+Ins** (kopēt) un
**Shift+Ins** (ielīmēt primāro atlasi). Nav iestatījuma, kas šos taustiņus atdotu atpakaļ, tāpēc to vietā lietojiet
**Ctrl+C / Ctrl+X / Ctrl+V** (vai Ctrl+Alt+C / X / V).

Tie arī ignorē programmas pieprasījumus lietot starpliktuvi, tāpēc kopēšanai no Navigator **starpliktuves rīks ir
obligāts**.

Terminālī **xfce4-terminal** atveriet arī *Edit > Preferences > Advanced* un ieslēdziet **Disable all menu access
keys** un **Disable menu shortcut key**. Citādi terminālis atver savas izvēlnes ar Alt+E, Alt+F, Alt+V, Alt+T,
Alt+B, Alt+H un F10, ko lieto Navigator. Ar starpliktuvi tam nav nekāda sakara, taču tā ir nākamā lieta, ar ko jūs
saskartos.

### PyCharm un citas JetBrains IDE

Iebūvētais terminālis ignorē programmas pieprasījumus lietot starpliktuvi, tāpēc instalējiet starpliktuves rīku. Ja
*Sistēmas starpliktuve* ir izslēgta, kopēšana un ielīmēšana Navigator iekšienē darbojas arī bez tā.

## Bez starpliktuves rīka

Navigator darbojas arī tad, ja starpliktuves rīks nav instalēts:

- Kopēšana un ielīmēšana **Navigator iekšienē** darbojas. Kad darbvirsmas starpliktuvi nevar nolasīt, Navigator
  ielīmē savu pēdējo kopiju. Pirmajā reizē, kad tā notiek, ziņojums iesaka instalēt starpliktuves rīku.
- Kopēšana **no Navigator** uz citām programmām darbojas tikai tad, ja jūsu terminālis pieņem pieprasījumu (Ghostty
  pieņem; xfce4-terminal, GNOME Terminal un PyCharm ne).
- Ielīmēšana **Navigator** no citām programmām vienmēr darbojas ar jūsu termināļa paša ielīmēšanas taustiņu
  (Ctrl+Shift+V).

Āķis ir tāds, ka Navigator ielīmēšana tad var ielīmēt to, *ko pēdējo nokopējāt Navigator*, nevis to, ko kopš tā
laika nokopējāt citā programmā.

## Attālā serverī caur ssh

Kad darbināt Navigator citā datorā caur ssh, Navigator darbojas *tur*, bet vajadzīgā starpliktuve ir *jūsu* datorā.
Starpliktuves rīks serverī viens pats palīdzēt nevar: serverim nav darbvirsmas, tāpēc `xclip` tur nav kur likt
tekstu. Ir trīs veidi, kā šo plaisu pārvarēt, un var lietot vairākus.

**Kopēšana un ielīmēšana Navigator iekšienē darbojas vienmēr**, lai ko jūs iestatītu. Kad jūsu datora starpliktuvei
nevar piekļūt, Navigator ielīmē savu pēdējo kopiju.

### Ielīmēšana: termināļa ielīmēšanas taustiņš

Jūsu termināļa paša ielīmēšana (parasti **Ctrl+Shift+V** vai tā izvēlne) ieraksta jūsu lokālās starpliktuves saturu
ssh sesijā. Tai nekas nav jāiestata, un tas ir ātrākais veids, kā ienest tekstu no jūsu datora, jo nekam nav
jāceļo atpakaļ, lai to paņemtu. Navigator paša ielīmēšanas taustiņi vajadzīgi tikai tekstam, ko nokopējāt Navigator
iekšienē.

### Kopēšana ārā: jūsu terminālis (OSC 52)

Navigator lūdz jūsu lokālo termināli ielikt nokopēto tekstu jūsu starpliktuvē, izmantojot termināļa iespēju OSC 52.
Pieprasījums ceļo pa ssh savienojumu tāpat kā jebkura cita izvade, tāpēc serverī tam nekas nav vajadzīgs. Vai tas
darbojas, atkarīgs no jūsu **lokālā** termināļa:

| Terminālis                                | Kopēšana ārā                                     |
|-------------------------------------------|--------------------------------------------------|
| Ghostty, WezTerm, foot                    | Darbojas                                         |
| kitty                                     | Darbojas (`clipboard_control` jāatļauj `write-clipboard`, kā tas ir pēc noklusējuma) |
| Alacritty                                 | Darbojas (`osc52` sadaļā `[terminal]` nedrīkst būt `Disabled`) |
| xfce4-terminal, GNOME Terminal, Tilix     | Netiek atbalstīts; lietojiet X11 pāradresāciju (zemāk) |
| PyCharm un citi JetBrains termināļi       | Netiek atbalstīts                                |

Lai pārbaudītu savu termināli bez Navigator, palaidiet šo serverī un tad ielīmējiet savā datorā:

```sh
printf '\e]52;c;%s\a' "$(printf hello | base64)"
```

Ja `hello` atnāk, kopēšana no Navigator arī darbojas. Ja ne, jūsu terminālis ignorē OSC 52.

OSC 52 var arī *nolasīt* starpliktuvi, taču vairums termināļu atsakās vai vispirms pajautā jums, tāpēc ielīmēšanai
lietojiet termināļa ielīmēšanas taustiņu.

### Abos virzienos: X11 pāradresācija

ssh var pārnest X11 savienojumus no servera atpakaļ uz jūsu datoru. Tad serveris saņem `DISPLAY`, kas ved uz jūsu
darbvirsmu, un Navigator starpliktuves rīks serverī sasniedz **jūsu** starpliktuvi gan kopēšanai, gan ielīmēšanai,
lai ko atbalstītu jūsu terminālis.

Vajadzīgs:

- **Jūsu datorā**: X serveris. Tāds ir jebkurai X11 darbvirsmai; Wayland vidē šo darbu veic XWayland, un tas dala
  starpliktuvi ar Wayland programmām.
- **Serverī**: `xclip` (vai `xsel`) un `xauth` (`sudo apt install xclip xauth` vai `sudo dnf install xclip
  xorg-x11-xauth`), un `X11Forwarding yes` failā `/etc/ssh/sshd_config`, ko vairums distribūciju jau iestata.
  Pārbaudiet ar `sudo sshd -T | grep -i x11forwarding`.

Tad pievienojieties ar **`-Y`**:

```sh
ssh -Y user@server
```

Pirmajā reizē var parādīties `/usr/bin/xauth: file /home/user/.Xauthority does not exist`. Tas ir nekaitīgi: `xauth`
izveido failu, un ziņojums vairs neatgriežas. Lai pārbaudītu, vai tas darbojas:

```sh
echo $DISPLAY                            # kaut kas līdzīgs localhost:10.0
echo hello | xclip -selection clipboard  # tad ielīmējiet savā datorā
```

Palaidiet Navigator no tās pašas sesijas ar ieslēgtu *Sistēmas starpliktuve*. Lai pāradresētu X11 katru reizi, kad
pievienojaties šim serverim, pievienojiet šo failam `~/.ssh/config` savā datorā:

```
Host server
    ForwardX11 yes
    ForwardX11Trusted yes
```

Kas jāzina:

- **Drošība.** `-Y` uztic serverim jūsu X sesiju: programma tajā vai ikviens, kam tur ir root tiesības, var nolasīt
  jūsu taustiņsitienus, ekrānu un starpliktuvi, kamēr esat pievienojies. Lietojiet to tikai ar serveriem, kuriem
  uzticaties. Vienkāršais `-X` serveri ierobežo, taču ierobežojums var arī neļaut `xclip` nolasīt jūsu starpliktuvi,
  tāpēc ielīmēšana var nedarboties.
- **Ielīmēšanai ir neliela aizkave.** Katra Navigator ielīmēšana palaiž `xclip` serverī, kas paņem jūsu starpliktuvi
  pa tīklu. Pa internetu daži simti milisekunžu ir normāli. Jūsu termināļa ielīmēšanas taustiņš šo turp un atpakaļ
  ceļu apiet. Ja paņemšana ilgst vairāk nekā 2 sekundes, Navigator padodas un ielīmē savu pēdējo kopiju.
- **Kopija var pazust, kad atvienojaties.** `xclip` turpina pasniegt nokopēto tekstu no servera, tāpēc, ja tas jums
  vēlāk vajadzīgs, ielīmējiet to kaut kur savā datorā, pirms izrakstāties.

### tmux vai screen vidē

**tmux** vidē ļaujiet tmux nodot OSC 52 kopēšanas pieprasījumus tālāk jūsu terminālim, pievienojot šo failam
`~/.tmux.conf`:

```
set -g set-clipboard on
```

X11 pāradresācija tmux vidē darbojas, ja vien tmux sesija tika palaista no ssh sesijas ar pāradresāciju. Agrāk
izveidota sesija vai sesija, kas atkal pievienota no jauna savienojuma, patur veco `DISPLAY`. Palaidiet tur `export
DISPLAY=...` ar jauno vērtību vai palaidiet Navigator jaunā tmux logā.

Ja terminālis, kopējot, izdrukā nesakarīgas rakstzīmes, termināļa ceļu var izslēgt, palaižot Navigator ar
`NAVKIT_CLIPBOARD=off nav`.

## Problēmu novēršana

**Kopēšana neko nedara, vai teksts nenonāk citās programmās.**
Nav instalēts starpliktuves rīks, un jūsu terminālis ignorē Navigator pieprasījumu. Instalējiet `xclip` vai
`wl-clipboard` (skatiet [Ātrais sākums](#ātrais-sākums)).

**Ielīmēšana ielīmē vecu tekstu, nevis to, ko tikko nokopēju citā programmā.**
Navigator nevarēja nolasīt darbvirsmas starpliktuvi un izmantoja savu pēdējo kopiju. Instalējiet starpliktuves rīku.
Ghostty var arī iestatīt `clipboard-read = allow`. Līdz tam lietojiet termināļa ielīmēšanas taustiņu (Ctrl+Shift+V).

**Shift+Ins ielīmē ko citu nekā Ctrl+V.**
Jūsu terminālis pārtvēra Shift+Ins un starpliktuves vietā ielīmēja *primāro atlasi* (pēdējo tekstu, ko jebkur
iezīmējāt). Ghostty atsaistiet to, kā parādīts iepriekš. xfce4-terminal un GNOME Terminal lietojiet Ctrl+V.

**Taustiņš vispār neko nedara.**
Jūsu terminālis vai darbvirsma, visticamāk, šo taustiņu patur sev. No Navigator pirmkoda kopijas var redzēt, kas
patiesībā atnāk:

```sh
./venv/bin/python tools/keyprobe.py
```

Nospiediet taustiņu. Ja nekas netiek izdrukāts, terminālis to paturēja. Lai izietu, divreiz nospiediet `q`.
Lietojiet citu no iepriekš minētajiem taustiņiem vai piesaistiet savu (nākamā sadaļa).

**Caur ssh nokopētais teksts nekad nenonāk manā datorā.**
Serverim nav darbvirsmas, un jūsu lokālais terminālis ignorē OSC 52. Lietojiet X11 pāradresāciju (`ssh -Y`) vai
termināli, kas atbalsta OSC 52; skatiet [Attālā serverī caur ssh](#attālā-serverī-caur-ssh).

**Caur ssh ielīmēšana aizņem brīdi.**
Ar X11 pāradresāciju katra ielīmēšana paņem jūsu starpliktuvi pa tīklu. Tekstam no sava datora lietojiet termināļa
ielīmēšanas taustiņu (Ctrl+Shift+V); tam nav vajadzīgs ceļš turp un atpakaļ.

**Vienā terminālī darbojas, citā ne.**
Tā tam jābūt. Pārbaudiet šo termināli sadaļā [Piezīmes par termināļiem](#piezīmes-par-termināļiem).

## Taustiņu maiņa

Jebkuru taustiņu varat mainīt sadaļā **Iestatījumi > Konfigurācija > Taustiņu piesaiste** vai failā
`~/.config/navigator/keybindings.ini`. Komandai var būt vairāki taustiņi, atdalīti ar komatiem:

```ini
clipboard_cut = shift+delete, ctrl+x, ctrl+alt+x
clipboard_copy = ctrl+insert, ctrl+c, ctrl+alt+c
clipboard_paste = shift+insert, ctrl+v, ctrl+alt+v
```

Taustiņš vienā vietā var piederēt tikai vienai komandai. Lai redaktorā atdotu Ctrl+C kam citam, vispirms noņemiet to
no `clipboard_copy`.

Navigator, pirmo reizi startējot, ieraksta failu ar visiem noklusējumiem un patur to, kas tajā ierakstīts. Ja jūsu
fails ir vecāks par noklusējumu maiņu, tas patur jūsu vecos taustiņus. Izvēlieties komandu dialogā Taustiņu piesaiste
un nospiediet **Noklusēts**, lai paņemtu jaunos.
