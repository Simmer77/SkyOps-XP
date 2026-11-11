import React, { useState, useEffect } from 'react';
import { 
  Plane, Gauge, Briefcase, Wrench, BookOpen, Radio, 
  Fuel, AlertTriangle, CheckCircle, ArrowRight, RefreshCw, 
  MapPin, Zap, Shield, ShieldAlert, Award, Plus, Trash2, Key, Info, HelpCircle, Clock,
  Edit3, Camera, Calendar, Cpu, DollarSign, TrendingUp, TrendingDown,
  ArrowUpRight, ArrowDownRight, Wallet, FileText, Filter
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('flight'); // 'flight', 'fleet', 'rental', 'jobs', 'simbrief', 'maintenance', 'finances', 'logbook'
  const [systemStatus, setSystemStatus] = useState(null);
  const [fleet, setFleet] = useState([]);
  const [rentalCatalog, setRentalCatalog] = useState([]);
  const [selectedAircraft, setSelectedAircraft] = useState(null);
  const [activeFlight, setActiveFlight] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [simbriefOfp, setSimbriefOfp] = useState(null);
  const [simbriefInput, setSimbriefInput] = useState('');
  const [financialGuide, setFinancialGuide] = useState(null);
  const [financialOverview, setFinancialOverview] = useState(null);
  const [financialLedger, setFinancialLedger] = useState([]);
  const [financeSubTab, setFinanceSubTab] = useState('overview'); // 'overview', 'ledger', 'rules'
  const [financePeriodFilter, setFinancePeriodFilter] = useState('ALL'); // 'ALL' | 'YYYY-MM'
  const [ledgerCategoryFilter, setLedgerCategoryFilter] = useState('ALL');
  const [flightHistory, setFlightHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  // Modal State for adding custom owned aircraft
  const [showAddModal, setShowAddModal] = useState(false);
  const [newAircraft, setNewAircraft] = useState({
    tail_number: '',
    name: '',
    aircraft_type: '',
    category: 'GA',
    current_icao: 'LIRN',
    fuel_capacity_kg: 900,
    fuel_quantity_kg: 450,
    year_manufactured: 2022,
    purchase_date: new Date().toISOString().split('T')[0],
    purchase_price_eur: 1850000,
    image_url: '',
    engine_type: '',
    avionics_system: ''
  });

  // Modal State for editing aircraft
  const [showEditModal, setShowEditModal] = useState(false);
  const [editFormData, setEditFormData] = useState({});

  // Modal State for renting / acquiring from XP12 Market
  const [marketAircraft, setMarketAircraft] = useState([]);
  const [marketCategoryFilter, setMarketCategoryFilter] = useState('ALL');
  const [marketManufFilter, setMarketManufFilter] = useState('ALL');
  const [showAcquireModal, setShowAcquireModal] = useState(false);
  const [selectedMarketItem, setSelectedMarketItem] = useState(null);
  const [acquireMode, setAcquireMode] = useState('RENTAL_HOURLY');
  const [deliveryOption, setDeliveryOption] = useState('PICKUP_DEALERSHIP'); // 'PICKUP_DEALERSHIP' | 'DELIVER_HOME'
  const [acquireTail, setAcquireTail] = useState('');
  const [acquireIcao, setAcquireIcao] = useState('LIRN');

  // Onboarding Profile State
  const [profileForm, setProfileForm] = useState({
    name: 'AeroSky Executive Ops',
    home_base_icao: 'LIRN',
    difficulty_level: 'REALISTIC',
    economy_mode: 'REALISTIC',
    starting_capital_eur: 150000,
    simbrief_id: '',
    xp12_install_path: ''
  });

  // Dispatch (SimBrief + Manual) & Pre/Post Flight Checks State
  const [dispatchMode, setDispatchMode] = useState('simbrief'); // 'simbrief' | 'manual'
  const [planIsCommercial, setPlanIsCommercial] = useState(true); // Default: tutti i voli ad incasso
  const [planExcludeCrew, setPlanExcludeCrew] = useState(false); // Escludi costi equipaggio (es. Volo Solo VFR)
  const [planFlightRules, setPlanFlightRules] = useState('IFR'); // 'IFR' | 'VFR' (VFR esenta Eurocontrol & Handling)
  const [planTourId, setPlanTourId] = useState(''); // Optional Tour ID (es. IVAO World Tour)
  const [crewOverride, setCrewOverride] = useState(null); // Override manuale in HUD (null = usa piano/tracker)
  const [flightRulesOverride, setFlightRulesOverride] = useState(null); // 'IFR' | 'VFR' | null
  const [flightTourOverride, setFlightTourOverride] = useState(undefined); // undefined = usa piano, ''/id = override
  const [crewRoster, setCrewRoster] = useState(null);
  const [toursList, setToursList] = useState([]);
  const [selectedTourId, setSelectedTourId] = useState(null);
  const [selectedTourDetail, setSelectedTourDetail] = useState(null);
  const [logbookSubTab, setLogbookSubTab] = useState('flights'); // 'flights' | 'tours'
  const [newTourName, setNewTourName] = useState('');
  const [newTourDesc, setNewTourDesc] = useState('');
  const [manualPlan, setManualPlan] = useState({
    origin_icao: '',
    destination_icao: '',
    alternate_icao: '',
    flight_number: '',
    distance_nm: '',
    pax_count: 2,
    cargo_kg: 0,
    route: ''
  });
  const [manualEstimate, setManualEstimate] = useState(null);
  const [showDiversionPanel, setShowDiversionPanel] = useState(false);
  const [actualArrivalIcao, setActualArrivalIcao] = useState('');
  const [diversionReason, setDiversionReason] = useState('');
  const [lastFlightSummary, setLastFlightSummary] = useState(null);

  // Modal State for legacy renting
  const [showRentModal, setShowRentModal] = useState(false);
  const [selectedRentalTemplate, setSelectedRentalTemplate] = useState(null);
  const [rentPickupIcao, setRentPickupIcao] = useState('LIRN');
  const [rentCustomTail, setRentCustomTail] = useState('');

  // Live telemetry from WebSocket
  const [liveTelemetry, setLiveTelemetry] = useState({
    ias_kts: 0,
    groundspeed_kts: 0,
    elevation_m: 0,
    vs_fpm: 0,
    g_force: 1.0,
    on_ground: 1,
    fuel_total_kg: 0,
    parking_brake: 1,
    engine_running: 0
  });
  const [xpConnected, setXpConnected] = useState(false);
  const [xpAircraftIcao, setXpAircraftIcao] = useState('');
  const [xpAircraftTailnum, setXpAircraftTailnum] = useState('');
  const [flightPhase, setFlightPhase] = useState('OFFLINE');

  const isModelMismatch = Boolean(
    xpConnected &&
    xpAircraftIcao &&
    selectedAircraft &&
    xpAircraftIcao.toUpperCase() !== (selectedAircraft.aircraft_type || '').toUpperCase()
  );

  const matchingFleetAircraft = xpAircraftIcao
    ? fleet.find(ac => (ac.aircraft_type || '').toUpperCase() === xpAircraftIcao.toUpperCase())
    : null;

  const showNotice = (msg, type = 'info') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const formatEuro = (val) => {
    if (val === undefined || val === null || isNaN(val)) return '€ 0,00';
    return '€ ' + Number(val).toLocaleString('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const formatVirtualDate = (dateStr) => {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('it-IT', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const formatOperatingMonth = (ymStr, short = false) => {
    if (!ymStr || !ymStr.includes('-')) return '';
    const full = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno', 'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre'];
    const abbr = ['', 'Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic'];
    const [y, m] = ymStr.split('-');
    const idx = parseInt(m, 10);
    if (!idx || idx < 1 || idx > 12) return ymStr;
    return `${short ? abbr[idx] : full[idx]} ${y}`;
  };

  // 1. Initial Load & Fetchers
  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/system/status');
      if (res.ok) {
        const data = await res.json();
        setSystemStatus(data);
        if (data.recently_closed_months && data.recently_closed_months.length > 0) {
          const closedLabels = data.recently_closed_months.map(m => `${m.label} (-${formatEuro(m.total_deductions_eur)})`).join(', ');
          showNotice(`Chiusura mensile automatica registrata: ${closedLabels}`, 'info');
          fetchFleet();
          fetchFinances();
        }
        if (data.xp12_detected_path) {
          setProfileForm(prev => ({
            ...prev,
            xp12_install_path: prev.xp12_install_path || data.xp12_detected_path
          }));
        }
        const savedSimbrief = data.company?.simbrief_pilot_id || data.company?.simbrief_username;
        if (savedSimbrief && !simbriefInput) {
          setSimbriefInput(savedSimbrief);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchMarket = async () => {
    try {
      const res = await fetch('/api/fleet/market');
      if (res.ok) {
        const data = await res.json();
        setMarketAircraft(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchFleet = async () => {
    try {
      const res = await fetch('/api/fleet/');
      if (res.ok) {
        const data = await res.json();
        setFleet(data);
        setSelectedAircraft((prev) => {
          if (data.length === 0) return null;
          if (!prev) return data[0];
          return data.find((a) => a.id === prev.id) || data[0];
        });
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchRentalCatalog = async () => {
    try {
      const res = await fetch('/api/fleet/rentals/catalog');
      if (res.ok) {
        const data = await res.json();
        setRentalCatalog(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchFinancialGuide = async () => {
    try {
      const res = await fetch('/api/system/financial_guide');
      if (res.ok) {
        const data = await res.json();
        setFinancialGuide(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchActiveFlight = async (acOverride = null, altOverride = null) => {
    try {
      const acId = acOverride ?? selectedAircraft?.id;
      const alt = altOverride ?? (showDiversionPanel ? actualArrivalIcao : '');
      const params = new URLSearchParams();
      if (acId) params.set('aircraft_id', acId);
      if (alt && alt.trim().length >= 3) params.set('alternate_icao', alt.trim());
      const qs = params.toString() ? `?${params.toString()}` : '';
      const res = await fetch(`/api/flights/active${qs}`);
      if (res.ok) {
        const data = await res.json();
        setActiveFlight(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchJobs = async (airport) => {
    const icao = airport || (selectedAircraft ? selectedAircraft.current_icao : 'LIRN');
    try {
      const res = await fetch(`/api/jobs/?airport=${icao}`);
      if (res.ok) {
        const data = await res.json();
        setJobs(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch('/api/flights/history');
      if (res.ok) {
        const data = await res.json();
        setFlightHistory(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchFinances = async (periodOverride = null) => {
    try {
      const period = periodOverride ?? financePeriodFilter;
      const monthParam = period && period !== 'ALL' ? `?month=${encodeURIComponent(period)}` : '';
      const ledgerMonthParam = period && period !== 'ALL' ? `&month=${encodeURIComponent(period)}` : '';
      const [resOverview, resLedger] = await Promise.all([
        fetch(`/api/finances/overview${monthParam}`),
        fetch(`/api/finances/ledger?limit=150${ledgerMonthParam}`)
      ]);
      if (resOverview.ok) {
        const data = await resOverview.json();
        setFinancialOverview(data);
      }
      if (resLedger.ok) {
        const data = await resLedger.json();
        setFinancialLedger(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchCrewRoster = async () => {
    try {
      const res = await fetch('/api/crew/');
      if (res.ok) setCrewRoster(await res.json());
    } catch (e) { console.error(e); }
  };

  const handleHireCrew = async (category) => {
    setLoading(true);
    try {
      const res = await fetch('/api/crew/hire', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category })
      });
      const data = await res.json();
      if (res.ok) {
        showNotice(data.message, 'success');
        await Promise.all([fetchCrewRoster(), fetchFinances(), fetchActiveFlight()]);
      } else {
        showNotice(data.detail || 'Errore assunzione equipaggio', 'error');
      }
    } catch (e) {
      showNotice('Errore di rete assunzione equipaggio', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleFireCrew = async (crewId) => {
    if (!confirm('Vuoi chiudere il contratto mensile di questo equipaggio e tornare al regime freelance per volo?')) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/crew/${crewId}`, { method: 'DELETE' });
      const data = await res.json();
      if (res.ok) {
        showNotice(data.message, 'info');
        await Promise.all([fetchCrewRoster(), fetchFinances(), fetchActiveFlight()]);
      } else {
        showNotice(data.detail || 'Errore chiusura contratto', 'error');
      }
    } catch (e) {
      showNotice('Errore di rete', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchTours = async () => {
    try {
      const res = await fetch('/api/tours/');
      if (res.ok) {
        const list = await res.json();
        setToursList(list);
        if (list.length > 0 && !selectedTourId) {
          setSelectedTourId(list[0].id);
          fetchTourDetail(list[0].id);
        } else if (selectedTourId) {
          const stillExists = list.some(t => t.id === selectedTourId);
          if (stillExists) fetchTourDetail(selectedTourId);
          else {
            setSelectedTourId(list[0]?.id || null);
            if (list[0]) fetchTourDetail(list[0].id);
            else setSelectedTourDetail(null);
          }
        }
      }
    } catch (e) { console.error(e); }
  };

  const fetchTourDetail = async (tourId) => {
    if (!tourId) { setSelectedTourDetail(null); return; }
    try {
      const res = await fetch(`/api/tours/${tourId}`);
      if (res.ok) setSelectedTourDetail(await res.json());
    } catch (e) { console.error(e); }
  };

  const handleCreateTour = async (customName = null) => {
    const nameToUse = (customName ?? newTourName).trim();
    if (!nameToUse) {
      showNotice('Inserisci il nome del Tour (es. IVAO World Tour)', 'error');
      return null;
    }
    try {
      const res = await fetch('/api/tours/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: nameToUse, description: newTourDesc.trim() })
      });
      const data = await res.json();
      if (res.ok) {
        showNotice(data.message, 'success');
        setNewTourName('');
        setNewTourDesc('');
        await fetchTours();
        setSelectedTourId(data.tour.id);
        fetchTourDetail(data.tour.id);
        return data.tour;
      } else {
        showNotice(data.detail || 'Errore creazione tour', 'error');
      }
    } catch (e) {
      showNotice('Errore di rete creazione tour', 'error');
    }
    return null;
  };

  const handleDeleteTour = async (tourId) => {
    if (!confirm('Eliminare questo Tour? I voli effettuati resteranno salvati nel normale Logbook.')) return;
    try {
      const res = await fetch(`/api/tours/${tourId}`, { method: 'DELETE' });
      const data = await res.json();
      if (res.ok) {
        showNotice(data.message, 'info');
        fetchTours();
      }
    } catch (e) { showNotice('Errore eliminazione tour', 'error'); }
  };

  const handleToggleTourStatus = async (tour) => {
    const nextStatus = tour.status === 'ACTIVE' ? 'COMPLETED' : 'ACTIVE';
    try {
      const res = await fetch(`/api/tours/${tour.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus })
      });
      if (res.ok) {
        showNotice(`Tour "${tour.name}" impostato su ${nextStatus}`, 'success');
        fetchTours();
      }
    } catch (e) { showNotice('Errore aggiornamento tour', 'error'); }
  };

  const handlePayoffAircraftDebt = async (aircraft) => {
    if (!aircraft) return;
    const debt = aircraft.financed_amount_remaining_eur || 0;
    if (!confirm(`Vuoi estinguere anticipatamente il debito residuo di ${formatEuro(debt)} per ${aircraft.tail_number} (${aircraft.name})?`)) {
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`/api/fleet/${aircraft.id}/payoff`, { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        showNotice(data.message, 'success');
        await Promise.all([fetchStatus(), fetchFleet(), fetchFinances()]);
      } else {
        showNotice(data.detail || 'Errore estinzione anticipata', 'error');
      }
    } catch (e) {
      showNotice('Errore di rete durante estinzione debito', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProfile = async (e) => {
    if (e) e.preventDefault();
    if (!profileForm.name.trim()) {
      showNotice('Inserisci il nome della tua società aerea.', 'error');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('/api/company/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...profileForm,
          sync_xp12: true
        })
      });
      const data = await res.json();
      if (res.ok) {
        const syncedCount = data.xp12_sync?.count || 0;
        showNotice(`Profilo creato! Sincronizzati ${syncedCount} velivoli dal tuo X-Plane 12 nel Mercato & Noleggio.`, 'success');
        await Promise.all([fetchStatus(), fetchMarket(), fetchFleet(), fetchFinances()]);
        setActiveTab('rental');
      } else {
        showNotice(data.detail || 'Errore creazione profilo', 'error');
      }
    } catch (e) {
      showNotice('Errore di rete durante la creazione profilo', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSyncXP12 = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/company/sync_xp12', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ xp12_install_path: systemStatus?.company?.xp12_install_path || profileForm.xp12_install_path || null })
      });
      const data = await res.json();
      if (res.ok) {
        showNotice(data.message, 'success');
        fetchMarket();
      } else {
        showNotice(data.detail || 'Errore sincronizzazione XP12', 'error');
      }
    } catch (e) {
      showNotice('Errore sincronizzazione X-Plane 12', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleResetProfile = async () => {
    if (!confirm("⚠️ ATTENZIONE: Questa operazione cancellerà definitivamente il tuo profilo aziendale, tutta la flotta, i voli registrati e il bilancio economico riportando il sistema a ZERO.\n\nVuoi procedere?")) {
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('/api/company/reset', { method: 'DELETE' });
      if (res.ok) {
        setFleet([]);
        setMarketAircraft([]);
        setSelectedAircraft(null);
        setFinancialOverview(null);
        setFinancialLedger([]);
        setFlightHistory([]);
        setJobs([]);
        setSimbriefOfp(null);
        setSimbriefInput('');
        await fetchStatus();
        showNotice('Profilo azzerato. Puoi ora creare una nuova compagnia!', 'info');
      } else {
        showNotice('Errore durante il reset del profilo', 'error');
      }
    } catch (e) {
      showNotice('Errore di connessione durante il reset', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAcquireAircraft = async () => {
    if (!selectedMarketItem) return;
    if (!acquireTail.trim()) {
      showNotice('Inserisci le marche (Tail Number) del velivolo.', 'error');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('/api/fleet/acquire', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          market_aircraft_id: selectedMarketItem.id,
          tail_number: acquireTail.trim().toUpperCase(),
          acquisition_mode: acquireMode,
          delivery_option: deliveryOption,
          pickup_icao: acquireIcao.trim().toUpperCase() || systemStatus?.company?.home_base_icao || 'LIRN'
        })
      });
      const data = await res.json();
      if (res.ok) {
        showNotice(data.message, 'success');
        setShowAcquireModal(false);
        await Promise.all([fetchStatus(), fetchFleet(), fetchFinances()]);
        if (data.aircraft) {
          setSelectedAircraft(data.aircraft);
        }
        setActiveTab(acquireMode === 'RENTAL_HOURLY' ? 'rental' : 'fleet');
      } else {
        showNotice(data.detail || "Errore durante l'acquisizione", 'error');
      }
    } catch (e) {
      showNotice("Errore di rete durante l'acquisizione", 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchFleet();
    fetchMarket();
    fetchRentalCatalog();
    fetchFinancialGuide();
    fetchActiveFlight();
    fetchHistory();
    fetchFinances();
    fetchCrewRoster();
    fetchTours();
  }, []);

  useEffect(() => {
    if (activeTab === 'finances') {
      fetchFinances();
      fetchCrewRoster();
    } else if (activeTab === 'logbook') {
      fetchHistory();
      fetchTours();
    } else if (activeTab === 'rental') {
      fetchMarket();
    } else if (activeTab === 'flight') {
      fetchActiveFlight();
      fetchTours();
    } else if (activeTab === 'fleet') {
      const owned = fleet.filter((a) => a.ownership === 'OWNED');
      if (owned.length > 0 && (!selectedAircraft || selectedAircraft.ownership !== 'OWNED')) {
        setSelectedAircraft(owned[0]);
      }
    } else if (activeTab === 'simbrief') {
      fetchTours();
      fetchCrewRoster();
      if (selectedAircraft && !manualPlan.origin_icao) {
        setManualPlan(prev => ({ ...prev, origin_icao: selectedAircraft.current_icao || '' }));
      }
    }
  }, [activeTab, fleet]);

  useEffect(() => {
    if (activeTab !== 'flight') return;
    const interval = setInterval(() => {
      fetchActiveFlight();
    }, 2000);
    return () => clearInterval(interval);
  }, [activeTab, selectedAircraft, showDiversionPanel, actualArrivalIcao]);

  useEffect(() => {
    if (selectedAircraft) {
      fetchJobs(selectedAircraft.current_icao);
      fetchActiveFlight(selectedAircraft.id);
      setManualPlan(prev => ({ ...prev, origin_icao: selectedAircraft.current_icao || prev.origin_icao }));
    }
  }, [selectedAircraft]);

  useEffect(() => {
    setCrewOverride(null);
    setFlightRulesOverride(null);
    setFlightTourOverride(undefined);
  }, [selectedAircraft?.id]);

  // 2. WebSocket Telemetry Stream
  useEffect(() => {
    let ws;
    const connectWs = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      ws = new WebSocket(`${protocol}//${window.location.host}/api/system/ws`);
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setXpConnected(data.xp_connected);
          setXpAircraftIcao(data.xp_aircraft_icao || '');
          setXpAircraftTailnum(data.xp_aircraft_tailnum || '');
          setFlightPhase(data.flight_phase);
          if (data.telemetry) {
            setLiveTelemetry(data.telemetry);
          }
        } catch (e) {}
      };

      ws.onclose = () => {
        setTimeout(connectWs, 2000);
      };
    };

    connectWs();
    return () => {
      if (ws) ws.close();
    };
  }, []);

  // Action: Add Owned Aircraft
  const handleAddAircraft = async (e) => {
    e.preventDefault();
    if (!newAircraft.tail_number || !newAircraft.name) {
      showNotice('Inserisci almeno Marche e Nome Modello', 'error');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('/api/fleet/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tail_number: newAircraft.tail_number.toUpperCase().trim(),
          name: newAircraft.name.trim(),
          aircraft_type: (newAircraft.aircraft_type || newAircraft.tail_number).toUpperCase().trim(),
          category: newAircraft.category,
          ownership: 'OWNED',
          current_icao: (newAircraft.current_icao || 'LIRN').toUpperCase().trim(),
          fuel_capacity_kg: parseFloat(newAircraft.fuel_capacity_kg) || 900,
          fuel_quantity_kg: parseFloat(newAircraft.fuel_quantity_kg) || 450,
          hourly_lease_rate: 0.0,
          year_manufactured: parseInt(newAircraft.year_manufactured) || 2021,
          purchase_date: newAircraft.purchase_date || null,
          purchase_price_eur: parseFloat(newAircraft.purchase_price_eur) || 0.0,
          image_url: newAircraft.image_url || '',
          engine_type: newAircraft.engine_type || 'Standard',
          avionics_system: newAircraft.avionics_system || 'Standard Avionics'
        })
      });
      const data = await res.json();
      if (res.ok) {
        showNotice(`Aeromobile ${data.tail_number} aggiunto con successo al tuo hangar!`, 'success');
        setShowAddModal(false);
        setNewAircraft({
          tail_number: '',
          name: '',
          aircraft_type: '',
          category: 'GA',
          current_icao: 'LIRN',
          fuel_capacity_kg: 900,
          fuel_quantity_kg: 450,
          year_manufactured: 2022,
          purchase_date: new Date().toISOString().split('T')[0],
          purchase_price_eur: 1850000,
          image_url: '',
          engine_type: '',
          avionics_system: ''
        });
        fetchFleet();
        setSelectedAircraft(data);
      } else {
        showNotice(data.detail, 'error');
      }
    } catch (e) {
      showNotice('Errore durante il salvataggio dell aeromobile', 'error');
    } finally {
      setLoading(false);
    }
  };

  const openEditModal = (aircraft) => {
    let pDate = '';
    if (aircraft.purchase_date) {
      try {
        pDate = aircraft.purchase_date.split('T')[0];
      } catch (e) {
        pDate = '';
      }
    }
    setEditFormData({
      tail_number: aircraft.tail_number || '',
      purchase_date: pDate,
      name: aircraft.name || '',
      aircraft_type: aircraft.aircraft_type || '',
      category: aircraft.category || 'GA',
      current_icao: aircraft.current_icao || 'LIRN',
      fuel_capacity_kg: aircraft.fuel_capacity_kg || 900,
      fuel_quantity_kg: aircraft.fuel_quantity_kg || 450,
      year_manufactured: aircraft.year_manufactured || 2021,
      purchase_price_eur: aircraft.purchase_price_eur || 0,
      image_url: aircraft.image_url || '',
      engine_type: aircraft.engine_type || '',
      avionics_system: aircraft.avionics_system || ''
    });
    setShowEditModal(true);
  };

  const handleUpdateAircraft = async (e) => {
    e.preventDefault();
    if (!selectedAircraft) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/fleet/${selectedAircraft.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editFormData)
      });
      const data = await res.json();
      if (res.ok) {
        showNotice(`Scheda tecnica di ${data.tail_number} aggiornata!`, 'success');
        setShowEditModal(false);
        fetchFleet();
        setSelectedAircraft(data);
      } else {
        showNotice(data.detail, 'error');
      }
    } catch (e) {
      showNotice('Errore durante l aggiornamento', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleImageFileUpload = async (file) => {
    if (!file || !selectedAircraft) return;
    const formData = new FormData();
    formData.append('file', file);
    setLoading(true);
    try {
      const res = await fetch(`/api/fleet/${selectedAircraft.id}/upload_image`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        showNotice(data.message, 'success');
        setEditFormData(prev => ({ ...prev, image_url: data.image_url }));
        setSelectedAircraft(data.aircraft);
        fetchFleet();
      } else {
        showNotice(data.detail || 'Errore caricamento immagine', 'error');
      }
    } catch (err) {
      showNotice('Errore durante l invio del file immagine', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Action: Rent Aircraft
  const handleRentAircraft = async () => {
    if (!selectedRentalTemplate) return;
    setLoading(true);
    try {
      const tail = rentCustomTail.trim() || `I-RNT${Math.floor(10 + Math.random() * 89)}`;
      const res = await fetch('/api/fleet/rent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: selectedRentalTemplate.id,
          tail_number: tail,
          pickup_icao: rentPickupIcao.toUpperCase().trim() || 'LIRN'
        })
      });
      const data = await res.json();
      if (res.ok) {
        showNotice(data.message, 'success');
        setShowRentModal(false);
        fetchFleet();
        setActiveTab('fleet');
      } else {
        showNotice(data.detail, 'error');
      }
    } catch (e) {
      showNotice('Errore durante la stipula del noleggio', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Action: Delete / Return Aircraft
  const handleDeleteAircraft = async (aircraft) => {
    const isLeased = aircraft.ownership === 'LEASED';
    const actionText = isLeased ? 'restituire questo aereo a noleggio' : 'rimuovere questo aereo dall hangar';
    if (!confirm(`Sei sicuro di voler ${actionText} (${aircraft.tail_number})?`)) return;

    try {
      const res = await fetch(`/api/fleet/${aircraft.id}`, { method: 'DELETE' });
      const data = await res.json();
      if (res.ok) {
        showNotice(data.message, 'success');
        if (selectedAircraft?.id === aircraft.id) {
          setSelectedAircraft(null);
        }
        fetchFleet();
      } else {
        showNotice(data.detail, 'error');
      }
    } catch (e) {
      showNotice('Errore durante la rimozione', 'error');
    }
  };

  // Job generation & Acceptance
  const handleGenerateJobs = async () => {
    if (!selectedAircraft) return;
    setLoading(true);
    try {
      const res = await fetch('/api/jobs/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          origin_icao: selectedAircraft.current_icao,
          category: selectedAircraft.category,
          count: 5
        })
      });
      if (res.ok) {
        showNotice(`Generati 5 nuovi contratti da ${selectedAircraft.current_icao}!`, 'success');
        fetchJobs(selectedAircraft.current_icao);
      }
    } catch (e) {
      showNotice('Errore nella generazione contratti', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptJob = async (jobId) => {
    if (!selectedAircraft) return;
    try {
      const res = await fetch(`/api/jobs/${jobId}/accept`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ aircraft_id: selectedAircraft.id })
      });
      const data = await res.json();
      if (res.ok) {
        showNotice(data.message, 'success');
        fetchJobs(selectedAircraft.current_icao);
        fetchActiveFlight();
      } else {
        showNotice(data.detail, 'error');
      }
    } catch (e) {
      showNotice('Errore durante accettazione incarico', 'error');
    }
  };

  // SimBrief
  const handleFetchSimbrief = async () => {
    const cleaned = simbriefInput.trim();
    if (!cleaned) {
      showNotice('Inserisci il tuo Pilot ID numerico (es. 1106351) o Username SimBrief', 'error');
      return;
    }
    setLoading(true);
    try {
      const isNumericId = /^\d+$/.test(cleaned);
      const paramKey = isNumericId ? 'pilot_id' : 'username';
      const cat = selectedAircraft?.category || 'GA';
      const mtow = selectedAircraft?.mtow_kg || 0;
      const res = await fetch(`/api/simbrief/latest?${paramKey}=${encodeURIComponent(cleaned)}&category=${cat}&mtow_kg=${mtow}`);
      if (res.ok) {
        const ofp = await res.json();
        setSimbriefOfp(ofp);
        showNotice(`Piano ${ofp.flight_number} scaricato: ${ofp.origin_icao} → ${ofp.destination_icao}`, 'success');
      } else {
        const err = await res.json();
        showNotice(err.detail || 'Piano SimBrief non trovato', 'error');
      }
    } catch (e) {
      showNotice('Errore connessione a SimBrief', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleImportSimbriefFlight = async () => {
    if (!selectedAircraft || !simbriefOfp) {
      showNotice('Seleziona prima un aeromobile dalla flotta', 'error');
      return;
    }
    const cleaned = simbriefInput.trim();
    const isNumericId = /^\d+$/.test(cleaned);
    setLoading(true);
    try {
      const res = await fetch('/api/simbrief/import_flight', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: isNumericId ? null : cleaned,
          pilot_id: isNumericId ? cleaned : null,
          aircraft_id: selectedAircraft.id,
          is_commercial: planIsCommercial,
          exclude_crew_cost: planExcludeCrew,
          flight_rules: planFlightRules,
          tour_id: planTourId ? parseInt(planTourId, 10) : null
        })
      });
      const data = await res.json();
      if (res.ok) {
        setCrewOverride(null);
        setFlightRulesOverride(null);
        setFlightTourOverride(undefined);
        showNotice(`${data.message} Vai in Plancia per completare i controlli Pre-Volo.`, 'success');
        await Promise.all([fetchFleet(), fetchActiveFlight(selectedAircraft.id)]);
        setActiveTab('flight');
      } else {
        showNotice(data.detail, 'error');
      }
    } catch (e) {
      showNotice('Errore importazione SimBrief', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchManualEstimate = async (orig, dest, pax, cargo, commercial) => {
    if (!orig || orig.trim().length < 3 || !dest || dest.trim().length < 3) {
      setManualEstimate(null);
      return;
    }
    try {
      const cat = selectedAircraft?.category || 'GA';
      const res = await fetch(
        `/api/jobs/estimate_route?origin=${encodeURIComponent(orig)}&destination=${encodeURIComponent(dest)}&category=${cat}&pax=${pax || 0}&cargo=${cargo || 0}&is_commercial=${commercial}`
      );
      if (res.ok) {
        const d = await res.json();
        setManualEstimate(d);
      }
    } catch (e) {}
  };

  const handleCreateManualPlan = async (e) => {
    if (e) e.preventDefault();
    if (!selectedAircraft) {
      showNotice('Seleziona prima un aeromobile dalla flotta', 'error');
      return;
    }
    if (!manualPlan.origin_icao.trim() || !manualPlan.destination_icao.trim()) {
      showNotice('Inserisci i codici ICAO di Partenza e Destinazione.', 'error');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('/api/jobs/plan_manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          aircraft_id: selectedAircraft.id,
          origin_icao: manualPlan.origin_icao.trim().toUpperCase(),
          destination_icao: manualPlan.destination_icao.trim().toUpperCase(),
          alternate_icao: manualPlan.alternate_icao.trim().toUpperCase(),
          flight_number: manualPlan.flight_number.trim().toUpperCase(),
          distance_nm: manualPlan.distance_nm ? parseFloat(manualPlan.distance_nm) : 0.0,
          pax_count: parseInt(manualPlan.pax_count) || 0,
          cargo_kg: parseFloat(manualPlan.cargo_kg) || 0.0,
          route: manualPlan.route,
          is_commercial: planIsCommercial,
          exclude_crew_cost: planExcludeCrew,
          flight_rules: planFlightRules,
          tour_id: planTourId ? parseInt(planTourId, 10) : null
        })
      });
      const data = await res.json();
      if (res.ok) {
        setCrewOverride(null);
        setFlightRulesOverride(null);
        setFlightTourOverride(undefined);
        showNotice(data.message, 'success');
        await Promise.all([fetchFleet(), fetchActiveFlight(selectedAircraft.id)]);
        setActiveTab('flight');
      } else {
        showNotice(data.detail || 'Errore creazione piano manuale', 'error');
      }
    } catch (e) {
      showNotice('Errore di rete nella creazione piano', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Flight lifecycle
  const handleStartFlight = async (jobId = null) => {
    if (!selectedAircraft) return;
    if (isModelMismatch && !jobId) {
      if (!confirm(`⚠️ ATTENZIONE MODELLO DIVERSO!\n\nIn X-Plane 12 risulta caricato: ${xpAircraftIcao} (${xpAircraftTailnum || 'N/D'})\nIn SkyOps XP hai selezionato: ${selectedAircraft.tail_number} (${selectedAircraft.aircraft_type})\n\nVuoi avviare comunque il monitoraggio volo su ${selectedAircraft.tail_number}?`)) {
        return;
      }
    }
    try {
      const effectiveExcludeCrew = crewOverride !== null ? crewOverride : Boolean(activeFlight?.exclude_crew_cost);
      const effectiveRules = flightRulesOverride || activeFlight?.flight_rules || 'IFR';
      const effectiveTourId = flightTourOverride !== undefined ? (flightTourOverride ? parseInt(flightTourOverride, 10) : null) : (activeFlight?.tour_id || null);
      const res = await fetch('/api/flights/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          aircraft_id: selectedAircraft.id,
          job_id: jobId || activeFlight?.job?.id || null,
          exclude_crew_cost: effectiveExcludeCrew,
          flight_rules: effectiveRules,
          tour_id: effectiveTourId
        })
      });
      const data = await res.json();
      if (res.ok) {
        setLastFlightSummary(null);
        setCrewOverride(null);
        setFlightRulesOverride(null);
        setFlightTourOverride(undefined);
        showNotice(data.message || `Volo avviato per ${selectedAircraft.tail_number}!`, 'success');
        fetchStatus();
        fetchFleet();
        fetchActiveFlight();
        fetchFinances();
      } else {
        showNotice(data.detail, 'error');
      }
    } catch (e) {
      showNotice('Errore avvio volo', 'error');
    }
  };

  const handleRefuelAircraft = async (aircraftOverride = null) => {
    const targetAc = aircraftOverride || selectedAircraft;
    if (!targetAc) return;
    const currentKg = Number(targetAc.fuel_quantity_kg || 0).toFixed(1);
    const maxKg = Number(targetAc.fuel_capacity_kg || 0).toFixed(0);
    const activeMode = (financialOverview?.economy_mode || systemStatus?.company?.economy_mode || 'REALISTIC').toUpperCase();
    const estPrice = activeMode === 'STANDARD' ? 1.05 : (targetAc.category === 'AIRLINER' ? 0.90 : targetAc.category === 'BIZJET' ? 1.25 : 1.35);
    const targetInput = prompt(
      `Carburante attuale salvato: ${currentKg} kg / Max ${maxKg} kg.\n` +
      `Inserisci quantità totale desiderata in kg (pagherai SOLO la differenza aggiunta a ${estPrice.toFixed(2)} €/kg):`,
      maxKg
    );
    if (!targetInput) return;
    const parsedTarget = parseFloat(targetInput);
    if (Number.isNaN(parsedTarget) || parsedTarget < 0) {
      showNotice('Valore carburante non valido.', 'error');
      return;
    }
    try {
      const res = await fetch(`/api/fleet/${targetAc.id}/refuel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_fuel_kg: parsedTarget })
      });
      const data = await res.json();
      if (res.ok) {
        const addedNote = data.fuel_added_kg > 0
          ? ` (+${data.fuel_added_kg.toFixed(1)} kg aggiunti, costo ${formatEuro(data.cost_eur)})`
          : '';
        showNotice(`${data.message}${addedNote}`, 'success');
        fetchStatus();
        fetchFleet();
        fetchFinances();
      } else {
        showNotice(data.detail || 'Errore rifornimento', 'error');
      }
    } catch (e) {
      showNotice('Errore di rete durante il rifornimento', 'error');
    }
  };

  const handleFinalizeFlight = async () => {
    setLoading(true);
    try {
      const effectiveExcludeCrew = crewOverride !== null ? crewOverride : Boolean(activeFlight?.exclude_crew_cost);
      const effectiveRules = flightRulesOverride || activeFlight?.flight_rules || 'IFR';
      const effectiveTourId = flightTourOverride !== undefined ? (flightTourOverride ? parseInt(flightTourOverride, 10) : null) : (activeFlight?.tour_id || null);
      const payload = {
        exclude_crew_cost: effectiveExcludeCrew,
        flight_rules: effectiveRules,
        tour_id: effectiveTourId,
        ...((showDiversionPanel && actualArrivalIcao.trim())
          ? {
              actual_arrival_icao: actualArrivalIcao.trim().toUpperCase(),
              diversion_reason: diversionReason.trim() || 'Dirottamento / Emergenza'
            }
          : {})
      };
      const res = await fetch('/api/flights/finalize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        setLastFlightSummary(data.summary);
        setCrewOverride(null);
        setFlightRulesOverride(null);
        setFlightTourOverride(undefined);
        showNotice(`Volo completato! Utile netto: ${formatEuro(data.summary.financials.net_profit)}`, 'success');
        setShowDiversionPanel(false);
        setActualArrivalIcao('');
        setDiversionReason('');
        fetchStatus();
        fetchFleet();
        fetchActiveFlight();
        fetchHistory();
        fetchFinances();
        fetchTours();
      } else {
        showNotice(data.detail, 'error');
      }
    } catch (e) {
      showNotice('Errore chiusura volo', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSyncToXplane = async (aircraftId) => {
    try {
      const res = await fetch(`/api/fleet/${aircraftId}/sync_xp`, { method: 'POST' });
      const data = await res.json();
      showNotice(data.message, data.status === 'success' ? 'success' : 'warning');
    } catch (e) {
      showNotice('Errore sincronizzazione X-Plane', 'error');
    }
  };

  const handleService = async (aircraftId, serviceCode) => {
    try {
      const res = await fetch(`/api/fleet/${aircraftId}/service`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service_code: serviceCode })
      });
      const data = await res.json();
      if (res.ok) {
        showNotice(data.message, 'success');
        fetchStatus();
        fetchFleet();
        fetchFinances();
      } else {
        showNotice(data.detail, 'error');
      }
    } catch (e) {
      showNotice('Errore durante la manutenzione', 'error');
    }
  };

  const handleInjectFailureTest = async (dref) => {
    try {
      const res = await fetch('/api/system/inject_failure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ failure_dref: dref, mode: 6 })
      });
      const data = await res.json();
      showNotice(data.message, 'warning');
    } catch (e) {
      showNotice('Errore invio avaria', 'error');
    }
  };

  // Onboarding Screen if no active profile exists
  if (systemStatus && systemStatus.has_profile === false) {
    const difficultyOptions = [
      { id: 'HARDCORE', label: 'Pilota Indipendente (Hardcore)', capital: 35000, desc: 'Capitale minimo. Dovrai partire noleggiando piccoli monomotori GA a ore.' },
      { id: 'REALISTIC', label: 'Start-up Regionale (Realistica)', capital: 150000, desc: 'Perfetta per noleggiare GA/BizJet o versare l’anticipo di un piccolo usato.' },
      { id: 'STANDARD', label: 'Compagnia Emergente (Standard)', capital: 500000, desc: 'Budget per acquistare subito il primo aereo GA o avviare un leasing VLJ.' },
      { id: 'EXECUTIVE', label: 'Operatore Executive (Avanzato)', capital: 2500000, desc: 'Capitale solido per acquisire un Vision Jet o accedere ai Business Jet.' },
      { id: 'MAGNATE', label: 'Major Airline / Magnate', capital: 25000000, desc: 'Alto capitale per acquistare flotta BizJet e Airliner commerciali.' }
    ];

    return (
      <div className="min-h-screen bg-aviation-dark flex items-center justify-center p-6 font-sans relative overflow-hidden readable-ui">
        {/* Toast Notification */}
        {notification && (
          <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-xl text-sm font-medium border flex items-center gap-2 ${
            notification.type === 'success' ? 'bg-emerald-950/90 text-emerald-300 border-emerald-700' :
            notification.type === 'error' ? 'bg-rose-950/90 text-rose-300 border-rose-700' :
            'bg-cyan-950/90 text-cyan-300 border-cyan-700'
          }`}>
            {notification.msg}
          </div>
        )}

        <div className="max-w-3xl w-full glass-panel p-8 rounded-2xl border border-cyan-500/30 shadow-2xl space-y-6 relative z-10">
          <div className="flex items-center gap-4 border-b border-slate-800 pb-5">
            <div className="p-3 bg-cyan-500/15 border border-cyan-500/40 rounded-xl text-cyan-400">
              <Plane size={32} className="rotate-45" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-black tracking-wider text-white">SKYOPS XP12</h1>
                <span className="text-xs font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-mono">CONFIGURAZIONE INIZIALE</span>
              </div>
              <p className="text-sm text-slate-400 mt-0.5">
                Crea il profilo della tua compagnia aerea e sincronizza gli aeromobili dal tuo X-Plane 12.
              </p>
            </div>
          </div>

          <form onSubmit={handleCreateProfile} className="space-y-5 font-mono text-xs" noValidate>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <label className="text-slate-300 block mb-1.5 font-semibold">Nome della Società Aerea *</label>
                <input
                  type="text"
                  required
                  value={profileForm.name}
                  onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
                  placeholder="es. AeroSky Executive Ops"
                  className="w-full bg-slate-900 border border-slate-700 p-2.5 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div>
                <label className="text-slate-300 block mb-1.5 font-semibold">Base Operativa (ICAO) *</label>
                <input
                  type="text"
                  required
                  maxLength={4}
                  value={profileForm.home_base_icao}
                  onChange={(e) => setProfileForm({ ...profileForm, home_base_icao: e.target.value.toUpperCase() })}
                  placeholder="es. LIRN"
                  className="w-full bg-slate-900 border border-slate-700 p-2.5 rounded-lg text-cyan-300 font-bold text-sm uppercase focus:outline-none focus:border-cyan-400"
                />
              </div>
            </div>

            {/* 5 Capital / Difficulty Tiers */}
            <div>
              <label className="text-slate-300 block mb-2 font-semibold">Capitale Iniziale & Livello di Progressione (€ Euro)</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                {difficultyOptions.map((opt) => {
                  const selected = profileForm.difficulty_level === opt.id;
                  return (
                    <div
                      key={opt.id}
                      onClick={() => setProfileForm({
                        ...profileForm,
                        difficulty_level: opt.id,
                        starting_capital_eur: opt.capital
                      })}
                      className={`p-3 rounded-xl border cursor-pointer transition-all ${
                        selected
                          ? 'bg-cyan-950/40 border-cyan-400 ring-1 ring-cyan-400 shadow-lg'
                          : 'bg-slate-900/60 border-slate-800 hover:border-slate-600'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <span className={`font-bold text-xs ${selected ? 'text-cyan-300' : 'text-white'}`}>{opt.label}</span>
                      </div>
                      <div className="text-base font-black text-emerald-400 mt-1">{formatEuro(opt.capital)}</div>
                      <p className="text-[11px] text-slate-400 font-sans mt-1 leading-snug">{opt.desc}</p>
                    </div>
                  );
                })}
              </div>
            </div>

                    <div className="pt-2">
                      <label className="text-slate-300 block mb-2 font-semibold">Modello Economico (Margini & Sfida):</label>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                        {[
                          { id: 'REALISTIC', title: '🎯 REALISTICO (Consigliato)', desc: 'Margini reali aviazione (4%–12%), riserve motori/check-C, FBO/Ground Handling, Eurocontrol & IOC.' },
                          { id: 'STANDARD', title: '🕹️ STANDARD (Rilassato)', desc: 'Ricavi +25% e costi accessori ridotti (-40%) per far crescere la flotta più rapidamente.' },
                        ].map((m) => {
                          const sel = (profileForm.economy_mode || 'REALISTIC') === m.id;
                          return (
                            <div
                              key={m.id}
                              onClick={() => setProfileForm({ ...profileForm, economy_mode: m.id })}
                              className={`p-3 rounded-xl border cursor-pointer transition ${
                                sel ? 'bg-emerald-950/35 border-emerald-400 ring-1 ring-emerald-400' : 'bg-slate-900/70 border-slate-800 hover:border-slate-600'
                              }`}
                            >
                              <div className={`font-bold ${sel ? 'text-emerald-300' : 'text-white'}`}>{m.title}</div>
                              <p className="text-[11px] text-slate-400 font-sans mt-1">{m.desc}</p>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
              <div>
                <label className="text-slate-300 block mb-1.5 font-semibold">SimBrief Pilot ID / Username (Opzionale)</label>
                <input
                  type="text"
                  value={profileForm.simbrief_id}
                  onChange={(e) => setProfileForm({ ...profileForm, simbrief_id: e.target.value })}
                  placeholder="es. 1106351"
                  className="w-full bg-slate-900 border border-slate-700 p-2.5 rounded-lg text-white focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div>
                <label className="text-slate-300 block mb-1.5 font-semibold">Cartella Installazione X-Plane 12</label>
                <input
                  type="text"
                  value={profileForm.xp12_install_path}
                  onChange={(e) => setProfileForm({ ...profileForm, xp12_install_path: e.target.value })}
                  placeholder="/percorso/a/X-Plane 12"
                  className="w-full bg-slate-900 border border-slate-700 p-2.5 rounded-lg text-slate-200 focus:outline-none focus:border-cyan-400"
                />
                {systemStatus.xp12_detected_path && (
                  <span className="text-[10px] text-emerald-400 mt-1 block">✓ X-Plane 12 rilevato automaticamente nel sistema</span>
                )}
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                type="submit"
                disabled={loading}
                className="w-full md:w-auto flex items-center justify-center gap-2.5 bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 text-white font-bold text-sm px-6 py-3 rounded-xl shadow-lg transition disabled:opacity-50"
              >
                <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                Sincronizza il tuo X-Plane 12 & Crea Profilo
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-aviation-dark flex flex-col font-sans readable-ui">
      {/* Toast Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-xl text-sm font-medium border flex items-center gap-2 transition-all ${
          notification.type === 'success' ? 'bg-emerald-950/90 text-emerald-300 border-emerald-700' :
          notification.type === 'error' ? 'bg-rose-950/90 text-rose-300 border-rose-700' :
          'bg-cyan-950/90 text-cyan-300 border-cyan-700'
        }`}>
          {notification.type === 'success' && <CheckCircle size={18} />}
          {notification.type === 'error' && <AlertTriangle size={18} />}
          {notification.type === 'info' && <Radio size={18} />}
          {notification.msg}
        </div>
      )}

      {/* Top Glass Cockpit Header */}
      <header className="glass-panel border-b border-slate-800/80 px-6 py-3 sticky top-0 z-40">
        <div className="max-w-[1600px] mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-cyan-400">
              <Plane size={24} className="rotate-45" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-black text-lg tracking-wider text-white">SKYOPS</span>
                <span className="text-xs font-bold px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">XP12</span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                {systemStatus?.company?.name || 'AeroSky Executive Ops'} • Base: <span className="text-cyan-300 font-bold">{systemStatus?.company?.home_base_icao || 'LIRN'}</span>
              </p>
            </div>
          </div>

          {/* Quick Metrics Bar in € EURO */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded-lg">
              <span className="text-emerald-400 font-bold text-base">€</span>
              <div>
                <div className="text-[10px] text-slate-400 uppercase font-mono">Capitale Aziendale</div>
                <div className="text-sm font-bold font-mono text-emerald-400">
                  {formatEuro(systemStatus?.company?.cash_balance ?? 175000)}
                </div>
              </div>
            </div>

            {/* Operating Month & Real Calendar Widget */}
            <div 
              onClick={() => setActiveTab('finances')}
              className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 hover:border-amber-500/50 cursor-pointer px-3 py-1.5 rounded-lg transition"
              title="Clicca per aprire Bilancio, Mese Operativo e Oneri Mensili"
            >
              <Calendar size={16} className="text-amber-400" />
              <div>
                <div className="text-[10px] text-slate-400 uppercase font-mono">Mese Operativo</div>
                <div className="text-sm font-bold font-mono text-amber-300">
                  {systemStatus?.company?.operating_month_label || financialOverview?.operating_month_label || formatOperatingMonth(new Date().toISOString().slice(0, 7))}
                  <span className="text-[11px] text-slate-400 font-normal ml-1.5">
                    ({formatVirtualDate(systemStatus?.company?.virtual_date || new Date().toISOString())})
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded-lg">
              <Award size={16} className="text-cyan-400" />
              <div>
                <div className="text-[10px] text-slate-400 uppercase font-mono">Reputazione</div>
                <div className="text-sm font-bold font-mono text-cyan-300">
                  {systemStatus?.company?.reputation || 100}%
                </div>
              </div>
            </div>

            {/* X-Plane 12 Connection Badge */}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-mono font-semibold ${
              !xpConnected
                ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                : isModelMismatch
                  ? 'bg-amber-500/15 border-amber-500/50 text-amber-300'
                  : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            }`}
            title={xpConnected && xpAircraftIcao ? `Aereo attivo su X-Plane 12: ${xpAircraftIcao} (${xpAircraftTailnum || 'N/D'})` : ''}
            >
              <span className={`w-2 h-2 rounded-full ${
                !xpConnected ? 'bg-rose-400' : isModelMismatch ? 'bg-amber-400 animate-ping' : 'bg-emerald-400 animate-pulse'
              }`} />
              {!xpConnected
                ? 'XP12 OFFLINE'
                : xpAircraftIcao
                  ? `XP12: ${xpAircraftIcao}${isModelMismatch ? ' ⚠️' : ''}`
                  : 'XP12 CONNESSO'}
            </div>

            {/* Reset Profile Button */}
            <button
              onClick={handleResetProfile}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-950/50 hover:bg-rose-900/80 border border-rose-800/60 text-rose-300 text-xs font-mono transition"
              title="Cancella profilo aziendale e ricomincia da zero"
            >
              <Trash2 size={14} /> Reset Profilo
            </button>
          </div>
        </div>
      </header>

      {/* Main Layout with Left Sidebar Navigation */}
      <div className="flex-1 flex flex-col lg:flex-row max-w-[1600px] w-full mx-auto">
        {/* Left Sidebar */}
        <aside className="lg:w-72 shrink-0 border-b lg:border-b-0 lg:border-r border-slate-800/80 bg-slate-950/60 p-4 flex flex-col justify-between gap-4">
          <nav className="flex lg:flex-col gap-1.5 overflow-x-auto lg:overflow-visible pb-1 lg:pb-0">
            {[
              { id: 'flight', label: 'Volo Attivo & HUD', icon: Gauge },
              { id: 'fleet', label: 'Hangar (Proprietà)', icon: Plane },
              { id: 'rental', label: 'Mercato & Noleggio', icon: Key },
              { id: 'jobs', label: 'Incarichi & Contratti', icon: Briefcase },
              { id: 'simbrief', label: 'Piano di Volo & Dispatch', icon: Radio },
              { id: 'maintenance', label: 'Officina & Usura', icon: Wrench },
              { id: 'finances', label: 'Bilancio & Finanze', icon: TrendingUp },
              { id: 'logbook', label: 'Registro Voli', icon: BookOpen },
            ].map((tab) => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-all whitespace-nowrap text-left border ${
                    active 
                      ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/50 shadow-md lg:border-l-4 lg:border-l-cyan-400 font-bold' 
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/50 border-transparent'
                  }`}
                >
                  <Icon size={18} className={active ? 'text-cyan-400 shrink-0' : 'text-slate-400 shrink-0'} />
                  <span className="text-sm">{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Active Aircraft Quick Sidebar Card */}
          {selectedAircraft && (
            <div className="hidden lg:block glass-panel p-4 rounded-xl border border-slate-800 space-y-2 mt-4">
              <div className="text-[10px] font-mono uppercase text-slate-400 tracking-wider">Aeromobile Selezionato</div>
              <div className="flex items-center justify-between">
                <span className="font-black font-mono text-cyan-300 text-base">{selectedAircraft.tail_number}</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-200">{selectedAircraft.aircraft_type}</span>
              </div>
              <div className="text-xs text-white font-semibold truncate" title={selectedAircraft.name}>{selectedAircraft.name}</div>
              <div className="text-xs font-mono text-slate-400 flex items-center gap-1 pt-1 border-t border-slate-800/80">
                <MapPin size={13} className="text-rose-400" /> Base attuale: <strong className="text-white">{selectedAircraft.current_icao}</strong>
              </div>
            </div>
          )}
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 p-5 lg:p-8 min-w-0">
        
        {/* TAB 1: FLIGHT DECK & HUD */}
        {activeTab === 'flight' && (
          <div className="space-y-6">
            {/* Aircraft Mismatch Warning Banner */}
            {isModelMismatch && (
              <div className="p-4 rounded-xl border border-amber-500/60 bg-amber-950/35 flex flex-wrap items-center justify-between gap-4 shadow-lg">
                <div className="flex items-start gap-3">
                  <AlertTriangle size={22} className="text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-sm font-bold text-amber-300 font-mono">
                      MODELLO DIVERSO CARICATO IN X-PLANE 12!
                    </div>
                    <p className="text-xs text-slate-200 mt-0.5">
                      Su X-Plane 12 stai pilotando un <strong className="text-white font-mono">{xpAircraftIcao}</strong>
                      {xpAircraftTailnum ? <span className="text-amber-200 font-mono"> ({xpAircraftTailnum})</span> : ''}, 
                      mentre in SkyOps XP è selezionato <strong className="text-white font-mono">{selectedAircraft?.tail_number} ({selectedAircraft?.aircraft_type})</strong>.
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {matchingFleetAircraft ? (
                    <button
                      onClick={() => {
                        setSelectedAircraft(matchingFleetAircraft);
                        showNotice(`Selezionato ${matchingFleetAircraft.tail_number} (${matchingFleetAircraft.aircraft_type}) per allineamento a XP12`, 'success');
                      }}
                      className="bg-amber-500 hover:bg-amber-400 text-slate-950 font-mono font-bold text-xs px-3.5 py-2 rounded-lg shadow transition"
                    >
                      Usa {matchingFleetAircraft.tail_number} ({matchingFleetAircraft.aircraft_type})
                    </button>
                  ) : (
                    <button
                      onClick={() => setActiveTab('rental')}
                      className="bg-slate-800 hover:bg-slate-700 text-amber-300 border border-amber-500/40 font-mono font-bold text-xs px-3.5 py-2 rounded-lg transition"
                    >
                      Cerca {xpAircraftIcao} nel Mercato
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Mission Overview Banner */}
            <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold uppercase ${
                      flightPhase === 'ENROUTE' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 animate-pulse' :
                      flightPhase === 'TOUCHDOWN' || flightPhase === 'TAXI_IN' || flightPhase === 'PARKED' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
                      'bg-slate-800 text-slate-300'
                    }`}>
                      FASE: {flightPhase}
                    </span>
                    {fleet.length > 0 ? (
                      <select
                        value={selectedAircraft?.id || ''}
                        onChange={(e) => {
                          const ac = fleet.find(a => a.id === parseInt(e.target.value));
                          if (ac) setSelectedAircraft(ac);
                        }}
                        className="bg-slate-900 border border-slate-700 text-white font-mono text-xs font-bold px-3 py-1 rounded-lg focus:outline-none focus:border-cyan-500"
                      >
                        {fleet.map((ac) => (
                          <option key={ac.id} value={ac.id}>
                            {ac.tail_number} ({ac.name}) {ac.ownership === 'LEASED' ? '[NOLEGGIO]' : ''}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <button
                        onClick={() => setActiveTab('rental')}
                        className="text-xs font-mono text-cyan-300 hover:underline flex items-center gap-1"
                      >
                        <Key size={13} /> Nessun aereo in flotta — Vai a Mercato & Noleggio
                      </button>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 mt-1.5 font-mono">
                    Posizione salvata: <strong className="text-white">{selectedAircraft?.current_icao || 'N/D'}</strong> | Carburante a bordo: {liveTelemetry.fuel_total_kg > 0 ? liveTelemetry.fuel_total_kg.toFixed(0) : selectedAircraft?.fuel_quantity_kg?.toFixed(0)} kg
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2.5">
                  {selectedAircraft && (() => {
                    const isCrewExcluded = crewOverride !== null ? crewOverride : Boolean(activeFlight?.exclude_crew_cost);
                    const hasSalaried = Boolean(activeFlight?.has_salaried_crew);
                    const effRules = flightRulesOverride || activeFlight?.flight_rules || 'IFR';
                    const effTourVal = flightTourOverride !== undefined ? flightTourOverride : (activeFlight?.tour_id ? String(activeFlight.tour_id) : '');
                    const crewSpec = activeFlight?.crew_spec || {
                      label: selectedAircraft.category === 'AIRLINER' ? '2 Piloti + 4 A/V' : selectedAircraft.category === 'BIZJET' ? '2 Piloti + 1 A/V' : '1 Pilota',
                      hourly_rate_eur: selectedAircraft.category === 'AIRLINER' ? 520 : selectedAircraft.category === 'BIZJET' ? 240 : 90
                    };
                    return (
                      <>
                        <button
                          type="button"
                          onClick={() => setCrewOverride(!isCrewExcluded)}
                          className={`flex items-center gap-1.5 font-mono text-xs font-semibold px-3 py-2 rounded-lg border transition ${
                            isCrewExcluded
                              ? 'bg-amber-950/40 border-amber-500/50 text-amber-300 hover:bg-amber-900/40'
                              : hasSalaried
                                ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-200 hover:bg-emerald-900/40'
                                : 'bg-indigo-950/40 border-indigo-500/40 text-indigo-200 hover:bg-indigo-900/40'
                          }`}
                          title="Clicca per escludere/includere equipaggio (es. Volo Solo VFR)"
                        >
                          {isCrewExcluded
                            ? '🧑‍✈️ Volo Solo (Equip. € 0)'
                            : hasSalaried
                              ? `👨‍✈️ Equip. Fisso (${crewSpec.label} • € 0/h)`
                              : `👨‍✈️ Equipaggio: ${crewSpec.label} (€ ${crewSpec.hourly_rate_eur}/h)`}
                        </button>
                        <button
                          type="button"
                          onClick={() => setFlightRulesOverride(effRules === 'IFR' ? 'VFR' : 'IFR')}
                          className={`font-mono text-xs font-bold px-3 py-2 rounded-lg border transition ${
                            effRules === 'VFR'
                              ? 'bg-sky-950/40 border-sky-400/50 text-sky-300 hover:bg-sky-900/40'
                              : 'bg-slate-800/80 border-slate-700 text-cyan-300 hover:bg-slate-700'
                          }`}
                          title="IFR paga Eurocontrol & Handling Pax; VFR è esente"
                        >
                          {effRules === 'VFR' ? '🌤️ VFR (No Eurocontrol)' : '🛫 IFR (Eurocontrol ON)'}
                        </button>
                        {toursList.length > 0 && (
                          <select
                            value={effTourVal}
                            onChange={(e) => setFlightTourOverride(e.target.value)}
                            className="bg-slate-900 border border-slate-700 text-amber-300 font-mono text-xs font-semibold px-2.5 py-2 rounded-lg focus:outline-none focus:border-amber-400"
                            title="Associa questo volo a un Tour IVAO"
                          >
                            <option value="">🗺️ Nessun Tour</option>
                            {toursList.map((tr) => (
                              <option key={tr.id} value={String(tr.id)}>
                                🗺️ {tr.name}
                              </option>
                            ))}
                          </select>
                        )}
                      </>
                    );
                  })()}
                  {flightPhase === 'OFFLINE' && selectedAircraft && (
                    <button
                      onClick={handleRefuelAircraft}
                      className="flex items-center gap-2 font-semibold px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-purple-300 border border-purple-500/30 transition text-sm"
                      title="Rifornisci il serbatoio pagando solo i kg aggiunti (1,75 €/kg)"
                    >
                      <Fuel size={15} /> Rifornisci
                    </button>
                  )}
                  {flightPhase === 'OFFLINE' ? (
                    <button
                      onClick={() => handleStartFlight()}
                      disabled={!selectedAircraft}
                      className={`flex items-center gap-2 font-semibold px-4 py-2 rounded-lg shadow transition ${
                        activeFlight?.flight_checks?.xp_connected && liveTelemetry.parking_brake >= 0.5 && liveTelemetry.on_ground > 0.5 && activeFlight?.flight_checks?.at_origin
                          ? 'bg-cyan-600 hover:bg-cyan-500 text-white'
                          : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700'
                      }`}
                    >
                      <Zap size={16} /> Avvia Monitoraggio Volo
                    </button>
                  ) : (
                    <button
                      onClick={handleFinalizeFlight}
                      disabled={loading}
                      className={`flex items-center gap-2 font-semibold px-4 py-2 rounded-lg shadow transition ${
                        liveTelemetry.parking_brake >= 0.5 && liveTelemetry.on_ground > 0.5 && activeFlight?.flight_checks?.at_destination
                          ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                          : 'bg-slate-800 hover:bg-slate-700 text-amber-300 border border-amber-500/40'
                      }`}
                    >
                      <CheckCircle size={16} /> Concludi Volo & Registra Bilancio
                    </button>
                  )}
                </div>
              </div>

              {/* Active Planned Mission / Contract Summary */}
              {activeFlight?.job ? (
                <div className="bg-slate-900/70 p-3.5 rounded-lg border border-cyan-500/30 flex flex-wrap items-center justify-between gap-3 font-mono text-xs">
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                      activeFlight.job.reward_usd > 0 ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-700 text-slate-300'
                    }`}>
                      {activeFlight.job.reward_usd > 0 ? 'COMMERCIALE' : 'PERSONALE / FERRY'}
                    </span>
                    <div>
                      <span className="font-bold text-white text-sm">{activeFlight.job.origin_icao} ➔ {activeFlight.job.destination_icao}</span>
                      <span className="text-slate-400 ml-2">({activeFlight.job.distance_nm} NM • {activeFlight.job.pax_count} pax • {activeFlight.job.cargo_kg} kg cargo)</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-400">Ricavo Previsto: </span>
                    <span className={`font-bold text-sm ${activeFlight.job.reward_usd > 0 ? 'text-emerald-400' : 'text-slate-400'}`}>
                      {activeFlight.job.reward_usd > 0 ? formatEuro(activeFlight.job.reward_usd) : '€ 0,00 (Solo Costi)'}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="bg-slate-900/50 p-3 rounded-lg border border-dashed border-slate-700 flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
                  <span className="text-slate-400">Nessun piano di volo attivo assegnato a {selectedAircraft?.tail_number}.</span>
                  <button
                    onClick={() => setActiveTab('simbrief')}
                    className="text-cyan-400 hover:underline font-bold"
                  >
                    + Pianifica Volo (SimBrief o Manuale)
                  </button>
                </div>
              )}

              {/* Live Pre-Flight / Post-Flight Verification Checklist */}
              {(() => {
                const fc = activeFlight?.flight_checks;
                const brakeOn = liveTelemetry.parking_brake >= 0.5;
                const stoppedOnGround = liveTelemetry.on_ground > 0.5 && liveTelemetry.groundspeed_kts < 5.0;

                if (flightPhase === 'OFFLINE') {
                  const originCode = fc?.planned_origin_icao || selectedAircraft?.current_icao || 'N/D';
                  const dist = fc?.origin_distance_nm;
                  const atOrigin = fc?.at_origin ?? false;
                  return (
                    <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800 space-y-2 font-mono text-[11px]">
                      <div className="text-slate-400 font-bold uppercase tracking-wider">Controlli Pre-Volo Obbligatori per l'Avvio:</div>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                        <div className={`px-2.5 py-1.5 rounded border flex items-center gap-2 ${xpConnected ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-300' : 'bg-rose-950/30 border-rose-500/30 text-rose-300'}`}>
                          {xpConnected ? <CheckCircle size={13} /> : <AlertTriangle size={13} />}
                          <span>XP12: {xpConnected ? 'Connesso' : 'Disconnesso'}</span>
                        </div>
                        <div className={`px-2.5 py-1.5 rounded border flex items-center gap-2 ${atOrigin && xpConnected ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-300' : 'bg-rose-950/30 border-rose-500/30 text-rose-300'}`}>
                          {atOrigin && xpConnected ? <CheckCircle size={13} /> : <AlertTriangle size={13} />}
                          <span>
                            Su {originCode}: {dist !== null && dist !== undefined ? (dist <= 5 ? `OK (${dist} NM)` : `Distante ${dist} NM!`) : (xpConnected ? 'OK' : 'N/D')}
                          </span>
                        </div>
                        <div className={`px-2.5 py-1.5 rounded border flex items-center gap-2 ${brakeOn && stoppedOnGround ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-300' : 'bg-amber-950/30 border-amber-500/30 text-amber-300'}`}>
                          {brakeOn && stoppedOnGround ? <CheckCircle size={13} /> : <AlertTriangle size={13} />}
                          <span>Freni Parcheggio: {brakeOn ? 'INSERITI' : 'DISINSERITI'}</span>
                        </div>
                      </div>
                    </div>
                  );
                }

                // Post-Flight / Arrival Checklist + Emergency Diversion Box
                const targetCode = fc?.planned_destination_icao || 'N/D';
                const destDist = fc?.destination_distance_nm;
                const atDest = fc?.at_destination ?? false;
                return (
                  <div className="bg-slate-950/70 p-3.5 rounded-lg border border-slate-800 space-y-3 font-mono text-[11px]">
                    <div className="flex flex-wrap justify-between items-center gap-2">
                      <span className="text-slate-400 font-bold uppercase tracking-wider">Controlli Chiusura & Parcheggio Finale:</span>
                      <button
                        type="button"
                        onClick={() => setShowDiversionPanel(!showDiversionPanel)}
                        className="text-amber-300 hover:text-amber-200 underline text-[11px]"
                      >
                        {showDiversionPanel ? 'Nascondi Dirottamento / Alternato' : '⚠️ Emergenza o Atterraggio ad Alternato?'}
                      </button>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      <div className={`px-2.5 py-1.5 rounded border flex items-center gap-2 ${stoppedOnGround ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-300' : 'bg-amber-950/30 border-amber-500/30 text-amber-300'}`}>
                        {stoppedOnGround ? <CheckCircle size={13} /> : <AlertTriangle size={13} />}
                        <span>Assetto: {stoppedOnGround ? 'Fermo a terra' : 'In volo / Movimento'}</span>
                      </div>
                      <div className={`px-2.5 py-1.5 rounded border flex items-center gap-2 ${brakeOn ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-300' : 'bg-amber-950/30 border-amber-500/30 text-amber-300'}`}>
                        {brakeOn ? <CheckCircle size={13} /> : <AlertTriangle size={13} />}
                        <span>Freni Parcheggio: {brakeOn ? 'INSERITI' : 'DISINSERITI'}</span>
                      </div>
                      <div className={`px-2.5 py-1.5 rounded border flex items-center gap-2 ${atDest && xpConnected ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-300' : 'bg-rose-950/30 border-rose-500/30 text-rose-300'}`}>
                        {atDest && xpConnected ? <CheckCircle size={13} /> : <AlertTriangle size={13} />}
                        <span>
                          Arrivo {targetCode}: {destDist !== null && destDist !== undefined ? (destDist <= 5 ? `OK (${destDist} NM)` : `Distante ${destDist} NM!`) : (xpConnected ? 'OK' : 'N/D')}
                        </span>
                      </div>
                    </div>

                    {showDiversionPanel && (
                      <div className="bg-amber-950/20 border border-amber-500/30 p-3 rounded-lg grid grid-cols-1 sm:grid-cols-3 gap-3 items-end">
                        <div>
                          <label className="text-amber-300 block mb-1 font-semibold">ICAO Arrivo Effettivo (Alternato)</label>
                          <input
                            type="text"
                            maxLength={4}
                            placeholder="es. LIRA"
                            value={actualArrivalIcao}
                            onChange={(e) => setActualArrivalIcao(e.target.value.toUpperCase())}
                            className="w-full bg-slate-900 border border-amber-500/40 p-2 rounded text-white font-bold uppercase focus:outline-none focus:border-amber-400"
                          />
                        </div>
                        <div className="sm:col-span-2">
                          <label className="text-slate-300 block mb-1">Motivo Dirottamento / Emergenza (Opzionale)</label>
                          <input
                            type="text"
                            placeholder="es. Meteo avverso / Emergenza tecnica / Pista chiusa"
                            value={diversionReason}
                            onChange={(e) => setDiversionReason(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-amber-400"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>

            {/* Post-Flight Debriefing & Economic Summary Card */}
            {lastFlightSummary && (
              <div className="glass-panel p-6 rounded-2xl border border-emerald-500/50 bg-gradient-to-br from-slate-900/95 via-slate-900/80 to-emerald-950/25 shadow-2xl space-y-5">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 bg-emerald-500/20 text-emerald-400 rounded-xl border border-emerald-500/30">
                      <CheckCircle size={24} />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        Riepilogo Fine Volo & Registrazione Bilancio
                      </h3>
                      <p className="text-xs text-slate-300 font-mono">
                        Volo <strong className="text-cyan-300">{lastFlightSummary.flight_number}</strong> • {lastFlightSummary.tail_number} ({lastFlightSummary.aircraft_name}) • Rotta: <strong className="text-white">{lastFlightSummary.origin_icao} ➔ {lastFlightSummary.destination_icao}</strong>
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setActiveTab('finances')}
                      className="px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-mono font-bold text-xs transition"
                    >
                      Apri Bilancio & Libro Mastro
                    </button>
                    <button
                      onClick={() => setLastFlightSummary(null)}
                      className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs transition"
                    >
                      ✕ Chiudi
                    </button>
                  </div>
                </div>

                {lastFlightSummary.notes && (
                  <div className="p-2.5 rounded-lg bg-amber-950/30 border border-amber-500/40 text-amber-300 text-xs font-mono">
                    ⚠️ {lastFlightSummary.notes}
                  </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 font-mono text-xs">
                  {/* Column 1: Flight Metrics & Touchdown */}
                  <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2.5">
                    <div className="text-slate-400 font-bold uppercase border-b border-slate-800 pb-1.5">Dati di Volo & Atterraggio</div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Durata Volo (Block Time):</span>
                      <span className="text-white font-bold">{lastFlightSummary.duration_min} min</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Carburante Consumato:</span>
                      <span className="text-purple-300 font-bold">{lastFlightSummary.fuel_used_kg} kg</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Rateo Touchdown:</span>
                      <span className="text-cyan-300 font-bold">
                        {lastFlightSummary.touchdown?.fpm !== null && lastFlightSummary.touchdown?.fpm !== undefined ? `${lastFlightSummary.touchdown.fpm} fpm` : 'N/D'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Impatto G-Force:</span>
                      <span className="text-amber-300 font-bold">
                        {lastFlightSummary.touchdown?.g ? `${lastFlightSummary.touchdown.g} G` : 'N/D'} ({lastFlightSummary.touchdown?.rating || 'OK'})
                      </span>
                    </div>
                    {lastFlightSummary.reputation && (
                      <div className="flex justify-between pt-1 border-t border-slate-800/80">
                        <span className="text-slate-400">Reputazione Azienda:</span>
                        <span className={`font-bold ${lastFlightSummary.reputation.delta >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {lastFlightSummary.reputation.new}% ({lastFlightSummary.reputation.delta >= 0 ? '+' : ''}{lastFlightSummary.reputation.delta}%)
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Column 2: Economic Breakdown */}
                  <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2">
                    <div className="text-slate-400 font-bold uppercase border-b border-slate-800 pb-1.5 flex justify-between">
                      <span>Conto Economico del Volo</span>
                      <span className="text-cyan-400">{lastFlightSummary.flight_rules || 'IFR'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-emerald-400">(+) Ricavo Lordo Volo:</span>
                      <span className="text-emerald-400 font-bold">+{formatEuro(lastFlightSummary.financials?.gross_revenue)}</span>
                    </div>
                    {lastFlightSummary.financials?.reputation_bonus_eur !== 0 && lastFlightSummary.financials?.reputation_bonus_eur !== undefined && (
                      <div className="flex justify-between text-[11px] pl-2">
                        <span className="text-slate-400">di cui Bonus/Malus Qualità ({lastFlightSummary.financials?.reputation_bonus_pct > 0 ? '+' : ''}{lastFlightSummary.financials?.reputation_bonus_pct}%):</span>
                        <span className={lastFlightSummary.financials.reputation_bonus_eur >= 0 ? 'text-emerald-300' : 'text-amber-300'}>
                          {lastFlightSummary.financials.reputation_bonus_eur >= 0 ? '+' : ''}{formatEuro(lastFlightSummary.financials.reputation_bonus_eur)}
                        </span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-slate-400">Carburante Bruciato:</span>
                      <span className="text-slate-300 font-mono text-[11px]">Già pagato al rifornimento (€ 0,00)</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400 flex items-center gap-1.5">
                        (-) Tassa Atterraggio:
                        {lastFlightSummary.financials?.is_home_base && (
                          <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold">
                            BASE -{lastFlightSummary.financials?.landing_fee_discount_pct}%
                          </span>
                        )}
                      </span>
                      <span className="text-rose-400">-{formatEuro(lastFlightSummary.financials?.landing_fee)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">(-) Navigazione Eurocontrol:</span>
                      <span className={lastFlightSummary.financials?.nav_fee > 0 ? 'text-rose-400' : 'text-slate-400'}>
                        {lastFlightSummary.financials?.nav_fee > 0
                          ? `-${formatEuro(lastFlightSummary.financials.nav_fee)}`
                          : lastFlightSummary.financials?.nav_exempt_reason === 'EXTRA_EU'
                            ? '€ 0,00 (Extra-UE / No Eurocontrol)'
                            : lastFlightSummary.financials?.nav_exempt_reason === 'MTOW_UNDER_2T'
                              ? '€ 0,00 (< 2t Esente)'
                              : '€ 0,00 (Esente VFR)'}
                      </span>
                    </div>
                    {lastFlightSummary.financials?.handling_fee > 0 && (
                      <div className="flex justify-between">
                        <span className="text-slate-400">(-) FBO / Ground Handling & Pax:</span>
                        <span className="text-rose-400">-{formatEuro(lastFlightSummary.financials.handling_fee)}</span>
                      </div>
                    )}
                    {lastFlightSummary.financials?.maint_reserve_cost > 0 && (
                      <div className="flex justify-between">
                        <span className="text-slate-400">(-) Riserva Manutenzione (Ore):</span>
                        <span className="text-rose-400">-{formatEuro(lastFlightSummary.financials.maint_reserve_cost)}</span>
                      </div>
                    )}
                    {lastFlightSummary.financials?.ioc_cost > 0 && (
                      <div className="flex justify-between">
                        <span className="text-slate-400">(-) Costi Indiretti (GDS/Broker/OCC):</span>
                        <span className="text-rose-400">-{formatEuro(lastFlightSummary.financials.ioc_cost)}</span>
                      </div>
                    )}
                    {lastFlightSummary.financials?.lease_cost > 0 && (
                      <div className="flex justify-between">
                        <span className="text-slate-400">(-) Canone Noleggio Orario:</span>
                        <span className="text-rose-400">-{formatEuro(lastFlightSummary.financials.lease_cost)}</span>
                      </div>
                    )}
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400 flex items-center gap-1.5">
                        (-) Equipaggio ({lastFlightSummary.financials?.crew_label || 'Piloti/A.V.'}):
                        {lastFlightSummary.financials?.crew_source === 'SOLO_VFR' && (
                          <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] font-bold">SOLO</span>
                        )}
                        {lastFlightSummary.financials?.crew_source === 'SALARIED' && (
                          <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold">FISSO</span>
                        )}
                      </span>
                      <span className={lastFlightSummary.financials?.crew_cost > 0 ? 'text-rose-400' : 'text-slate-400'}>
                        {lastFlightSummary.financials?.crew_cost > 0 ? `-${formatEuro(lastFlightSummary.financials.crew_cost)}` : '€ 0,00'}
                      </span>
                    </div>
                    {lastFlightSummary.financials?.penalty_eur > 0 && (
                      <div className="flex justify-between text-rose-300 font-bold">
                        <span>(-) Penale / Risarcimento Touchdown:</span>
                        <span>-{formatEuro(lastFlightSummary.financials.penalty_eur)}</span>
                      </div>
                    )}
                    <div className="flex justify-between border-t border-slate-800 pt-2 font-bold text-sm">
                      <span className="text-white">(=) Utile Netto Volo:</span>
                      <span className={lastFlightSummary.financials?.net_profit >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                        {lastFlightSummary.financials?.net_profit >= 0 ? '+' : ''}{formatEuro(lastFlightSummary.financials?.net_profit)}
                      </span>
                    </div>
                    <div className="flex justify-between text-[11px] pt-1 text-slate-400">
                      <span>Nuovo Saldo Cassa:</span>
                      <span className="text-emerald-300 font-bold">{formatEuro(lastFlightSummary.new_cash_balance)}</span>
                    </div>
                  </div>

                  {/* Column 3: Component Wear Applied */}
                  <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2">
                    <div className="text-slate-400 font-bold uppercase border-b border-slate-800 pb-1.5">Usura Applicata alle Componenti</div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Motore / Propulsori:</span>
                      <span className="text-amber-300">-{lastFlightSummary.wear?.engine?.toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Cellula & Struttura:</span>
                      <span className="text-amber-300">-{lastFlightSummary.wear?.airframe?.toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Pneumatici Carrello:</span>
                      <span className="text-amber-300">-{lastFlightSummary.wear?.tires?.toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Impianto Frenante:</span>
                      <span className="text-amber-300">-{lastFlightSummary.wear?.brakes?.toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Avionica & Sensori:</span>
                      <span className="text-amber-300">-{lastFlightSummary.wear?.avionics?.toFixed(2)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Glass Cockpit Gauges Grid (unchanged flight gauge sizing) */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 hud-gauges">
              <div className="glass-panel p-4 rounded-xl border border-slate-800/80">
                <div className="text-xs text-slate-400 font-mono uppercase">Velocità Indicata (IAS)</div>
                <div className="text-3xl font-black font-mono text-cyan-400 mt-1">
                  {liveTelemetry.ias_kts.toFixed(0)} <span className="text-sm font-normal text-slate-400">kts</span>
                </div>
                <div className="text-xs text-slate-500 font-mono mt-1">
                  GS: {liveTelemetry.groundspeed_kts.toFixed(0)} kts
                </div>
              </div>

              <div className="glass-panel p-4 rounded-xl border border-slate-800/80">
                <div className="text-xs text-slate-400 font-mono uppercase">Altitudine</div>
                <div className="text-3xl font-black font-mono text-emerald-400 mt-1">
                  {(liveTelemetry.elevation_m * 3.28084).toFixed(0)} <span className="text-sm font-normal text-slate-400">ft</span>
                </div>
                <div className="text-xs text-slate-500 font-mono mt-1">
                  VS: {liveTelemetry.vs_fpm.toFixed(0)} fpm
                </div>
              </div>

              <div className="glass-panel p-4 rounded-xl border border-slate-800/80">
                <div className="text-xs text-slate-400 font-mono uppercase">Carico G</div>
                <div className="text-3xl font-black font-mono text-amber-400 mt-1">
                  {liveTelemetry.g_force.toFixed(2)} <span className="text-sm font-normal text-slate-400">G</span>
                </div>
                <div className="text-xs text-slate-500 font-mono mt-1">
                  Max: {activeFlight?.max_g?.toFixed(2) || '1.00'} G
                </div>
              </div>

              <div className="glass-panel p-4 rounded-xl border border-slate-800/80">
                <div className="text-xs text-slate-400 font-mono uppercase">Carburante Residuo</div>
                <div className="text-3xl font-black font-mono text-purple-400 mt-1">
                  {liveTelemetry.fuel_total_kg.toFixed(0)} <span className="text-sm font-normal text-slate-400">kg</span>
                </div>
                <div className="text-xs text-slate-500 font-mono mt-1">
                  Freno Parcheggio: {liveTelemetry.parking_brake > 0.5 ? 'ATTIVO' : 'RILASCIATO'}
                </div>
              </div>
            </div>

            {/* Landing Quality Banner (if landed) */}
            {activeFlight?.touchdown_fpm !== null && activeFlight?.touchdown_fpm !== undefined && (
              <div className="p-4 rounded-xl border bg-emerald-950/40 border-emerald-500/40 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-emerald-500/20 text-emerald-400 rounded-lg">
                    <Award size={24} />
                  </div>
                  <div>
                    <div className="text-xs font-mono uppercase text-emerald-400">Analisi Contatto Pista</div>
                    <div className="text-lg font-bold text-white">
                      Giudizio: <span className="text-emerald-300 font-mono">{activeFlight.touchdown_rating || 'OTTIMO'}</span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-6 text-right font-mono">
                  <div>
                    <div className="text-xs text-slate-400">Rateo di Discesa</div>
                    <div className="text-base font-bold text-cyan-300">{activeFlight.touchdown_fpm} fpm</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">G-Force Touchdown</div>
                    <div className="text-base font-bold text-amber-300">{activeFlight.touchdown_g} G</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: HANGAR & OWNED FLEET (DETAILED VIEW WITH DROPDOWN) */}
        {activeTab === 'fleet' && (() => {
          const ownedFleet = fleet.filter((a) => a.ownership === 'OWNED');
          const hangarAircraft = (selectedAircraft && selectedAircraft.ownership === 'OWNED'
            ? ownedFleet.find((a) => a.id === selectedAircraft.id) || selectedAircraft
            : ownedFleet[0]) || null;

          return (
          <div className="space-y-6">
            {/* Top Toolbar with Dropdown */}
            <div className="glass-panel p-5 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <Plane size={22} className="text-cyan-400 rotate-45" /> Hangar Personale (Aerei di Proprietà)
                </h2>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  Scheda tecnica, cronistoria d'acquisto, motorizzazione e scadenziario manutenzioni per ogni velivolo.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                {/* Aircraft Dropdown Selector */}
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-400 uppercase font-semibold">Aereo:</span>
                  <select
                    value={hangarAircraft?.id || ''}
                    onChange={(e) => {
                      const ac = ownedFleet.find(a => a.id === parseInt(e.target.value));
                      if (ac) setSelectedAircraft(ac);
                    }}
                    className="bg-slate-900 border border-cyan-500/50 text-cyan-300 font-mono font-bold text-sm px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-400 cursor-pointer shadow-lg"
                  >
                    {ownedFleet.map((ac) => (
                      <option key={ac.id} value={ac.id} className="bg-slate-900 text-white">
                        {ac.tail_number} — {ac.name} @ {ac.current_icao}
                      </option>
                    ))}
                    {ownedFleet.length === 0 && (
                      <option value="">Nessun aereo presente</option>
                    )}
                  </select>
                </div>

                <button
                  onClick={() => setShowAddModal(true)}
                  className="flex items-center gap-1.5 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold font-mono text-xs px-3.5 py-2 rounded-lg shadow transition"
                >
                  <Plus size={15} /> Aggiungi Aereo
                </button>

                {hangarAircraft && (
                  <>
                    <button
                      onClick={() => openEditModal(hangarAircraft)}
                      className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold font-mono text-xs px-3.5 py-2 rounded-lg transition"
                    >
                      <Edit3 size={14} className="text-amber-400" /> Modifica Dati & Foto
                    </button>
                    <button
                      onClick={() => handleDeleteAircraft(hangarAircraft)}
                      title="Elimina dall hangar"
                      className="p-2 rounded-lg bg-slate-800 hover:bg-rose-950 text-slate-400 hover:text-rose-400 border border-slate-700 transition"
                    >
                      <Trash2 size={16} />
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Selected Aircraft Full Presentation */}
            {hangarAircraft ? (
              <div className="space-y-6">
                {/* Hero Showcase Card */}
                <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden grid grid-cols-1 lg:grid-cols-12 gap-0">
                  {/* Left: Aircraft Photo / Blueprint Banner */}
                  <div className="lg:col-span-5 relative bg-slate-950 min-h-[260px] flex items-center justify-center overflow-hidden border-b lg:border-b-0 lg:border-r border-slate-800">
                    {hangarAircraft.image_url ? (
                      <img 
                        src={hangarAircraft.image_url} 
                        alt={hangarAircraft.name}
                        className="w-full h-full object-cover min-h-[260px]"
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                    ) : null}
                    
                    {/* Fallback Graphic if no image */}
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-900/60 to-transparent flex flex-col justify-end p-5 pointer-events-none">
                      <div className="text-3xl font-black font-mono tracking-wider text-cyan-400/90 drop-shadow">
                        {hangarAircraft.tail_number}
                      </div>
                      <div className="text-xs font-mono text-slate-300">
                        {hangarAircraft.aircraft_type} • {hangarAircraft.category}
                      </div>
                    </div>

                    <label className="absolute top-3 right-3 bg-slate-900/90 hover:bg-cyan-600 text-white px-3 py-1.5 rounded-lg backdrop-blur-md border border-slate-700 text-xs font-mono flex items-center gap-1.5 shadow transition cursor-pointer z-10">
                      <Camera size={14} /> Carica Foto PC
                      <input 
                        type="file" 
                        accept="image/*" 
                        className="hidden" 
                        onChange={(e) => {
                          if (e.target.files?.[0]) handleImageFileUpload(e.target.files[0]);
                        }} 
                      />
                    </label>
                  </div>

                  {/* Right: Aircraft Overview & Operations */}
                  <div className="lg:col-span-7 p-6 flex flex-col justify-between space-y-4">
                    <div>
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl font-black text-white">{hangarAircraft.name}</span>
                          <span className="text-xs px-2.5 py-0.5 rounded font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                            {hangarAircraft.category}
                          </span>
                        </div>
                        {(hangarAircraft.remaining_payments_months > 0 || hangarAircraft.financed_amount_remaining_eur > 0) ? (
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-xs px-3 py-1 rounded-full font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                              {hangarAircraft.acquisition_mode === 'FINANCIAL_LEASE' ? 'LEASING FINANZIARIO' : 'MUTUO BANCARIO'} • {formatEuro(hangarAircraft.monthly_payment_eur || 0)}/mese ({hangarAircraft.remaining_payments_months || 0} mesi • Debito {formatEuro(hangarAircraft.financed_amount_remaining_eur || 0)})
                            </span>
                            <button
                              type="button"
                              onClick={() => handlePayoffAircraftDebt(hangarAircraft)}
                              disabled={loading}
                              className="text-xs px-3 py-1 rounded-full font-mono font-bold bg-emerald-600/25 hover:bg-emerald-600/40 text-emerald-300 border border-emerald-500/40 transition disabled:opacity-50"
                              title="Salda subito l'intero capitale residuo e azzera le rate mensili"
                            >
                              💳 Estingui Debito ({formatEuro(hangarAircraft.financed_amount_remaining_eur || 0)})
                            </button>
                          </div>
                        ) : (
                          <span className="text-xs px-3 py-1 rounded-full font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                            {hangarAircraft.ownership === 'LEASED' ? 'NOLEGGIO ORARIO' : 'DI PROPRIETÀ (CASH)'}
                          </span>
                        )}
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 font-mono text-xs">
                        <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                          <div className="text-slate-400">Anno Fabbricazione</div>
                          <div className="text-base font-bold text-white mt-0.5">{hangarAircraft.year_manufactured || 2021}</div>
                        </div>

                        <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                          <div className="text-slate-400">Data Acquisto</div>
                          <div className="text-base font-bold text-white mt-0.5">
                            {hangarAircraft.purchase_date ? new Date(hangarAircraft.purchase_date).toLocaleDateString() : 'N/D'}
                          </div>
                        </div>

                        <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                          <div className="text-slate-400">Valore di Acquisto</div>
                          <div className="text-base font-bold text-emerald-400 mt-0.5">
                            {formatEuro(hangarAircraft.purchase_price_eur || 0)}
                          </div>
                        </div>

                        <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                          <div className="text-slate-400">Aeroporto Base</div>
                          <div className="text-base font-bold text-cyan-300 mt-0.5 flex items-center gap-1">
                            <MapPin size={14} className="text-rose-400" /> {hangarAircraft.current_icao}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Quick Fuel & Actions */}
                    <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
                      <div className="font-mono text-xs">
                        <span className="text-slate-400">Carburante Attuale: </span>
                        <span className="text-purple-300 font-bold">{(hangarAircraft.fuel_quantity_kg || 0).toFixed(0)} kg</span>
                        <span className="text-slate-500"> / {(hangarAircraft.fuel_capacity_kg || 0).toFixed(0)} kg</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleSyncToXplane(hangarAircraft.id)}
                          className="flex items-center gap-1.5 text-xs font-mono font-semibold px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/30 transition"
                        >
                          <RefreshCw size={13} /> Sincronizza su XP12
                        </button>
                        <button
                          onClick={() => handleRefuelAircraft(hangarAircraft)}
                          className="flex items-center gap-1.5 text-xs font-mono font-semibold px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-purple-300 border border-purple-500/30 transition"
                        >
                          <Fuel size={13} /> Rifornisci
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 3 Detailed Technical Inspection Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-mono text-xs">
                  {/* Card 1: Powerplant & Avionics */}
                  <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-2">
                      <Cpu size={16} className="text-cyan-400" /> Propulsione & Avionica
                    </h3>
                    <div className="space-y-2 text-slate-300">
                      <div>
                        <div className="text-slate-400 text-[11px]">Motorizzazione</div>
                        <div className="font-bold text-white">{hangarAircraft.engine_type || 'Standard Turbofan/Piston'}</div>
                      </div>
                      <div>
                        <div className="text-slate-400 text-[11px]">Suite Avionica</div>
                        <div className="font-bold text-white">{hangarAircraft.avionics_system || 'Standard Flight Deck'}</div>
                      </div>
                      <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/80">
                        <div>
                          <div className="text-slate-400">Ore Cellula:</div>
                          <div className="font-bold text-cyan-300 text-sm">{(hangarAircraft.airframe_hours || 0).toFixed(1)} h</div>
                        </div>
                        <div>
                          <div className="text-slate-400">Ore Motore:</div>
                          <div className="font-bold text-emerald-300 text-sm">{(hangarAircraft.engine_hours || 0).toFixed(1)} h</div>
                        </div>
                      </div>
                      <div className="pt-2 text-[11px] text-slate-400">
                        Ore residue al TBO Motore: <span className="text-amber-300 font-bold">{((hangarAircraft.tbo_hours || 3500) - (hangarAircraft.engine_hours || 0)).toFixed(1)} h</span>
                      </div>
                    </div>
                  </div>

                  {/* Card 2: Maintenance Deadlines */}
                  <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-2">
                      <Calendar size={16} className="text-amber-400" /> Scadenziario Manutenzioni
                    </h3>
                    
                    {/* 50h check */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-slate-300">
                        <span>Tagliando 50 Ore (Olio):</span>
                        <span className="font-bold text-white">
                          {Math.max(0, (hangarAircraft.next_50h_inspection_hours || 50) - (hangarAircraft.airframe_hours || 0)).toFixed(1)} h rimaste
                        </span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5">
                        <div 
                          className="bg-emerald-500 h-1.5 rounded-full" 
                          style={{ width: `${Math.min(100, Math.max(5, (1 - ((hangarAircraft.next_50h_inspection_hours || 50) - (hangarAircraft.airframe_hours || 0)) / 50) * 100))}%` }} 
                        />
                      </div>
                    </div>

                    {/* 100h check */}
                    <div className="space-y-1 pt-1">
                      <div className="flex justify-between text-slate-300">
                        <span>Ispezione 100 Ore:</span>
                        <span className="font-bold text-white">
                          {Math.max(0, (hangarAircraft.next_100h_inspection_hours || 100) - (hangarAircraft.airframe_hours || 0)).toFixed(1)} h rimaste
                        </span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5">
                        <div 
                          className="bg-cyan-500 h-1.5 rounded-full" 
                          style={{ width: `${Math.min(100, Math.max(5, (1 - ((hangarAircraft.next_100h_inspection_hours || 100) - (hangarAircraft.airframe_hours || 0)) / 100) * 100))}%` }} 
                        />
                      </div>
                    </div>

                    {/* Annual check */}
                    <div className="pt-2 border-t border-slate-800/80">
                      <div className="text-slate-400 text-[11px]">Scadenza Ispezione Annuale Certificata:</div>
                      <div className="text-emerald-400 font-bold text-sm mt-0.5">
                        {hangarAircraft.next_annual_inspection ? new Date(hangarAircraft.next_annual_inspection).toLocaleDateString() : 'Valida (12 Mesi)'}
                      </div>
                    </div>
                  </div>

                  {/* Card 3: Health Overview */}
                  <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-2">
                      <Wrench size={16} className="text-emerald-400" /> Integrità Componenti
                    </h3>
                    <div className="space-y-2">
                      {[
                        { label: 'Motore', pct: hangarAircraft.health_engine_pct ?? 100 },
                        { label: 'Freni & Pastiglie', pct: hangarAircraft.health_brakes_pct ?? 100 },
                        { label: 'Pneumatici', pct: hangarAircraft.health_tires_pct ?? 100 },
                        { label: 'Struttura Cellula', pct: hangarAircraft.health_airframe_pct ?? 100 },
                      ].map((item, idx) => (
                        <div key={idx}>
                          <div className="flex justify-between text-[11px] text-slate-300 mb-0.5">
                            <span>{item.label}</span>
                            <span className="font-bold text-white">{item.pct.toFixed(0)}%</span>
                          </div>
                          <div className="w-full bg-slate-800 rounded-full h-1.5">
                            <div 
                              className={`h-1.5 rounded-full ${item.pct > 75 ? 'bg-emerald-500' : item.pct > 40 ? 'bg-amber-500' : 'bg-rose-500'}`}
                              style={{ width: `${item.pct}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-16 glass-panel rounded-xl border border-dashed border-slate-800 space-y-4">
                <p className="text-slate-400 font-mono text-sm">Nessun aereo di proprietà selezionato o presente nell'hangar.</p>
                <div className="flex flex-wrap justify-center gap-3">
                  <button
                    onClick={() => setActiveTab('rental')}
                    className="bg-cyan-600 hover:bg-cyan-500 text-white font-mono font-bold text-xs px-4 py-2 rounded-lg flex items-center gap-1.5 transition"
                  >
                    <Key size={14} /> Vai al Mercato & Noleggio (XP12)
                  </button>
                  <button
                    onClick={() => setShowAddModal(true)}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-mono text-xs px-4 py-2 rounded-lg flex items-center gap-1.5 transition"
                  >
                    <Plus size={14} /> Inserisci Manualmente
                  </button>
                </div>
              </div>
            )}

            {/* Modal: Edit Aircraft Details & Photo */}
            {showEditModal && selectedAircraft && (
              <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
                <div className="glass-panel p-6 rounded-2xl border border-cyan-500/40 max-w-lg w-full space-y-4 max-h-[90vh] overflow-y-auto">
                  <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <Edit3 size={18} className="text-cyan-400" /> Modifica Dati Velivolo ({selectedAircraft.tail_number})
                    </h3>
                    <button onClick={() => setShowEditModal(false)} className="text-slate-400 hover:text-white">✕</button>
                  </div>

                  <form onSubmit={handleUpdateAircraft} noValidate className="space-y-3 font-mono text-xs">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-slate-400 block mb-1">Marche / Registrazione (Tail Number)*</label>
                        <input
                          type="text"
                          required
                          value={editFormData.tail_number || ''}
                          onChange={(e) => setEditFormData({...editFormData, tail_number: e.target.value.toUpperCase()})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-cyan-300 font-bold focus:outline-none focus:border-cyan-500 font-mono text-xs"
                        />
                      </div>
                      <div>
                        <label className="text-slate-400 block mb-1">Tipo ICAO (es. SF50, B738)</label>
                        <input
                          type="text"
                          value={editFormData.aircraft_type || ''}
                          onChange={(e) => setEditFormData({...editFormData, aircraft_type: e.target.value.toUpperCase()})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500 font-mono text-xs"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-slate-400 block mb-1">Nome Modello & Versione</label>
                        <input
                          type="text"
                          value={editFormData.name || ''}
                          onChange={(e) => setEditFormData({...editFormData, name: e.target.value})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500 text-xs"
                        />
                      </div>
                      <div>
                        <label className="text-slate-400 block mb-1">Data di Acquisto</label>
                        <input
                          type="date"
                          value={editFormData.purchase_date || ''}
                          onChange={(e) => setEditFormData({...editFormData, purchase_date: e.target.value})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500 font-mono text-xs"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="text-slate-400 block mb-1">Foto Velivolo</label>
                      
                      <div className="flex flex-wrap gap-2 items-center mb-2">
                        <label className="bg-cyan-600 hover:bg-cyan-500 text-white px-3 py-1.5 rounded-lg text-xs font-mono font-semibold flex items-center gap-1.5 cursor-pointer shadow transition">
                          <Camera size={14} /> Carica File Foto dal PC
                          <input 
                            type="file" 
                            accept="image/*" 
                            className="hidden" 
                            onChange={(e) => {
                              if (e.target.files?.[0]) handleImageFileUpload(e.target.files[0]);
                            }} 
                          />
                        </label>
                        <span className="text-slate-500 text-[11px]">oppure inserisci un URL diretto:</span>
                      </div>

                      <input
                        type="text"
                        placeholder="https://... o /uploads/..."
                        value={editFormData.image_url || ''}
                        onChange={(e) => setEditFormData({...editFormData, image_url: e.target.value})}
                        className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500 font-mono text-xs"
                      />
                      {editFormData.image_url && (
                        <div className="mt-2 rounded overflow-hidden max-h-36 border border-slate-700 bg-slate-950 flex items-center justify-center">
                          <img src={editFormData.image_url} alt="Anteprima" className="w-full h-36 object-cover" />
                        </div>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-slate-400 block mb-1">Anno Fabbricazione</label>
                        <input
                          type="number"
                          value={editFormData.year_manufactured || 2021}
                          onChange={(e) => setEditFormData({...editFormData, year_manufactured: parseInt(e.target.value)})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                        />
                      </div>
                      <div>
                        <label className="text-slate-400 block mb-1">Prezzo Acquisto (€)</label>
                        <input
                          type="number"
                          value={editFormData.purchase_price_eur || 0}
                          onChange={(e) => setEditFormData({...editFormData, purchase_price_eur: parseFloat(e.target.value)})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="text-slate-400 block mb-1">Motorizzazione</label>
                      <input
                        type="text"
                        placeholder="es. 1x Williams International FJ33-5A Turbofan"
                        value={editFormData.engine_type || ''}
                        onChange={(e) => setEditFormData({...editFormData, engine_type: e.target.value})}
                        className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    <div>
                      <label className="text-slate-400 block mb-1">Suite Avionica</label>
                      <input
                        type="text"
                        placeholder="es. Cirrus Perspective+ by Garmin"
                        value={editFormData.avionics_system || ''}
                        onChange={(e) => setEditFormData({...editFormData, avionics_system: e.target.value})}
                        className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-slate-400 block mb-1">Aeroporto Stazionamento (ICAO)</label>
                        <input
                          type="text"
                          value={editFormData.current_icao || ''}
                          onChange={(e) => setEditFormData({...editFormData, current_icao: e.target.value.toUpperCase()})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                        />
                      </div>
                      <div>
                        <label className="text-slate-400 block mb-1">Capacità Serbatoio (kg)</label>
                        <input
                          type="number"
                          value={editFormData.fuel_capacity_kg || 900}
                          onChange={(e) => setEditFormData({...editFormData, fuel_capacity_kg: parseFloat(e.target.value)})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                        />
                      </div>
                    </div>

                    <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                      <button
                        type="button"
                        onClick={() => setShowEditModal(false)}
                        className="px-4 py-2 rounded bg-slate-800 text-slate-300 hover:bg-slate-700"
                      >
                        Annulla
                      </button>
                      <button
                        type="submit"
                        disabled={loading}
                        className="px-4 py-2 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold"
                      >
                        Salva Modifiche
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {/* Modal: Add Aircraft */}
            {showAddModal && (
              <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
                <div className="glass-panel p-6 rounded-2xl border border-cyan-500/40 max-w-lg w-full space-y-4 max-h-[90vh] overflow-y-auto">
                  <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <Plus size={18} className="text-cyan-400" /> Aggiungi Aeromobile all Hangar
                    </h3>
                    <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-white">✕</button>
                  </div>

                  <form onSubmit={handleAddAircraft} noValidate className="space-y-3 font-mono text-xs">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-slate-400 block mb-1">Marche (Tail Number)*</label>
                        <input
                          type="text"
                          placeholder="es. I-ALPA, N516SF"
                          required
                          value={newAircraft.tail_number}
                          onChange={(e) => setNewAircraft({...newAircraft, tail_number: e.target.value.toUpperCase()})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                        />
                      </div>
                      <div>
                        <label className="text-slate-400 block mb-1">Tipo ICAO (es. SF50, C172, B738)</label>
                        <input
                          type="text"
                          placeholder="es. SF50"
                          value={newAircraft.aircraft_type}
                          onChange={(e) => setNewAircraft({...newAircraft, aircraft_type: e.target.value.toUpperCase()})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="text-slate-400 block mb-1">Nome Modello & Versione*</label>
                      <input
                        type="text"
                        placeholder="es. Cirrus Vision SF50 G2"
                        required
                        value={newAircraft.name}
                        onChange={(e) => setNewAircraft({...newAircraft, name: e.target.value})}
                        className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-slate-400 block mb-1">Categoria Operativa</label>
                        <select
                          value={newAircraft.category}
                          onChange={(e) => setNewAircraft({...newAircraft, category: e.target.value})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                        >
                          <option value="GA">GA (General Aviation)</option>
                          <option value="BIZJET">BIZJET (Business Jet)</option>
                          <option value="AIRLINER">AIRLINER (Linea Commerciale)</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-slate-400 block mb-1">Aeroporto ICAO Iniziale</label>
                        <input
                          type="text"
                          placeholder="es. LIRN"
                          required
                          value={newAircraft.current_icao}
                          onChange={(e) => setNewAircraft({...newAircraft, current_icao: e.target.value.toUpperCase()})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-3">
                      <div>
                        <label className="text-slate-400 block mb-1">Anno Fabbricazione</label>
                        <input
                          type="number"
                          value={newAircraft.year_manufactured}
                          onChange={(e) => setNewAircraft({...newAircraft, year_manufactured: e.target.value})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500 font-mono text-xs"
                        />
                      </div>
                      <div>
                        <label className="text-slate-400 block mb-1">Data di Acquisto</label>
                        <input
                          type="date"
                          value={newAircraft.purchase_date}
                          onChange={(e) => setNewAircraft({...newAircraft, purchase_date: e.target.value})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500 font-mono text-xs"
                        />
                      </div>
                      <div>
                        <label className="text-slate-400 block mb-1">Prezzo Acquisto (€)</label>
                        <input
                          type="number"
                          value={newAircraft.purchase_price_eur}
                          onChange={(e) => setNewAircraft({...newAircraft, purchase_price_eur: e.target.value})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500 font-mono text-xs"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="text-slate-400 block mb-1">Motorizzazione</label>
                      <input
                        type="text"
                        placeholder="es. 1x Williams International FJ33-5A Turbofan"
                        value={newAircraft.engine_type}
                        onChange={(e) => setNewAircraft({...newAircraft, engine_type: e.target.value})}
                        className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    <div>
                      <label className="text-slate-400 block mb-1">Suite Avionica</label>
                      <input
                        type="text"
                        placeholder="es. Cirrus Perspective+ Garmin G3000"
                        value={newAircraft.avionics_system}
                        onChange={(e) => setNewAircraft({...newAircraft, avionics_system: e.target.value})}
                        className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    <div>
                      <label className="text-slate-400 block mb-1">Foto Velivolo (Carica File dal PC o incolla URL)</label>
                      
                      <div className="flex flex-wrap gap-2 items-center mb-2">
                        <label className="bg-cyan-600 hover:bg-cyan-500 text-white px-3 py-1.5 rounded-lg text-xs font-mono font-semibold flex items-center gap-1.5 cursor-pointer shadow transition">
                          <Camera size={14} /> Scegli File Immagine dal PC
                          <input 
                            type="file" 
                            accept="image/*" 
                            className="hidden" 
                            onChange={(e) => {
                              const file = e.target.files?.[0];
                              if (file) {
                                const reader = new FileReader();
                                reader.onload = (ev) => {
                                  setNewAircraft(prev => ({ ...prev, image_url: ev.target.result }));
                                };
                                reader.readAsDataURL(file);
                              }
                            }} 
                          />
                        </label>
                        <span className="text-slate-500 text-[11px]">oppure inserisci un URL:</span>
                      </div>

                      <input
                        type="text"
                        placeholder="https://... o link foto"
                        value={newAircraft.image_url}
                        onChange={(e) => setNewAircraft({...newAircraft, image_url: e.target.value})}
                        className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500 font-mono text-xs"
                      />
                      {newAircraft.image_url && (
                        <div className="mt-2 rounded overflow-hidden max-h-36 border border-slate-700 bg-slate-950 flex items-center justify-center">
                          <img src={newAircraft.image_url} alt="Anteprima" className="w-full h-36 object-cover" />
                        </div>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-slate-400 block mb-1">Capacità Fuel (kg)</label>
                        <input
                          type="number"
                          value={newAircraft.fuel_capacity_kg}
                          onChange={(e) => setNewAircraft({...newAircraft, fuel_capacity_kg: e.target.value})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                        />
                      </div>
                      <div>
                        <label className="text-slate-400 block mb-1">Fuel Iniziale (kg)</label>
                        <input
                          type="number"
                          value={newAircraft.fuel_quantity_kg}
                          onChange={(e) => setNewAircraft({...newAircraft, fuel_quantity_kg: e.target.value})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                        />
                      </div>
                    </div>

                    <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                      <button
                        type="button"
                        onClick={() => setShowAddModal(false)}
                        className="px-4 py-2 rounded bg-slate-800 text-slate-300 hover:bg-slate-700"
                      >
                        Annulla
                      </button>
                      <button
                        type="submit"
                        disabled={loading}
                        className="px-4 py-2 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold"
                      >
                        Salva nell Hangar
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </div>
          );
        })()}

        {/* TAB 3: MERCATO & NOLEGGIO (FLOTTA SINCRONIZZATA DA X-PLANE 12) */}
        {activeTab === 'rental' && (() => {
          const categoriesMeta = [
            { id: 'GA', label: 'GA — General Aviation & Turboprop', color: 'text-emerald-300 border-emerald-500/40 bg-emerald-500/10' },
            { id: 'BIZJET', label: 'BIZJET — Business & Executive Jet', color: 'text-amber-300 border-amber-500/40 bg-amber-500/10' },
            { id: 'AIRLINER', label: 'AIRLINER — Aerei di Linea Commerciali', color: 'text-cyan-300 border-cyan-500/40 bg-cyan-500/10' }
          ];

          const catFiltered = marketCategoryFilter === 'ALL'
            ? marketAircraft
            : marketAircraft.filter(m => m.category === marketCategoryFilter);

          const availableManufs = [...new Set(catFiltered.map(m => m.manufacturer))].sort();
          const finalFiltered = marketManufFilter === 'ALL'
            ? catFiltered
            : catFiltered.filter(m => m.manufacturer === marketManufFilter);

          const activeCatOrder = marketCategoryFilter === 'ALL' ? ['GA', 'BIZJET', 'AIRLINER'] : [marketCategoryFilter];

          return (
            <div className="space-y-6">
              {/* Top Header & Sync Button */}
              <div className="glass-panel p-5 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <Key size={20} className="text-cyan-400" /> Mercato & Noleggio (Catalogo X-Plane 12)
                  </h2>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">
                    Tutti gli aeromobili presenti nel tuo X-Plane 12, suddivisi per Macro Categoria, Costruttore e Modello.
                  </p>
                </div>

                <button
                  onClick={handleSyncXP12}
                  disabled={loading}
                  className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-500 text-white font-mono font-bold text-xs px-4 py-2.5 rounded-lg shadow transition disabled:opacity-50"
                >
                  <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Ri-sincronizza Aerei da X-Plane 12
                </button>
              </div>

              {/* Currently Rented Aircraft in Fleet */}
              {fleet.filter(ac => ac.ownership === 'LEASED').length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-sm font-bold text-amber-300 font-mono uppercase">I Tuoi Aerei a Noleggio Attivi</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {fleet.filter(ac => ac.ownership === 'LEASED').map((ac) => {
                      const isSelected = selectedAircraft?.id === ac.id;
                      return (
                        <div key={ac.id} className={`glass-panel p-4 rounded-xl border ${isSelected ? 'border-amber-500 ring-1 ring-amber-500' : 'border-amber-900/40 bg-amber-950/10'}`}>
                          <div className="flex justify-between items-start gap-3">
                            <div className="flex items-center gap-3">
                              {ac.image_url && (
                                <img src={ac.image_url} alt={ac.name} className="w-16 h-12 object-cover rounded border border-slate-700 bg-slate-900" />
                              )}
                              <div>
                                <div className="flex items-center gap-2">
                                  <span className="text-base font-black font-mono text-amber-400">{ac.tail_number}</span>
                                  <span className="text-xs px-2 py-0.5 rounded font-mono bg-amber-500/20 text-amber-300">
                                    {formatEuro(ac.hourly_lease_rate)} / ora
                                  </span>
                                </div>
                                <h4 className="text-sm font-bold text-white mt-0.5">{ac.name}</h4>
                                <p className="text-xs text-slate-400 font-mono">Stazionato a: <span className="text-white font-bold">{ac.current_icao}</span></p>
                              </div>
                            </div>
                            
                            <div className="flex gap-2">
                              <button
                                onClick={() => setSelectedAircraft(ac)}
                                className={`px-3 py-1.5 rounded text-xs font-mono font-bold ${isSelected ? 'bg-amber-400 text-black' : 'bg-slate-800 text-slate-200'}`}
                              >
                                {isSelected ? 'IN USO' : 'SELEZIONA'}
                              </button>
                              <button
                                onClick={() => handleDeleteAircraft(ac)}
                                className="px-2.5 py-1.5 rounded bg-rose-950/60 hover:bg-rose-900 text-rose-300 border border-rose-800 text-xs font-mono"
                                title="Restituisci noleggio"
                              >
                                Riconsegna
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Macro Category Filter Tabs */}
              <div className="space-y-3 bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
                  <span className="text-slate-400 font-semibold mr-1">Macro Categoria:</span>
                  <button
                    onClick={() => { setMarketCategoryFilter('ALL'); setMarketManufFilter('ALL'); }}
                    className={`px-3 py-1.5 rounded-lg font-bold transition ${
                      marketCategoryFilter === 'ALL'
                        ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50'
                        : 'bg-slate-800/80 text-slate-400 hover:text-white'
                    }`}
                  >
                    TUTTE ({marketAircraft.length})
                  </button>
                  {categoriesMeta.map((c) => {
                    const cnt = marketAircraft.filter(m => m.category === c.id).length;
                    const active = marketCategoryFilter === c.id;
                    return (
                      <button
                        key={c.id}
                        onClick={() => { setMarketCategoryFilter(c.id); setMarketManufFilter('ALL'); }}
                        className={`px-3 py-1.5 rounded-lg font-bold transition ${
                          active
                            ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50'
                            : 'bg-slate-800/80 text-slate-400 hover:text-white'
                        }`}
                      >
                        {c.id} ({cnt})
                      </button>
                    );
                  })}
                </div>

                {/* Manufacturer Sub-Filter */}
                {availableManufs.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 text-[11px] font-mono pt-2 border-t border-slate-800/80">
                    <span className="text-slate-400 mr-1">Costruttore (Manufacturer):</span>
                    <button
                      onClick={() => setMarketManufFilter('ALL')}
                      className={`px-2.5 py-1 rounded transition ${
                        marketManufFilter === 'ALL' ? 'bg-slate-700 text-white font-bold' : 'bg-slate-900 text-slate-400 hover:text-white'
                      }`}
                    >
                      Tutti
                    </button>
                    {availableManufs.map((man) => (
                      <button
                        key={man}
                        onClick={() => setMarketManufFilter(man)}
                        className={`px-2.5 py-1 rounded transition ${
                          marketManufFilter === man ? 'bg-cyan-600/30 text-cyan-300 border border-cyan-500/40 font-bold' : 'bg-slate-900 text-slate-400 hover:text-white'
                        }`}
                      >
                        {man}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Hierarchical Display: Macro Category -> Manufacturer -> Models */}
              {finalFiltered.length === 0 ? (
                <div className="glass-panel p-10 rounded-xl border border-slate-800 text-center space-y-3">
                  <Plane size={36} className="mx-auto text-slate-600" />
                  <div className="text-slate-300 font-bold">Nessun aeromobile nel Mercato per i filtri selezionati.</div>
                  <p className="text-xs text-slate-400 font-mono">
                    Premi "Ri-sincronizza Aerei da X-Plane 12" in alto per leggere la tua cartella Aircraft.
                  </p>
                </div>
              ) : (
                <div className="space-y-8">
                  {activeCatOrder.map((catCode) => {
                    const catMeta = categoriesMeta.find(c => c.id === catCode);
                    const itemsInCat = finalFiltered.filter(m => m.category === catCode);
                    if (itemsInCat.length === 0) return null;

                    const manufsInCat = [...new Set(itemsInCat.map(m => m.manufacturer))].sort();

                    return (
                      <div key={catCode} className="space-y-5">
                        {/* Macro Category Banner */}
                        <div className={`px-4 py-2.5 rounded-xl border flex items-center justify-between ${catMeta.color}`}>
                          <span className="font-black font-mono text-sm tracking-wide">{catMeta.label}</span>
                          <span className="text-xs font-mono font-bold">{itemsInCat.length} modelli disponibili</span>
                        </div>

                        {/* Grouped by Manufacturer */}
                        {manufsInCat.map((manuf) => {
                          const models = itemsInCat.filter(m => m.manufacturer === manuf);
                          return (
                            <div key={manuf} className="space-y-3 pl-1">
                              <div className="flex items-center gap-2 border-b border-slate-800 pb-1.5">
                                <span className="text-sm font-bold text-white font-mono uppercase tracking-wider">{manuf}</span>
                                <span className="text-[11px] font-mono text-slate-500">({models.length})</span>
                              </div>

                              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                                {models.map((item) => (
                                  <div key={item.id} className="glass-panel rounded-xl border border-slate-800 hover:border-cyan-500/50 transition overflow-hidden flex flex-col justify-between">
                                    <div>
                                      {/* XP12 Aircraft Preview Image */}
                                      <div className="h-36 bg-slate-950 relative border-b border-slate-800 flex items-center justify-center overflow-hidden">
                                        {item.image_url ? (
                                          <img src={item.image_url} alt={item.name} className="w-full h-full object-contain p-2 bg-gradient-to-b from-slate-900 to-slate-950" />
                                        ) : (
                                          <Plane size={42} className="text-slate-700" />
                                        )}
                                        <span className="absolute top-2 left-2 px-2 py-0.5 rounded bg-slate-900/90 border border-slate-700 text-[11px] font-mono font-bold text-cyan-300">
                                          {item.aircraft_type}
                                        </span>
                                        <span className="absolute top-2 right-2 px-2 py-0.5 rounded bg-slate-900/90 border border-slate-700 text-[10px] font-mono text-slate-300">
                                          Anno {item.year_manufactured} • {item.airframe_hours}h
                                        </span>
                                        <span className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-emerald-950/90 border border-emerald-500/40 text-[10px] font-mono font-bold text-emerald-300">
                                          Stato: {item.condition_pct}%
                                        </span>
                                      </div>

                                      <div className="p-4 space-y-2.5">
                                        <div>
                                          <h4 className="text-sm font-bold text-white leading-snug">{item.name}</h4>
                                          {item.studio && (
                                            <div className="text-[10px] font-mono text-slate-500">Studio: {item.studio}</div>
                                          )}
                                        </div>

                                        <p className="text-[11px] text-slate-400 leading-relaxed line-clamp-2">{item.description}</p>

                                        <div className="grid grid-cols-2 gap-1.5 text-[11px] font-mono text-slate-400 bg-slate-900/60 p-2 rounded border border-slate-800/80">
                                          <div>Crociera: <span className="text-white font-semibold">{item.cruise_speed_kts} kts</span></div>
                                          <div>Serbatoio: <span className="text-purple-300 font-semibold">{item.fuel_capacity_kg} kg</span></div>
                                          <div className="col-span-2 truncate" title={item.engine_type}>
                                            Motore: <span className="text-slate-200">{item.engine_type}</span>
                                          </div>
                                        </div>

                                        {/* Transparent Pricing Box */}
                                        <div className="bg-slate-950/80 p-2.5 rounded-lg border border-slate-800 space-y-1 font-mono text-xs">
                                          <div className="flex justify-between items-center">
                                            <span className="text-slate-400">Acquisto Cash:</span>
                                            <span className="font-bold text-white">{formatEuro(item.purchase_price_eur)}</span>
                                          </div>
                                          <div className="flex justify-between items-center">
                                            <span className="text-slate-400">Anticipo Mutuo (10%):</span>
                                            <span className="text-cyan-300 font-semibold">{formatEuro(item.financing_options?.bank_loan?.down_payment_eur)}</span>
                                          </div>
                                          <div className="flex justify-between items-center border-t border-slate-800 pt-1">
                                            <span className="text-slate-400">Noleggio Orario:</span>
                                            <span className="font-bold text-emerald-400">{formatEuro(item.hourly_lease_rate_eur)} / ora</span>
                                          </div>
                                        </div>
                                      </div>
                                    </div>

                                    <div className="px-4 pb-4">
                                      <button
                                        onClick={() => {
                                          setSelectedMarketItem(item);
                                          setAcquireTail(item.default_tail || `I-${item.aircraft_type.slice(0, 3)}`);
                                          setAcquireIcao(systemStatus?.company?.home_base_icao || 'LIRN');
                                          setAcquireMode((systemStatus?.company?.cash_balance || 0) >= item.purchase_price_eur ? 'OWNED_CASH' : 'RENTAL_HOURLY');
                                          setShowAcquireModal(true);
                                        }}
                                        className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-mono font-bold text-xs py-2.5 rounded-lg shadow transition flex items-center justify-center gap-2"
                                      >
                                        <Key size={14} /> Acquista / Finanzia / Noleggia
                                      </button>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* ACQUISITION MODAL (4 REAL-WORLD MODES + CONTINENTAL DEALERSHIP DELIVERY) */}
              {showAcquireModal && selectedMarketItem && (() => {
                const cash = systemStatus?.company?.cash_balance || 0;
                const opts = selectedMarketItem.financing_options;
                const delInfo = selectedMarketItem.delivery_info || {
                  continent_label: 'Europa',
                  home_base_icao: systemStatus?.company?.home_base_icao || 'LIRN',
                  dealership_icao: 'LFPB',
                  dealership_name: 'Sede Regionale',
                  distance_nm: 0,
                  ferry_delivery_fee_eur: 0
                };

                const modes = [
                  {
                    id: 'RENTAL_HOURLY',
                    title: 'Noleggio Orario (Dry Lease)',
                    badge: 'Zero Anticipo',
                    down: 0,
                    monthly: 0,
                    sub: `Tariffa volo: ${formatEuro(selectedMarketItem.hourly_lease_rate_eur)} / ora • Riconsegna libera quando vuoi`
                  },
                  {
                    id: 'OWNED_CASH',
                    title: 'Acquisto Immediato (Cash)',
                    badge: '100% Proprietà',
                    down: opts.cash.down_payment_eur,
                    monthly: 0,
                    sub: 'Proprietà immediata e totale • Nessuna rata mensile'
                  },
                  {
                    id: 'FINANCIAL_LEASE',
                    title: 'Leasing Finanziario (12 Mesi)',
                    badge: 'Anticipo 20%',
                    down: opts.financial_lease.down_payment_eur,
                    monthly: opts.financial_lease.monthly_eur,
                    sub: `12 rate mensili da ${formatEuro(opts.financial_lease.monthly_eur)}/mese • Riscatto automatico`
                  },
                  {
                    id: 'FINANCED_LOAN',
                    title: 'Mutuo Bancario (24 Mesi)',
                    badge: 'Anticipo 10%',
                    down: opts.bank_loan.down_payment_eur,
                    monthly: opts.bank_loan.monthly_eur,
                    sub: `24 rate mensili da ${formatEuro(opts.bank_loan.monthly_eur)}/mese • Rate leggere per liquidità`
                  }
                ];
                const currentModeObj = modes.find(m => m.id === acquireMode) || modes[0];
                const isPurchase = acquireMode !== 'RENTAL_HOURLY';
                const ferryCost = (isPurchase && deliveryOption === 'DELIVER_HOME') ? (delInfo.ferry_delivery_fee_eur || 0) : 0;
                const totalDueToday = currentModeObj.down + ferryCost;
                const hasEnoughCash = cash >= totalDueToday;

                return (
                  <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
                    <div className="glass-panel p-6 rounded-2xl border border-cyan-500/40 max-w-2xl w-full space-y-5 my-8 max-h-[92vh] overflow-y-auto">
                      <div className="flex justify-between items-start border-b border-slate-800 pb-3">
                        <div className="flex items-center gap-3">
                          {selectedMarketItem.image_url && (
                            <img src={selectedMarketItem.image_url} alt={selectedMarketItem.name} className="w-16 h-12 object-contain rounded bg-slate-900 border border-slate-700" />
                          )}
                          <div>
                            <h3 className="text-base font-bold text-white">{selectedMarketItem.name}</h3>
                            <p className="text-xs font-mono text-slate-400">
                              {selectedMarketItem.manufacturer} • {selectedMarketItem.aircraft_type} • Prezzo listino: {formatEuro(selectedMarketItem.purchase_price_eur)}
                            </p>
                          </div>
                        </div>
                        <button onClick={() => setShowAcquireModal(false)} className="text-slate-400 hover:text-white text-lg">✕</button>
                      </div>

                      {/* Tail & Rental Base */}
                      <div className={`grid grid-cols-1 ${!isPurchase ? 'sm:grid-cols-2' : ''} gap-4 font-mono text-xs`}>
                        <div>
                          <label className="text-slate-400 block mb-1">Marche Immatricolazione (Tail Number)</label>
                          <input
                            type="text"
                            value={acquireTail}
                            onChange={(e) => setAcquireTail(e.target.value.toUpperCase())}
                            className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-cyan-300 font-bold focus:outline-none focus:border-cyan-500"
                          />
                        </div>
                        {!isPurchase && (
                          <div>
                            <label className="text-slate-400 block mb-1">Aeroporto di Ritiro Noleggio (ICAO)</label>
                            <input
                              type="text"
                              maxLength={4}
                              value={acquireIcao}
                              onChange={(e) => setAcquireIcao(e.target.value.toUpperCase())}
                              className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white font-bold focus:outline-none focus:border-cyan-500"
                            />
                          </div>
                        )}
                      </div>

                      {/* 4 Acquisition Mode Selector Cards */}
                      <div className="space-y-2">
                        <label className="text-xs font-mono text-slate-300 font-bold block">Scegli la Formula di Acquisizione:</label>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
                          {modes.map((m) => {
                            const selected = acquireMode === m.id;
                            const affordable = cash >= m.down;
                            return (
                              <div
                                key={m.id}
                                onClick={() => setAcquireMode(m.id)}
                                className={`p-3 rounded-xl border cursor-pointer transition ${
                                  selected
                                    ? 'bg-cyan-950/40 border-cyan-400 ring-1 ring-cyan-400'
                                    : 'bg-slate-900/70 border-slate-800 hover:border-slate-600'
                                } ${!affordable ? 'opacity-70' : ''}`}
                              >
                                <div className="flex justify-between items-start gap-2">
                                  <span className={`font-bold ${selected ? 'text-cyan-300' : 'text-white'}`}>{m.title}</span>
                                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 whitespace-nowrap">{m.badge}</span>
                                </div>
                                <div className="mt-1.5 flex justify-between items-baseline">
                                  <span className="text-slate-400">Quota Aereo:</span>
                                  <span className={`font-bold text-sm ${affordable ? 'text-emerald-400' : 'text-rose-400'}`}>
                                    {formatEuro(m.down)}
                                  </span>
                                </div>
                                <p className="text-[10px] text-slate-400 font-sans mt-1 leading-snug">{m.sub}</p>
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* Delivery Options (For Purchases Only!) */}
                      {isPurchase && (
                        <div className="space-y-2 pt-1">
                          <div className="flex items-center justify-between text-xs font-mono">
                            <label className="text-slate-300 font-bold">
                              Logistica Consegna Velivolo (Area {delInfo.continent_label})
                            </label>
                            <span className="text-[11px] text-cyan-400">
                              Hub Costruttore: <strong>{delInfo.dealership_icao}</strong>
                            </span>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
                            {/* Option 1: Pickup at Continental Dealership */}
                            <div
                              onClick={() => setDeliveryOption('PICKUP_DEALERSHIP')}
                              className={`p-3 rounded-xl border cursor-pointer transition ${
                                deliveryOption === 'PICKUP_DEALERSHIP'
                                  ? 'bg-emerald-950/35 border-emerald-400 ring-1 ring-emerald-400'
                                  : 'bg-slate-900/70 border-slate-800 hover:border-slate-600'
                              }`}
                            >
                              <div className="flex justify-between items-start gap-2">
                                <span className={`font-bold ${deliveryOption === 'PICKUP_DEALERSHIP' ? 'text-emerald-300' : 'text-white'}`}>
                                  ✈️ Ritiro in Sede di Vendita
                                </span>
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold">
                                  GRATIS
                                </span>
                              </div>
                              <div className="mt-1.5 text-[11px] text-cyan-300 font-bold">
                                Aeroporto: {delInfo.dealership_icao}
                              </div>
                              <div className="text-[10px] text-slate-300 font-sans truncate" title={delInfo.dealership_name}>
                                {delInfo.dealership_name}
                              </div>
                              <p className="text-[10px] text-slate-400 font-sans mt-1.5 leading-snug">
                                Volerai tu stesso il trasferimento (Ferry Flight) di {delInfo.distance_nm} NM verso la tua base {delInfo.home_base_icao}!
                              </p>
                            </div>

                            {/* Option 2: Ferry Delivery to Home Base */}
                            <div
                              onClick={() => setDeliveryOption('DELIVER_HOME')}
                              className={`p-3 rounded-xl border cursor-pointer transition ${
                                deliveryOption === 'DELIVER_HOME'
                                  ? 'bg-amber-950/35 border-amber-400 ring-1 ring-amber-400'
                                  : 'bg-slate-900/70 border-slate-800 hover:border-slate-600'
                              }`}
                            >
                              <div className="flex justify-between items-start gap-2">
                                <span className={`font-bold ${deliveryOption === 'DELIVER_HOME' ? 'text-amber-300' : 'text-white'}`}>
                                  🚚 Consegna alla Base ({delInfo.home_base_icao})
                                </span>
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold whitespace-nowrap">
                                  +{formatEuro(delInfo.ferry_delivery_fee_eur)}
                                </span>
                              </div>
                              <div className="mt-1.5 text-[11px] text-amber-200 font-bold">
                                Tratta Ferry: {delInfo.dealership_icao} ➔ {delInfo.home_base_icao} ({delInfo.distance_nm} NM)
                              </div>
                              <p className="text-[10px] text-slate-400 font-sans mt-1.5 leading-snug">
                                Un equipaggio Ferry certificato consegnerà il velivolo pronto al volo direttamente nel tuo hangar a {delInfo.home_base_icao}.
                              </p>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Financial Summary Banner */}
                      <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 font-mono text-xs space-y-1">
                        <div className="flex justify-between">
                          <span className="text-slate-400">Capitale Attuale Disponibile:</span>
                          <span className="font-bold text-white">{formatEuro(cash)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Quota Acquisizione Velivolo:</span>
                          <span className="text-slate-200">-{formatEuro(currentModeObj.down)}</span>
                        </div>
                        {ferryCost > 0 && (
                          <div className="flex justify-between">
                            <span className="text-slate-400">Consegna Ferry a Domicilio ({delInfo.distance_nm} NM):</span>
                            <span className="text-amber-300">-{formatEuro(ferryCost)}</span>
                          </div>
                        )}
                        <div className="flex justify-between border-t border-slate-800 pt-1">
                          <span className="text-slate-300 font-bold">Totale Esborso Oggi:</span>
                          <span className={`font-bold ${hasEnoughCash ? 'text-amber-300' : 'text-rose-400'}`}>
                            -{formatEuro(totalDueToday)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Saldo Cassa Dopo Operazione:</span>
                          <span className={`font-bold ${hasEnoughCash ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {formatEuro(cash - totalDueToday)}
                          </span>
                        </div>
                        {!hasEnoughCash && (
                          <div className="text-[11px] text-rose-400 font-sans pt-1">
                            ⚠️ Fondi liquidi insufficienti per questa operazione. Valuta il ritiro in sede (risparmi {formatEuro(delInfo.ferry_delivery_fee_eur)}), il Mutuo o il Noleggio Orario.
                          </div>
                        )}
                      </div>

                      <div className="flex justify-end gap-3 pt-2">
                        <button
                          type="button"
                          onClick={() => setShowAcquireModal(false)}
                          className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 text-xs font-mono"
                        >
                          Annulla
                        </button>
                        <button
                          type="button"
                          onClick={handleAcquireAircraft}
                          disabled={loading || !hasEnoughCash}
                          className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs font-mono disabled:opacity-40 transition"
                        >
                          Conferma Operazione
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>
          );
        })()}

        {/* TAB 4: JOBS & CONTRACTS */}
        {activeTab === 'jobs' && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white">Bacheca Incarichi Operativi</h2>
                <p className="text-xs text-slate-400 font-mono">
                  Contratti commerciali disponibili da <span className="text-cyan-300 font-bold">{selectedAircraft?.current_icao}</span> per {selectedAircraft?.tail_number}
                </p>
              </div>

              <button
                onClick={handleGenerateJobs}
                disabled={loading}
                className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold px-4 py-2 rounded-lg text-sm transition"
              >
                <RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Genera Nuovi Incarichi
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {jobs.map((job) => (
                <div key={job.id} className="glass-panel p-5 rounded-xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between text-xs font-mono mb-2">
                      <span className={`px-2 py-0.5 rounded font-bold ${
                        job.job_type === 'VIP' ? 'bg-amber-500/20 text-amber-300' :
                        job.job_type === 'MEDEVAC' ? 'bg-rose-500/20 text-rose-300' :
                        job.job_type === 'CARGO' ? 'bg-blue-500/20 text-blue-300' :
                        'bg-purple-500/20 text-purple-300'
                      }`}>
                        {job.job_type}
                      </span>
                      <span className="text-slate-400">{job.distance_nm} NM</span>
                    </div>

                    <h3 className="font-bold text-white text-sm">{job.title}</h3>

                    <div className="flex items-center gap-3 my-3 text-sm font-mono">
                      <div className="font-black text-cyan-400">{job.origin_icao}</div>
                      <ArrowRight size={14} className="text-slate-500" />
                      <div className="font-black text-emerald-400">{job.destination_icao}</div>
                    </div>

                    <div className="text-xs text-slate-400 font-mono space-y-1">
                      {job.pax_count > 0 && <div>Passeggeri: <span className="text-white">{job.pax_count} pax</span></div>}
                      {job.cargo_kg > 0 && <div>Carico Merci: <span className="text-white">{job.cargo_kg} kg</span></div>}
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                    <div>
                      <div className="text-[10px] font-mono text-slate-400 uppercase">Ricavo Netto</div>
                      <div className="text-base font-bold font-mono text-emerald-400">{formatEuro(job.reward_usd)}</div>
                    </div>

                    <button
                      onClick={() => handleAcceptJob(job.id)}
                      className="bg-cyan-500 hover:bg-cyan-400 text-black font-semibold font-mono text-xs px-3 py-1.5 rounded transition"
                    >
                      Accetta Incarico
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {jobs.length === 0 && (
              <div className="text-center py-12 glass-panel rounded-xl border border-dashed border-slate-800">
                <p className="text-slate-400 font-mono text-sm">Nessun incarico attivo per questo aeroporto.</p>
                <button
                  onClick={handleGenerateJobs}
                  className="mt-3 text-cyan-400 hover:underline font-mono text-xs"
                >
                  Clicca qui per generare 4-5 proposte di volo da {selectedAircraft?.current_icao}
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 5: PIANO DI VOLO & DISPATCH (SIMBRIEF + MANUALE + COMMERCIALE/PERSONALE) */}
        {activeTab === 'simbrief' && (
          <div className="space-y-6">
            {/* Header & Mode Switcher */}
            <div className="glass-panel p-5 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <Radio size={20} className="text-cyan-400" /> Piano di Volo & Dispatch
                </h2>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  Importa il piano operativo da SimBrief oppure compila manualmente la rotta e scegli se operare a scopo commerciale o personale/ferry.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                {/* Aircraft Selector */}
                <select
                  value={selectedAircraft?.id || ''}
                  onChange={(e) => {
                    const ac = fleet.find(a => a.id === parseInt(e.target.value));
                    if (ac) setSelectedAircraft(ac);
                  }}
                  className="bg-slate-900 border border-cyan-500/40 text-cyan-300 font-mono font-bold text-xs px-3 py-2 rounded-lg focus:outline-none"
                >
                  {fleet.map((ac) => (
                    <option key={ac.id} value={ac.id}>
                      {ac.tail_number} — {ac.name} @ {ac.current_icao}
                    </option>
                  ))}
                  {fleet.length === 0 && <option value="">Nessun aereo in flotta</option>}
                </select>

                {/* Switcher */}
                <div className="flex bg-slate-900 border border-slate-800 p-1 rounded-lg text-xs font-mono">
                  <button
                    onClick={() => setDispatchMode('simbrief')}
                    className={`px-3 py-1.5 rounded-md font-bold transition ${
                      dispatchMode === 'simbrief' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    📡 Da SimBrief
                  </button>
                  <button
                    onClick={() => setDispatchMode('manual')}
                    className={`px-3 py-1.5 rounded-md font-bold transition ${
                      dispatchMode === 'manual' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    ✍️ Piano Manuale
                  </button>
                </div>
              </div>
            </div>

            {/* Economic Regime Selector (Default = Commercial with Revenue) */}
            <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-2">
              <div className="text-xs font-mono text-slate-300 font-bold">Regime Economico del Volo:</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
                <div
                  onClick={() => {
                    setPlanIsCommercial(true);
                    if (dispatchMode === 'manual') fetchManualEstimate(manualPlan.origin_icao, manualPlan.destination_icao, manualPlan.pax_count, manualPlan.cargo_kg, true);
                  }}
                  className={`p-3 rounded-xl border cursor-pointer transition ${
                    planIsCommercial
                      ? 'bg-emerald-950/35 border-emerald-400 ring-1 ring-emerald-400'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-600'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className={`font-bold ${planIsCommercial ? 'text-emerald-300' : 'text-white'}`}>
                      💰 Volo Commerciale ad Incasso (Default)
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300">RICAVI ATTIVI</span>
                  </div>
                  <p className="text-[11px] text-slate-400 font-sans mt-1">
                    Genera ricavi automatici in base a distanza, passeggeri e carico trasportato al netto di carburante e tasse.
                  </p>
                </div>

                <div
                  onClick={() => {
                    setPlanIsCommercial(false);
                    if (dispatchMode === 'manual') fetchManualEstimate(manualPlan.origin_icao, manualPlan.destination_icao, manualPlan.pax_count, manualPlan.cargo_kg, false);
                  }}
                  className={`p-3 rounded-xl border cursor-pointer transition ${
                    !planIsCommercial
                      ? 'bg-amber-950/30 border-amber-400 ring-1 ring-amber-400'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-600'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className={`font-bold ${!planIsCommercial ? 'text-amber-300' : 'text-white'}`}>
                      ✈️ Volo Personale / Trasferimento Ferry
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">€ 0 RICAVI</span>
                  </div>
                  <p className="text-[11px] text-slate-400 font-sans mt-1">
                    Nessun compenso (€ 0,00). Vengono registrati solo i costi reali (carburante, tasse, usura): perfetto per voli privati o ritiro aereo in sede!
                  </p>
                </div>
              </div>

              {/* Crew Cost Toggle Option */}
              {(() => {
                const selectedCat = selectedAircraft?.category || 'GA';
                const hasSalaried = crewRoster?.hired?.some(c => c.category === selectedCat && c.is_active);
                return (
                  <div
                    onClick={() => setPlanExcludeCrew(!planExcludeCrew)}
                    className={`mt-2 p-3 rounded-xl border cursor-pointer transition flex flex-wrap items-center justify-between gap-3 ${
                      planExcludeCrew
                        ? 'bg-amber-950/25 border-amber-500/50'
                        : 'bg-slate-900/50 border-slate-800 hover:border-slate-600'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <input
                        type="checkbox"
                        checked={planExcludeCrew}
                        onChange={(e) => setPlanExcludeCrew(e.target.checked)}
                        onClick={(e) => e.stopPropagation()}
                        className="w-4 h-4 accent-amber-500 rounded cursor-pointer"
                      />
                      <div>
                        <span className={`font-mono text-xs font-bold ${planExcludeCrew ? 'text-amber-300' : 'text-slate-200'}`}>
                          🧑‍✈️ Escludi Costo Equipaggio (Volo Solo / VFR / Pilota Proprietario)
                        </span>
                        <p className="text-[11px] text-slate-400 font-sans">
                          {planExcludeCrew
                            ? 'Attivo: nessun costo orario di piloti o assistenti di volo verrà addebitato.'
                            : hasSalaried
                              ? `Coperto da Equipaggio Fisso Assunto (${selectedCat}): € 0/ora in volo (già nello stipendio mensile).`
                              : `Freelance (${selectedCat}): verrà addebitato a ora di volo (${selectedCat === 'AIRLINER' ? '2 Piloti + 4 A/V • € 520/h' : selectedCat === 'BIZJET' ? '2 Piloti + 1 A/V • € 240/h' : '1 Pilota • € 90/h'}).`}
                        </p>
                      </div>
                    </div>
                    <span className={`font-mono text-[11px] font-bold px-2 py-0.5 rounded ${
                      planExcludeCrew ? 'bg-amber-500/20 text-amber-300' : hasSalaried ? 'bg-emerald-500/20 text-emerald-300' : 'bg-indigo-500/20 text-indigo-300'
                    }`}>
                      {planExcludeCrew ? 'EQUIPAGGIO € 0' : hasSalaried ? 'ASSUNTO FISSO (€ 0/h)' : 'FREELANCE'}
                    </span>
                  </div>
                );
              })()}

              {/* Regole IFR/VFR & Associazione Tour IVAO */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 font-mono text-xs">
                <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800 flex items-center justify-between gap-3">
                  <div>
                    <div className="font-bold text-slate-200">Regole di Volo (Eurocontrol & Handling)</div>
                    <div className="text-[11px] text-slate-400 font-sans">
                      {planFlightRules === 'IFR'
                        ? 'IFR: applica tasse di sorvolo Eurocontrol e Catering/Handling Pax.'
                        : 'VFR: esente da tasse di rotta Eurocontrol e Handling Pax.'}
                    </div>
                  </div>
                  <div className="flex bg-slate-950 border border-slate-800 p-0.5 rounded-lg shrink-0">
                    {['IFR', 'VFR'].map((r) => (
                      <button
                        key={r}
                        type="button"
                        onClick={() => setPlanFlightRules(r)}
                        className={`px-3 py-1 rounded font-bold transition ${
                          planFlightRules === r
                            ? (r === 'VFR' ? 'bg-sky-600 text-white' : 'bg-cyan-600 text-white')
                            : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        {r}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-1 min-w-[200px]">
                    <span className="text-amber-300 font-bold shrink-0">🗺️ Tour:</span>
                    <select
                      value={planTourId}
                      onChange={(e) => setPlanTourId(e.target.value)}
                      className="flex-1 bg-slate-950 border border-slate-700 text-white px-2.5 py-1.5 rounded-lg text-xs focus:outline-none focus:border-amber-400"
                    >
                      <option value="">Nessun Tour (Volo singolo)</option>
                      {toursList.map((tr) => (
                        <option key={tr.id} value={String(tr.id)}>
                          {tr.name} ({tr.legs_count} tappe)
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    type="button"
                    onClick={async () => {
                      const tName = prompt('Nome del nuovo Tour (es. IVAO World Tour 2026):');
                      if (tName) {
                        const created = await handleCreateTour(tName);
                        if (created) setPlanTourId(String(created.id));
                      }
                    }}
                    className="px-2.5 py-1.5 rounded-lg bg-amber-600/20 hover:bg-amber-600/35 text-amber-300 border border-amber-500/40 font-bold text-[11px] transition"
                  >
                    + Nuovo Tour
                  </button>
                </div>
              </div>
            </div>

            {/* MODE A: SIMBRIEF OFP */}
            {dispatchMode === 'simbrief' && (
              <div className="space-y-6">
                <div className="glass-panel p-6 rounded-xl border border-slate-800">
                  <h3 className="text-base font-bold text-white">Scarica OFP da SimBrief</h3>
                  <div className="flex flex-wrap gap-3 mt-3">
                    <input
                      type="text"
                      placeholder="Pilot ID numerico (es. 1106351) o Username SimBrief"
                      value={simbriefInput}
                      onChange={(e) => setSimbriefInput(e.target.value)}
                      className="bg-slate-900 border border-slate-700 px-4 py-2 rounded-lg text-sm font-mono text-white flex-1 min-w-[260px] focus:outline-none focus:border-cyan-500"
                    />
                    <button
                      onClick={handleFetchSimbrief}
                      disabled={loading}
                      className="bg-cyan-600 hover:bg-cyan-500 text-white font-semibold px-4 py-2 rounded-lg text-sm font-mono transition flex items-center gap-2"
                    >
                      <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Scarica Ultimo Piano
                    </button>
                  </div>
                </div>

                {simbriefOfp && (
                  <div className="glass-panel p-6 rounded-xl border border-cyan-500/40">
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                      <div className="flex items-center gap-3">
                        <span className="text-xl font-black font-mono text-cyan-400">{simbriefOfp.flight_number}</span>
                        <span className="text-xs px-2 py-0.5 rounded font-mono bg-cyan-500/20 text-cyan-300">
                          {simbriefOfp.aircraft_icao}
                        </span>
                      </div>
                      <div className="text-xs font-mono text-slate-400">Rilasciato: {simbriefOfp.created_at}</div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 my-4 font-mono text-xs">
                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                        <div className="text-slate-400">Rotta</div>
                        <div className="text-sm font-bold text-white mt-0.5">
                          {simbriefOfp.origin_icao} → {simbriefOfp.destination_icao}
                        </div>
                        <div className="text-[10px] text-slate-500">Alt: {simbriefOfp.alternate_icao || 'N/A'}</div>
                      </div>

                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                        <div className="text-slate-400">Distanza & Tempo</div>
                        <div className="text-sm font-bold text-cyan-300 mt-0.5">{simbriefOfp.distance_nm} NM</div>
                        <div className="text-[10px] text-slate-500">{simbriefOfp.est_time_enroute_min} min enroute</div>
                      </div>

                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                        <div className="text-slate-400">Block Fuel Richiesto</div>
                        <div className="text-sm font-bold text-purple-300 mt-0.5">{simbriefOfp.block_fuel_kg} kg</div>
                        <div className="text-[10px] text-slate-500">Burn: {simbriefOfp.trip_fuel_kg} kg</div>
                      </div>

                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                        <div className="text-slate-400">Incasso Previsto</div>
                        <div className={`text-sm font-bold mt-0.5 ${planIsCommercial ? 'text-emerald-400' : 'text-slate-400'}`}>
                          {planIsCommercial ? formatEuro(simbriefOfp.estimated_reward_eur || (simbriefOfp.distance_nm * 20 + simbriefOfp.pax_count * 120)) : '€ 0,00 (Personale)'}
                        </div>
                        <div className="text-[10px] text-slate-500">{simbriefOfp.pax_count} pax | {simbriefOfp.cargo_kg} kg merci</div>
                      </div>
                    </div>

                    {simbriefOfp.route && (
                      <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 font-mono text-xs mb-4">
                        <span className="text-slate-400">Routing ATC:</span> <span className="text-slate-200">{simbriefOfp.route}</span>
                      </div>
                    )}

                    <div className="flex justify-end gap-3 pt-2">
                      <button
                        onClick={handleImportSimbriefFlight}
                        disabled={loading || !selectedAircraft}
                        className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold font-mono text-sm px-5 py-2.5 rounded-lg shadow transition disabled:opacity-50"
                      >
                        <CheckCircle size={16} /> Conferma Piano SimBrief & Vai in Plancia
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* MODE B: INSERIMENTO MANUALE PIANO DI VOLO */}
            {dispatchMode === 'manual' && (
              <form onSubmit={handleCreateManualPlan} className="glass-panel p-6 rounded-xl border border-cyan-500/30 space-y-5 font-mono text-xs" noValidate>
                <div className="border-b border-slate-800 pb-3">
                  <h3 className="text-base font-bold text-white">Compilazione Manuale Piano di Volo (Senza SimBrief)</h3>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Inserisci partenza, arrivo e carico: la distanza reale e l'eventuale incasso verranno calcolati automaticamente dagli aeroporti di X-Plane 12.
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <label className="text-slate-400 block mb-1">Aeroporto Partenza (ICAO) *</label>
                    <input
                      type="text"
                      maxLength={4}
                      placeholder="es. LIRN"
                      value={manualPlan.origin_icao}
                      onChange={(e) => {
                        const val = e.target.value.toUpperCase();
                        setManualPlan({ ...manualPlan, origin_icao: val });
                        fetchManualEstimate(val, manualPlan.destination_icao, manualPlan.pax_count, manualPlan.cargo_kg, planIsCommercial);
                      }}
                      className="w-full bg-slate-900 border border-slate-700 p-2.5 rounded-lg text-cyan-300 font-bold uppercase focus:outline-none focus:border-cyan-400"
                    />
                  </div>

                  <div>
                    <label className="text-slate-400 block mb-1">Aeroporto Destinazione (ICAO) *</label>
                    <input
                      type="text"
                      maxLength={4}
                      placeholder="es. LIRF"
                      value={manualPlan.destination_icao}
                      onChange={(e) => {
                        const val = e.target.value.toUpperCase();
                        setManualPlan({ ...manualPlan, destination_icao: val });
                        fetchManualEstimate(manualPlan.origin_icao, val, manualPlan.pax_count, manualPlan.cargo_kg, planIsCommercial);
                      }}
                      className="w-full bg-slate-900 border border-slate-700 p-2.5 rounded-lg text-emerald-300 font-bold uppercase focus:outline-none focus:border-cyan-400"
                    />
                  </div>

                  <div>
                    <label className="text-slate-400 block mb-1">Alternato (Opzionale)</label>
                    <input
                      type="text"
                      maxLength={4}
                      placeholder="es. LIRA"
                      value={manualPlan.alternate_icao}
                      onChange={(e) => setManualPlan({ ...manualPlan, alternate_icao: e.target.value.toUpperCase() })}
                      className="w-full bg-slate-900 border border-slate-700 p-2.5 rounded-lg text-white uppercase focus:outline-none focus:border-cyan-400"
                    />
                  </div>

                  <div>
                    <label className="text-slate-400 block mb-1">Callsign / N. Volo (Opzionale)</label>
                    <input
                      type="text"
                      placeholder="es. SO104"
                      value={manualPlan.flight_number}
                      onChange={(e) => setManualPlan({ ...manualPlan, flight_number: e.target.value.toUpperCase() })}
                      className="w-full bg-slate-900 border border-slate-700 p-2.5 rounded-lg text-white uppercase focus:outline-none focus:border-cyan-400"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="text-slate-400 block mb-1">
                      Distanza NM {manualEstimate?.distance_nm ? `(Auto: ${manualEstimate.distance_nm} NM)` : '(Auto se vuoto)'}
                    </label>
                    <input
                      type="number"
                      placeholder={manualEstimate?.distance_nm ? String(manualEstimate.distance_nm) : 'Calcolo automatico'}
                      value={manualPlan.distance_nm}
                      onChange={(e) => setManualPlan({ ...manualPlan, distance_nm: e.target.value })}
                      className="w-full bg-slate-900 border border-slate-700 p-2.5 rounded-lg text-white focus:outline-none focus:border-cyan-400"
                    />
                  </div>

                  <div>
                    <label className="text-slate-400 block mb-1">Passeggeri a Bordo (Pax)</label>
                    <input
                      type="number"
                      min="0"
                      value={manualPlan.pax_count}
                      onChange={(e) => {
                        const v = e.target.value;
                        setManualPlan({ ...manualPlan, pax_count: v });
                        fetchManualEstimate(manualPlan.origin_icao, manualPlan.destination_icao, v, manualPlan.cargo_kg, planIsCommercial);
                      }}
                      className="w-full bg-slate-900 border border-slate-700 p-2.5 rounded-lg text-white focus:outline-none focus:border-cyan-400"
                    />
                  </div>

                  <div>
                    <label className="text-slate-400 block mb-1">Cargo / Bagagli (kg)</label>
                    <input
                      type="number"
                      min="0"
                      value={manualPlan.cargo_kg}
                      onChange={(e) => {
                        const v = e.target.value;
                        setManualPlan({ ...manualPlan, cargo_kg: v });
                        fetchManualEstimate(manualPlan.origin_icao, manualPlan.destination_icao, manualPlan.pax_count, v, planIsCommercial);
                      }}
                      className="w-full bg-slate-900 border border-slate-700 p-2.5 rounded-lg text-white focus:outline-none focus:border-cyan-400"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-slate-400 block mb-1">Rotta / Note (Opzionale)</label>
                  <input
                    type="text"
                    placeholder="es. VFR diretto / DCT TEA / Piani personali"
                    value={manualPlan.route}
                    onChange={(e) => setManualPlan({ ...manualPlan, route: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 p-2.5 rounded-lg text-slate-200 focus:outline-none focus:border-cyan-400"
                  />
                </div>

                {/* Live Preview & Submit */}
                <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <div className="text-slate-400">Riepilogo Economico Previsto:</div>
                    <div className="text-base font-bold text-white mt-0.5">
                      {manualPlan.origin_icao || '----'} ➔ {manualPlan.destination_icao || '----'}
                      {manualEstimate?.estimated_distance_nm && (
                        <span className="text-cyan-300 text-xs ml-2">({manualPlan.distance_nm || manualEstimate.estimated_distance_nm} NM)</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-[10px] text-slate-400 uppercase">Compenso Previsto</div>
                      <div className={`text-lg font-black ${planIsCommercial ? 'text-emerald-400' : 'text-slate-400'}`}>
                        {planIsCommercial
                          ? formatEuro(manualEstimate?.estimated_reward_eur ?? 650)
                          : '€ 0,00 (Solo Costi)'}
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={loading || !selectedAircraft}
                      className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs px-5 py-3 rounded-lg shadow transition disabled:opacity-50"
                    >
                      <CheckCircle size={16} /> Conferma Piano Manuale & Vai in Plancia
                    </button>
                  </div>
                </div>
              </form>
            )}
          </div>
        )}

        {/* TAB 6: MAINTENANCE & WORKSHOP */}
        {activeTab === 'maintenance' && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 glass-panel p-5 rounded-xl border border-slate-800">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <Wrench size={22} className="text-cyan-400" /> Officina e Stato Usura Componenti
                </h2>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  Seleziona dal menu a tendina il velivolo da ispezionare e gestire.
                </p>
              </div>

              {/* Aircraft Dropdown Selector */}
              <div className="flex items-center gap-3">
                <label className="text-xs font-mono text-slate-400 uppercase font-semibold">
                  Velivolo Selezionato:
                </label>
                <select
                  value={selectedAircraft?.id || ''}
                  onChange={(e) => {
                    const ac = fleet.find(a => a.id === parseInt(e.target.value));
                    if (ac) setSelectedAircraft(ac);
                  }}
                  className="bg-slate-900 border border-cyan-500/50 text-cyan-300 font-mono font-bold text-sm px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-400 cursor-pointer shadow-lg"
                >
                  {fleet.map((ac) => (
                    <option key={ac.id} value={ac.id} className="bg-slate-900 text-white">
                      {ac.tail_number} — {ac.name} [{ac.ownership === 'OWNED' ? 'PROPRIETÀ' : 'NOLEGGIO'}] @ {ac.current_icao}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Quick Aircraft Info Strip */}
            {selectedAircraft && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
                <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800 flex items-center gap-2">
                  <MapPin size={15} className="text-rose-400" />
                  <div>
                    <div className="text-slate-400">Posizione Attuale</div>
                    <div className="font-bold text-white text-sm">{selectedAircraft.current_icao}</div>
                  </div>
                </div>

                <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800 flex items-center gap-2">
                  <Clock size={15} className="text-cyan-400" />
                  <div>
                    <div className="text-slate-400">Ore Cellula / Motore</div>
                    <div className="font-bold text-white text-sm">{selectedAircraft.airframe_hours.toFixed(1)} h / {selectedAircraft.engine_hours.toFixed(1)} h</div>
                  </div>
                </div>

                <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800 flex items-center gap-2">
                  <Fuel size={15} className="text-purple-400" />
                  <div>
                    <div className="text-slate-400">Carburante a Bordo</div>
                    <div className="font-bold text-white text-sm">{selectedAircraft.fuel_quantity_kg.toFixed(0)} / {selectedAircraft.fuel_capacity_kg.toFixed(0)} kg</div>
                  </div>
                </div>

                <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800 flex items-center gap-2">
                  <ShieldAlert size={15} className="text-amber-400" />
                  <div>
                    <div className="text-slate-400">Tipo Possesso</div>
                    <div className="font-bold text-emerald-400 text-sm">
                      {selectedAircraft.ownership === 'OWNED' ? 'DI PROPRIETÀ' : `NOLEGGIO (${formatEuro(selectedAircraft.hourly_lease_rate)}/h)`}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Health Bars Grid */}
            {selectedAircraft && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                {[
                  { name: 'Motore', health: selectedAircraft.health_engine_pct, color: 'emerald' },
                  { name: 'Freni', health: selectedAircraft.health_brakes_pct, color: 'cyan' },
                  { name: 'Pneumatici', health: selectedAircraft.health_tires_pct, color: 'blue' },
                  { name: 'Cellula', health: selectedAircraft.health_airframe_pct, color: 'purple' },
                  { name: 'Avionica', health: selectedAircraft.health_avionics_pct, color: 'amber' },
                ].map((comp, idx) => (
                  <div key={idx} className="glass-panel p-4 rounded-xl border border-slate-800">
                    <div className="flex justify-between items-center text-xs font-mono mb-2">
                      <span className="text-slate-300 font-bold">{comp.name}</span>
                      <span className={`font-bold ${
                        comp.health > 80 ? 'text-emerald-400' : comp.health > 40 ? 'text-amber-400' : 'text-rose-400'
                      }`}>
                        {comp.health.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          comp.health > 80 ? 'bg-emerald-500' : comp.health > 40 ? 'bg-amber-500' : 'bg-rose-500 animate-pulse'
                        }`}
                        style={{ width: `${Math.max(5, comp.health)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Service & Repairs Operations */}
            <div className="glass-panel p-6 rounded-xl border border-slate-800">
              <h3 className="text-base font-bold text-white mb-3 flex items-center gap-2">
                <Wrench size={18} className="text-cyan-400" /> Cataloghi Manutenzione Programmata & Straordinaria
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[
                  { code: 'OIL_AND_FILTER', name: 'Cambio Olio e Filtri (50h)', cost: 420, desc: 'Ispezione e lubrificazione base motore certificata' },
                  { code: 'INSPECTION_100H', name: 'Ispezione 100 Ore', cost: 2200, desc: 'Tagliando motore, compressione e candele' },
                  { code: 'TIRES_REPLACE', name: 'Sostituzione Pneumatici', cost: 1100, desc: 'Gomme nuove per carrello principale e anteriore' },
                  { code: 'BRAKES_OVERHAUL', name: 'Revisione Dischi & Pastiglie', cost: 1650, desc: 'Pastiglie nuove e spurgo idraulico' },
                  { code: 'ANNUAL_INSPECTION', name: 'Ispezione Annuale Certificata EASA', cost: 4400, desc: 'Revisione cellula, cavi comandi e avionica' },
                  { code: 'ENGINE_OVERHAUL', name: 'Revisione Generale Motore (TBO)', cost: 35000, desc: 'Ricostruzione a ore zero motore' },
                ].map((srv) => (
                  <div key={srv.code} className="bg-slate-900/60 p-4 rounded-lg border border-slate-800 flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-start">
                        <h4 className="font-bold text-sm text-white">{srv.name}</h4>
                        <span className="font-mono font-bold text-emerald-400 text-sm">{formatEuro(srv.cost)}</span>
                      </div>
                      <p className="text-xs text-slate-400 font-mono mt-1">{srv.desc}</p>
                    </div>

                    <button
                      onClick={() => handleService(selectedAircraft.id, srv.code)}
                      disabled={!selectedAircraft}
                      className="mt-4 bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/30 text-xs font-mono font-semibold py-1.5 rounded transition"
                    >
                      Esegui Intervento
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Test Injection Failure Panel */}
            <div className="glass-panel p-5 rounded-xl border border-rose-900/40 bg-rose-950/10">
              <h3 className="text-sm font-bold text-rose-300 flex items-center gap-2 mb-1">
                <ShieldAlert size={16} /> Banco Prova Guasti Reali (Simulatore Iniezione X-Plane 12)
              </h3>
              <p className="text-xs text-slate-400 font-mono mb-3">
                Usa questi pulsanti per testare l'iniezione bidirezionale di avarie native direttamente nei Dataref di X-Plane 12:
              </p>
              
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handleInjectFailureTest('sim/operation/failures/rel_engfai0')}
                  className="bg-rose-900/50 hover:bg-rose-800/80 border border-rose-700/60 text-rose-200 text-xs font-mono px-3 py-1.5 rounded"
                >
                  ⚡ Test: Piantata Motore 1
                </button>
                <button
                  onClick={() => handleInjectFailureTest('sim/operation/failures/rel_l_tire')}
                  className="bg-rose-900/50 hover:bg-rose-800/80 border border-rose-700/60 text-rose-200 text-xs font-mono px-3 py-1.5 rounded"
                >
                  ⚡ Test: Scoppio Gomma SX
                </button>
                <button
                  onClick={() => handleInjectFailureTest('sim/operation/failures/rel_lbrak')}
                  className="bg-rose-900/50 hover:bg-rose-800/80 border border-rose-700/60 text-rose-200 text-xs font-mono px-3 py-1.5 rounded"
                >
                  ⚡ Test: Perdita Idraulica Freni
                </button>
                <button
                  onClick={() => handleInjectFailureTest('sim/operation/failures/rel_pitot')}
                  className="bg-rose-900/50 hover:bg-rose-800/80 border border-rose-700/60 text-rose-200 text-xs font-mono px-3 py-1.5 rounded"
                >
                  ⚡ Test: Blocco Tubo Pitot
                </button>
              </div>
            </div>
          </div>
        )}

        {/* TAB 7: BILANCIO, FINANZE & GIORNO OPERATIVO */}
        {activeTab === 'finances' && (
          <div className="space-y-6">
            {/* Header & Title */}
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <TrendingUp size={22} className="text-emerald-400" /> Bilancio, Economia & Tempo Operativo
                </h2>
                <p className="text-xs text-slate-400 font-mono mt-1">
                  Gestione patrimoniale e contabile, controllo cassa, conto economico e dilatazione temporale per costi fissi.
                </p>
              </div>

              {/* Sub-Tabs Switcher */}
              <div className="flex flex-wrap items-center gap-1 bg-slate-900/90 border border-slate-800 p-1 rounded-lg text-xs font-mono">
                {[
                  { id: 'overview', label: 'Quadro & Bilancio', icon: FileText },
                  { id: 'crew', label: `Personale Fisso (${crewRoster?.hired?.length || 0})`, icon: Shield },
                  { id: 'ledger', label: `Registro Cassa (${financialLedger.length})`, icon: Wallet },
                  { id: 'rules', label: 'Regole & Formule', icon: HelpCircle }
                ].map((st) => {
                  const SIcon = st.icon;
                  const active = financeSubTab === st.id;
                  return (
                    <button
                      key={st.id}
                      onClick={() => setFinanceSubTab(st.id)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition ${
                        active 
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold' 
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                      }`}
                    >
                      <SIcon size={14} />
                      {st.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* HERO BANNER: MESE OPERATIVO & CALENDARIO REALE */}
            <div className="glass-panel p-5 rounded-xl border border-amber-500/30 bg-gradient-to-br from-slate-900/90 via-slate-900/70 to-amber-950/20 shadow-xl relative overflow-hidden">
              <div className="absolute top-0 right-0 -mr-16 -mt-16 w-56 h-56 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
              
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
                <div className="lg:col-span-7 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] font-mono font-bold uppercase tracking-wider flex items-center gap-1">
                      <Clock size={11} /> Calendario Reale Mensile
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      1 Mese Reale = 1 Mese Operativo
                    </span>
                  </div>

                  <div className="flex flex-wrap items-baseline gap-3">
                    <span className="text-3xl font-black text-white font-mono tracking-tight">
                      Mese Operativo: {financialOverview?.operating_month_label || systemStatus?.company?.operating_month_label || formatOperatingMonth(new Date().toISOString().slice(0, 7))}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 font-mono flex items-center gap-1.5">
                    <Calendar size={13} className="text-cyan-400" />
                    Data Reale di Sistema: <strong className="text-white">{formatVirtualDate(financialOverview?.virtual_date || new Date().toISOString())}</strong>
                  </p>

                  <p className="text-xs text-slate-400 font-sans leading-relaxed pt-1">
                    I costi fissi di gestione (hangar, assicurazioni e rate mensili) sono addebitati automaticamente una sola volta per ogni mese reale trascorso, indipendentemente dal fatto che tu faccia 1 o 100 voli nel mese. Le assenze di più mesi reali maturano tutti i mesi trascorsi.
                  </p>
                </div>

                {/* Right side: Monthly Fixed Cost Projections */}
                <div className="lg:col-span-5 bg-slate-950/70 p-4 rounded-xl border border-slate-800 space-y-3">
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-slate-400 flex items-center gap-1.5">
                      <Fuel size={13} className="text-amber-400" /> Chiusura Mensile ({financialOverview?.operating_month_label || 'Mese Corrente'}):
                    </span>
                    <span className="font-bold text-rose-400 text-sm">
                      {formatEuro(financialOverview?.upcoming_fixed_costs_monthly?.total_fixed_eur || 0)}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono bg-slate-900/60 p-2 rounded border border-slate-800/80">
                    <div>
                      <span className="text-slate-400 block">Hangar/Mese:</span>
                      <span className="text-slate-200 font-semibold">{formatEuro(financialOverview?.upcoming_fixed_costs_monthly?.total_hangar_eur || 0)}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Assic./Mese:</span>
                      <span className="text-slate-200 font-semibold">{formatEuro(financialOverview?.upcoming_fixed_costs_monthly?.total_insurance_eur || 0)}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Rate/Mese:</span>
                      <span className="text-amber-300 font-semibold">{formatEuro(financialOverview?.upcoming_fixed_costs_monthly?.total_financing_eur || 0)}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Stipendi/Mese:</span>
                      <span className="text-indigo-300 font-semibold">{formatEuro(financialOverview?.upcoming_fixed_costs_monthly?.total_crew_salaries_eur || 0)}</span>
                    </div>
                  </div>

                  <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between pt-1">
                    <span>Flotta di proprietà attiva: <strong className="text-white">{financialOverview?.upcoming_fixed_costs_monthly?.owned_aircraft_count ?? 0}</strong></span>
                    <span className="text-emerald-400">● Addebito automatico a cambio mese</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Period Filter Selector (Storico vs Mese Operativo) */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800 font-mono text-xs">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-slate-400 flex items-center gap-1 mr-1">
                  <Calendar size={13} className="text-cyan-400" /> Periodo Conto Economico:
                </span>
                <button
                  onClick={() => {
                    setFinancePeriodFilter('ALL');
                    fetchFinances('ALL');
                  }}
                  className={`px-3 py-1 rounded-lg transition ${
                    financePeriodFilter === 'ALL'
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                      : 'bg-slate-800/70 text-slate-400 hover:text-white'
                  }`}
                >
                  Storico Totale
                </button>
                {(financialOverview?.available_months || []).map((m) => (
                  <button
                    key={m.ym}
                    onClick={() => {
                      setFinancePeriodFilter(m.ym);
                      fetchFinances(m.ym);
                    }}
                    className={`px-3 py-1 rounded-lg transition ${
                      financePeriodFilter === m.ym
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold'
                        : 'bg-slate-800/70 text-slate-400 hover:text-white'
                    }`}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
              <span className="flex items-center gap-2 text-[11px]">
                <span className="text-slate-400">Economia:</span>
                {['REALISTIC', 'STANDARD'].map((em) => {
                  const activeMode = (financialOverview?.economy_mode || systemStatus?.company?.economy_mode || 'REALISTIC').toUpperCase() === em;
                  return (
                    <button
                      key={em}
                      type="button"
                      onClick={async () => {
                        const r = await fetch('/api/company/economy_mode', {
                          method: 'PATCH',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ economy_mode: em })
                        });
                        const d = await r.json();
                        if (r.ok) {
                          showNotice(d.message, 'success');
                          await Promise.all([fetchStatus(), fetchFinances(), fetchActiveFlight()]);
                        }
                      }}
                      className={`px-2.5 py-1 rounded border font-bold transition ${
                        activeMode
                          ? (em === 'REALISTIC' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' : 'bg-amber-500/20 text-amber-300 border-amber-500/40')
                          : 'bg-slate-800/70 text-slate-400 border-slate-700 hover:text-white'
                      }`}
                    >
                      {em === 'REALISTIC' ? '🎯 Realistica' : '🕹️ Standard'}
                    </button>
                  );
                })}
              </span>
            </div>

            {/* SUB-VIEW 1: QUADRO GENERALE & BILANCIO (P&L + STATO PATRIMONIALE) */}
            {financeSubTab === 'overview' && (
              <div className="space-y-6">
                {/* 4 Hero KPI Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Card 1: Liquidità Cassa */}
                  <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-1">
                    <div className="flex justify-between items-center text-slate-400 text-xs font-mono">
                      <span>LIQUIDITÀ CASSA</span>
                      <Wallet size={16} className="text-emerald-400" />
                    </div>
                    <div className="text-xl font-bold font-mono text-emerald-400">
                      {formatEuro(financialOverview?.balance_sheet?.cash_balance_eur ?? systemStatus?.company?.cash_balance ?? 175000)}
                    </div>
                    <p className="text-[11px] text-slate-400">Disponibilità immediata per DOC e riparazioni</p>
                  </div>

                  {/* Card 2: Valore Flotta */}
                  <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-1">
                    <div className="flex justify-between items-center text-slate-400 text-xs font-mono">
                      <span>VALORE FLOTTA ATTIVA</span>
                      <Plane size={16} className="text-cyan-400" />
                    </div>
                    <div className="text-xl font-bold font-mono text-cyan-300">
                      {formatEuro(financialOverview?.balance_sheet?.fleet_book_value_eur ?? 0)}
                    </div>
                    <p className="text-[11px] text-slate-400">
                      {financialOverview?.balance_sheet?.owned_aircraft_count ?? 0} velivoli di proprietà a bilancio
                    </p>
                  </div>

                  {/* Card 3: Patrimonio Netto */}
                  <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-1">
                    <div className="flex justify-between items-center text-slate-400 text-xs font-mono">
                      <span>PATRIMONIO NETTO (ASSETS)</span>
                      <Award size={16} className="text-purple-400" />
                    </div>
                    <div className="text-xl font-bold font-mono text-purple-300">
                      {formatEuro(financialOverview?.balance_sheet?.total_net_worth_eur ?? 0)}
                    </div>
                    <p className="text-[11px] text-slate-400">Capitale liquido + valore flotta aziendale</p>
                  </div>

                  {/* Card 4: Utile Netto */}
                  <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-1">
                    <div className="flex justify-between items-center text-slate-400 text-xs font-mono">
                      <span>UTILE NETTO COMPLESSIVO</span>
                      <TrendingUp size={16} className={
                        (financialOverview?.income_statement?.net_profit_eur || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      } />
                    </div>
                    <div className={`text-xl font-bold font-mono ${
                      (financialOverview?.income_statement?.net_profit_eur || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}>
                      {formatEuro(financialOverview?.income_statement?.net_profit_eur ?? 0)}
                    </div>
                    <p className="text-[11px] text-slate-400">
                      Margine operativo: <strong className="text-white">{financialOverview?.income_statement?.profit_margin_pct ?? 0}%</strong>
                    </p>
                  </div>
                </div>

                {/* 2 Main Panels: Stato Patrimoniale vs Conto Economico (P&L) */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  
                  {/* Panel A: STATO PATRIMONIALE */}
                  <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-4">
                    <div className="border-b border-slate-800 pb-3 flex justify-between items-center">
                      <div>
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                          <FileText size={16} className="text-cyan-400" /> Stato Patrimoniale (Asset & Flotta)
                        </h3>
                        <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                          Consistenza patrimoniale societaria • {financialOverview?.operating_month_label || 'Mese Corrente'}
                        </p>
                      </div>
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        Patrimonio Netto
                      </span>
                    </div>

                    <div className="space-y-3 font-mono text-xs">
                      {/* Attivo Circolante */}
                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800 space-y-2">
                        <div className="flex justify-between items-center text-slate-300 font-bold">
                          <span>1. ATTIVO CIRCOLANTE</span>
                          <span className="text-emerald-400">
                            {formatEuro(financialOverview?.balance_sheet?.cash_balance_eur ?? 175000)}
                          </span>
                        </div>
                        <div className="flex justify-between items-center text-slate-400 pl-3">
                          <span>Disponibilità liquide (Conto aziendale)</span>
                          <span className="text-slate-200">
                            {formatEuro(financialOverview?.balance_sheet?.cash_balance_eur ?? 175000)}
                          </span>
                        </div>
                      </div>

                      {/* Attivo Fisso Immobilizzato */}
                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800 space-y-2">
                        <div className="flex justify-between items-center text-slate-300 font-bold">
                          <span>2. IMMOBILIZZAZIONI MATERIALI (FLOTTA)</span>
                          <span className="text-cyan-300">
                            {formatEuro(financialOverview?.balance_sheet?.fleet_book_value_eur ?? 0)}
                          </span>
                        </div>
                        
                        <div className="divide-y divide-slate-800/60 pl-3 space-y-1.5 pt-1">
                          {fleet.filter(a => a.ownership === 'OWNED').map((ac) => (
                            <div key={ac.id} className="pt-1.5 flex justify-between items-center">
                              <div>
                                <span className="font-bold text-white">{ac.tail_number}</span>
                                <span className="text-slate-400 ml-1.5">{ac.name} ({ac.year_manufactured || 2021})</span>
                              </div>
                              <span className="text-slate-300">{formatEuro(ac.purchase_price_eur || 0)}</span>
                            </div>
                          ))}
                          {fleet.filter(a => a.ownership === 'OWNED').length === 0 && (
                            <div className="text-slate-500 py-1">Nessun aereo di proprietà registrato.</div>
                          )}
                        </div>
                      </div>

                      {/* Aeromobili a Noleggio (Fuori Bilancio) */}
                      <div className="bg-slate-900/40 p-3 rounded-lg border border-slate-800/60 text-slate-400 space-y-1">
                        <div className="flex justify-between items-center text-slate-300 font-semibold text-[11px]">
                          <span>3. AEROMOBILI IN LEASE / NOLEGGIO ATTIVI</span>
                          <span className="text-amber-400">{fleet.filter(a => a.ownership === 'LEASED').length} aerei</span>
                        </div>
                        <p className="text-[10px] text-slate-500 font-sans">
                          Gli aeromobili a noleggio non concorrono al patrimonio aziendale ma generano costi orari variabili (DOC) durante l uso.
                        </p>
                      </div>

                      {/* Totale Patrimonio Netto */}
                      <div className="p-3 rounded-lg bg-cyan-950/20 border border-cyan-500/30 flex justify-between items-center font-bold text-sm">
                        <span className="text-white">TOTALE PATRIMONIO NETTO</span>
                        <span className="text-cyan-300">
                          {formatEuro(financialOverview?.balance_sheet?.total_net_worth_eur ?? 0)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Panel B: CONTO ECONOMICO (P&L - PROFITTI & PERDITE) */}
                  <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-4">
                    <div className="border-b border-slate-800 pb-3 flex justify-between items-center">
                      <div>
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                          <TrendingUp size={16} className="text-emerald-400" /> Conto Economico Progressivo (P&L)
                        </h3>
                        <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                          Dettaglio ricavi, costi operativi DOC, manutenzioni e oneri fissi
                        </p>
                      </div>
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        In Euro (€)
                      </span>
                    </div>

                    <div className="space-y-3 font-mono text-xs">
                      {/* (+) Ricavi Operativi */}
                      <div className="bg-emerald-950/20 p-3 rounded-lg border border-emerald-500/30 space-y-1.5">
                        <div className="flex justify-between items-center font-bold text-emerald-300">
                          <span>(+) RICAVI TOTALI DA VOLI & INCARICHI</span>
                          <span className="text-sm">
                            {formatEuro(financialOverview?.income_statement?.gross_revenue_eur ?? 0)}
                          </span>
                        </div>
                        <p className="text-[11px] text-emerald-400/80 font-sans">
                          Compensi contratti passeggeri, merci cargo, voli charter VIP e sanitari
                        </p>
                      </div>

                      {/* (-) Costi Operativi Diretti (DOC) */}
                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800 space-y-2">
                        <div className="flex justify-between items-center font-bold text-slate-300">
                          <span>(-) COSTI OPERATIVI DIRETTI (DOC)</span>
                          <span className="text-rose-400">
                            -{formatEuro(financialOverview?.income_statement?.direct_operating_costs?.total_eur ?? 0)}
                          </span>
                        </div>
                        <div className="pl-3 space-y-1 text-slate-400">
                          <div className="flex justify-between items-center">
                            <span>Carburante Jet-A1 (1.75 €/kg)</span>
                            <span className="text-slate-200">
                              {formatEuro(financialOverview?.income_statement?.direct_operating_costs?.fuel_eur ?? 0)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span>Tasse Atterraggio (MTOW / Base)</span>
                            <span className="text-slate-200">
                              {formatEuro(financialOverview?.income_statement?.direct_operating_costs?.landing_fees_eur ?? 0)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span>Sorvolo & Navigazione Eurocontrol (IFR)</span>
                            <span className="text-slate-200">
                              {formatEuro(financialOverview?.income_statement?.direct_operating_costs?.nav_fees_eur ?? 0)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span>Catering, FBO & Handling Passeggeri</span>
                            <span className="text-slate-200">
                              {formatEuro(financialOverview?.income_statement?.direct_operating_costs?.handling_fees_eur ?? 0)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span>Riserva Manutenzione (Power-by-the-Hour)</span>
                            <span className="text-slate-200">
                              {formatEuro(financialOverview?.income_statement?.direct_operating_costs?.maint_reserves_eur ?? 0)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span>Costi Indiretti IOC (GDS / Broker / EU261)</span>
                            <span className="text-slate-200">
                              {formatEuro(financialOverview?.income_statement?.direct_operating_costs?.ioc_costs_eur ?? 0)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span>Canoni Orari Noleggio (Lease Block Hours)</span>
                            <span className="text-slate-200">
                              {formatEuro(financialOverview?.income_statement?.direct_operating_costs?.aircraft_leases_eur ?? 0)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span>Equipaggio Freelance a Volo (Piloti / A.V.)</span>
                            <span className="text-slate-200">
                              {formatEuro(financialOverview?.income_statement?.direct_operating_costs?.crew_eur ?? 0)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span>Penali & Risarcimenti Touchdown</span>
                            <span className="text-rose-300">
                              {formatEuro(financialOverview?.income_statement?.direct_operating_costs?.penalties_eur ?? 0)}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* (-) Manutenzione e Officina */}
                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800 space-y-1.5">
                        <div className="flex justify-between items-center font-bold text-slate-300">
                          <span>(-) MANUTENZIONE & RIPARAZIONI OFFICINA</span>
                          <span className="text-rose-400">
                            -{formatEuro(financialOverview?.income_statement?.maintenance_costs?.total_eur ?? 0)}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 pl-3">
                          Tagliandi 50h/100h, ispezioni annuali EASA, freni, gomme e revisioni motore
                        </p>
                      </div>

                      {/* (-) Costi Fissi di Gestione */}
                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800 space-y-2">
                        <div className="flex justify-between items-center font-bold text-slate-300">
                          <span>(-) ONERI FISSI MENSILI</span>
                          <span className="text-rose-400">
                            -{formatEuro(financialOverview?.income_statement?.fixed_overheads?.total_eur ?? 0)}
                          </span>
                        </div>
                        <div className="pl-3 space-y-1 text-slate-400">
                          <div className="flex justify-between items-center">
                            <span>Rimessaggio & Hangaraggio Mensile</span>
                            <span className="text-slate-200">
                              {formatEuro(financialOverview?.income_statement?.fixed_overheads?.hangar_eur ?? 0)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span>Polizze Assicurative Flotta (Corpi & RC)</span>
                            <span className="text-slate-200">
                              {formatEuro(financialOverview?.income_statement?.fixed_overheads?.insurance_eur ?? 0)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span>Rate Leasing Finanziario & Mutui</span>
                            <span className="text-amber-300">
                              {formatEuro(financialOverview?.income_statement?.fixed_overheads?.financing_eur ?? 0)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span>Stipendi Mensili Equipaggi Assunti</span>
                            <span className="text-indigo-300">
                              {formatEuro(financialOverview?.income_statement?.fixed_overheads?.crew_salaries_eur ?? 0)}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* (=) UTILE NETTO FINALE */}
                      <div className={`p-3.5 rounded-lg border flex justify-between items-center font-bold text-sm ${
                        (financialOverview?.income_statement?.net_profit_eur || 0) >= 0
                          ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-300'
                          : 'bg-rose-950/30 border-rose-500/40 text-rose-300'
                      }`}>
                        <div>
                          <span>RISULTATO D ESERCIZIO (UTILE NETTO)</span>
                          <span className="text-[11px] font-normal block text-slate-400">
                            Margine Operativo sul Fatturato: {financialOverview?.income_statement?.profit_margin_pct ?? 0}%
                          </span>
                        </div>
                        <span className="text-base font-mono">
                          {formatEuro(financialOverview?.income_statement?.net_profit_eur ?? 0)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* SUB-VIEW 1B: PERSONALE FISSO VS FREELANCE */}
            {financeSubTab === 'crew' && (
              <div className="space-y-6">
                <div className="glass-panel p-5 rounded-xl border border-indigo-500/30 space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h3 className="text-base font-bold text-white flex items-center gap-2">
                        <Shield size={18} className="text-indigo-400" /> Gestione Equipaggi: Assunto Fisso Mensile vs Freelance
                      </h3>
                      <p className="text-xs text-slate-400 font-sans mt-0.5">
                        Assumi un equipaggio fisso mensile per una classe di velivoli per azzerare il costo orario su ogni singolo volo (€ 0/h). Ideale se voli più di 20 ore al mese in quella categoria; altrimenti conviene restare in regime Freelance a chiamata.
                      </p>
                    </div>
                    <div className="bg-slate-950/70 px-4 py-2 rounded-lg border border-slate-800 text-right font-mono">
                      <div className="text-[10px] text-slate-400 uppercase">Monte Stipendi Mensile</div>
                      <div className="text-lg font-bold text-indigo-300">
                        {formatEuro(crewRoster?.total_monthly_salaries_eur || 0)} / mese
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-5 font-mono text-xs">
                  {(crewRoster?.catalog || []).map((item) => (
                    <div
                      key={item.category}
                      className={`glass-panel p-5 rounded-2xl border space-y-4 flex flex-col justify-between ${
                        item.is_hired
                          ? 'border-emerald-500/50 bg-emerald-950/10'
                          : 'border-slate-800'
                      }`}
                    >
                      <div className="space-y-3">
                        <div className="flex justify-between items-start gap-2">
                          <div>
                            <span className="px-2 py-0.5 rounded bg-slate-800 text-cyan-300 font-bold text-[10px]">
                              CLASSE {item.category}
                            </span>
                            <h4 className="text-base font-bold text-white mt-1.5">{item.role_label}</h4>
                          </div>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            item.is_hired
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                              : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                          }`}>
                            {item.is_hired ? 'ASSUNTO FISSO' : 'FREELANCE'}
                          </span>
                        </div>

                        <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 space-y-1.5">
                          <div className="flex justify-between">
                            <span className="text-slate-400">Stipendio Mensile Fisso:</span>
                            <span className="text-white font-bold">{formatEuro(item.monthly_salary_eur)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">Tariffa Freelance a Volo:</span>
                            <span className="text-slate-300">{formatEuro(item.freelance_hourly_eur)} / ora</span>
                          </div>
                          <div className="flex justify-between pt-1 border-t border-slate-800/80 text-[11px]">
                            <span className="text-slate-400">Soglia Convenienza:</span>
                            <span className="text-amber-300 font-bold">&gt; {item.breakeven_hours_per_month} ore / mese</span>
                          </div>
                        </div>

                        {item.is_hired && item.hired_member && (
                          <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-500/30 text-emerald-300 text-[11px]">
                            ✓ Attivo: <strong>{item.hired_member.name}</strong> — tutti i voli {item.category} hanno costo equipaggio orario € 0,00.
                          </div>
                        )}
                      </div>

                      {item.is_hired && item.hired_member ? (
                        <button
                          type="button"
                          onClick={() => handleFireCrew(item.hired_member.id)}
                          disabled={loading}
                          className="w-full py-2.5 rounded-xl bg-rose-950/50 hover:bg-rose-900/60 text-rose-300 border border-rose-500/40 font-bold transition disabled:opacity-50"
                        >
                          Licenzia & Torna a Freelance
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleHireCrew(item.category)}
                          disabled={loading}
                          className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold shadow transition disabled:opacity-50"
                        >
                          Assumi Equipaggio Fisso ({formatEuro(item.monthly_salary_eur)}/mese)
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* SUB-VIEW 2: LIBRO MASTRO / REGISTRO CASSA (TRANSACTIONS LEDGER) */}
            {financeSubTab === 'ledger' && (
              <div className="space-y-4">
                {/* Category Filter Pills */}
                <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                  <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
                    <span className="text-slate-400 flex items-center gap-1 mr-1">
                      <Filter size={13} /> Filtra Categoria:
                    </span>
                    {[
                      { id: 'ALL', label: 'Tutti' },
                      { id: 'REVENUE', label: 'Incassi Voli (+)' },
                      { id: 'FUEL', label: 'Carburante' },
                      { id: 'LANDING_FEE', label: 'Tasse Atterraggio' },
                      { id: 'NAV_FEE', label: 'Eurocontrol' },
                      { id: 'HANDLING', label: 'Handling/FBO' },
                      { id: 'MAINT_RESERVE', label: 'Riserve Manut.' },
                      { id: 'IOC', label: 'IOC / GDS' },
                      { id: 'MAINTENANCE', label: 'Officina' },
                      { id: 'CREW', label: 'Equipaggio Volo' },
                      { id: 'CREW_SALARY', label: 'Stipendi Fissi' },
                      { id: 'PENALTY', label: 'Penali' },
                      { id: 'LEASE', label: 'Noleggi' },
                      { id: 'FIXED_HANGAR', label: 'Hangar' },
                      { id: 'FIXED_INSURANCE', label: 'Assicurazioni' },
                      { id: 'FINANCING', label: 'Rate/Mutui' },
                    ].map((btn) => (
                      <button
                        key={btn.id}
                        onClick={() => setLedgerCategoryFilter(btn.id)}
                        className={`px-2.5 py-1 rounded transition ${
                          ledgerCategoryFilter === btn.id
                            ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                            : 'bg-slate-800/60 text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        {btn.label}
                      </button>
                    ))}
                  </div>

                  <button
                    onClick={fetchFinances}
                    className="flex items-center gap-1 text-xs font-mono text-slate-400 hover:text-cyan-300 transition"
                  >
                    <RefreshCw size={12} /> Aggiorna Registro
                  </button>
                </div>

                {/* Ledger Table */}
                <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left font-mono text-xs">
                      <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800">
                        <tr>
                          <th className="p-3">Mese / Data</th>
                          <th className="p-3">Categoria</th>
                          <th className="p-3">Velivolo</th>
                          <th className="p-3">Descrizione / Causale Operazione</th>
                          <th className="p-3 text-right">Importo (€)</th>
                          <th className="p-3 text-right">Saldo Cassa</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 text-slate-200">
                        {financialLedger
                          .filter(tx => ledgerCategoryFilter === 'ALL' || tx.category === ledgerCategoryFilter)
                          .map((tx) => (
                            <tr key={tx.id} className="hover:bg-slate-800/30 transition">
                              <td className="p-3 text-slate-400 whitespace-nowrap">
                                <span className="font-bold text-amber-300/90">
                                  {tx.operating_month ? formatOperatingMonth(tx.operating_month, true) : formatOperatingMonth(new Date(tx.timestamp).toISOString().slice(0, 7), true)}
                                </span>
                                <span className="text-[10px] block text-slate-500">
                                  {new Date(tx.timestamp).toLocaleString('it-IT', { dateStyle: 'short', timeStyle: 'short' })}
                                </span>
                              </td>
                              <td className="p-3 whitespace-nowrap">
                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  tx.category === 'REVENUE' || tx.category === 'REVENUE_FLIGHT' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                                  tx.category === 'FUEL' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' :
                                  tx.category === 'LANDING_FEE' || tx.category === 'NAV_FEE' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' :
                                  tx.category === 'HANDLING' ? 'bg-teal-500/20 text-teal-300 border border-teal-500/30' :
                                  tx.category === 'MAINT_RESERVE' ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30' :
                                  tx.category === 'IOC' ? 'bg-slate-700/70 text-slate-200 border border-slate-600' :
                                  tx.category === 'MAINTENANCE' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                                  tx.category === 'CREW' || tx.category === 'CREW_SALARY' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' :
                                  tx.category === 'PENALTY' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' :
                                  tx.category === 'LEASE' ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' :
                                  'bg-slate-800 text-slate-300'
                                }`}>
                                  {tx.category}
                                </span>
                              </td>
                              <td className="p-3 font-bold text-white whitespace-nowrap">
                                {tx.related_aircraft_tail ? (
                                  <span className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                                    {tx.related_aircraft_tail}
                                  </span>
                                ) : (
                                  <span className="text-slate-500">-</span>
                                )}
                              </td>
                              <td className="p-3">
                                <div className="font-semibold text-white">{tx.title}</div>
                                {tx.description && (
                                  <div className="text-[11px] text-slate-400 font-sans">{tx.description}</div>
                                )}
                              </td>
                              <td className={`p-3 text-right font-bold whitespace-nowrap ${
                                tx.amount_eur >= 0 ? 'text-emerald-400' : 'text-rose-400'
                              }`}>
                                {tx.amount_eur >= 0 ? '+' : ''}{formatEuro(tx.amount_eur)}
                              </td>
                              <td className="p-3 text-right font-bold text-slate-300 font-mono whitespace-nowrap">
                                {formatEuro(tx.balance_after_eur)}
                              </td>
                            </tr>
                          ))}
                        {financialLedger.length === 0 && (
                          <tr>
                            <td colSpan={6} className="p-8 text-center text-slate-500">
                              Nessuna transazione contabile registrata. Le transazioni verranno generate automaticamente al termine di ciascun volo, rifornimento o manutenzione.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* SUB-VIEW 3: REGOLE E FORMULE ECONOMICHE */}
            {financeSubTab === 'rules' && financialGuide && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <Info size={18} className="text-cyan-400" /> Trasparenza Calcoli & Formule Economiche Verosimili
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">
                    Tutti i conti di SkyOps XP si basano su tariffe realistiche europee (EASA, IATA e aeroportuali).
                  </p>
                </div>

                {/* 1. Fuel Rules */}
                <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-2">
                  <div className="flex items-center gap-2 text-purple-400 font-bold text-sm font-mono">
                    <Fuel size={16} /> 1. CARBURANTE (JET-A1 KEROSENE)
                  </div>
                  <div className="text-xs text-slate-300 font-mono leading-relaxed">
                    <div className="font-bold text-white mb-1">{financialGuide.fuel_rules.formula}</div>
                    <p className="text-slate-400">{financialGuide.fuel_rules.notes}</p>
                    <div className="mt-2 grid grid-cols-2 max-w-sm gap-2 bg-slate-900/60 p-2.5 rounded border border-slate-800">
                      <div>Prezzo Jet-A1 al Kg: <span className="text-purple-300 font-bold">{formatEuro(financialGuide.fuel_rules.price_per_kg_eur)}/kg</span></div>
                      <div>Equivalente al Litro: <span className="text-slate-300 font-bold">{formatEuro(financialGuide.fuel_rules.price_per_litre_approx_eur)}/L</span></div>
                    </div>
                  </div>
                </div>

                {/* 2. Landing Fees */}
                <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm font-mono">
                    <MapPin size={16} /> 2. TASSE D ATTERRAGGIO (LANDING & HANDLING FEES)
                  </div>
                  <div className="text-xs text-slate-300 font-mono leading-relaxed">
                    <div className="font-bold text-white mb-1">{financialGuide.landing_fee_rules.formula}</div>
                    {financialGuide.landing_fee_rules.notes && (
                      <p className="text-emerald-300/90 mb-2">{financialGuide.landing_fee_rules.notes}</p>
                    )}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      {financialGuide.landing_fee_rules.categories.map((cat, idx) => (
                        <div key={idx} className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                          <div className="font-bold text-cyan-300">{cat.category}</div>
                          <div className="text-slate-400 mt-1">Quota Base: <span className="text-white">{cat.base}</span></div>
                          <div className="text-slate-400">Quota Peso: <span className="text-white">{cat.per_tonne}</span></div>
                          <div className="text-[11px] text-emerald-400 mt-2 font-semibold">{cat.typical_cost}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* 3. Revenue Rules */}
                <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
                  <div className="flex items-center gap-2 text-cyan-400 font-bold text-sm font-mono">
                    <Briefcase size={16} /> 3. CALCOLO RICAVI DEI VOLI (JOB REWARDS)
                  </div>
                  <div className="text-xs text-slate-300 font-mono leading-relaxed">
                    <div className="font-bold text-white mb-2">{financialGuide.revenue_rules.formula}</div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {financialGuide.revenue_rules.breakdown.map((item, idx) => (
                        <div key={idx} className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                          <div className="font-bold text-slate-200">{item.component}</div>
                          <div className="text-slate-400 mt-0.5">{item.description}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* 4. Touchdown & Wear Table */}
                <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
                  <div className="flex items-center gap-2 text-amber-400 font-bold text-sm font-mono">
                    <Wrench size={16} /> 4. MECCANICA USURA E ATTERRAGGI (TOUCHDOWN DYNAMICS)
                  </div>
                  <div className="text-xs text-slate-300 font-mono leading-relaxed">
                    <p className="text-slate-400 mb-3">
                      Ogni componente si usura in proporzione al tempo di volo, ma lo stress maggiore si concentra all atterraggio e nelle manovre brusche:
                    </p>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left border border-slate-800 rounded">
                        <thead className="bg-slate-900 text-slate-400">
                          <tr>
                            <th className="p-2.5">Giudizio Contatto</th>
                            <th className="p-2.5">Soglie Telemetriche</th>
                            <th className="p-2.5">Impatto su Gomme e Carrello</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {financialGuide.wear_and_maintenance_rules.touchdown_impact_table.map((row, idx) => (
                            <tr key={idx} className="hover:bg-slate-800/30">
                              <td className="p-2.5 font-bold text-white">{row.rating}</td>
                              <td className="p-2.5 text-cyan-300">{row.fpm}</td>
                              <td className="p-2.5 text-slate-300">{row.impact}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                {/* 5. Crew Rules */}
                {financialGuide.crew_rules && (
                  <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
                    <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm font-mono">
                      <Shield size={16} /> 5. PERSONALE DI BORDO (PILOTI & ASSISTENTI DI VOLO)
                    </div>
                    <div className="text-xs text-slate-300 font-mono leading-relaxed">
                      <div className="font-bold text-white mb-1">{financialGuide.crew_rules.formula}</div>
                      <p className="text-slate-400 mb-3">{financialGuide.crew_rules.notes}</p>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        {financialGuide.crew_rules.categories.map((cat, idx) => (
                          <div key={idx} className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                            <div className="font-bold text-indigo-300">{cat.category}</div>
                            <div className="text-slate-300 mt-1">{cat.crew}</div>
                            <div className="text-emerald-400 font-bold mt-1">{cat.rate}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* 6. Monthly Fixed Costs Rules */}
                {financialGuide.fixed_costs_rules && (
                  <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
                    <div className="flex items-center gap-2 text-amber-400 font-bold text-sm font-mono">
                      <Calendar size={16} /> 6. MESE OPERATIVO REALE & COSTI FISSI MENSILI
                    </div>
                    <div className="text-xs text-slate-300 font-mono leading-relaxed">
                      <div className="font-bold text-white mb-1">{financialGuide.fixed_costs_rules.formula}</div>
                      <p className="text-slate-400 mb-3">{financialGuide.fixed_costs_rules.notes}</p>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        {financialGuide.fixed_costs_rules.categories.map((cat, idx) => (
                          <div key={idx} className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                            <div className="font-bold text-amber-300">{cat.category}</div>
                            <div className="text-slate-400 mt-1">Hangar: <span className="text-white">{cat.hangar}</span></div>
                            <div className="text-slate-400">Assicurazione: <span className="text-white">{cat.insurance}</span></div>
                            <div className="text-rose-400 font-bold mt-2">Totale: {cat.total}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
                {/* 7. Eurocontrol & Reputation Rules */}
                {financialGuide.eurocontrol_and_handling_rules && (
                  <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
                    <div className="flex items-center gap-2 text-cyan-400 font-bold text-sm font-mono">
                      <Radio size={16} /> 7. TARIFFE EUROCONTROL, HANDLING PAX & REPUTAZIONE
                    </div>
                    <div className="text-xs text-slate-300 font-mono leading-relaxed space-y-2">
                      <div>
                        <div className="font-bold text-white">{financialGuide.eurocontrol_and_handling_rules.formula}</div>
                        <p className="text-slate-400">{financialGuide.eurocontrol_and_handling_rules.notes}</p>
                      </div>
                      {financialGuide.reputation_rules && (
                        <div className="pt-2 border-t border-slate-800">
                          <div className="font-bold text-emerald-300">{financialGuide.reputation_rules.formula}</div>
                          <p className="text-slate-400">{financialGuide.reputation_rules.notes}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB 8: LOGBOOK & DIARIO TOUR IVAO */}
        {activeTab === 'logbook' && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <BookOpen size={22} className="text-cyan-400" /> Registro Voli & Diario Tour IVAO
                </h2>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  Cronologia completa dei voli e mappa interattiva delle tappe raggruppate per Tour.
                </p>
              </div>
              <div className="flex items-center gap-1 bg-slate-900/90 border border-slate-800 p-1 rounded-lg text-xs font-mono">
                <button
                  onClick={() => setLogbookSubTab('flights')}
                  className={`px-3.5 py-1.5 rounded-md transition ${
                    logbookSubTab === 'flights'
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  📜 Logbook Voli ({flightHistory.length})
                </button>
                <button
                  onClick={() => setLogbookSubTab('tours')}
                  className={`px-3.5 py-1.5 rounded-md transition ${
                    logbookSubTab === 'tours'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  🗺️ Tour & Mappa Rotte ({toursList.length})
                </button>
              </div>
            </div>

            {logbookSubTab === 'flights' && (
              <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left font-mono text-xs">
                    <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="p-3">Data</th>
                        <th className="p-3">Volo</th>
                        <th className="p-3">Regole</th>
                        <th className="p-3">Rotta</th>
                        <th className="p-3">Durata</th>
                        <th className="p-3">Fuel (kg)</th>
                        <th className="p-3">Touchdown</th>
                        <th className="p-3">G-Force</th>
                        <th className="p-3 text-right">Ricavo Netto</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-200">
                      {flightHistory.map((log) => (
                        <tr key={log.id} className="hover:bg-slate-800/30">
                          <td className="p-3 text-slate-400">{new Date(log.start_time).toLocaleDateString()}</td>
                          <td className="p-3 font-bold text-cyan-400">{log.flight_number}</td>
                          <td className="p-3">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              log.flight_rules === 'VFR' ? 'bg-sky-500/20 text-sky-300' : 'bg-slate-800 text-slate-300'
                            }`}>
                              {log.flight_rules || 'IFR'}
                            </span>
                          </td>
                          <td className="p-3 font-bold">{log.origin_icao} → {log.destination_icao}</td>
                          <td className="p-3">{log.flight_duration_min} min</td>
                          <td className="p-3">{log.fuel_used_kg} kg</td>
                          <td className="p-3">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              log.touchdown_rating === 'BUTTER' ? 'bg-emerald-500/20 text-emerald-300' :
                              log.touchdown_rating === 'GOOD' ? 'bg-cyan-500/20 text-cyan-300' :
                              'bg-amber-500/20 text-amber-300'
                            }`}>
                              {log.touchdown_fpm ? `${log.touchdown_fpm} fpm` : 'N/A'}
                            </span>
                          </td>
                          <td className="p-3">{log.touchdown_g ? `${log.touchdown_g} G` : `${log.max_g_force} G`}</td>
                          <td className={`p-3 text-right font-bold ${log.net_profit_usd >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {formatEuro(log.net_profit_usd)}
                          </td>
                        </tr>
                      ))}
                      {flightHistory.length === 0 && (
                        <tr>
                          <td colSpan={9} className="p-8 text-center text-slate-500">
                            Nessun volo registrato finora. Completa il tuo primo volo con SkyOps XP!
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {logbookSubTab === 'tours' && (
              <div className="space-y-6">
                {/* Create Tour Bar + Tour Pills */}
                <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-4">
                  <div className="flex flex-wrap items-center gap-3 font-mono text-xs">
                    <input
                      type="text"
                      placeholder="Nome nuovo Tour (es. IVAO World Tour 2026)"
                      value={newTourName}
                      onChange={(e) => setNewTourName(e.target.value)}
                      className="flex-1 min-w-[220px] bg-slate-900 border border-slate-700 px-3 py-2 rounded-lg text-white focus:outline-none focus:border-amber-400"
                    />
                    <input
                      type="text"
                      placeholder="Descrizione opzionale (es. Giro del mondo in SF50)"
                      value={newTourDesc}
                      onChange={(e) => setNewTourDesc(e.target.value)}
                      className="flex-1 min-w-[220px] bg-slate-900 border border-slate-700 px-3 py-2 rounded-lg text-slate-200 focus:outline-none focus:border-amber-400"
                    />
                    <button
                      type="button"
                      onClick={() => handleCreateTour()}
                      className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold transition flex items-center gap-1.5"
                    >
                      <Plus size={14} /> Crea Tour
                    </button>
                  </div>

                  {toursList.length > 0 && (
                    <div className="flex flex-wrap gap-2 font-mono text-xs pt-2 border-t border-slate-800">
                      {toursList.map((tr) => {
                        const active = selectedTourId === tr.id;
                        return (
                          <button
                            key={tr.id}
                            onClick={() => {
                              setSelectedTourId(tr.id);
                              fetchTourDetail(tr.id);
                            }}
                            className={`px-3 py-1.5 rounded-lg border transition flex items-center gap-2 ${
                              active
                                ? 'bg-amber-500/20 border-amber-400 text-amber-300 font-bold'
                                : 'bg-slate-900 border-slate-700 text-slate-300 hover:border-slate-500'
                            }`}
                          >
                            <span>🗺️ {tr.name}</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300">
                              {tr.legs_count} tappe
                            </span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                              tr.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-cyan-500/15 text-cyan-300'
                            }`}>
                              {tr.status}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>

                {selectedTourDetail ? (() => {
                  const legs = selectedTourDetail.legs || [];
                  const stats = selectedTourDetail.stats || {};
                  const tourObj = selectedTourDetail.tour;

                  // Compute bounding box for automatic zoom on SVG map (equirectangular 1000x480)
                  const projX = (lon) => ((lon + 180) / 360) * 1000;
                  const projY = (lat) => ((90 - lat) / 180) * 480;
                  let minX = 0, maxX = 1000, minY = 0, maxY = 480;
                  if (legs.length > 0) {
                    const xs = legs.flatMap(l => [projX(l.origin_lon), projX(l.destination_lon)]);
                    const ys = legs.flatMap(l => [projY(l.origin_lat), projY(l.destination_lat)]);
                    const rawMinX = Math.min(...xs), rawMaxX = Math.max(...xs);
                    const rawMinY = Math.min(...ys), rawMaxY = Math.max(...ys);
                    const padX = Math.max(45, (rawMaxX - rawMinX) * 0.22);
                    const padY = Math.max(30, (rawMaxY - rawMinY) * 0.25);
                    minX = Math.max(0, rawMinX - padX);
                    maxX = Math.min(1000, rawMaxX + padX);
                    minY = Math.max(0, rawMinY - padY);
                    maxY = Math.min(480, rawMaxY + padY);
                    if ((maxX - minX) / (maxY - minY) < 1.8) {
                      const cx = (minX + maxX) / 2;
                      const targetW = Math.min(1000, (maxY - minY) * 2.08);
                      minX = Math.max(0, cx - targetW / 2);
                      maxX = Math.min(1000, cx + targetW / 2);
                    }
                  }
                  const vbW = Math.max(80, maxX - minX);
                  const vbH = Math.max(40, maxY - minY);
                  const scaleF = vbW / 1000;

                  // Unique waypoints for markers
                  const wpMap = new Map();
                  legs.forEach((lg) => {
                    if (!wpMap.has(lg.origin_icao)) {
                      wpMap.set(lg.origin_icao, { icao: lg.origin_icao, name: lg.origin_name, x: projX(lg.origin_lon), y: projY(lg.origin_lat), idx: lg.leg_number });
                    }
                    wpMap.set(lg.destination_icao, { icao: lg.destination_icao, name: lg.destination_name, x: projX(lg.destination_lon), y: projY(lg.destination_lat), idx: lg.leg_number + 1 });
                  });
                  const waypoints = Array.from(wpMap.values());

                  return (
                    <div className="space-y-5">
                      {/* Tour Header & KPIs */}
                      <div className="glass-panel p-5 rounded-xl border border-amber-500/30 space-y-4">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div>
                            <h3 className="text-lg font-bold text-white flex items-center gap-2">
                              🗺️ {tourObj.name}
                              <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                                tourObj.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-cyan-500/20 text-cyan-300'
                              }`}>
                                {tourObj.status}
                              </span>
                            </h3>
                            {tourObj.description && (
                              <p className="text-xs text-slate-400 mt-0.5">{tourObj.description}</p>
                            )}
                          </div>
                          <div className="flex items-center gap-2 font-mono text-xs">
                            <button
                              onClick={() => handleToggleTourStatus(tourObj)}
                              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-300 border border-emerald-500/30 transition"
                            >
                              {tourObj.status === 'ACTIVE' ? '✓ Segna Completato' : '↺ Riapri Tour'}
                            </button>
                            <button
                              onClick={() => handleDeleteTour(tourObj.id)}
                              className="px-3 py-1.5 rounded-lg bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 border border-rose-500/30 transition"
                            >
                              Elimina Tour
                            </button>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-6 gap-3 font-mono text-xs">
                          <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
                            <div className="text-slate-400">Tappe Volate</div>
                            <div className="text-lg font-bold text-white">{stats.legs_count || 0}</div>
                          </div>
                          <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
                            <div className="text-slate-400">Distanza Totale</div>
                            <div className="text-lg font-bold text-cyan-300">{stats.total_nm || 0} NM</div>
                          </div>
                          <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
                            <div className="text-slate-400">Ore di Volo</div>
                            <div className="text-lg font-bold text-white">{stats.total_hours || 0} h</div>
                          </div>
                          <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
                            <div className="text-slate-400">Fuel Bruciato</div>
                            <div className="text-lg font-bold text-purple-300">{stats.total_fuel_kg || 0} kg</div>
                          </div>
                          <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
                            <div className="text-slate-400">Media Touchdown</div>
                            <div className="text-lg font-bold text-amber-300">{stats.avg_touchdown_fpm ? `-${stats.avg_touchdown_fpm} fpm` : 'N/D'}</div>
                          </div>
                          <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
                            <div className="text-slate-400">Bilancio Tour</div>
                            <div className={`text-lg font-bold ${(stats.total_net_profit_eur || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                              {formatEuro(stats.total_net_profit_eur || 0)}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Interactive SVG Route Map */}
                      <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-2">
                        <div className="flex justify-between items-center font-mono text-xs text-slate-400">
                          <span className="font-bold text-cyan-300">🛰️ Mappa Tracciato Tappe</span>
                          <span>{legs.length > 0 ? `${legs[0].origin_icao} ➔ ... ➔ ${legs[legs.length - 1].destination_icao}` : 'Nessuna tappa ancora completata'}</span>
                        </div>
                        <div className="bg-slate-950 rounded-xl border border-slate-800 overflow-hidden">
                          <svg viewBox={`${minX} ${minY} ${vbW} ${vbH}`} className="w-full h-72 select-none">
                            {/* Lat/Lon Graticule */}
                            {[-60, -30, 0, 30, 60].map((lat) => (
                              <line key={`lat-${lat}`} x1={0} y1={projY(lat)} x2={1000} y2={projY(lat)} stroke="#1e293b" strokeWidth={0.7 * scaleF} strokeDasharray={`${3 * scaleF},${3 * scaleF}`} />
                            ))}
                            {[-150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150].map((lon) => (
                              <line key={`lon-${lon}`} x1={projX(lon)} y1={0} x2={projX(lon)} y2={480} stroke="#1e293b" strokeWidth={0.7 * scaleF} strokeDasharray={`${3 * scaleF},${3 * scaleF}`} />
                            ))}
                            {/* Flight Route Legs */}
                            {legs.map((lg) => {
                              const x1 = projX(lg.origin_lon), y1 = projY(lg.origin_lat);
                              const x2 = projX(lg.destination_lon), y2 = projY(lg.destination_lat);
                              return (
                                <g key={lg.flight_log_id}>
                                  <line
                                    x1={x1} y1={y1} x2={x2} y2={y2}
                                    stroke="#38bdf8"
                                    strokeWidth={2.4 * scaleF}
                                    strokeLinecap="round"
                                    opacity="0.88"
                                  />
                                </g>
                              );
                            })}
                            {/* Waypoints */}
                            {waypoints.map((wp, i) => (
                              <g key={`${wp.icao}-${i}`}>
                                <circle
                                  cx={wp.x}
                                  cy={wp.y}
                                  r={4.5 * scaleF}
                                  fill={i === waypoints.length - 1 ? '#10b981' : '#f59e0b'}
                                  stroke="#0f172a"
                                  strokeWidth={1.5 * scaleF}
                                />
                                <text
                                  x={wp.x + 6 * scaleF}
                                  y={wp.y - 4 * scaleF}
                                  fill="#e2e8f0"
                                  fontSize={10 * scaleF}
                                  fontFamily="monospace"
                                  fontWeight="bold"
                                >
                                  {wp.icao}
                                </text>
                              </g>
                            ))}
                          </svg>
                        </div>
                      </div>

                      {/* Chronological Legs Table */}
                      <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
                        <div className="overflow-x-auto">
                          <table className="w-full text-left font-mono text-xs">
                            <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800">
                              <tr>
                                <th className="p-3">Tappa</th>
                                <th className="p-3">Volo</th>
                                <th className="p-3">Tratta</th>
                                <th className="p-3">Distanza</th>
                                <th className="p-3">Durata</th>
                                <th className="p-3">Touchdown</th>
                                <th className="p-3 text-right">Netto (€)</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/60 text-slate-200">
                              {legs.map((lg) => (
                                <tr key={lg.flight_log_id} className="hover:bg-slate-800/30">
                                  <td className="p-3 font-bold text-amber-300">#{lg.leg_number}</td>
                                  <td className="p-3 text-cyan-400 font-bold">{lg.flight_number}</td>
                                  <td className="p-3 font-bold">
                                    {lg.origin_icao} ➔ {lg.destination_icao}
                                    <span className="text-[10px] text-slate-400 block font-sans">
                                      {lg.origin_name} ➔ {lg.destination_name}
                                    </span>
                                  </td>
                                  <td className="p-3">{lg.distance_nm} NM</td>
                                  <td className="p-3">{lg.duration_min} min</td>
                                  <td className="p-3">
                                    {lg.touchdown_fpm !== null ? `${lg.touchdown_fpm} fpm (${lg.touchdown_rating})` : 'N/D'}
                                  </td>
                                  <td className={`p-3 text-right font-bold ${lg.net_profit_eur >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                    {formatEuro(lg.net_profit_eur)}
                                  </td>
                                </tr>
                              ))}
                              {legs.length === 0 && (
                                <tr>
                                  <td colSpan={7} className="p-6 text-center text-slate-500">
                                    Nessuna tappa completata in questo Tour. Seleziona "{tourObj.name}" in Pianifica Volo o in Plancia HUD per registrare le prossime tratte!
                                  </td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  );
                })() : (
                  <div className="glass-panel p-10 rounded-xl border border-dashed border-slate-800 text-center text-slate-400 font-mono text-sm">
                    Crea il tuo primo Tour (es. "IVAO World Tour") qui sopra per tracciare tappe, mappa rotta e statistiche cumulative.
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        </main>
      </div>
    </div>
  );
}
