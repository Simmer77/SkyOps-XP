import os
import re
import hashlib
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app.models.schema import MarketAircraft

logger = logging.getLogger("SkyOps.XPScanner")

LBS_TO_KG = 0.45359237

# Curated real-world aviation database for accurate pricing, lease rates, engines, and avionics
REAL_AIRCRAFT_DB: Dict[str, Dict[str, Any]] = {
    "C172": {
        "manufacturer": "Cessna",
        "category": "GA",
        "year": 2018,
        "price_eur": 345000.0,
        "lease_eur_h": 165.0,
        "cruise_kts": 122,
        "engine": "1x Lycoming IO-360-L2A (180 HP)",
        "avionics": "Garmin G1000 NXi Integrated Flight Deck",
        "hours": 840.0,
        "condition": 93.5,
        "desc": "Il velivolo da addestramento e turismo più diffuso al mondo. Affidabile, economico e ideale per iniziare."
    },
    "DR40": {
        "manufacturer": "Robin Aircraft",
        "category": "GA",
        "year": 2019,
        "price_eur": 285000.0,
        "lease_eur_h": 145.0,
        "cruise_kts": 135,
        "engine": "1x Continental CD-155 Jet-A1 Diesel (155 HP)",
        "avionics": "Garmin G500 / GTN650 Avionics",
        "hours": 620.0,
        "condition": 95.0,
        "desc": "Monomotore francese a ala bassa con motore diesel Jet-A1 ad bassissimo consumo specifico."
    },
    "SR22": {
        "manufacturer": "Cirrus",
        "category": "GA",
        "year": 2021,
        "price_eur": 780000.0,
        "lease_eur_h": 275.0,
        "cruise_kts": 183,
        "engine": "1x Continental IO-550-N (310 HP)",
        "avionics": "Cirrus Perspective+ by Garmin",
        "hours": 410.0,
        "condition": 96.5,
        "desc": "Monomotore ad alte prestazioni con paracadute balistico CAPS e avionica glass cockpit."
    },
    "SF50": {
        "manufacturer": "Cirrus",
        "category": "GA",
        "year": 2022,
        "price_eur": 2450000.0,
        "lease_eur_h": 460.0,
        "cruise_kts": 305,
        "engine": "1x Williams International FJ33-5A Turbofan",
        "avionics": "Cirrus Perspective Touch+ (Garmin G3000)",
        "hours": 180.0,
        "condition": 98.0,
        "desc": "Personal Jet monomotore a reazione con cabina pressurizzata, autothrottle e paracadute CAPS."
    },
    "BE58": {
        "manufacturer": "Beechcraft",
        "category": "GA",
        "year": 2016,
        "price_eur": 1120000.0,
        "lease_eur_h": 340.0,
        "cruise_kts": 200,
        "engine": "2x Continental IO-550-C (300 HP cad.)",
        "avionics": "Garmin G1000 NXi Twin Engine Suite",
        "hours": 1240.0,
        "condition": 91.0,
        "desc": "Bimotore a pistoni executive di riferimento per velocità, carico utile e affidabilità."
    },
    "BE9L": {
        "manufacturer": "Beechcraft",
        "category": "GA",
        "year": 2014,
        "price_eur": 2850000.0,
        "lease_eur_h": 650.0,
        "cruise_kts": 270,
        "engine": "2x Pratt & Whitney PT6A-135A Turboprop",
        "avionics": "Rockwell Collins Pro Line 21",
        "hours": 2450.0,
        "condition": 89.5,
        "desc": "Biturboelica leggero pressurizzato capace di operare anche da piste corte non preparate."
    },
    "C90B": {
        "manufacturer": "Beechcraft",
        "category": "GA",
        "year": 2014,
        "price_eur": 2850000.0,
        "lease_eur_h": 650.0,
        "cruise_kts": 270,
        "engine": "2x Pratt & Whitney PT6A-21 Turboprop",
        "avionics": "Collins EFIS-84 / Garmin GTN750",
        "hours": 2650.0,
        "condition": 88.5,
        "desc": "Leggendario biturboelica executive King Air ideale per collegamenti regionali e VIP."
    },
    "PA18": {
        "manufacturer": "Piper",
        "category": "GA",
        "year": 1998,
        "price_eur": 145000.0,
        "lease_eur_h": 115.0,
        "cruise_kts": 100,
        "engine": "1x Lycoming O-320 (150 HP)",
        "avionics": "Analogica Classica VFR / VOR",
        "hours": 3120.0,
        "condition": 86.0,
        "desc": "Aereo bush STOL iconico, perfetto per piste in erba, montagna e piccoli aeroporti remoti."
    },
    "RV10": {
        "manufacturer": "Van's Aircraft",
        "category": "GA",
        "year": 2020,
        "price_eur": 295000.0,
        "lease_eur_h": 155.0,
        "cruise_kts": 175,
        "engine": "1x Lycoming IO-540-D4A5 (260 HP)",
        "avionics": "Garmin G3X Touch Experimental",
        "hours": 350.0,
        "condition": 96.0,
        "desc": "Quadriposto veloce ad alta efficienza aerodinamica ideale per voli cross-country."
    },
    "EVO": {
        "manufacturer": "Lancair",
        "category": "GA",
        "year": 2019,
        "price_eur": 1280000.0,
        "lease_eur_h": 390.0,
        "cruise_kts": 300,
        "engine": "1x Pratt & Whitney PT6A-135A Turboprop (750 SHP)",
        "avionics": "Garmin G900X Dual Display",
        "hours": 510.0,
        "condition": 94.5,
        "desc": "Turboprop sperimentale in fibra di carbonio con prestazioni velocistiche da jet leggero."
    },
    "EVOT": {
        "manufacturer": "Lancair",
        "category": "GA",
        "year": 2019,
        "price_eur": 1280000.0,
        "lease_eur_h": 390.0,
        "cruise_kts": 300,
        "engine": "1x Pratt & Whitney PT6A-135A Turboprop (750 SHP)",
        "avionics": "Garmin G900X Dual Display",
        "hours": 510.0,
        "condition": 94.5,
        "desc": "Turboprop sperimentale in fibra di carbonio con prestazioni velocistiche da jet leggero."
    },
    "E55P": {
        "manufacturer": "Embraer",
        "category": "BIZJET",
        "year": 2021,
        "price_eur": 8950000.0,
        "lease_eur_h": 1150.0,
        "cruise_kts": 453,
        "engine": "2x Pratt & Whitney Canada PW535E1",
        "avionics": "Prodigy Touch Flight Deck (Garmin G3000)",
        "hours": 780.0,
        "condition": 95.5,
        "desc": "Il light business jet più venduto al mondo. Autonomia intereuropea e prestazioni eccellenti in salita."
    },
    "C750": {
        "manufacturer": "Cessna",
        "category": "BIZJET",
        "year": 2015,
        "price_eur": 12400000.0,
        "lease_eur_h": 1650.0,
        "cruise_kts": 527,
        "engine": "2x Rolls-Royce AE 3007C2 Turbofan",
        "avionics": "Honeywell Primus 2000 / Garmin G5000",
        "hours": 2890.0,
        "condition": 90.0,
        "desc": "Business jet transcontinentale ad altissima velocità di crociera (Mach 0.935)."
    },
    "E35L": {
        "manufacturer": "Embraer",
        "category": "BIZJET",
        "year": 2017,
        "price_eur": 16800000.0,
        "lease_eur_h": 2100.0,
        "cruise_kts": 450,
        "engine": "2x Rolls-Royce AE 3007A2 Turbofan",
        "avionics": "Honeywell Primus Elite Avionics Suite",
        "hours": 2150.0,
        "condition": 92.5,
        "desc": "Heavy Business Jet a lungo raggio con cabina a tre zone e oltre 3.900 NM di autonomia."
    },
    "A319": {
        "manufacturer": "Airbus",
        "category": "AIRLINER",
        "year": 2016,
        "price_eur": 34500000.0,
        "lease_eur_h": 2350.0,
        "cruise_kts": 450,
        "engine": "2x CFM56-5B6 / IAE V2524-A5",
        "avionics": "Airbus Fly-By-Wire / Thales FMS",
        "hours": 11400.0,
        "condition": 91.5,
        "desc": "Airliner narrow-body corto/medio raggio ad alta efficienza operativa e certificazione ETOPS."
    },
    "B738": {
        "manufacturer": "Boeing",
        "category": "AIRLINER",
        "year": 2015,
        "price_eur": 38000000.0,
        "lease_eur_h": 2480.0,
        "cruise_kts": 455,
        "engine": "2x CFM International CFM56-7B26",
        "avionics": "Honeywell CDS / Collins FMC",
        "hours": 14200.0,
        "condition": 91.0,
        "desc": "Il pilastro mondiale del trasporto commerciale medio raggio. Capienza fino a 189 passeggeri."
    },
    "MD82": {
        "manufacturer": "McDonnell Douglas",
        "category": "AIRLINER",
        "year": 1996,
        "price_eur": 6800000.0,
        "lease_eur_h": 1750.0,
        "cruise_kts": 438,
        "engine": "2x Pratt & Whitney JT8D-217C",
        "avionics": "Honeywell EFIS / FMS Classico",
        "hours": 28400.0,
        "condition": 84.0,
        "desc": "Classico jet bimotore con motori in coda. Prezzo d'acquisto contenuto, ideale per charter cargo/pax economici."
    },
    "A333": {
        "manufacturer": "Airbus",
        "category": "AIRLINER",
        "year": 2014,
        "price_eur": 68000000.0,
        "lease_eur_h": 4200.0,
        "cruise_kts": 470,
        "engine": "2x Rolls-Royce Trent 772B-60",
        "avionics": "Airbus Fly-By-Wire Widebody Suite",
        "hours": 19800.0,
        "condition": 90.0,
        "desc": "Widebody intercontinentale a doppio corridoio per grandi tratte cargo e passeggeri lungo raggio."
    },
    "DA42": {
        "manufacturer": "Diamond",
        "category": "GA",
        "year": 2020,
        "price_eur": 790000.0,
        "lease_eur_h": 295.0,
        "cruise_kts": 190,
        "engine": "2x Austro Engine AE300 Jet-A1 Diesel",
        "avionics": "Garmin G1000 NXi Twin Engine Suite",
        "hours": 450.0,
        "condition": 96.0,
        "desc": "Bimotore leggero in fibra di carbonio con motori Jet-A1 ad altissima efficienza."
    },
    "DA50": {
        "manufacturer": "Diamond",
        "category": "GA",
        "year": 2022,
        "price_eur": 920000.0,
        "lease_eur_h": 310.0,
        "cruise_kts": 181,
        "engine": "1x Continental CD-300 Jet-A1 (300 HP)",
        "avionics": "Garmin G1000 NXi + GFC700",
        "hours": 240.0,
        "condition": 97.5,
        "desc": "Monomotore retrattile di lusso a 5 posti alimentato a cherosene Jet-A1."
    },
    "DA62": {
        "manufacturer": "Diamond",
        "category": "GA",
        "year": 2021,
        "price_eur": 1290000.0,
        "lease_eur_h": 385.0,
        "cruise_kts": 192,
        "engine": "2x Austro Engine AE330 Jet-A1 Diesel (360 HP tot.)",
        "avionics": "Garmin G1000 NXi 3-Axis Autopilot",
        "hours": 390.0,
        "condition": 96.5,
        "desc": "SUV dei cieli bimotore a 7 posti con autonomia superiore a 1.200 NM."
    },
    "TBM9": {
        "manufacturer": "Daher",
        "category": "GA",
        "year": 2020,
        "price_eur": 3950000.0,
        "lease_eur_h": 790.0,
        "cruise_kts": 330,
        "engine": "1x Pratt & Whitney PT6A-66D Turboprop (850 SHP)",
        "avionics": "Garmin G1000 NXi / Autothrottle",
        "hours": 610.0,
        "condition": 95.5,
        "desc": "Il monoturbina più veloce della categoria: prestazioni da light jet con consumi ridotti."
    },
    "PC12": {
        "manufacturer": "Pilatus",
        "category": "GA",
        "year": 2019,
        "price_eur": 4450000.0,
        "lease_eur_h": 820.0,
        "cruise_kts": 285,
        "engine": "1x Pratt & Whitney PT6A-67P Turboprop",
        "avionics": "Honeywell Primus Apex Executive",
        "hours": 1150.0,
        "condition": 94.0,
        "desc": "Monoturbina svizzero versatile per missioni VIP, cargo e aeroporti alpini/corti."
    },
    "PC24": {
        "manufacturer": "Pilatus",
        "category": "BIZJET",
        "year": 2022,
        "price_eur": 10800000.0,
        "lease_eur_h": 1450.0,
        "cruise_kts": 440,
        "engine": "2x Williams FJ44-4A-QPM Turbofan",
        "avionics": "Pilatus ACE (Honeywell Primus Epic)",
        "hours": 420.0,
        "condition": 97.0,
        "desc": "Super Versatile Jet capace di atterrare su piste corte e non asfaltate con portellone cargo."
    },
    "P06T": {
        "manufacturer": "Tecnam",
        "category": "GA",
        "year": 2019,
        "price_eur": 560000.0,
        "lease_eur_h": 240.0,
        "cruise_kts": 145,
        "engine": "2x Rotax 912 S3 (100 HP cad.)",
        "avionics": "Garmin G950 IFR Twin",
        "hours": 780.0,
        "condition": 94.5,
        "desc": "Bimotore leggero italiano dai costi operativi minimi, perfetto per scuola e collegamenti brevi."
    },
    "P212": {
        "manufacturer": "Tecnam",
        "category": "GA",
        "year": 2021,
        "price_eur": 2450000.0,
        "lease_eur_h": 540.0,
        "cruise_kts": 194,
        "engine": "2x Lycoming TEO-540-C1A",
        "avionics": "Garmin G1000 NXi Airline Commuter",
        "hours": 950.0,
        "condition": 95.0,
        "desc": "Commuter italiano a 11 posti progettato per rotte regionali e collegamenti isole."
    },
    "CL60": {
        "manufacturer": "Bombardier",
        "category": "BIZJET",
        "year": 2018,
        "price_eur": 19500000.0,
        "lease_eur_h": 2650.0,
        "cruise_kts": 470,
        "engine": "2x General Electric CF34-3B Turbofan",
        "avionics": "Collins Pro Line 21 Advanced",
        "hours": 1850.0,
        "condition": 94.0,
        "desc": "Heavy Business Jet transatlantico (Challenger 650) di riferimento mondiale per comfort ed autonomia."
    },
    "CRJ7": {
        "manufacturer": "Bombardier",
        "category": "AIRLINER",
        "year": 2013,
        "price_eur": 18500000.0,
        "lease_eur_h": 1750.0,
        "cruise_kts": 447,
        "engine": "2x GE CF34-8C5B1",
        "avionics": "Collins Pro Line 4 Regional Jet",
        "hours": 16200.0,
        "condition": 89.5,
        "desc": "Regional Jet da 70-78 passeggeri veloce ed agile per collegamenti nazionali e secondari."
    },
    "CRJ9": {
        "manufacturer": "Bombardier",
        "category": "AIRLINER",
        "year": 2015,
        "price_eur": 22500000.0,
        "lease_eur_h": 1920.0,
        "cruise_kts": 450,
        "engine": "2x GE CF34-8C5A1",
        "avionics": "Collins Pro Line 4 Regional Jet",
        "hours": 14100.0,
        "condition": 91.0,
        "desc": "Regional Jet allungato fino a 90 passeggeri ideale per feeder aeroportuali."
    },
    "FA50": {
        "manufacturer": "Dassault",
        "category": "BIZJET",
        "year": 2005,
        "price_eur": 6500000.0,
        "lease_eur_h": 1550.0,
        "cruise_kts": 465,
        "engine": "3x Honeywell TFE731-40",
        "avionics": "Collins Pro Line 4",
        "hours": 4800.0,
        "condition": 89.0,
        "desc": "Iconico tri-jet executive francese capace di operare anche da piste impegnative."
    },
    "FA8X": {
        "manufacturer": "Dassault",
        "category": "BIZJET",
        "year": 2021,
        "price_eur": 42000000.0,
        "lease_eur_h": 3450.0,
        "cruise_kts": 488,
        "engine": "3x Pratt & Whitney PW307D",
        "avionics": "EASy III Flight Deck (Honeywell Primus Epic)",
        "hours": 650.0,
        "condition": 97.5,
        "desc": "Tri-jet ammiraglia ultra-lungo raggio (6.450 NM) con cabina fly-by-wire."
    },
    "A320": {
        "manufacturer": "Airbus",
        "category": "AIRLINER",
        "year": 2016,
        "price_eur": 39500000.0,
        "lease_eur_h": 2450.0,
        "cruise_kts": 450,
        "engine": "2x CFM56-5B4 / IAE V2527-A5",
        "avionics": "Airbus Fly-By-Wire / Thales FMS",
        "hours": 12400.0,
        "condition": 92.0,
        "desc": "Il re del medio raggio commerciale europeo. Capacità fino a 180 passeggeri."
    },
    "A20N": {
        "manufacturer": "Airbus",
        "category": "AIRLINER",
        "year": 2022,
        "price_eur": 54000000.0,
        "lease_eur_h": 2680.0,
        "cruise_kts": 455,
        "engine": "2x Pratt & Whitney PW1127G / CFM LEAP-1A",
        "avionics": "Airbus Fly-By-Wire Neo Suite",
        "hours": 3200.0,
        "condition": 96.5,
        "desc": "A320neo di nuova generazione con consumi ridotti del 15-20% sulle rotte di linea."
    },
    "A321": {
        "manufacturer": "Airbus",
        "category": "AIRLINER",
        "year": 2018,
        "price_eur": 46500000.0,
        "lease_eur_h": 2750.0,
        "cruise_kts": 452,
        "engine": "2x CFM56-5B3 / IAE V2533",
        "avionics": "Airbus Fly-By-Wire",
        "hours": 9800.0,
        "condition": 93.0,
        "desc": "Airliner narrow-body ad alta capacità fino a 220 passeggeri."
    },
    "A21N": {
        "manufacturer": "Airbus",
        "category": "AIRLINER",
        "year": 2023,
        "price_eur": 62000000.0,
        "lease_eur_h": 2950.0,
        "cruise_kts": 455,
        "engine": "2x CFM LEAP-1A32 / PW1133G",
        "avionics": "Airbus Fly-By-Wire LR/XLR",
        "hours": 1950.0,
        "condition": 97.5,
        "desc": "A321neo a lungo raggio capace di rotte transatlantiche leggere ed europee ad alta densità."
    },
    "A346": {
        "manufacturer": "Airbus",
        "category": "AIRLINER",
        "year": 2009,
        "price_eur": 44000000.0,
        "lease_eur_h": 4650.0,
        "cruise_kts": 475,
        "engine": "4x Rolls-Royce Trent 556-61",
        "avionics": "Airbus Quad-Jet Long Haul",
        "hours": 32000.0,
        "condition": 87.5,
        "desc": "Quadrimotore lungo raggio da oltre 75 metri di fusoliera per rotte intercontinentali."
    },
    "A359": {
        "manufacturer": "Airbus",
        "category": "AIRLINER",
        "year": 2021,
        "price_eur": 115000000.0,
        "lease_eur_h": 5400.0,
        "cruise_kts": 488,
        "engine": "2x Rolls-Royce Trent XWB-84",
        "avionics": "Airbus Next-Gen 6-Display Glass Cockpit",
        "hours": 5800.0,
        "condition": 96.0,
        "desc": "Widebody di ultima generazione in composito carbonio per collegamenti ultra-long haul."
    },
    "B752": {
        "manufacturer": "Boeing",
        "category": "AIRLINER",
        "year": 2002,
        "price_eur": 19500000.0,
        "lease_eur_h": 2650.0,
        "cruise_kts": 460,
        "engine": "2x Rolls-Royce RB211-535E4 / PW2040",
        "avionics": "Honeywell Pegasus / Classic EFIS",
        "hours": 29400.0,
        "condition": 86.5,
        "desc": "Narrow-body potente ad altissime prestazioni in decollo, ricercatissimo anche per cargo."
    },
    "B763": {
        "manufacturer": "Boeing",
        "category": "AIRLINER",
        "year": 2008,
        "price_eur": 36000000.0,
        "lease_eur_h": 3450.0,
        "cruise_kts": 465,
        "engine": "2x GE CF6-80C2 / PW4060",
        "avionics": "Honeywell Boeing EFIS Widebody",
        "hours": 24800.0,
        "condition": 88.5,
        "desc": "Widebody bimotore transatlantico ETOPS di grandissima versatilità passeggeri e merci."
    },
    "B77W": {
        "manufacturer": "Boeing",
        "category": "AIRLINER",
        "year": 2018,
        "price_eur": 98000000.0,
        "lease_eur_h": 5100.0,
        "cruise_kts": 485,
        "engine": "2x General Electric GE90-115B",
        "avionics": "Honeywell 777 Glass Cockpit",
        "hours": 11500.0,
        "condition": 94.0,
        "desc": "Ammiraglia bicorridoio a lungo raggio con i motori più potenti al mondo."
    },
    "MD11": {
        "manufacturer": "McDonnell Douglas",
        "category": "AIRLINER",
        "year": 1998,
        "price_eur": 24000000.0,
        "lease_eur_h": 3700.0,
        "cruise_kts": 472,
        "engine": "3x GE CF6-80C2 / PW4460",
        "avionics": "Honeywell VIA 2000 Tri-Jet Glass Cockpit",
        "hours": 34200.0,
        "condition": 85.0,
        "desc": "Leggendario trimotore cargo/passeggeri a lungo raggio per grandi spedizioni intercontinentali."
    },
    "DH8D": {
        "manufacturer": "De Havilland",
        "category": "AIRLINER",
        "year": 2016,
        "price_eur": 16500000.0,
        "lease_eur_h": 1480.0,
        "cruise_kts": 360,
        "engine": "2x Pratt & Whitney PW150A Turboprop (5.071 SHP)",
        "avionics": "Thales / Universal UNS-1Ew Flight Deck",
        "hours": 11200.0,
        "condition": 91.5,
        "desc": "Turboelica regionale ad alta velocità (Q400) capace di operare su piste corte."
    },
    "AT76": {
        "manufacturer": "ATR",
        "category": "AIRLINER",
        "year": 2019,
        "price_eur": 17800000.0,
        "lease_eur_h": 1420.0,
        "cruise_kts": 275,
        "engine": "2x Pratt & Whitney PW127M Turboprop",
        "avionics": "Thales New Avionics Suite (ATR-600)",
        "hours": 6800.0,
        "condition": 94.5,
        "desc": "Il turboelica regionale più diffuso ed economico per rotte brevi ed isole."
    }
}

