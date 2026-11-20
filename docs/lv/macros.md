# Makro

Navigator ir divu veidu makro: taustiņi, ko ierakstāt un atskaņojat jebkur, un makro, kas redaktoram uzrakstīti
failā.

## Taustiņu makro

Taustiņu makro ir tā ieraksts, ko rakstāt. To ir deviņi, numurēti no 1 līdz 9, un tie saglabājas no vienas sesijas
uz nākamo.

| Taustiņš | Ko tas dara |
|---|---|
| `Ctrl+J` `R` `1` līdz `9` | Sāk ierakstīt šajā makro |
| `Ctrl+J` `R` un jebkurš cipars ierakstīšanas laikā | Aptur ierakstīšanu |
| `Ctrl+J` `1` līdz `9` | Atskaņo šo makro |

Spiediet taustiņus vienu pēc otra: `Ctrl+J`, tad `R`, tad ciparu. Kamēr makro tiek ierakstīts, blakus pulkstenim
redzams `>MACRO<`.

Tiek ierakstīts viss, ko rakstāt, un tas, ko ielīmējat, jebkurā logā vai dialoglodziņā. Ierakstīšanu nevar sākt vai
apturēt, kamēr ir atvērts dialoglodziņš, tāpēc atveriet lodziņu pēc sākšanas un aizveriet to pirms apturēšanas.

Kamēr konsolē vai komandu logā darbojas programma, `Ctrl+J` nonāk programmā.

## Redaktora makro

Redaktora makro ir redaktora komandu saraksts ar nosaukumu. `Ctrl+J` `0` [redaktorā](editor.md) uzskaita
rediģējamajam failam paredzētos makro un atskaņo to, ko izvēlaties.

Makro atrodas failā `macros.ini`, ko atver *Iestatījumi > Konfigurācija > Makro fails*. Sadaļa nosauc failus, kam
paredzēti tās makro, ar maskām, kas atdalītas ar `;`. Sadaļa `[*]` ir katram failam.

```ini
[*]
MACRO Date and time
  InsertDate
  PRINT ' '
  InsertTime
ENDMACRO

[*.c;*.h]
MACRO Block
  PRINT '{'^M'}'
  MoveUp
ENDMACRO
```

Katra makro rinda ir viena no šīm:

| Rinda | Ko tā dara |
|---|---|
| `PRINT 'text', n` | Ieraksta tekstu `n` reizes; `n` var izlaist |
| `GOTOXY x, y` | Pārvieto kursoru uz rindas `y` kolonnu `x`, abas skaitot no 0 |
| `GOTOX x`, `GOTOY y` | Pārvietojas tikai uz kolonnu vai tikai uz rindu |
| `MARK n`, `GOTO n` | Iestata marķieri `n` no 1 līdz 9 vai pāriet uz to |
| `Command, n` | Palaiž redaktora komandu `n` reizes |

`PRINT` tekstu raksta vienpēdiņās, un `''` tajās ir pēdiņa. Ārpus pēdiņām `^M` ir vadības rakstzīme, šeit
`Enter`, un `#13` ir rakstzīme, kas dota ar tās kodu.

Komandu raksta ar DOS Navigator nosaukumu, piemēram, `WordLeft`, `MoveUp` vai `DelChar`, vai ar tās nosaukumu failā
`keybindings.ini`, piemēram, `word_left`. Nezināms nosaukums tiek izlaists, un jums pasaka, kurš.

Rinda, kas sākas ar `;`, ir komentārs.
