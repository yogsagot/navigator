# Darbs kā root

Ja darbība jūsu diskā tiek atteikta, jo jums trūkst atļaujas, Navigator var to izdarīt vēlreiz kā root. Tas prasa
jūsu paroli ar `sudo` palīdzību vai ļauj to prasīt `pkexec`. Parole netiek saglabāta, bet root piekļuve paliek
atvērta dažas minūtes pēc tās pēdējās darbības un aizveras, kad Navigator beidz darbu.

## Jautājums Kā root

Ja tiek atteikta kopēšana, pārvietošana, dzēšana, pārdēvēšana, direktorijas vai saites izveide, atribūtu maiņa,
saglabāšana redaktorā vai faila lasīšana, ziņojums piedāvā *Kā root*: blakus *Izlaist* un *Atcelt*, ja ir vēl
faili, ar kuriem turpināt, kā kopējot vai dzēšot, un citādi blakus tikai *Atcelt*. Izvēlieties to, ievadiet paroli,
un darbība tiek izdarīta vēlreiz kā root — tāpat kā katra nākamā tās pašas operācijas darbība, vairs nejautājot.

Ieejot direktorijā, ko jums nav atļauts lasīt, tiek uzdots tas pats jautājums. Ja uz to atbildat, panelis rāda
direktoriju kā root: tās ceļš tiek rādīts kā `root:///path`, un kopēšana, dzēšana, skatīšana, rediģēšana un pārējais
tur darbojas tāpat kā jebkur citur. Komandas, kas darbotos jūsu, nevis root vārdā, piemēram, *Izvade panelī* un
*Rādīt cietās saites*, tur ir pelēkas. Uzkāpjot direktorijā, ko jums ir atļauts lasīt, panelis atgriežas uz disku.

## Root piekļuve

*Rīki > Iegūt root piekļuvi* vienreiz pieprasa paroli un patur root piekļuvi atvērtu: kamēr tā nav aizvērta,
direktorija, ko jums nav atļauts lasīt, atveras kā root bez jautāšanas, un [konsole](console.md) darbina root čaulu,
kas seko panelim. Kamēr tā ir atvērta, izvēlņu joslā blakus pulkstenim redzams *ROOT*, bet taustiņu joslā, ja
izvēlņu josla paslēpta vai redzama konsole.

*Rīki > Aizvērt root piekļuvi* — tas pats ieraksts, pārdēvēts, kamēr root piekļuve ir atvērta, — vai klikšķis uz
*ROOT* to aizver: paneļi, kas pārlūkoja kā root, atgriežas uz disku, un konsole atgriežas pie jūsu čaulas.

Root piekļuve aizveras arī pati, ja kādu laiku nav izmantota, un vienmēr, kad Navigator beidz darbu.

## Iestatījumi

Iestatījumu lappusē [Sistēma](settings.md#sistēma):

- *Root piekļuve* izvēlas, kā kļūt par root: *Automātiski* izmanto `sudo`, citādi `pkexec`; *sudo* un *pkexec*
  izmanto attiecīgo; *Nepiedāvāt* to izslēdz. Ar *Nepiedāvāt* vai ja nav instalēta neviena no programmām, nekas
  nepiedāvā *Kā root*.
- *Turēt root vaļā dīkstāvē* ir minūšu skaits, cik ilgi root piekļuve paliek atvērta pēc tās pēdējās darbības. Ar
  `0` tā aizveras, tiklīdz beidzas katra operācija.

Ja Navigator jau darbojas kā root, nekas netiek piedāvāts: katra darbība ir root darbība.