BIZJET_ICAOS = {
    "E55P", "E50P", "E35L", "C750", "C56X", "C525", "C510", "C25A", "C25B",
    "C25C", "CL30", "CL60", "GL5T", "GLEX", "FA50", "FA7X", "F900", "EA50",
    "LJ45", "LJ75", "HDJT", "PRM1", "PC24", "E550", "C680", "C68A", "GLF4", "GLF5", "G550", "G650"
}

AIRLINER_ICAOS = {
    "A318", "A319", "A320", "A20N", "A321", "A21N", "A332", "A333", "A339", "A343", "A346", "A359", "A388",
    "B712", "B733", "B734", "B735", "B736", "B737", "B738", "B739", "B38M", "B744", "B748", "B752", "B763",
    "B772", "B77W", "B788", "B789", "MD80", "MD82", "MD83", "MD88", "MD11", "E170", "E175", "E190", "E195",
    "CRJ2", "CRJ7", "CRJ9", "AT75", "AT76", "DH8D", "B463", "RJ85", "BCS1", "BCS3"
}

SKIP_KEYWORDS = ["f-14", "f14", "f-4", "f4", "ask21", "aerolite", "alia-250", "r22", "s-76", "sikorsky", "robinson"]


class XP12ScannerService:
    @staticmethod
    def detect_xp12_path() -> Optional[str]:
        """Auto-detects X-Plane 12 root installation directory across Linux, macOS, and Windows."""
        candidates: List[Path] = []
        
        # 1. Official X-Plane 12 install registry file
        home = Path.home()
        linux_reg = home / ".x-plane" / "x-plane_install_12.txt"
        mac_reg = home / "Library" / "Preferences" / "x-plane_install_12.txt"
        win_reg = Path(os.environ.get("LOCALAPPDATA", "")) / "x-plane_install_12.txt"
        
        for reg_file in [linux_reg, mac_reg, win_reg]:
            if reg_file.exists() and reg_file.is_file():
                try:
                    lines = reg_file.read_text(encoding="utf-8", errors="ignore").splitlines()
                    for line in lines:
                        p = line.strip()
                        if p and Path(p).exists() and (Path(p) / "Aircraft").exists():
                            return str(Path(p))
                except Exception:
                    pass
                    
        # 2. Common default folders
        common_paths = [
            Path("/mnt/games/SteamLibrary/steamapps/common/X-Plane 12"),
            home / ".local/share/Steam/steamapps/common/X-Plane 12",
            home / "X-Plane 12",
            home / "Desktop/X-Plane 12",
            Path("/Applications/X-Plane 12"),
            Path("C:/X-Plane 12"),
            Path("D:/X-Plane 12"),
            Path("C:/Program Files (x86)/Steam/steamapps/common/X-Plane 12"),
        ]
        for cp in common_paths:
            if cp.exists() and (cp / "Aircraft").exists():
                return str(cp)
                
        return None

    @staticmethod
    def _parse_acf_file(acf_path: Path) -> Optional[Dict[str, Any]]:
        """Extracts metadata from an X-Plane 12 .acf file."""
        try:
            props: Dict[str, str] = {}
            with open(acf_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.startswith("P acf/_"):
                        parts = line.strip().split(" ", 2)
                        if len(parts) >= 3:
                            key = parts[1].replace("acf/_", "")
                            props[key] = parts[2].strip()
            return props
        except Exception as e:
            logger.warning(f"Failed to parse ACF {acf_path}: {e}")
            return None

    @staticmethod
    def _classify_and_enrich(acf_path: Path, props: Dict[str, str], icons_dest_dir: Path) -> Optional[Dict[str, Any]]:
        """Normalizes parsed ACF metadata and generates realistic economic values."""
        name = props.get("name") or acf_path.stem.replace("_", " ")
        icao = props.get("ICAO", "").upper().strip()
        raw_manuf = props.get("manufacturer", "").strip()
        studio = props.get("studio", "").strip()
        is_heli = props.get("is_helicopter", "0") == "1"
        is_airliner_flag = props.get("is_airliner", "0") == "1"
        
        # Skip military, gliders, ultralights, helicopters for GA/BizJet/Airliner civil fleet
        lower_check = f"{name} {icao} {acf_path.name}".lower()
        if is_heli or any(k in lower_check for k in SKIP_KEYWORDS):
            return None
            
        # Numeric fields
        def to_f(val: str, default: float) -> float:
            try:
                return float(val)
            except Exception:
                return default
                
        fuel_lbs = to_f(props.get("m_fuel_max_tot", "2000"), 2000.0)
        mtow_lbs = to_f(props.get("m_max", "6000"), 6000.0)
        vno_kts = to_f(props.get("Vno_kts", "200"), 200.0)
        num_engines = int(to_f(props.get("num_engn", "1"), 1.0))
        
        fuel_kg = max(80.0, round(fuel_lbs * LBS_TO_KG, 1))
        mtow_kg = max(600.0, round(mtow_lbs * LBS_TO_KG, 1))
        
        # Map known missing ICAOs
        if not icao:
            if "dr401" in lower_check:
                icao = "DR40"
            elif "lancair" in lower_check or "evolution" in lower_check:
                icao = "EVO"
            elif "king air" in lower_check or "c90" in lower_check:
                icao = "C90B"
            elif "baron" in lower_check:
                icao = "BE58"
            elif "rv-10" in lower_check or "rv10" in lower_check:
                icao = "RV10"
            elif "sr22" in lower_check:
                icao = "SR22"
            elif "pa-18" in lower_check:
                icao = "PA18"
            elif "c172" in lower_check or "172" in lower_check:
                icao = "C172"
            else:
                icao = acf_path.stem[:4].upper()

        # Look up curated specs
        curated = REAL_AIRCRAFT_DB.get(icao)
        
        # Determine category
        if curated:
            category = curated["category"]
        elif icao in AIRLINER_ICAOS or (is_airliner_flag and mtow_kg > 24000):
            category = "AIRLINER"
        elif icao in BIZJET_ICAOS or (num_engines >= 2 and mtow_kg > 4800 and mtow_kg <= 42000 and vno_kts >= 240):
            category = "BIZJET"
        else:
            category = "GA"

        # Normalize manufacturer cleanly
        manufacturer = raw_manuf
        if curated:
            manufacturer = curated["manufacturer"]
        elif not manufacturer:
            for m in ["Airbus", "Boeing", "Embraer", "Cessna", "Cirrus", "Beechcraft", "Piper", "Diamond", "Daher", "Socata", "Tecnam", "Bombardier", "Dassault", "Gulfstream", "Pilatus", "ATR", "De Havilland", "Robin", "Mooney", "Lancair", "Saab", "Fokker", "McDonnell Douglas"]:
                if m.lower() in f"{name} {acf_path.parent.name}".lower():
                    manufacturer = m
                    break
            if not manufacturer:
                manufacturer = studio or "Altro Costruttore"
                
        if manufacturer.lower() in ["beech", "beechcraft"]:
            manufacturer = "Beechcraft"
        elif "robin" in manufacturer.lower():
            manufacturer = "Robin Aircraft"
        elif "mcdonnell" in manufacturer.lower():
            manufacturer = "McDonnell Douglas"
        elif "van" in manufacturer.lower():
            manufacturer = "Van's Aircraft"

        # Pricing & Specs
        if curated:
            year = curated["year"]
            price_eur = curated["price_eur"]
            lease_eur_h = curated["lease_eur_h"]
            cruise_kts = curated["cruise_kts"]
            engine_type = curated["engine"]
            avionics_system = curated["avionics"]
            hours = curated["hours"]
            condition = curated["condition"]
            desc = curated["desc"]
        else:
            # Realistic dynamic fallback by category & MTOW
            if category == "AIRLINER":
                year = 2015
                price_eur = round(max(15000000.0, mtow_kg * 520.0), -4)
                lease_eur_h = round(max(1600.0, mtow_kg * 0.035), -1)
                cruise_kts = max(420, int(vno_kts * 1.25))
                engine_type = f"{num_engines}x High-Bypass Turbofan"
                avionics_system = "Glass Cockpit EFIS / FMS"
                hours = 12000.0
                condition = 91.0
                desc = f"Aeromobile commerciale di linea ({icao}) rilevato da X-Plane 12."
            elif category == "BIZJET":
                year = 2019
                price_eur = round(max(4500000.0, mtow_kg * 950.0), -4)
                lease_eur_h = round(max(750.0, mtow_kg * 0.12), -1)
                cruise_kts = max(380, int(vno_kts * 1.25))
                engine_type = f"{num_engines}x Executive Turbofan"
                avionics_system = "Prodigy / Garmin Executive Suite"
                hours = 1100.0
                condition = 94.0
                desc = f"Business Jet executive ({icao}) rilevato da X-Plane 12."
            else:
                year = 2018
                price_eur = round(max(180000.0, mtow_kg * 195.0), -3)
                lease_eur_h = round(max(135.0, mtow_kg * 0.085), -1)
                cruise_kts = max(110, int(vno_kts))
                engine_type = f"{num_engines}x {'Turbofan / Turboprop' if vno_kts > 210 else 'Aviazione Generale Pistoni'}"
                avionics_system = "Garmin Glass Cockpit / IFR Suite"
                hours = 650.0
                condition = 94.0
                desc = f"Aeromobile General Aviation ({icao}) rilevato da X-Plane 12."

        # Check for X-Plane 12 preview icon PNG in aircraft directory
        image_url = ""
        stem = acf_path.stem
        icon_candidates = [
            acf_path.parent / f"{stem}_icon11.png",
            acf_path.parent / f"{stem}_icon11_thumb.png",
        ]
        # fallback: any *_icon11.png in parent directory
        if not any(p.exists() for p in icon_candidates):
            for png in acf_path.parent.glob("*_icon11.png"):
                icon_candidates.append(png)
                break

        for ic in icon_candidates:
            if ic.exists() and ic.is_file():
                os.makedirs(icons_dest_dir, exist_ok=True)
                path_hash = hashlib.md5(str(acf_path).encode("utf-8")).hexdigest()[:10]
                dest_name = f"xp_{icao.lower()}_{path_hash}.png"
                dest_path = icons_dest_dir / dest_name
                try:
                    shutil.copy2(ic, dest_path)
                    image_url = f"/uploads/xp_icons/{dest_name}"
                    break
                except Exception as e:
                    logger.warning(f"Failed copying icon {ic}: {e}")

        tail = props.get("tailnum", "").strip()
        if not tail or len(tail) < 3:
            tail = f"I-{icao[:3]}"

        # Distinguish custom variants cleanly
        display_name = name
        if "g1000" in acf_path.stem.lower() and "g1000" not in display_name.lower():
            display_name = f"{display_name} (G1000)"
        elif "seaplane" in acf_path.stem.lower() and "seaplane" not in display_name.lower() and "floats" not in display_name.lower():
            display_name = f"{display_name} (Seaplane)"
        elif "4k" in acf_path.stem.lower() and "4k" not in display_name.lower():
            display_name = f"{display_name} (4K)"

        return {
            "acf_path": str(acf_path),
            "name": display_name,
            "aircraft_type": icao,
            "manufacturer": manufacturer,
            "studio": studio,
            "category": category,
            "fuel_capacity_kg": fuel_kg,
            "mtow_kg": mtow_kg,
            "cruise_speed_kts": cruise_kts,
            "num_engines": num_engines,
            "engine_type": engine_type,
            "avionics_system": avionics_system,
            "year_manufactured": year,
            "airframe_hours": hours,
            "condition_pct": condition,
            "is_used": hours > 200.0,
            "purchase_price_eur": price_eur,
            "hourly_lease_rate_eur": lease_eur_h,
            "image_url": image_url,
            "default_tail": tail,
            "description": desc,
        }

    @classmethod
    async def scan_and_sync_to_db(cls, session: AsyncSession, xp12_root_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Scans the user's X-Plane 12/Aircraft directory, parses all civil aircraft .acf files,
        copies preview thumbnails, and populates the MarketAircraft catalog table.
        """
        root_str = xp12_root_path.strip() if xp12_root_path else ""
        if not root_str:
            root_str = cls.detect_xp12_path() or ""
            
        if not root_str or not Path(root_str).exists():
            return {
                "success": False,
                "error": "Percorso X-Plane 12 non trovato. Specifica la cartella principale di X-Plane 12.",
                "count": 0,
                "xp12_path": root_str
            }
            
        aircraft_dir = Path(root_str) / "Aircraft"
        if not aircraft_dir.exists():
            # Maybe user pointed directly to Aircraft folder
            if Path(root_str).name == "Aircraft":
                aircraft_dir = Path(root_str)
            else:
                return {
                    "success": False,
                    "error": f"Cartella 'Aircraft' non trovata dentro {root_str}",
                    "count": 0,
                    "xp12_path": root_str
                }

        icons_dest_dir = Path(__file__).resolve().parent.parent / "static" / "uploads" / "xp_icons"
        os.makedirs(icons_dest_dir, exist_ok=True)

        discovered_files: List[Path] = []
        for root_dir, dirs, files in os.walk(aircraft_dir):
            # Ignore plugin folders
            if "plugins" in Path(root_dir).parts:
                continue
            acf_in_dir = [f for f in files if f.lower().endswith(".acf")]
            for fname in acf_in_dir:
                low = fname.lower()
                # Skip XP11, AI, StdDef, mariner/4k duplicates if base file exists
                if "_xp11" in low or "_ai." in low or "_stddef" in low or "_mariner" in low:
                    continue
                if "_4k.acf" in low and fname.replace("_4k.acf", ".acf").replace("_4K.acf", ".acf") in acf_in_dir:
                    continue
                discovered_files.append(Path(root_dir) / fname)

        parsed_items: List[Dict[str, Any]] = []
        for acf_file in sorted(discovered_files):
            props = cls._parse_acf_file(acf_file)
            if not props:
                continue
            item = cls._classify_and_enrich(acf_file, props, icons_dest_dir)
            if item:
                parsed_items.append(item)

        # Replace MarketAircraft table cleanly with freshly synced catalog
        await session.execute(delete(MarketAircraft))
        for item in parsed_items:
            session.add(MarketAircraft(**item))
        await session.commit()

        logger.info(f"Synced {len(parsed_items)} aircraft from X-Plane 12 at {root_str}")
        return {
            "success": True,
            "xp12_path": root_str,
            "count": len(parsed_items),
            "by_category": {
                "GA": sum(1 for x in parsed_items if x["category"] == "GA"),
                "BIZJET": sum(1 for x in parsed_items if x["category"] == "BIZJET"),
                "AIRLINER": sum(1 for x in parsed_items if x["category"] == "AIRLINER"),
            }
        }
