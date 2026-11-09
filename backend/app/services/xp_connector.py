import socket
import struct
import asyncio
import logging
from typing import Dict, Any, Callable, Optional, List

logger = logging.getLogger("SkyOps.XPConnector")

# Dataref IDs for RREF subscriptions
DATAREF_MAP = {
    1: "sim/flightmodel/position/latitude",
    2: "sim/flightmodel/position/longitude",
    3: "sim/flightmodel/position/elevation",
    4: "sim/flightmodel/position/groundspeed",        # m/s
    5: "sim/flightmodel/position/indicated_airspeed",  # KIAS
    6: "sim/flightmodel/position/vh_ind_fpm",         # FPM
    7: "sim/flightmodel2/misc/gforce_normal",         # Gs
    8: "sim/flightmodel/failures/onground_any",       # 1 = on ground, 0 = airborne
    9: "sim/flightmodel/weight/m_fuel_total",         # kg
    10: "sim/flightmodel/weight/m_total",             # kg
    11: "sim/cockpit2/controls/parking_brake_ratio",  # 0 to 1
    12: "sim/flightmodel/engine/POINT_running[0]",    # 1 if engine 1 running
    13: "sim/cockpit2/controls/left_brake_ratio",     # 0 to 1
    14: "sim/cockpit2/controls/right_brake_ratio",    # 0 to 1
    15: "sim/cockpit2/engine/indicators/EGT_deg_C[0]",
}

ID_TO_NAME = DATAREF_MAP
NAME_TO_ID = {v: k for k, v in DATAREF_MAP.items()}

