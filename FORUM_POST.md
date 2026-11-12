# SkyOps XP12 — Release v1.0.0 (Forum Post & Announcement)

Di seguito trovi il testo pronto per la pubblicazione sui forum (es. X-Plane.org, AVSIM) e server Discord dedicati alla simulazione di volo, sia in italiano che in inglese.

---

## 🇮🇹 Versione Italiana

**Titolo del Topic:**  
`[RELEASE v1.0.0] SkyOps XP12 — Carriera persistente, gestione flotta ed economia reale per X-Plane 12 (Zero Plugin)`

**Messaggio:**

Ciao a tutti!

Dopo settimane di sviluppo e collaudo approfondito, sono felice di condividere con la community **SkyOps XP12** (versione 1.0.0).

### Di cosa si tratta?
SkyOps XP è una piattaforma progettata per arricchire X-Plane 12 con una componente gestionale, economica e operativa completa:
* **Zero Plugin da installare:** SkyOps comunica con X-Plane 12 tramite l'interfaccia di rete nativa UDP (porta 49000). Non richiede file `.xpl` o script da inserire nella cartella del simulatore.
* **Flotta Persistente:** Memorizza l'ultimo aeroporto in cui hai parcheggiato, il carburante residuo nei serbatoi e le ore motore/cellula.
* **Economia Reale (Trip P&L):** Analisi dettagliata del conto economico di ogni volo con ricavi passeggeri, ancillari, cargo, tasse di atterraggio (scontate alla base), handling e riserve manutenzione.
* **Tariffe di Sorvolo Mondiali (ANSP):** Motore globale multi-regione: voli USA domestici esenti da tasse di rotta (come nella realtà), Eurocontrol in Europa, NAV CANADA, Airservices Australia/NZ e ICAO per il resto del mondo. I voli VFR e gli aerei sotto le 2 tonnellate sono sempre esenti ovunque.
* **Mese Operativo:** I costi fissi (hangar e assicurazione) seguono il calendario reale mensile, garantendo coerenza sia che si voli tutti i giorni sia che si faccia una pausa.
* **Bilingue & Multi-Valuta:** Supporto completo per Italiano e Inglese, con contabilità selezionabile in Euro (€) o Dollari ($).
* **Compatibile con Tablet e iPad:** L'interfaccia web responsive può essere aperta da browser su tablet o secondo monitor collegato al Wi-Fi locale.
* **Tour IVAO & Personalizzati:** Raggruppa i tuoi voli in tappe con mappa interattiva e statistiche cumulative.

### Come iniziare:
1. Scarica lo zip allegato.
2. Su **Windows**, esegui semplicemente `run.bat` (richiede solo Python 3.10+ installato nel sistema).
3. Su **Linux/macOS**, avvia `./run.sh`.
4. Apri `http://localhost:8000` nel browser.

### Invito al feedback:
Questo è il primo rilascio pubblico: il vostro parere, suggerimento e riscontro è fondamentale per arricchire ulteriormente la piattaforma. Se notate anomalie o avete idee per nuove funzionalità, scrivetele qui sotto!

Buoni voli!

---

## 🇬🇧 English Version

**Topic Title:**  
`[RELEASE v1.0.0] SkyOps XP12 — Persistent Career, Fleet Operations & Authentic Airline Economics (Zero Plugins Required)`

**Post Content:**

Hi everyone!

I am excited to announce the first public release of **SkyOps XP12** (v1.0.0).

### What is SkyOps XP?
SkyOps XP is an open operations and economy management platform crafted specifically for Laminar Research X-Plane 12:
* **Zero Simulator Plugins:** SkyOps communicates directly with X-Plane 12 through its native binary UDP interface (port 49000). No `.xpl` files or plugin managers needed.
* **Persistent Fleet & Fuel State:** Remembers your exact parking airport, airframe/engine hours, and residual fuel between sessions.
* **Authentic Flight P&L:** Calibrated commercial yields, touchdown quality ratings (Butter, Good, Hard), landing fees, ground handling, power-by-the-hour engine reserves, and indirect costs.
* **Global Multi-Region ANSP Navigation Fees:** FAA US domestic flights are route-fee exempt, Eurocontrol for Europe, NAV CANADA, Airservices Australia/NZ, and ICAO regional rates. All VFR flights and aircraft under 2 tonnes are 100% exempt worldwide.
* **Calendar Operating Month:** Hangar and insurance overhead accrue on a real calendar basis, accurately reflecting aircraft ownership.
* **Bilingual & Multi-Currency:** Full English and Italian support with dynamic toggle between USD ($) and EUR (€).
* **Tablet / EFB Ready:** Responsive glass-cockpit web interface accessible from your iPad or tablet over local Wi-Fi.
* **IVAO & Custom Tour Tracker:** Group legs into tours with interactive route maps and aggregated stats.

### Quick Start:
1. Download and extract the release zip.
2. On **Windows**, double-click `run.bat` (requires Python 3.10+ installed).
3. On **Linux/macOS**, run `./run.sh`.
4. Open your browser at `http://localhost:8000`.

### We want your feedback!
This is a v1.0.0 release for the flight simulation community. Your feedback, bug reports, and feature requests are very welcome to guide future development!

Happy flying!
