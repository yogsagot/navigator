# Navigator palaišana

Komanda ir `nav`:

```sh
nav [LEFT] [RIGHT] [options]
```

`LEFT` un `RIGHT` ir direktorijas, kurās atveras abi paneļi. Ja dota viena, abi paneļi atveras tajā; ja neviena —
abi atveras pašreizējā direktorijā. Jebkura var būt vietas ārpus diska adrese, piemēram, `sftp://user@host/dir`,
`ftp://host/`, `smb://host/share` vai `s3://s3.amazonaws.com/bucket`; skatiet [Vietas ārpus diska](drives.md).

Komandrindā dota opcija ir spēkā tikai šai sesijai. Tā ir svarīgāka par [iestatījumiem](settings.md) un nekad
netiek tajos ierakstīta.

## Faili un vietas

| Opcija | Ko tā dara |
|---|---|
| `-e FILE`, `--edit FILE` | Sākumā atver failu [redaktorā](editor.md). Norādiet to vairākkārt vairākiem failiem. Vēl neesošs nosaukums tiek izveidots, kad saglabājat |
| `--config PATH` | Lasa un saglabā iestatījumus citā failā, nevis `~/.config/navigator/navigator.ini` |
| `--database PATH` | Glabā vēstures un grāmatzīmes citā failā, nevis `~/.local/state/navigator/navigator.db` |
| `--version` | Izdrukā versiju un to, kura Navigator kopija ir instalēta, un iziet |

Faili, kas atrodas blakus `navigator.ini`, — [lietotāja izvēlne un failu asociācijas](user-menu.md), taustiņu
piesaistes, paletes — ar `--config` nepārvietojas: tie paliek `~/.config/navigator`.

## Krāsas un rakstzīmes

| Opcija | Ko tā dara |
|---|---|
| `--theme NAME` | Izmanto citu krāsu shēmu |
| `--list-themes` | Izdrukā krāsu shēmu nosaukumus un iziet |
| `--palette dos` | Rāda katru krāsu tā, kā to rādīja DOS Navigator VGA karte, neatkarīgi no termināļa krāsu shēmas |
| `--palette terminal` | Atstāj sešpadsmit krāsas termināļa paša krāsu shēmai |
| `--reprogram-palette` | Kamēr Navigator darbojas, iestata termināļa sešpadsmit krāsas uz DOS krāsām — terminālim, kam krāsas citādi nevar uzdot |
| `--colors DEPTH` | Cik krāsu rāda terminālis: `mono`, `8`, `16`, `256` vai `truecolor`. `auto` vadās pēc `$COLORTERM` un `$TERM` |
| `--glyphs SET` | Kuras rakstzīmes zīmē termināļa fonts: `ascii` zīmē rāmjus ar `+` un `-`, `unicode` zīmē lodziņus, `nerd` pievieno ikonu blakus katram faila nosaukumam Nerd Font fontam. `auto` uzmin |
| `--marks LOOK` | Kā izskatās izvēles rūtiņas un radiopogas: `dos` ir `[X]` un `(•)`, `brackets` ir `[✓]` un `(●)`, `boxes` ir bez iekavām |
| `--charset NAME` | Termināļa, kas nav UTF-8, rakstzīmju kopa, piemēram, `koi8-r`, `cp866` vai `iso8859-2`. Bez tās tiek izmantota lokalizācijas kopa |
| `--graphics HOW` | Kā skatītājs zīmē attēlu: `kitty`, `sixel` vai `none`, lai rādītu tā baitus. Bez tās tiek jautāts terminālim |
| `--no-dim-modal` | Atstāj to, kas ir aiz dialoglodziņa, pilnās krāsās, nevis bālu; `--dim-modal` to atkal ieslēdz |

Vairāk par tēmām — lappusē [Taustiņi un krāsas](customizing.md#krāsas).

## Valoda un virziens

| Opcija | Ko tā dara |
|---|---|
| `--language CODE` | Uzrakstu un ziņojumu valoda, piemēram, `lv`, `ru`, `ja` vai `en`. Bez tās tiek izmantota iestatījumu *Valoda*, citādi `$LANG` |
| `--direction auto` | Spoguļo ekrānu, ja valodu raksta no labās uz kreiso, piemēram, ivritu vai arābu. Bez opcijas tiek izmantots iestatījumu *Teksta virziens*, kas sākumā ir šis |
| `--direction rtl` | Spoguļo ekrānu neatkarīgi no valodas, lai tas lasītos no labās uz kreiso |
| `--direction ltr` | Nekad nespoguļo ekrānu |
| `--bidi app` | Navigator pats izkārto no labās uz kreiso rakstāmo tekstu pirms tā nosūtīšanas. Bez opcijas terminālis tiek atpazīts un izvēlēts pareizais veids |
| `--bidi words` | Katrs no labās uz kreiso rakstāmais vārds tiek nosūtīts apgriezts — terminālim, piemēram, kitty, kas to atkal apgriež |

Tās pašas izvēles ir iestatījumu lappusē [Saskarne](settings.md#saskarne).

## Ja kaut kas noiet greizi

| Opcija | Ko tā dara |
|---|---|
| `--on-error dialog` | Negaidīta kļūda parāda lodziņu ar tās informāciju, un varat turpināt |
| `--on-error crash` | Negaidīta kļūda aizver Navigator un izdrukā tās informāciju |

Jebkurā gadījumā kļūda tiek pievienota failam `errors.log` blakus datubāzei: direktorijā `~/.local/state/navigator`
vai direktorijā, ko nosauc `--database`. Iestatījumu lappusē [Sistēma](settings.md#sistēma) ir tā pati izvēle.

## Navigator iekšienē

`nav` ierakstīšana paša Navigator komandrindā nepalaiž otru kopiju: tā paziņo, ka Navigator jau darbojas un ka
`Ctrl+O` atgriež tajā.
