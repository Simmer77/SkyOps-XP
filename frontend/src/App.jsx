import React, { useState, useEffect } from 'react';
import { 
  Plane, Gauge, Briefcase, Wrench, BookOpen, Radio, 
  Fuel, AlertTriangle, CheckCircle, ArrowRight, RefreshCw, 
  MapPin, Zap, ShieldAlert, Award, Plus, Trash2, Key, Info, HelpCircle, Clock
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('flight'); // 'flight', 'fleet', 'rental', 'jobs', 'simbrief', 'maintenance', 'economics', 'logbook'
  const [systemStatus, setSystemStatus] = useState(null);
  const [fleet, setFleet] = useState([]);
  const [rentalCatalog, setRentalCatalog] = useState([]);
  const [selectedAircraft, setSelectedAircraft] = useState(null);
  const [activeFlight, setActiveFlight] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [simbriefOfp, setSimbriefOfp] = useState(null);
  const [simbriefInput, setSimbriefInput] = useState('');
  const [financialGuide, setFinancialGuide] = useState(null);
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
    fuel_quantity_kg: 450
  });

  // Modal State for renting
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
  const [flightPhase, setFlightPhase] = useState('OFFLINE');

  const showNotice = (msg, type = 'info') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const formatEuro = (val) => {
    if (val === undefined || val === null || isNaN(val)) return '€ 0,00';
    return '€ ' + Number(val).toLocaleString('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  // 1. Initial Load & Fetchers
  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/system/status');
      if (res.ok) {
        const data = await res.json();
        setSystemStatus(data);
        if (data.company?.simbrief_username && !simbriefInput) {
          setSimbriefInput(data.company.simbrief_username);
        }
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
        if (data.length > 0 && !selectedAircraft) {
          setSelectedAircraft(data[0]);
        }
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

  const fetchActiveFlight = async () => {
    try {
      const res = await fetch('/api/flights/active');
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

  useEffect(() => {
    fetchStatus();
    fetchFleet();
    fetchRentalCatalog();
    fetchFinancialGuide();
    fetchActiveFlight();
    fetchHistory();
  }, []);

  useEffect(() => {
    if (selectedAircraft) {
      fetchJobs(selectedAircraft.current_icao);
    }
  }, [selectedAircraft]);

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
          hourly_lease_rate: 0.0
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
          fuel_quantity_kg: 450
        });
        fetchFleet();
      } else {
        showNotice(data.detail, 'error');
      }
    } catch (e) {
      showNotice('Errore durante il salvataggio dell aeromobile', 'error');
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
    if (!simbriefInput) {
      showNotice('Inserisci il tuo username o Pilot ID SimBrief', 'error');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`/api/simbrief/latest?username=${encodeURIComponent(simbriefInput)}`);
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
    if (!selectedAircraft || !simbriefOfp) return;
    setLoading(true);
    try {
      const res = await fetch('/api/simbrief/import_flight', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: simbriefInput,
          aircraft_id: selectedAircraft.id
        })
      });
      const data = await res.json();
      if (res.ok) {
        showNotice(data.message, 'success');
        fetchFleet();
        fetchJobs(selectedAircraft.current_icao);
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

  // Flight lifecycle
  const handleStartFlight = async (jobId = null) => {
    if (!selectedAircraft) return;
    try {
      const res = await fetch('/api/flights/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          aircraft_id: selectedAircraft.id,
          job_id: jobId
        })
      });
      const data = await res.json();
      if (res.ok) {
        showNotice(`Volo avviato per ${selectedAircraft.tail_number}!`, 'success');
        fetchActiveFlight();
      } else {
        showNotice(data.detail, 'error');
      }
    } catch (e) {
      showNotice('Errore avvio volo', 'error');
    }
  };

  const handleFinalizeFlight = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/flights/finalize', { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        showNotice(`Volo completato! Utile netto: ${formatEuro(data.summary.financials.net_profit)}`, 'success');
        fetchStatus();
        fetchFleet();
        fetchActiveFlight();
        fetchHistory();
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

  return (
    <div className="min-h-screen bg-aviation-dark flex flex-col font-sans">
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
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
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
                {systemStatus?.company?.name || 'AeroSky Executive Ops'}
              </p>
            </div>
          </div>

          {/* Quick Metrics Bar in € EURO */}
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded-lg">
              <span className="text-emerald-400 font-bold text-base">€</span>
              <div>
                <div className="text-[10px] text-slate-400 uppercase font-mono">Capitale Aziendale</div>
                <div className="text-sm font-bold font-mono text-emerald-400">
                  {formatEuro(systemStatus?.company?.cash_balance ?? 175000)}
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
              xpConnected 
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
            }`}>
              <span className={`w-2 h-2 rounded-full ${xpConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
              {xpConnected ? 'XP12 CONNESSO (UDP 49000)' : 'XP12 DISCONNESSO'}
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-7xl mx-auto flex gap-1 mt-3 overflow-x-auto border-t border-slate-800/60 pt-2 text-sm">
          {[
            { id: 'flight', label: 'Volo Attivo & HUD', icon: Gauge },
            { id: 'fleet', label: 'Hangar (Proprietà)', icon: Plane },
            { id: 'rental', label: 'Mercato Noleggio', icon: Key },
            { id: 'jobs', label: 'Incarichi & Contratti', icon: Briefcase },
            { id: 'simbrief', label: 'SimBrief Dispatch', icon: Radio },
            { id: 'maintenance', label: 'Officina & Usura', icon: Wrench },
            { id: 'economics', label: 'Legenda Costi & Ricavi', icon: HelpCircle },
            { id: 'logbook', label: 'Registro Voli', icon: BookOpen },
          ].map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-medium transition-all whitespace-nowrap ${
                  active 
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <Icon size={15} />
                {tab.label}
              </button>
            );
          })}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        
        {/* TAB 1: FLIGHT DECK & HUD */}
        {activeTab === 'flight' && (
          <div className="space-y-6">
            {/* Mission Overview Banner */}
            <div className="glass-panel p-5 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold uppercase ${
                    flightPhase === 'ENROUTE' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 animate-pulse' :
                    flightPhase === 'TOUCHDOWN' || flightPhase === 'TAXI_IN' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
                    'bg-slate-800 text-slate-300'
                  }`}>
                    FASE: {flightPhase}
                  </span>
                  {selectedAircraft && (
                    <span className="text-sm font-semibold text-white">
                      {selectedAircraft.tail_number} ({selectedAircraft.name})
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-1 font-mono">
                  Posizione attuale: {selectedAircraft?.current_icao} | Carburante a bordo: {liveTelemetry.fuel_total_kg > 0 ? liveTelemetry.fuel_total_kg.toFixed(0) : selectedAircraft?.fuel_quantity_kg?.toFixed(0)} kg
                </p>
              </div>

              <div className="flex items-center gap-3">
                {flightPhase === 'OFFLINE' ? (
                  <button
                    onClick={() => handleStartFlight()}
                    disabled={!selectedAircraft}
                    className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold px-4 py-2 rounded-lg shadow transition"
                  >
                    <Zap size={16} /> Avvia Monitoraggio Volo
                  </button>
                ) : (
                  <button
                    onClick={handleFinalizeFlight}
                    disabled={loading}
                    className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-4 py-2 rounded-lg shadow transition"
                  >
                    <CheckCircle size={16} /> Concludi Volo & Incassa Ricavi
                  </button>
                )}
              </div>
            </div>

            {/* Glass Cockpit Gauges Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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

        {/* TAB 2: HANGAR & OWNED FLEET */}
        {activeTab === 'fleet' && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white">Hangar Personale (Aerei di Proprietà)</h2>
                <p className="text-xs text-slate-400 font-mono">
                  Inserisci i tuoi aerei personalizzati, gestisci il parcheggio e rifornisci i serbatoi prima del volo.
                </p>
              </div>

              <button
                onClick={() => setShowAddModal(true)}
                className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold font-mono text-xs px-4 py-2 rounded-lg shadow transition"
              >
                <Plus size={16} /> Aggiungi Aeromobile di Proprietà
              </button>
            </div>

            {/* Add Aircraft Modal */}
            {showAddModal && (
              <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
                <div className="glass-panel p-6 rounded-2xl border border-cyan-500/40 max-w-lg w-full space-y-4">
                  <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <Plus size={18} className="text-cyan-400" /> Aggiungi Aeromobile all Hangar
                    </h3>
                    <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-white">✕</button>
                  </div>

                  <form onSubmit={handleAddAircraft} className="space-y-3 font-mono text-xs">
                    <div>
                      <label className="text-slate-400 block mb-1">Marche / Registrazione (Tail Number)*</label>
                      <input
                        type="text"
                        placeholder="es. I-SF50, N172SP, I-ALPA"
                        required
                        value={newAircraft.tail_number}
                        onChange={(e) => setNewAircraft({...newAircraft, tail_number: e.target.value.toUpperCase()})}
                        className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    <div>
                      <label className="text-slate-400 block mb-1">Nome Modello & Versione*</label>
                      <input
                        type="text"
                        placeholder="es. Cirrus Vision SF50 G2, Phenom 300, Cessna 172"
                        required
                        value={newAircraft.name}
                        onChange={(e) => setNewAircraft({...newAircraft, name: e.target.value})}
                        className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-slate-400 block mb-1">Tipo ICAO (es. SF50, B738, C172)</label>
                        <input
                          type="text"
                          placeholder="es. SF50"
                          value={newAircraft.aircraft_type}
                          onChange={(e) => setNewAircraft({...newAircraft, aircraft_type: e.target.value.toUpperCase()})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                        />
                      </div>
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
                    </div>

                    <div className="grid grid-cols-3 gap-3">
                      <div>
                        <label className="text-slate-400 block mb-1">Aeroporto ICAO</label>
                        <input
                          type="text"
                          placeholder="es. LIRN"
                          required
                          value={newAircraft.current_icao}
                          onChange={(e) => setNewAircraft({...newAircraft, current_icao: e.target.value.toUpperCase()})}
                          className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                        />
                      </div>
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

            {/* Fleet Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {fleet.filter(ac => ac.ownership === 'OWNED').map((ac) => {
                const isSelected = selectedAircraft?.id === ac.id;
                return (
                  <div 
                    key={ac.id} 
                    className={`glass-panel p-5 rounded-xl border transition-all ${
                      isSelected ? 'border-cyan-500/80 ring-1 ring-cyan-500/50' : 'border-slate-800'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-lg font-black font-mono text-cyan-400">{ac.tail_number}</span>
                          <span className="text-xs px-2 py-0.5 rounded font-mono bg-slate-800 text-slate-300">
                            {ac.category}
                          </span>
                          <span className="text-xs px-2 py-0.5 rounded font-mono bg-emerald-500/20 text-emerald-300">
                            DI PROPRIETÀ
                          </span>
                        </div>
                        <h3 className="text-sm font-semibold text-white mt-1">{ac.name}</h3>
                        <p className="text-xs text-slate-400 font-mono mt-0.5 flex items-center gap-1">
                          <MapPin size={12} className="text-rose-400" /> Stazionato a: <span className="text-white font-bold">{ac.current_icao}</span>
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setSelectedAircraft(ac)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-semibold font-mono ${
                            isSelected ? 'bg-cyan-500 text-black' : 'bg-slate-800 hover:bg-slate-700 text-slate-200'
                          }`}
                        >
                          {isSelected ? 'AEREO ATTIVO' : 'SELEZIONA'}
                        </button>
                        <button
                          onClick={() => handleDeleteAircraft(ac)}
                          title="Elimina dall hangar"
                          className="p-1.5 rounded bg-slate-800 hover:bg-rose-900/60 text-slate-400 hover:text-rose-300 transition"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </div>

                    {/* Fuel & Hours Progress */}
                    <div className="mt-4 space-y-3 font-mono text-xs">
                      <div>
                        <div className="flex justify-between text-slate-400 mb-1">
                          <span>Carburante Serbatoio: {ac.fuel_quantity_kg.toFixed(0)} / {ac.fuel_capacity_kg.toFixed(0)} kg</span>
                          <span>{((ac.fuel_quantity_kg / ac.fuel_capacity_kg) * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-2">
                          <div 
                            className="bg-purple-500 h-2 rounded-full" 
                            style={{ width: `${Math.min(100, (ac.fuel_quantity_kg / ac.fuel_capacity_kg) * 100)}%` }} 
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-slate-400 pt-2 border-t border-slate-800/80">
                        <div>Ore Cellula: <span className="text-white">{ac.airframe_hours.toFixed(1)} h</span></div>
                        <div>Ore Motore: <span className="text-white">{ac.engine_hours.toFixed(1)} h</span></div>
                        <div>Salute Motore: <span className="text-emerald-400 font-bold">{ac.health_engine_pct.toFixed(0)}%</span></div>
                        <div>Freni & Gomme: <span className="text-cyan-400 font-bold">{ac.health_tires_pct.toFixed(0)}%</span></div>
                      </div>
                    </div>

                    {/* Action buttons */}
                    <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
                      <button
                        onClick={() => handleSyncToXplane(ac.id)}
                        className="flex items-center gap-1.5 text-xs font-mono font-semibold px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/30"
                      >
                        <RefreshCw size={13} /> Sincronizza su XP12
                      </button>

                      <button
                        onClick={async () => {
                          const target = prompt(`Inserisci quantità carburante desiderata in kg (Max ${ac.fuel_capacity_kg} kg):`, ac.fuel_capacity_kg);
                          if (target) {
                            const res = await fetch(`/api/fleet/${ac.id}/refuel`, {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ target_fuel_kg: parseFloat(target) })
                            });
                            const data = await res.json();
                            showNotice(data.message, 'success');
                            fetchStatus();
                            fetchFleet();
                          }
                        }}
                        className="flex items-center gap-1.5 text-xs font-mono font-semibold px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-purple-300 border border-purple-500/30"
                      >
                        <Fuel size={13} /> Rifornisci
                      </button>
                    </div>
                  </div>
                );
              })}

              {fleet.filter(ac => ac.ownership === 'OWNED').length === 0 && (
                <div className="col-span-2 text-center py-12 glass-panel rounded-xl border border-dashed border-slate-800">
                  <p className="text-slate-400 font-mono text-sm">Non hai ancora inserito nessun aereo di proprietà nel tuo hangar.</p>
                  <button
                    onClick={() => setShowAddModal(true)}
                    className="mt-3 text-cyan-400 hover:underline font-mono text-xs flex items-center gap-1 mx-auto"
                  >
                    <Plus size={14} /> Clicca qui per aggiungere il tuo primo aereo di proprietà
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: RENTAL MARKET (NOLEGGIO) */}
        {activeTab === 'rental' && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white">Mercato del Noleggio & Charter (Lease Market)</h2>
                <p className="text-xs text-slate-400 font-mono">
                  Hai voglia di volare con un aereo diverso senza doverlo acquistare? Noleggialo on-demand pagando solo le ore di volo effettive.
                </p>
              </div>
            </div>

            {/* Currently Rented Aircraft in Fleet */}
            {fleet.filter(ac => ac.ownership === 'LEASED').length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-amber-300 font-mono uppercase">I Tuoi Noleggi Attivi</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {fleet.filter(ac => ac.ownership === 'LEASED').map((ac) => {
                    const isSelected = selectedAircraft?.id === ac.id;
                    return (
                      <div key={ac.id} className={`glass-panel p-4 rounded-xl border ${isSelected ? 'border-amber-500 ring-1 ring-amber-500' : 'border-amber-900/40 bg-amber-950/10'}`}>
                        <div className="flex justify-between items-start">
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

            {/* Rental Catalog */}
            <h3 className="text-sm font-bold text-slate-300 font-mono uppercase mt-6">Catalogo Flotta a Noleggio Disponibile</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {rentalCatalog.map((item) => (
                <div key={item.id} className="glass-panel p-5 rounded-xl border border-slate-800 flex flex-col justify-between hover:border-cyan-500/40 transition">
                  <div>
                    <div className="flex justify-between items-start">
                      <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-cyan-300">
                        {item.category}
                      </span>
                      <div className="text-right">
                        <div className="text-base font-bold font-mono text-emerald-400">{formatEuro(item.hourly_rate_eur)}</div>
                        <div className="text-[10px] text-slate-400 font-mono">all ora di volo</div>
                      </div>
                    </div>

                    <h4 className="text-base font-bold text-white mt-2">{item.name}</h4>
                    <p className="text-xs text-slate-400 font-mono mt-2 leading-relaxed">{item.description}</p>

                    <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-slate-800/80 font-mono text-xs text-slate-400">
                      <div>Velocità Crociera: <span className="text-white">{item.cruising_speed_kts} kts</span></div>
                      <div>Autonomia: <span className="text-white">{item.range_nm} NM</span></div>
                      <div className="col-span-2">Serbatoio Max: <span className="text-purple-300">{item.fuel_capacity_kg} kg</span></div>
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      setSelectedRentalTemplate(item);
                      setRentCustomTail(`I-RNT${Math.floor(10 + Math.random() * 89)}`);
                      setRentPickupIcao(selectedAircraft?.current_icao || 'LIRN');
                      setShowRentModal(true);
                    }}
                    className="mt-5 w-full bg-cyan-600 hover:bg-cyan-500 text-white font-mono font-semibold text-xs py-2 rounded-lg transition flex items-center justify-center gap-2"
                  >
                    <Key size={14} /> Noleggia per questo Volo
                  </button>
                </div>
              ))}
            </div>

            {/* Rent Confirmation Modal */}
            {showRentModal && selectedRentalTemplate && (
              <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
                <div className="glass-panel p-6 rounded-2xl border border-cyan-500/40 max-w-md w-full space-y-4">
                  <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <Key size={18} className="text-cyan-400" /> Noleggia {selectedRentalTemplate.name}
                    </h3>
                    <button onClick={() => setShowRentModal(false)} className="text-slate-400 hover:text-white">✕</button>
                  </div>

                  <div className="space-y-3 font-mono text-xs">
                    <div className="bg-slate-900/80 p-3 rounded border border-slate-800">
                      <div className="text-slate-400">Tariffa Noleggio Orario (Dry Lease):</div>
                      <div className="text-lg font-bold text-emerald-400">{formatEuro(selectedRentalTemplate.hourly_rate_eur)} / ora di volo</div>
                      <div className="text-[10px] text-slate-500 mt-1">L importo verrà addebitato proporzionalmente alla durata effettiva dei voli effettuati.</div>
                    </div>

                    <div>
                      <label className="text-slate-400 block mb-1">Marche Personalizzate (facoltativo)</label>
                      <input
                        type="text"
                        value={rentCustomTail}
                        onChange={(e) => setRentCustomTail(e.target.value.toUpperCase())}
                        className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    <div>
                      <label className="text-slate-400 block mb-1">Aeroporto di Ritiro (ICAO)</label>
                      <input
                        type="text"
                        value={rentPickupIcao}
                        onChange={(e) => setRentPickupIcao(e.target.value.toUpperCase())}
                        className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-white focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                      <button
                        type="button"
                        onClick={() => setShowRentModal(false)}
                        className="px-4 py-2 rounded bg-slate-800 text-slate-300 hover:bg-slate-700"
                      >
                        Annulla
                      </button>
                      <button
                        type="button"
                        onClick={handleRentAircraft}
                        disabled={loading}
                        className="px-4 py-2 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold"
                      >
                        Conferma Noleggio
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

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

        {/* TAB 5: SIMBRIEF DISPATCH */}
        {activeTab === 'simbrief' && (
          <div className="space-y-6">
            <div className="glass-panel p-6 rounded-xl border border-slate-800">
              <h2 className="text-xl font-bold text-white">Sincronizzazione SimBrief OFP</h2>
              <p className="text-xs text-slate-400 font-mono mt-1">
                Scarica l'ultimo piano operativo generato su SimBrief per il tuo aeromobile e importalo direttamente come volo programmato.
              </p>

              <div className="flex flex-wrap gap-3 mt-4">
                <input
                  type="text"
                  placeholder="SimBrief Username o Pilot ID (es. simmer77)"
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
                    <div className="text-slate-400">Carico Utile (Payload)</div>
                    <div className="text-sm font-bold text-emerald-300 mt-0.5">{simbriefOfp.payload_kg} kg</div>
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
                    disabled={loading}
                    className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold font-mono text-sm px-5 py-2.5 rounded-lg shadow transition"
                  >
                    <CheckCircle size={16} /> Importa come Contratto e Prepara Aereo
                  </button>
                </div>
              </div>
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

        {/* TAB 7: FINANCIAL GUIDE & RULES (LEGENDA COSTI E RICAVI) */}
        {activeTab === 'economics' && financialGuide && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Info size={22} className="text-cyan-400" /> Legenda Economica & Modello Operativo
              </h2>
              <p className="text-xs text-slate-400 font-mono mt-1">
                Trasparenza totale: ecco esattamente come vengono calcolati i ricavi, i consumi, le tasse aeroportuali e l usura nella simulazione.
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
                <div className="font-bold text-white mb-2">{financialGuide.landing_fee_rules.formula}</div>
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
          </div>
        )}

        {/* TAB 8: LOGBOOK */}
        {activeTab === 'logbook' && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-white">Registro Storico Voli</h2>
            
            <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
              <table className="w-full text-left font-mono text-xs">
                <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-3">Data</th>
                    <th className="p-3">Volo</th>
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
                      <td colSpan={8} className="p-8 text-center text-slate-500">
                        Nessun volo registrato finora. Completa il tuo primo volo con SkyOps XP!
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
