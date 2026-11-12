# ✈️ SkyOps XP12 — Manuale Operativo & Guida Utente

Benvenuto in **SkyOps XP12**, la piattaforma gestionale, di monitoraggio telemetrico e di economia aerea per **X-Plane 12**.

SkyOps XP è progettata per trasformare la simulazione di volo in una vera carriera aeronautica persistente, colmando il divario tra la simulazione tecnica di volo e la gestione realistica dei costi operativi, della manutenzione e delle rotte commerciali.

**Caratteristica chiave:** SkyOps XP comunica direttamente con X-Plane 12 via socket di rete **UDP nativo (porta 49000)**. **Non richiede l'installazione di alcun plugin o file `.xpl` all'interno della cartella di X-Plane 12.**

---

## Indice dei Contenuti
1. [Requisiti di Sistema](#1-requisiti-di-sistema)
2. [Installazione e Avvio Rapido](#2-installazione-e-avvio-rapido)
   - [Su Windows](#su-windows)
   - [Su Linux e macOS](#su-linux-e-macos)
   - [Accesso da Tablet / iPad / Secondo Monitor](#accesso-da-tablet--ipad--secondo-monitor)
3. [Configurazione Iniziale (Setup Wizard)](#3-configurazione-iniziale-setup-wizard)
4. [Flusso Operativo di un Volo (Dall'Hangar all'Atterraggio)](#4-flusso-operativo-di-un-volo)
   - [Pianificazione e Dispatch (SimBrief o Manuale)](#a-pianificazione-e-dispatch)
   - [Controlli Pre-Volo (Carburante, Parcheggio, Aeroporto)](#b-controlli-pre-volo)
   - [Monitoraggio in Volo (HUD e Mappa Live)](#c-monitoraggio-in-volo)
   - [Chiusura Volo e Conto Economico (Trip P&L)](#d-chiusura-volo-e-conto-economico-trip-pl)
5. [Modello Economico e Contabilità Realistica](#5-modello-economico-e-contabilit%C3%A0-realistica)
   - [Modalità REALISTICA vs STANDARD](#modalit%C3%A0-realistica-vs-standard)
   - [Il Mese Operativo e i Costi Fissi Reali](#il-mese-operativo-e-i-costi-fissi-reali)
   - [Tariffe di Sorvolo ANSP Globali ed Esenzione FAA USA](#tariffe-di-sorvolo-ansp-globali-ed-esenzione-faa-usa)
   - [Equipaggio Fisso Salariato vs Freelance](#equipaggio-fisso-salariato-vs-freelance)
   - [Sconto Atterraggio alla Base Operativa](#sconto-atterraggio-alla-base-operativa)
6. [Gestione Flotta, Mercato e Finanziamenti](#6-gestione-flotta-mercato-e-finanziamenti)
7. [Officina, Usura e Avarie Dinamiche](#7-officina-usura-e-avarie-dinamiche)
8. [Tour IVAO e Ufficiali](#8-tour-ivao-e-ufficiali)
9. [Risoluzione Problemi e Domande Frequenti (FAQ)](#9-risoluzione-problemi-e-domande-frequenti-faq)

---

## 1. Requisiti di Sistema
* **Simulatore:** Laminar Research X-Plane 12 (qualsiasi versione).
* **Sistema Operativo:** Windows 10/11 (64-bit), Linux (Ubuntu, Debian, Fedora, Arch, Mint), oppure macOS (12+).
* **Python:** Python 3.10 o superiore installato sul computer ([python.org](https://www.python.org/downloads/)).
  * *Nota per Windows:* Durante l'installazione di Python, assicurati di spuntare la casella **"Add python.exe to PATH"**.
* **Browser Web:** Qualsiasi browser moderno (Chrome, Edge, Firefox, Safari).

---

## 2. Installazione e Avvio Rapido

Non è necessario installare nulla dentro `X-Plane 12/Resources/plugins`.

### Su Windows
1. Estrai l'archivio ZIP di SkyOps XP in una cartella a tua scelta (es. `C:\SkyOps-XP`).
2. Fai doppio clic sul file **`run.bat`**.
3. Al primo avvio, lo script creerà automaticamente l'ambiente virtuale isolato (`.venv`) e installerà le librerie necessarie.
4. Una volta visualizzato il messaggio di benvenuto, apri il browser all'indirizzo:
   ```text
   http://localhost:8000
   ```

### Su Linux e macOS
1. Estrai l'archivio e apri un terminale nella cartella di SkyOps XP.
2. Rendi eseguibile e lancia lo script:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```
3. Apri il browser su `http://localhost:8000`.

### Accesso da Tablet / iPad / Secondo Monitor
All'avvio, sia `run.bat` che `run.sh` rilevano l'indirizzo IP locale del tuo PC e lo stampano a schermo (es. `http://192.168.1.50:8000`).
Se il tuo tablet o secondo PC è collegato alla stessa rete Wi-Fi di casa, puoi aprire quell'indirizzo dal browser del tablet e usare SkyOps XP come una vera Electronic Flight Bag (EFB) touch da cockpit!

---

## 3. Configurazione Iniziale (Setup Wizard)
Se avvii SkyOps per la prima volta, apparirà la schermata di benvenuto:

1. **Lingua & Valuta:** Scegli subito se visualizzare l'interfaccia in **Italiano** o **English**, e se tenere la contabilità in **Euro (€)** o **Dollari ($)**. Puoi comunque cambiare lingua e valuta in qualsiasi momento dall'intestazione in alto.
2. **Nome della Compagnia Aerea:** Inserisci il nome del tuo vettore (es. *AeroSky Executive* o *Alp Line*).
3. **Base Operativa (ICAO):** Il codice a 4 lettere del tuo aeroporto principale (es. `LIPO`, `LIRN`, `LIMC`, `EDDS`, `KAPA`). Alla base operativa beneficerai di sconti fino al -70% sulle tasse di atterraggio.
4. **Capitale Iniziale & Livello di Difficoltà:** Scegli tra 5 livelli realistici:
   - *Pilota Indipendente (Hardcore):* 35.000 € – Inizi noleggiando piccoli monomotori GA a ore.
   - *Start-up Regionale (Realistica):* 150.000 € – Ideale per noleggiare jet leggeri o versare l'anticipo di un piccolo usato.
   - *Compagnia Emergente (Standard):* 500.000 € – Budget sufficiente per acquistare un GA o avviare un leasing.
   - *Operatore Executive (Avanzato):* 2.500.000 € – Accesso immediato a Vision Jet e Business Jet.
   - *Major Airline (Magnate):* 25.000.000 € – Per gestire grandi aerei di linea.
5. **Modello Economico:**
   - **Realistico (Consigliato):** Margini reali dell'aviazione (4%–12%), con costi completi di handling, riserve motore orarie, tasse di sorvolo e costi indiretti.
   - **Standard (Rilassato):** Ricavi maggiorati del +25% e costi accessori ridotti (-40%) per far crescere la flotta più rapidamente.
6. **SimBrief Pilot ID (Opzionale):** Inserisci il tuo Pilot ID numerico di SimBrief (es. `1106351`) per importare automaticamente i tuoi piani di volo.
7. **Sincronizzazione X-Plane 12:** SkyOps scansiona la tua cartella `X-Plane 12/Aircraft` e popola automaticamente il catalogo *Mercato & Noleggio* con tutti gli aerei che hai installato.

---

## 4. Flusso Operativo di un Volo

### A. Pianificazione e Dispatch
* **Import SimBrief con 1 Click:** Se generi un piano su SimBrief, apri la scheda **Piano di Volo & Dispatch** e premi *Importa SimBrief*. SkyOps scaricherà rotta, passeggeri, merci, carburante di blocco, aeroporto alternato e meteo.
* **Piano di Volo Manuale:** In alternativa, puoi compilare la tratta a mano (ICAO partenza, arrivo, passeggeri, merci e distanza in miglia nautiche).
* **Regole di Volo (IFR vs VFR):**
  - **IFR:** Il volo commerciale applica tariffe di rotta/sorvolo (Eurocontrol / NAV CANADA / ecc.) e assistenza handling passeggeri.
  - **VFR:** Volo a vista, **completamente esente da tasse di rotta e catering/handling passeggeri**.
* **Associazione Tour:** Se la tratta fa parte di un tour (es. IVAO World Tour), puoi selezionare il tour dal menu a tendina.

### B. Controlli Pre-Volo
Prima di decollare, la plancia di SkyOps effettua controlli automatici:
1. **Posizione Aeromobile:** Il velivolo deve trovarsi all'aeroporto di partenza previsto (oppure puoi traghettarlo pagando il costo di trasferimento).
2. **Freno di Parcheggio:** I freni devono essere inseriti prima della partenza.
3. **Carburante:** Il carburante a bordo viene sincronizzato automaticamente. Puoi effettuare il rifornimento direttamente dal pulsante `⛽ Rifornisci`, pagando solo i litri/kg aggiunti al serbatoio.

Premi **Avvia Monitoraggio Volo**: la barra di stato passerà a `IMBARCO` e poi `RULLAGGIO OUT`.

### C. Monitoraggio in Volo
Durante il volo, SkyOps rileva automaticamente:
* Fase di volo: `DECOLLO` → `IN VOLO (ROTA)` → `AVVICINAMENTO` → `ATTERRATO` → `PARCHEGGIATO`.
* Rateo di discesa al contatto (Vertical Speed in piedi al minuto al touchdown).
* Forza G al contatto (normale, over-G, impatto duro).
* Consumo carburante effettivo e usura progressiva di motore, cellula e carrello.
* Mappa interattiva con tracciamento GPS in tempo reale.

### D. Chiusura Volo e Conto Economico (Trip P&L)
All'arrivo, spegni i motori e inserisci il freno di parcheggio. SkyOps riconoscerà la fase `PARCHEGGIATO` e calcolerà il rendiconto finanziario analitico (*Trip P&L*):
* **(+) Ricavi Commerciali:** Biglietti passeggeri, ancillari (bagagli/posto) e cargo.
* **(+) Bonus Qualità Atterraggio & Reputazione:**
  - `BUTTER LANDING` (< 160 fpm): +5% tariffa charter e +1.5% reputazione aziendale!
  - `GOOD LANDING` (< 300 fpm): +0.5% reputazione.
  - `HARD LANDING` (> 400 fpm): Penale risarcimento passeggeri / ispezione straordinaria (-3% reputazione).
  - `STRUCTURAL DAMAGE` (> 600 fpm): Danno strutturale e penale assicurativa.
* **(-) Tassa di Atterraggio:** Calcolata in base al peso (MTOW) del velivolo. Scontata fino al -70% se atterri alla tua Base Operativa.
* **(-) Tariffe di Rotta & Sorvolo ANSP:** Calcolate secondo la formula internazionale $\sqrt{\text{MTOW} / 50} \times (\text{distanza} / 100) \times \text{tariffa}$. (Esenti per voli VFR, voli USA e aerei sotto le 2 tonnellate).
* **(-) FBO & Ground Handling:** Servizio passeggeri, rampa e gate.
* **(-) Riserva Manutenzione Oraria (Power-by-the-Hour):** Accantonamento obbligatorio per future revisioni motori e Check C/D.
* **(-) Costi Indiretti (IOC):** Commissioni carte, canali GDS e fondo irregolarità passeggeri.
* **(-) Equipaggio:** Pagamento orario freelance, oppure € 0 se hai assunto un pilota/equipaggio fisso salariato.

---

## 5. Modello Economico e Contabilità Realistica

### Modalità REALISTICA vs STANDARD
Puoi passare in ogni momento dall'intestazione o da Impostazioni tra:
* **REALISTICA (Consigliata per la massima immersione):** Ricalca i bilanci autentici di vettori executive e di linea, con margini operativi netti tipici del 4%–12%.
* **STANDARD (Rilassata):** Aumenta i ricavi del +25% e dimezza i costi accessori per chi desidera accumulare capitale più velocemente.

### Il Mese Operativo e i Costi Fissi Reali
I costi fissi di gestione (posto Hangar e Assicurazione Kasko/RC) sono **mensili reali**, calcolati sul calendario reale (es. `2026-11`):
* Che tu faccia 1 volo o 50 voli nel corso del mese, i costi fissi non cambiano.
* Se non voli per un periodo, al tuo ritorno i mesi trascorsi matureranno regolarmente i costi di stazionamento, esattamente come accade per un aereo reale in un hangar aeroportuale.

### Tariffe di Sorvolo ANSP Globali ed Esenzione FAA USA
SkyOps XP integra il primo motore ANSP globale multi-regione per X-Plane 12:
1. **Stati Uniti (Voli Domestici FAA, prefissi `K*`, `PA*`, `PH*`, `TJ*`, ecc.):** **€ 0,00 (FAA Esente)**. Negli USA i servizi ATC non addebitano tasse di sorvolo agli aerei civili (sono finanziati dalle accise carburante).
2. **Europa (Spazio Eurocontrol, `E*`, `L*`, `B*`):** Tassa Eurocontrol piena (€ 65/unità) + TNC radar di terminale.
3. **Canada (`C*`):** Tariffa NAV CANADA (€ 55/unità).
4. **Australia e Nuova Zelanda (`Y*`, `NZ*`):** Airservices Australia / Airways NZ (€ 52/unità).
5. **Resto del Mondo (Asia, Medio Oriente, Sud America, Africa, ICAO):** ANSP Regionale (€ 40/unità).
6. **Voli Transregionali (es. KJFK → EGLL):** Applicano la tariffa al 50% per la sola porzione fuori dallo spazio USA.
7. **Esenzioni Universali:** Tutti i voli **VFR** e tutti i velivoli con **MTOW < 2,0 tonnellate** (es. Cessna 172) pagano **€ 0,00** in tutto il mondo.

### Equipaggio Fisso Salariato vs Freelance
Dalla scheda *Finanze → Equipaggi*:
* **Freelance a Chiamata:** Paghi una tariffa oraria su ogni singolo volo effettuato (€ 90/h GA, € 240/h BizJet, € 520/h Airliner).
* **Equipaggio Fisso Assunto:** Puoi assumere un equipaggio con stipendio mensile fisso (€ 1.800/mese GA, € 4.800/mese BizJet, € 10.400/mese Airliner). Tutti i voli effettuati in quel mese avranno costo equipaggio pari a **€ 0,00**!

### Sconto Atterraggio alla Base Operativa
Quando atterri al tuo aeroporto base (`home_base_icao`):
* **Velivolo di Proprietà:** **-70%** di sconto sulla tassa di atterraggio (poiché stazionamento e servizi base sono già coperti dai costi fissi).
* **Velivolo a Noleggio:** **-35%** di sconto.

---

## 6. Gestione Flotta, Mercato e Finanziamenti
* **Aerei di Proprietà (Owned):** Memorizzano la posizione geografica reale, le ore motore/cellula e il carburante residuo nei serbatoi.
* **Noleggio a Secco (Dry Lease):** Paga una tariffa oraria solo per il tempo di blocco effettivamente volato. Il carburante è a tuo carico.
* **Acquisto con Finanziamento Rateale:** Puoi acquistare aerei versando un anticipo (20%) e pagando comode rate mensili. È possibile estinguere in anticipo il finanziamento in qualsiasi momento dalla scheda Hangar per risparmiare sugli oneri futuri.

---

## 7. Officina, Usura e Avarie Dinamiche
Ogni aeromobile è soggetto a usura realistica:
* **Motore (TBO):** Si consuma con le ore di volo e con regimi termici estremi (EGT elevate).
* **Freni e Pneumatici:** Subiscono attrito in atterraggio ed energia cinetica di frenata.
* **Ispezioni Obbligatorie:** Ispezione delle 50 ore, 100 ore e Revisione Annuale.
* **Avarie Dinamiche in Volo:** Se le condizioni di un componente scendono sotto soglie critiche (o in caso di atterraggi duri ripetuti), SkyOps può iniettare avarie realistiche direttamente nei dataref di X-Plane 12 (`sim/operation/failures/...`).

---

## 8. Tour IVAO e Ufficiali
Dalla scheda **Logbook & Tour** puoi:
* Creare un Tour (es. "IVAO World Tour 2026" o "Giro d'Italia GA").
* Assegnare i tuoi voli a un tour specifico.
* Visualizzare la mappa interattiva d'insieme con tutte le tappe collegate, la distanza totale percorsa, il tempo di volo complessivo e l'utile generato dall'intero viaggio.

---

## 9. Risoluzione Problemi e Domande Frequenti (FAQ)

#### D: Devo installare plugin dentro X-Plane 12?
**R:** No! SkyOps XP dialoga tramite l'interfaccia UDP standard di X-Plane sulla porta `49000`. Nessun file `.xpl` è necessario.

#### D: SkyOps mostra "XP12 OFFLINE" anche se X-Plane 12 è avviato.
**R:**
1. Assicurati che un volo sia caricato e attivo su X-Plane (non fermarti al menu principale).
2. Su X-Plane 12, vai in *Settings → Network* e verifica che la porta UDP per i dati in entrata sia impostata su `49000` (predefinita).
3. Se usi Windows Defender o un firewall di terze parti, consenti il traffico locale per Python/Uvicorn.

#### D: Posso usare SkyOps XP insieme ad altre app come XP12 WebDeck?
**R:** Sì! SkyOps XP usa la porta web `8000` e un listener UDP dedicato (`49005`), coesistendo pacificamente con altre dashboard (es. porta `8080`).

#### D: Come cambio la lingua o la valuta?
**R:** Nell'intestazione in alto trovi i selettori rapidi `[🇮🇹 IT / 🇬🇧 EN]` e `[€ EUR / $ USD]`. Basta un clic per aggiornare l'intera interfaccia istantaneamente.

---
*Buoni voli nei cieli di X-Plane 12 con SkyOps XP!*
