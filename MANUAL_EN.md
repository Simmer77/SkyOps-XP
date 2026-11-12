# ✈️ SkyOps XP12 — Operations Manual & User Guide

Welcome to **SkyOps XP12**, the modern flight operations, telemetry tracking, and authentic airline economy platform for **Laminar Research X-Plane 12**.

SkyOps XP is designed to transform flight simulation into an immersive, persistent career, bridging the gap between high-fidelity cockpit simulation and realistic airline business management, fleet maintenance, and route profitability.

**Key Feature:** SkyOps XP communicates natively with X-Plane 12 via its built-in binary **UDP network interface (port 49000)**. **Zero plugins or `.xpl` files are required inside your X-Plane 12 installation directory.**

---

## Table of Contents
1. [System Requirements](#1-system-requirements)
2. [Installation & Quick Start](#2-installation--quick-start)
   - [Windows Instructions](#windows-instructions)
   - [Linux & macOS Instructions](#linux--macos-instructions)
   - [Remote Tablet / iPad / Second Monitor Access](#remote-tablet--ipad--second-monitor-access)
3. [Initial Setup Wizard](#3-initial-setup-wizard)
4. [Flight Operations Workflow (Hangar to Shutdown)](#4-flight-operations-workflow)
   - [Dispatch & Planning (SimBrief or Manual)](#a-dispatch--planning)
   - [Pre-Flight Checks (Fuel, Brakes, Location)](#b-pre-flight-checks)
   - [In-Flight Telemetry (HUD & Live Map)](#c-in-flight-telemetry)
   - [Flight Closure & Trip P&L](#d-flight-closure--trip-pl)
5. [Economic Model & Authentic Aviation Accounting](#5-economic-model--authentic-aviation-accounting)
   - [REALISTIC vs STANDARD Economy Mode](#realistic-vs-standard-economy-mode)
   - [Calendar Operating Month & Fixed Overhead](#calendar-operating-month--fixed-overhead)
   - [Global ANSP Navigation Fees & FAA US Exemption](#global-ansp-navigation-fees--faa-us-exemption)
   - [Salaried Crew Retainer vs Freelance Rates](#salaried-crew-retainer-vs-freelance-rates)
   - [Home Base Landing Fee Discount](#home-base-landing-fee-discount)
6. [Fleet Management, Dealerships & Aircraft Financing](#6-fleet-management-dealerships--aircraft-financing)
7. [Maintenance Workshop, Wear & In-Flight Failures](#7-maintenance-workshop-wear--in-flight-failures)
8. [IVAO & Custom Tours Tracker](#8-ivao--custom-tours-tracker)
9. [Troubleshooting & Frequently Asked Questions (FAQ)](#9-troubleshooting--faq)

---

## 1. System Requirements
* **Simulator:** Laminar Research X-Plane 12 (any release).
* **Operating System:** Windows 10/11 (64-bit), Linux (Ubuntu, Debian, Fedora, Arch, Mint), or macOS (12+).
* **Python:** Python 3.10 or newer installed on your computer ([python.org](https://www.python.org/downloads/)).
  * *Windows Note:* Ensure **"Add python.exe to PATH"** is checked during Python installation.
* **Web Browser:** Any modern browser (Chrome, Edge, Firefox, Safari).

---

## 2. Installation & Quick Start

You do NOT need to copy any files into `X-Plane 12/Resources/plugins`.

### Windows Instructions
1. Unzip the SkyOps XP archive into any folder of your choice (e.g. `C:\SkyOps-XP`).
2. Double-click **`run.bat`**.
3. On first run, the script automatically provisions an isolated virtual environment (`.venv`) and installs the required dependencies.
4. When the startup banner appears, open your browser at:
   ```text
   http://localhost:8000
   ```

### Linux & macOS Instructions
1. Extract the archive and open a terminal in the SkyOps XP directory.
2. Make the launcher executable and run it:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```
3. Open your browser at `http://localhost:8000`.

### Remote Tablet / iPad / Second Monitor Access
Upon launch, `run.bat` and `run.sh` detect your local LAN IPv4 address (e.g. `http://192.168.1.50:8000`).
Connect your tablet or second PC to the same home Wi-Fi network and browse to that URL: SkyOps XP functions seamlessly as a responsive, glass-cockpit Electronic Flight Bag (EFB) at your side!

---

## 3. Initial Setup Wizard
When launching SkyOps XP for the first time, the Initial Setup screen guides you through:

1. **Language & Currency:** Choose your preferred interface language (**English** or **Italian**) and accounting currency (**USD $** or **EUR €**). You can toggle these anytime from the top navigation bar.
2. **Airline Name:** Enter your carrier name (e.g. *AeroSky Executive* or *Alp Line*).
3. **Home Base (ICAO):** Your 4-letter home airport code (e.g. `KAPA`, `EDDS`, `LIRN`, `EGLL`). Aircraft landing at your home base receive up to **-70% landing fee discounts**.
4. **Starting Capital & Progression Level:**
   - *Independent Pilot (Hardcore):* $35,000 / €35.000 – Start by renting single-engine GA aircraft by the hour.
   - *Regional Start-up (Realistic):* $150,000 / €150.000 – Ideal to lease GA/BizJets or put a down payment on a used plane.
   - *Emerging Airline (Standard):* $500,000 / €500.000 – Budget to acquire your first GA or start a VLJ lease.
   - *Executive Operator (Advanced):* $2,500,000 / €2.500.000 – Immediate access to Vision Jets and Business Jets.
   - *Major Airline (Magnate):* $25,000,000 / €25.000.000 – Capital to manage commercial airliners.
5. **Economy Model:**
   - **REALISTIC (Recommended for maximum immersion):** Authentic airline margins (4%–12%), ground handling, engine power-by-the-hour reserves, ANSP en-route fees, and indirect operating costs.
   - **STANDARD (Relaxed):** +25% revenue bonus and -40% lower fees for rapid progression.
6. **SimBrief Pilot ID (Optional):** Enter your numeric SimBrief ID (e.g. `1106351`) to import flight plans in one click.
7. **X-Plane 12 Sync:** Automatically scans your `X-Plane 12/Aircraft` folder and populates the *Market & Leases* catalog with every aircraft currently installed.

---

## 4. Flight Operations Workflow

### A. Dispatch & Planning
* **1-Click SimBrief Import:** Plan your flight on SimBrief, navigate to the **Flight Plan & Dispatch** tab, and click *Import SimBrief*. SkyOps loads your route, passengers, cargo, block fuel, alternate airport, and winds.
* **Manual Flight Dispatch:** Enter departure, destination, alternate, passenger count, cargo weight, and route distance directly.
* **Flight Rules (IFR vs VFR):**
  - **IFR:** Commercial flight applying regional ANSP navigation fees and passenger ground handling.
  - **VFR:** Visual flight rules, **100% exempt from ANSP navigation fees and passenger handling**.
* **Tour Association:** Group legs under an IVAO or Custom Tour to track cumulative progress on an interactive map.

### B. Pre-Flight Checks
Before departure, the SkyOps HUD verifies:
1. **Aircraft Position:** Your aircraft must be parked at the planned departure airport (ferry repositioning available if needed).
2. **Parking Brake:** Parking brakes must be engaged prior to start.
3. **Fuel On Board:** Synchronized live from X-Plane. Click `⛽ Refuel` to purchase fuel, paying only for the net kg added.

Click **Start Flight Tracking**: the status banner transitions to `BOARDING` and `TAXI OUT`.

### C. In-Flight Telemetry
During flight, SkyOps records real-time telemetry:
* Flight phase transitions: `TAKEOFF` → `EN ROUTE` → `APPROACH` → `LANDED` → `PARKED`.
* Touchdown vertical speed (FPM at wheel contact) and Normal G-force.
* True fuel burn, airframe hours, and engine telemetry.
* Live interactive map with GPS aircraft tracking and route path.

### D. Flight Closure & Trip P&L
After landing, taxi to the ramp, shut down engines, and set the parking brake. SkyOps detects `PARKED` and generates a comprehensive **Trip P&L (Profit & Loss)** report:
* **(+) Gross Commercial Revenue:** Passenger ticket yield, ancillary fees, and cargo.
* **(+) Touchdown Rating & Reputation Bonus:**
  - `BUTTER LANDING` (< 160 fpm): +5% charter bonus yield and +1.5% company reputation!
  - `GOOD LANDING` (< 300 fpm): +0.5% reputation.
  - `HARD LANDING` (> 400 fpm): Passenger compensation penalty & mandatory inspection (-3% reputation).
  - `STRUCTURAL DAMAGE` (> 600 fpm): Structural inspection and insurance deductible penalty.
* **(-) Landing Fee:** Proportional to MTOW, discounted up to -70% at home base.
* **(-) ANSP Navigation & Overflight Fee:** Computed via standard formula $\sqrt{\text{MTOW} / 50} \times (\text{distance} / 100) \times \text{unit rate}$. (Free for VFR, US domestic FAA flights, and aircraft under 2.0 tonnes).
* **(-) Ground Handling & FBO:** Ramp, baggage, gate handling, and passenger security fees.
* **(-) Hourly Maintenance Reserve:** Power-by-the-hour engine and airframe escrow for major checks.
* **(-) Indirect Operating Costs (IOC):** Credit card processing, PSS/GDS distribution, and EU261 passenger protection reserves.
* **(-) Flight Crew:** Hourly freelance pay, or $0 if you have a salaried crew on monthly retainer.

---

## 5. Economic Model & Authentic Aviation Accounting

### REALISTIC vs STANDARD Economy Mode
Toggle between modes at any time from Settings or Header:
* **REALISTIC:** Calibrated against real-world airline financials with typical 4%–12% operating margins.
* **STANDARD:** Relaxed margins (+25% revenue, -40% accessory costs) for faster progression.

### Calendar Operating Month & Fixed Overhead
Fixed operating overhead (Hangar space and Hull/Liability Insurance) is charged on a **real calendar month basis** (e.g. `2026-11`):
* Whether you complete 1 flight or 60 flights in a month, fixed monthly costs remain constant.
* If you take a hiatus of several months, all elapsed calendar months accrue normally upon your return, just like owning a real aircraft in a hangar.

### Global ANSP Navigation Fees & FAA US Exemption
SkyOps XP features a comprehensive multi-region global ANSP fee engine:
1. **United States (FAA Domestic Flights, prefixes `K*`, `PA*`, `PH*`, `TJ*`, etc.):** **$0.00 / €0.00 (FAA Exempt)**. US domestic airspace ATC is funded through aviation fuel and passenger ticket excise taxes rather than direct ATC overflight invoices.
2. **Europe (Eurocontrol Airspace, `E*`, `L*`, `B*`):** Eurocontrol en-route fee (€65/unit rate) + Terminal Navigation Charge (TNC).
3. **Canada (`C*`):** NAV CANADA en-route fee (€55/unit rate).
4. **Australia & New Zealand (`Y*`, `NZ*`):** Airservices Australia / Airways NZ (€52/unit rate).
5. **Rest of World (Asia, Middle East, South America, Africa, ICAO):** Regional ANSP fee (€40/unit rate).
6. **Cross-Region Flights (e.g. KJFK → EGLL):** Applies a 50% factor for the non-US airspace segment.
7. **Universal Exemptions:** All **VFR flights** and all aircraft with **MTOW < 2.0 tonnes** (e.g. Cessna 172) pay **$0.00 / €0.00** worldwide.

### Salaried Crew Retainer vs Freelance Rates
Under *Finances → Crew*:
* **Freelance on Call:** Pay an hourly rate for each flown hour ($90/h GA, $240/h BizJet, $520/h Airliner).
* **Salaried Staff Retainer:** Hire a dedicated pilot/crew on a fixed monthly retainer ($1,800/mo GA, $4,800/mo BizJet, $10,400/mo Airliner). All flights in that category for the entire month have **$0/h crew cost**!

### Home Base Landing Fee Discount
When landing at your company's home base (`home_base_icao`):
* **Owned Aircraft:** **-70% discount** on landing fees (as parking and basic services are covered by monthly hangar costs).
* **Leased Aircraft:** **-35% discount**.

---

## 6. Fleet Management, Dealerships & Aircraft Financing
* **Owned Aircraft:** Maintain persistent GPS parking location, engine/airframe hours, and residual fuel.
* **Dry Lease:** Pay an hourly rate only for the actual block hours flown; fuel is your responsibility.
* **Financed Purchase:** Buy new or used aircraft with a 20% down payment and 48 monthly installments. You can pay off loans early at any time from the Hangar to save on future payments.

---

## 7. Maintenance Workshop, Wear & In-Flight Failures
Every aircraft undergoes realistic wear:
* **Engine (TBO):** Degrades with flight hours and excessive temperature cycles (high EGT).
* **Brakes & Tires:** Incur friction wear based on touchdown energy and braking intensity.
* **Inspections:** 50-hour, 100-hour, and Annual inspections.
* **Dynamic In-Flight Failures:** When component health drops into critical zones, SkyOps can trigger authentic X-Plane 12 failure datarefs (`sim/operation/failures/...`).

---

## 8. IVAO & Custom Tours Tracker
Under the **Logbook & Tours** tab:
* Create a tour (e.g. "IVAO World Tour 2026" or "Caribbean Island Hopper").
* Assign flights to that tour during dispatch.
* View an interactive route map connecting all legs, total distance flown, cumulative flight hours, and net tour earnings.

---

## 9. Troubleshooting & FAQ

#### Q: Do I need to install any plugin inside X-Plane 12?
**A:** No! SkyOps XP connects directly through X-Plane's native UDP port `49000`. No `.xpl` files or plugin managers are needed.

#### Q: SkyOps shows "XP12 OFFLINE" even though X-Plane 12 is running.
**A:**
1. Ensure a flight is loaded and active in X-Plane (not sitting on the main menu).
2. In X-Plane 12, go to *Settings → Network* and verify the incoming data UDP port is set to `49000` (default).
3. Ensure your local firewall allows Python/Uvicorn network traffic.

#### Q: Can I run SkyOps XP alongside other web tools like XP12 WebDeck?
**A:** Yes! SkyOps XP runs on web port `8000` with its own UDP listener (`49005`), coexisting smoothly alongside other applications (e.g. port `8080`).

#### Q: How do I change the language or currency?
**A:** Use the quick toggle pills `[🇮🇹 IT / 🇬🇧 EN]` and `[€ EUR / $ USD]` in the top header bar to switch instantly.

---
*Happy flying in X-Plane 12 with SkyOps XP!*
