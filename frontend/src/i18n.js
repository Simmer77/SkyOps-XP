// SkyOps XP Internationalization (i18n) Dictionary
// Supported languages: 'en' (English), 'it' (Italian)

export const translations = {
  en: {
    // App Branding & Navigation
    app_title: 'SKYOPS XP12',
    app_subtitle: 'Operations & Real Airline Economy Platform for X-Plane 12',
    nav_cockpit: 'Dashboard & HUD',
    nav_hangar: 'Hangar & Fleet',
    nav_jobs: 'Contracts & Jobs',
    nav_dealership: 'Dealership & Leases',
    nav_maintenance: 'Maintenance & Shop',
    nav_finances: 'Finances & Ledger',
    nav_logbook: 'Logbook & Tours',
    nav_settings: 'Settings & Guide',

    // Header & Quick Badges
    rep_label: 'Reputation',
    base_label: 'Home Base',
    op_month_label: 'Operating Month',
    xp_connected: 'XP12 CONNECTED',
    xp_offline: 'XP12 OFFLINE',
    flight_phase_board: 'BOARDING',
    flight_phase_taxi_out: 'TAXI OUT',
    flight_phase_takeoff: 'TAKEOFF',
    flight_phase_enroute: 'EN ROUTE',
    flight_phase_approach: 'APPROACH',
    flight_phase_landed: 'LANDED',
    flight_phase_parked: 'PARKED',

    // Setup Wizard
    wizard_title: 'INITIAL CONFIGURATION',
    wizard_subtitle: 'Create your airline profile and synchronize installed aircraft from X-Plane 12.',
    wizard_lang_select: 'Select Language & Currency / Scegli Lingua & Valuta',
    wizard_company_name: 'Airline Name *',
    wizard_company_placeholder: 'e.g. AeroSky Executive Ops',
    wizard_base_icao: 'Home Base (ICAO) *',
    wizard_capital_title: 'Starting Capital & Progression Level',
    wizard_econ_mode_title: 'Economy Model (Margins & Challenge):',
    wizard_econ_realistic: '🎯 REALISTIC (Recommended)',
    wizard_econ_realistic_desc: 'Authentic airline margins (4%–12%), engine/check-C reserves, FBO/Ground Handling, ANSP Navigation & IOC.',
    wizard_econ_standard: '🕹️ STANDARD (Relaxed)',
    wizard_econ_standard_desc: '+25% route revenue and -40% accessory costs for faster fleet growth.',
    wizard_simbrief_id: 'SimBrief Pilot ID / Username (Optional)',
    wizard_xp12_path: 'X-Plane 12 Main Directory (Optional if auto-detected)',
    wizard_sync_checkbox: 'Automatically scan X-Plane 12 Aircraft folder and populate Dealership & Leases',
    wizard_btn_submit: '✈️ Synchronize your X-Plane 12 & Create Airline Profile',

    // Difficulty Options
    diff_hardcore: 'Bush / Independent Pilot',
    diff_hardcore_desc: 'Minimal capital. Start by renting single-engine GA aircraft by the hour.',
    diff_realistic: 'Regional Start-up',
    diff_realistic_desc: 'Ideal to lease GA/BizJet or place a down payment on a small used plane.',
    diff_standard: 'Emerging Airline',
    diff_standard_desc: 'Sufficient budget to buy your first GA or start a VLJ lease.',
    diff_executive: 'Executive Operator',
    diff_executive_desc: 'Solid capital to acquire a Vision Jet or access mid-size Business Jets.',
    diff_magnate: 'Major Airline / Magnate',
    diff_magnate_desc: 'High budget to purchase BizJet fleets and commercial airliners.',

    // Common Buttons & Actions
    btn_start_flight: 'Start Flight Tracking',
    btn_stop_flight: 'Finish / Close Flight',
    btn_cancel_flight: 'Abort Tracking',
    btn_refuel: 'Refuel',
    btn_import_simbrief: 'Import SimBrief OFP',
    btn_lease: 'Dry Lease',
    btn_buy: 'Purchase Aircraft',
    btn_payoff: 'Pay Off Financing',
    btn_inspect: 'Perform Inspection',
    btn_repair: 'Repair',
    btn_filter: 'Filter',
    btn_save: 'Save',
    btn_cancel: 'Cancel',

    // Flight Rules
    rules_ifr: '🛫 IFR (ANSP & Handling)',
    rules_vfr: '🌤️ VFR (ANSP Exempt)',
    rules_ifr_title: 'IFR: applies regional ANSP navigation fees & pax handling',
    rules_vfr_title: 'VFR: exempt from ANSP navigation fees & pax handling',

    // Flight Summary & DOC (Direct Operating Costs)
    summary_title: 'Flight Closed & Trip P&L',
    doc_gross_revenue: '(+) Gross Commercial Revenue',
    doc_rep_bonus: 'Reputation & Landing Quality Bonus',
    doc_landing_fee: '(-) Landing Fee',
    doc_nav_fee: '(-) ANSP Route & Overflight Fee',
    doc_handling_fee: '(-) Ground Handling & FBO',
    doc_maint_reserve: '(-) Maintenance Reserves (Hourly)',
    doc_ioc: '(-) Indirect Costs (GDS/Broker/EU261)',
    doc_crew: '(-) Flight Crew',
    doc_penalty: '(-) Hard Landing Penalty / Pax Compensation',
    doc_net_profit: 'Trip Net Profit',
    exempt_vfr: '€ 0.00 (VFR Exempt)',
    exempt_faa: '€ 0.00 (FAA USA Exempt)',
    exempt_mtow: '€ 0.00 (< 2t Exempt)',

    // Touchdown Ratings
    td_butter: 'BUTTER LANDING',
    td_good: 'GOOD / NORMAL',
    td_hard: 'HARD LANDING',
    td_structural: 'STRUCTURAL DAMAGE',

    // Hangar & Fleet
    hangar_status_owned: 'Owned',
    hangar_status_leased: 'Leased',
    hangar_status_financed: 'Financed',
    hangar_airframe_hours: 'Airframe Hours',
    hangar_engine_hours: 'Engine Hours',
    hangar_fuel: 'Fuel on Board',
    hangar_location: 'Location',
    hangar_maintenance_status: 'Maintenance & Inspection Status',

    // Ledger & Finances
    ledger_title: 'Financial Ledger & Cash Flow',
    fixed_costs_title: 'Monthly Fixed Costs',
    hangar_cost: 'Hangar Space',
    insurance_cost: 'Hull & Liability Insurance',
    crew_salary: 'Salaried Crew Retainer',
    loan_payment: 'Financing Installment',

    // Tours & Logbook
    tours_title: 'Official & IVAO Tours Progress',
    logbook_title: 'Flight Logbook',
    total_hours: 'Total Flight Hours',
    total_flights: 'Completed Flights',
    avg_touchdown: 'Average Touchdown'
  },
  it: {
    // App Branding & Navigation
    app_title: 'SKYOPS XP12',
    app_subtitle: 'Piattaforma Operativa & Economica Reale per X-Plane 12',
    nav_cockpit: 'Plancia & HUD',
    nav_hangar: 'Hangar & Flotta',
    nav_jobs: 'Contratti & Mercato',
    nav_dealership: 'Concessionaria & Noleggio',
    nav_maintenance: 'Officina & Manutenzione',
    nav_finances: 'Finanze & Libro Mastro',
    nav_logbook: 'Logbook & Tour',
    nav_settings: 'Impostazioni & Info',

    // Header & Quick Badges
    rep_label: 'Reputazione',
    base_label: 'Base Operativa',
    op_month_label: 'Mese Operativo',
    xp_connected: 'XP12 COLLEGATO',
    xp_offline: 'XP12 DISCONNESSO',
    flight_phase_board: 'IMBARCO',
    flight_phase_taxi_out: 'RULLAGGIO OUT',
    flight_phase_takeoff: 'DECOLLO',
    flight_phase_enroute: 'IN VOLO (ROTA)',
    flight_phase_approach: 'AVVICINAMENTO',
    flight_phase_landed: 'ATTERRATO',
    flight_phase_parked: 'PARCHEGGIATO',

    // Setup Wizard
    wizard_title: 'CONFIGURAZIONE INIZIALE',
    wizard_subtitle: 'Crea il profilo della tua compagnia aerea e sincronizza gli aeromobili dal tuo X-Plane 12.',
    wizard_lang_select: 'Scegli Lingua & Valuta / Select Language & Currency',
    wizard_company_name: 'Nome della Società Aerea *',
    wizard_company_placeholder: 'es. AeroSky Executive Ops',
    wizard_base_icao: 'Base Operativa (ICAO) *',
    wizard_capital_title: 'Capitale Iniziale & Livello di Progressione',
    wizard_econ_mode_title: 'Modello Economico (Margini & Sfida):',
    wizard_econ_realistic: '🎯 REALISTICO (Consigliato)',
    wizard_econ_realistic_desc: 'Margini reali aviazione (4%–12%), riserve motori/check-C, FBO/Ground Handling, Eurocontrol & IOC.',
    wizard_econ_standard: '🕹️ STANDARD (Rilassato)',
    wizard_econ_standard_desc: 'Ricavi rotta +25% e costi accessori ridotti (-40%) per far crescere la flotta più rapidamente.',
    wizard_simbrief_id: 'SimBrief Pilot ID / Username (Opzionale)',
    wizard_xp12_path: 'Cartella Principale X-Plane 12 (Opzionale se rilevata)',
    wizard_sync_checkbox: 'Scansiona automaticamente la cartella Aircraft di X-Plane 12 e popola Mercato & Noleggio',
    wizard_btn_submit: '✈️ Sincronizza il tuo X-Plane 12 & Crea Profilo',

    // Difficulty Options
    diff_hardcore: 'Pilota Indipendente (Hardcore)',
    diff_hardcore_desc: 'Capitale minimo. Dovrai partire noleggiando piccoli monomotori GA a ore.',
    diff_realistic: 'Start-up Regionale (Realistica)',
    diff_realistic_desc: 'Perfetta per noleggiare GA/BizJet o versare l’anticipo di un piccolo usato.',
    diff_standard: 'Compagnia Emergente (Standard)',
    diff_standard_desc: 'Budget per acquistare subito il primo aereo GA o avviare un leasing VLJ.',
    diff_executive: 'Operatore Executive (Avanzato)',
    diff_executive_desc: 'Capitale solido per acquisire un Vision Jet o accedere ai Business Jet.',
    diff_magnate: 'Major Airline / Magnate',
    diff_magnate_desc: 'Alto capitale per acquistare flotta BizJet e Airliner commerciali.',

    // Common Buttons & Actions
    btn_start_flight: 'Avvia Monitoraggio Volo',
    btn_stop_flight: 'Termina / Chiudi Volo',
    btn_cancel_flight: 'Annulla Volo',
    btn_refuel: 'Rifornisci',
    btn_import_simbrief: 'Importa Piano SimBrief',
    btn_lease: 'Noleggia (Dry Lease)',
    btn_buy: 'Acquista Aeromobile',
    btn_payoff: 'Estingui Finanziamento',
    btn_inspect: 'Esegui Ispezione',
    btn_repair: 'Ripara',
    btn_filter: 'Filtra',
    btn_save: 'Salva',
    btn_cancel: 'Annulla',

    // Flight Rules
    rules_ifr: '🛫 IFR (Sorvolo & ANSP)',
    rules_vfr: '🌤️ VFR (Esente ANSP)',
    rules_ifr_title: 'IFR: applica tariffe ANSP di rotta ed handling passeggeri',
    rules_vfr_title: 'VFR: esente da tariffe di rotta ANSP ed handling passeggeri',

    // Flight Summary & DOC (Direct Operating Costs)
    summary_title: 'Chiusura Volo & Conto Economico',
    doc_gross_revenue: '(+) Ricavo Commerciale Lordo',
    doc_rep_bonus: 'Bonus Reputazione & Qualità Contatto',
    doc_landing_fee: '(-) Tassa di Atterraggio',
    doc_nav_fee: '(-) Navigazione & Sorvolo ANSP',
    doc_handling_fee: '(-) Handling FBO & Passeggeri',
    doc_maint_reserve: '(-) Riserva Manutenzione (Ore)',
    doc_ioc: '(-) Costi Indiretti (GDS/Broker/EU261)',
    doc_crew: '(-) Equipaggio Volo',
    doc_penalty: '(-) Penale Atterraggio Duro / Risarcimento Pax',
    doc_net_profit: 'Utile Netto Volo',
    exempt_vfr: '€ 0,00 (Esente VFR)',
    exempt_faa: '€ 0,00 (FAA USA Esente)',
    exempt_mtow: '€ 0,00 (< 2t Esente)',

    // Touchdown Ratings
    td_butter: 'BUTTER LANDING',
    td_good: 'GOOD / NORMALE',
    td_hard: 'HARD LANDING',
    td_structural: 'DANNO STRUTTURALE',

    // Hangar & Fleet
    hangar_status_owned: 'Di Proprietà',
    hangar_status_leased: 'In Noleggio',
    hangar_status_financed: 'Finanziato',
    hangar_airframe_hours: 'Ore Cellula',
    hangar_engine_hours: 'Ore Motore',
    hangar_fuel: 'Carburante a Bordo',
    hangar_location: 'Posizione Attuale',
    hangar_maintenance_status: 'Stato Manutenzione & Ispezioni',

    // Ledger & Finances
    ledger_title: 'Libro Mastro & Flusso di Cassa',
    fixed_costs_title: 'Costi Fissi Mensili',
    hangar_cost: 'Posto Hangar',
    insurance_cost: 'Assicurazione Kasko & RC',
    crew_salary: 'Stipendio Equipaggio Fisso',
    loan_payment: 'Rata Finanziamento',

    // Tours & Logbook
    tours_title: 'Avanzamento Tour & Sfide',
    logbook_title: 'Registro di Volo (Logbook)',
    total_hours: 'Ore di Volo Totali',
    total_flights: 'Voli Completati',
    avg_touchdown: 'Media Touchdown'
  }
};

export const getTranslation = (lang, key, fallback = '') => {
  const selectedLang = lang === 'it' ? 'it' : 'en';
  return translations[selectedLang]?.[key] || translations['en']?.[key] || fallback || key;
};