class XPConnector:
    """
    Direct asynchronous UDP connector for X-Plane 12.
    Supports receiving telemetry (RREF) and injecting values/failures (DREF, CMND).
    """
    def __init__(self, xp_ip: str = "127.0.0.1", xp_port: int = 49000, listen_port: int = 49005):
        self.xp_ip = xp_ip
        self.xp_port = xp_port
        self.listen_port = listen_port
        self.sock: Optional[socket.socket] = None
        self.is_running = False
        self.is_connected = False
        self.last_packet_time = 0.0
        
        # Live state cache
        self.telemetry: Dict[str, float] = {
            "latitude": 0.0,
            "longitude": 0.0,
            "elevation_m": 0.0,
            "groundspeed_kts": 0.0,
            "ias_kts": 0.0,
            "vs_fpm": 0.0,
            "g_force": 1.0,
            "on_ground": 1.0,
            "fuel_total_kg": 0.0,
            "total_weight_kg": 0.0,
            "parking_brake": 1.0,
            "engine_running": 0.0,
            "brake_left": 0.0,
            "brake_right": 0.0,
            "egt_c": 0.0,
        }
        
        self.subscribers: List[Callable[[Dict[str, float]], Any]] = []

    def start(self):
        """Starts socket and background receiver task"""
        if self.is_running:
            return
            
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setblocking(False)
            self.sock.bind(("0.0.0.0", self.listen_port))
            self.is_running = True
            logger.info(f"XPConnector listening on UDP port {self.listen_port}, sending to {self.xp_ip}:{self.xp_port}")
        except Exception as e:
            logger.error(f"Failed to bind UDP socket: {e}")
            self.is_running = False

    def stop(self):
        self.is_running = False
        if self.sock:
            try:
                # Cancel subscriptions by sending freq 0
                for dref_id, dref_name in DATAREF_MAP.items():
                    self._send_rref(dref_name, dref_id, 0)
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        logger.info("XPConnector stopped.")

    def subscribe_all(self, freq_hz: int = 5):
        """Subscribe to all necessary telemetry datarefs at freq_hz frequency"""
        for dref_id, dref_name in DATAREF_MAP.items():
            self._send_rref(dref_name, dref_id, freq_hz)
        logger.info(f"Requested {len(DATAREF_MAP)} datarefs at {freq_hz} Hz from X-Plane")

    def _send_rref(self, dref_name: str, dref_id: int, freq_hz: int):
        """Builds and sends RREF packet to X-Plane"""
        if not self.sock:
            return
        # RREF struct: 4 chars 'RREF' + \x00 + 4 bytes int freq + 4 bytes int id + 400 chars name padded with nulls
        header = b'RREF\x00'
        body = struct.pack('<ii', freq_hz, dref_id)
        name_bytes = dref_name.encode('utf-8').ljust(400, b'\x00')
        packet = header + body + name_bytes
        try:
            self.sock.sendto(packet, (self.xp_ip, self.xp_port))
        except Exception as e:
            logger.debug(f"Error sending RREF for {dref_name}: {e}")

    def send_dref(self, dref_name: str, value: float):
        """
        Sets a Dataref value in X-Plane (e.g., fuel amount, payload, failure state).
        DREF packet: 4 chars 'DREF' + \x00 + 4 bytes float val + 500 chars name padded
        """
        if not self.sock:
            return False
        header = b'DREF\x00'
        body = struct.pack('<f', float(value))
        name_bytes = dref_name.encode('utf-8').ljust(500, b'\x00')
        packet = header + body + name_bytes
        try:
            self.sock.sendto(packet, (self.xp_ip, self.xp_port))
            logger.info(f"Injected DREF: {dref_name} = {value}")
            return True
        except Exception as e:
            logger.error(f"Error setting DREF {dref_name}: {e}")
            return False

    def inject_failure(self, failure_dref: str, mode: int = 6):
        """
        Triggers an X-Plane failure immediately.
        mode 6 = immediate failure in X-Plane failure datarefs.
        """
        logger.warning(f"🚨 INJECTING FAILURE INTO X-PLANE: {failure_dref} (mode: {mode})")
        return self.send_dref(failure_dref, float(mode))

    def set_fuel_kg(self, fuel_kg: float):
        """Sets aircraft total fuel weight in kg"""
        return self.send_dref("sim/flightmodel/weight/m_fuel_total", float(fuel_kg))

    def read_incoming(self):
        """Non-blocking read of all available packets in socket buffer"""
        if not self.sock or not self.is_running:
            return
        
        loop = asyncio.get_event_loop()
        now = loop.time()
        
        while True:
            try:
                data, addr = self.sock.recvfrom(2048)
                if not data:
                    break
                
                self.last_packet_time = now
                self.is_connected = True
                
                if data.startswith(b'RREF'):
                    # Payload begins after 5 bytes (RREF\x00)
                    offset = 5
                    while offset + 8 <= len(data):
                        dref_id, val = struct.unpack('<if', data[offset:offset+8])
                        offset += 8
                        self._process_dataref_val(dref_id, val)
                        
            except BlockingIOError:
                break
            except Exception as e:
                logger.debug(f"Socket read error: {e}")
                break
                
        # Connection timeout check (no packets for > 4 seconds)
        if self.is_connected and (now - self.last_packet_time > 4.0):
            self.is_connected = False
            logger.info("Lost connection to X-Plane (timeout)")

    def _process_dataref_val(self, dref_id: int, val: float):
        """Updates internal telemetry dictionary"""
        if dref_id == 1:
            self.telemetry["latitude"] = val
        elif dref_id == 2:
            self.telemetry["longitude"] = val
        elif dref_id == 3:
            self.telemetry["elevation_m"] = val
        elif dref_id == 4:
            self.telemetry["groundspeed_kts"] = val * 1.94384  # m/s to kts
        elif dref_id == 5:
            self.telemetry["ias_kts"] = val
        elif dref_id == 6:
            self.telemetry["vs_fpm"] = val
        elif dref_id == 7:
            self.telemetry["g_force"] = val
        elif dref_id == 8:
            self.telemetry["on_ground"] = val
        elif dref_id == 9:
            self.telemetry["fuel_total_kg"] = val
        elif dref_id == 10:
            self.telemetry["total_weight_kg"] = val
        elif dref_id == 11:
            self.telemetry["parking_brake"] = val
        elif dref_id == 12:
            self.telemetry["engine_running"] = val
        elif dref_id == 13:
            self.telemetry["brake_left"] = val
        elif dref_id == 14:
            self.telemetry["brake_right"] = val
        elif dref_id == 15:
            self.telemetry["egt_c"] = val

# Singleton instance
xp_connector = XPConnector()
