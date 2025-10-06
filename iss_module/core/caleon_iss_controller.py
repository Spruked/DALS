"""
CALEON ISS Controller - Enhanced Timestamping System
====================================================
Microsecond precision ISS implementation for CALEON's consciousness cycles.
Implements immutable_core.txt specifications for cycle timestamping.

Key Features:
- Microsecond precision timestamps for all vault operations
- Cycle start/end logging with zero drift expectation
- A priori and A posteriori vault verdict tracking
- Harmonizer ping confirmation logging
- Complete audit trail for CALEON's consciousness flow
"""

import time
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading
from dataclasses import dataclass, asdict

from .utils import (
    get_stardate,
    current_timecodes,
    ensure_folder,
)


@dataclass
class CaleonCycleTimestamp:
    """Microsecond precision timestamp for CALEON consciousness cycles"""
    cycle_id: str
    cycle_type: str  # 'A' or 'B' per immutable_core.txt
    timestamp_microseconds: float
    stardate: float
    operation: str  # 'start', 'end', 'vault_check', 'harmonizer_ping', etc.
    vault_operation: Optional[str] = None
    verdict_status: Optional[str] = None
    sync_token: Optional[str] = None
    drift_ns: Optional[float] = None


class CaleonISSController:
    """
    Enhanced ISS Controller for CALEON Consciousness System
    ======================================================
    
    Implements microsecond precision timestamping as specified in immutable_core.txt:
    - Records start time of every cycle
    - Checks A priori and A posteriori vaults for verdict resolution
    - Tracks harmonizer ping confirmations
    - Stamps end of every cycle
    - Maintains zero drift expectation through drift monitoring
    """
    
    def __init__(self, system_name: str = "CALEON_ISS"):
        self.system_name = system_name
        self.status = "healthy"
        self.cycle_counter = 0
        self.current_cycle_id = None
        self.current_cycle_type = None
        
        # Vault paths
        self.vault_folder = ensure_folder("vaults")
        self.a_priori_vault = Path(self.vault_folder) / "a_priori_vault.jsonl"
        self.a_posteriori_vault = Path(self.vault_folder) / "a_posteriori_vault.jsonl"
        
        # Logging setup
        self.log_folder = ensure_folder("logs")
        self.cycle_log_path = Path(self.log_folder) / "caleon_cycle_timestamps.jsonl"
        self.drift_log_path = Path(self.log_folder) / "caleon_drift_monitoring.jsonl"
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Drift monitoring
        self.baseline_time = time.time_ns()
        self.baseline_stardate = get_stardate()
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"{system_name}")
        
        self.logger.info(f"✅ CALEON ISS Controller initialized - Zero drift baseline established")
    
    def get_microsecond_timestamp(self) -> Dict[str, Any]:
        """Generate microsecond precision timestamp with all CALEON timing data"""
        now_ns = time.time_ns()
        now_dt = datetime.now(timezone.utc)
        stardate = get_stardate()
        
        # Calculate drift from baseline
        expected_time = self.baseline_time + (stardate - self.baseline_stardate) * 86400 * 1e9
        drift_ns = now_ns - expected_time
        
        return {
            'timestamp_microseconds': now_ns / 1000.0,  # Convert to microseconds
            'iso_timestamp': now_dt.isoformat(),
            'stardate': stardate,
            'unix_timestamp_ns': now_ns,
            'drift_ns': drift_ns,
            'anchor_hash': self._generate_cycle_anchor(now_dt, stardate)
        }
    
    def _generate_cycle_anchor(self, dt: datetime, stardate: float) -> str:
        """Generate unique anchor hash for cycle tracking"""
        import hashlib
        anchor_string = f"CALEON-{dt.isoformat()}-{stardate}-{self.cycle_counter}"
        return hashlib.sha256(anchor_string.encode()).hexdigest()[:16]
    
    def start_cycle(self, cycle_type: str) -> str:
        """
        Start a new CALEON consciousness cycle with microsecond timestamping.
        
        Args:
            cycle_type: 'A' or 'B' as specified in immutable_core.txt
            
        Returns:
            cycle_id: Unique identifier for this cycle
        """
        with self._lock:
            self.cycle_counter += 1
            cycle_id = f"CALEON_C{self.cycle_counter:06d}_{cycle_type}"
            self.current_cycle_id = cycle_id
            self.current_cycle_type = cycle_type
            
            timestamp_data = self.get_microsecond_timestamp()
            
            cycle_record = CaleonCycleTimestamp(
                cycle_id=cycle_id,
                cycle_type=cycle_type,
                timestamp_microseconds=timestamp_data['timestamp_microseconds'],
                stardate=timestamp_data['stardate'],
                operation='cycle_start',
                drift_ns=timestamp_data['drift_ns']
            )
            
            self._log_cycle_event(cycle_record)
            
            self.logger.info(f"🔄 CYCLE START [{cycle_type}] - ID: {cycle_id} - "
                           f"Timestamp: {timestamp_data['timestamp_microseconds']:.3f}μs - "
                           f"Drift: {timestamp_data['drift_ns']:.2f}ns")
            
            return cycle_id
    
    def check_vault_verdicts(self, cycle_id: str) -> Dict[str, Any]:
        """
        Check A priori and A posteriori vaults for verdict resolution.
        Implements immutable_core.txt vault scanning requirement.
        """
        timestamp_data = self.get_microsecond_timestamp()
        
        # Check A priori vault
        a_priori_verdict = self._scan_vault(self.a_priori_vault, "a_priori")
        
        # Check A posteriori vault  
        a_posteriori_verdict = self._scan_vault(self.a_posteriori_vault, "a_posteriori")
        
        # Log vault check operation
        vault_check_record = CaleonCycleTimestamp(
            cycle_id=cycle_id,
            cycle_type=self.current_cycle_type,
            timestamp_microseconds=timestamp_data['timestamp_microseconds'],
            stardate=timestamp_data['stardate'],
            operation='vault_check',
            vault_operation=f"a_priori:{a_priori_verdict['status']},a_posteriori:{a_posteriori_verdict['status']}",
            drift_ns=timestamp_data['drift_ns']
        )
        
        self._log_cycle_event(vault_check_record)
        
        verdict_result = {
            'a_priori': a_priori_verdict,
            'a_posteriori': a_posteriori_verdict,
            'has_verdict': a_priori_verdict['found'] or a_posteriori_verdict['found'],
            'timestamp': timestamp_data
        }
        
        self.logger.info(f"🗃️  VAULT CHECK [{cycle_id}] - A priori: {a_priori_verdict['status']} | "
                        f"A posteriori: {a_posteriori_verdict['status']} - "
                        f"Timestamp: {timestamp_data['timestamp_microseconds']:.3f}μs")
        
        return verdict_result
    
    def _scan_vault(self, vault_path: Path, vault_type: str) -> Dict[str, Any]:
        """Scan a specific vault for existing verdicts"""
        if not vault_path.exists():
            return {'found': False, 'status': 'empty', 'verdict': None}
        
        try:
            # Read last few entries to check for recent verdicts
            with open(vault_path, 'r') as f:
                lines = f.readlines()
                
            if not lines:
                return {'found': False, 'status': 'empty', 'verdict': None}
            
            # Check last 10 entries for active verdicts
            recent_entries = lines[-10:] if len(lines) >= 10 else lines
            
            for line in reversed(recent_entries):
                try:
                    entry = json.loads(line.strip())
                    if entry.get('verdict_active', False):
                        return {
                            'found': True, 
                            'status': 'active_verdict',
                            'verdict': entry
                        }
                except json.JSONDecodeError:
                    continue
            
            return {'found': False, 'status': 'no_active_verdict', 'verdict': None}
            
        except Exception as e:
            self.logger.error(f"❌ Error scanning {vault_type} vault: {e}")
            return {'found': False, 'status': 'error', 'verdict': None}
    
    def harmonizer_ping_confirmation(self, cycle_id: str, harmonizer_response: Dict[str, Any]) -> bool:
        """
        Log harmonizer ping confirmation as required by immutable_core.txt.
        Harmonizer pings ISS for timestamp and cycle clearance.
        """
        timestamp_data = self.get_microsecond_timestamp()
        
        harmonizer_record = CaleonCycleTimestamp(
            cycle_id=cycle_id,
            cycle_type=self.current_cycle_type,
            timestamp_microseconds=timestamp_data['timestamp_microseconds'],
            stardate=timestamp_data['stardate'],
            operation='harmonizer_ping',
            vault_operation=f"response:{harmonizer_response.get('status', 'unknown')}",
            verdict_status=harmonizer_response.get('verdict_confirmation'),
            drift_ns=timestamp_data['drift_ns']
        )
        
        self._log_cycle_event(harmonizer_record)
        
        cycle_cleared = harmonizer_response.get('cycle_clear', True)
        
        self.logger.info(f"🎵 HARMONIZER PING [{cycle_id}] - Response: {harmonizer_response.get('status')} - "
                        f"Cycle Clear: {cycle_cleared} - "
                        f"Timestamp: {timestamp_data['timestamp_microseconds']:.3f}μs")
        
        return cycle_cleared
    
    def end_cycle(self, cycle_id: str, final_resolution: Optional[str] = None) -> Dict[str, Any]:
        """
        End CALEON consciousness cycle with final timestamping.
        Implements zero drift expectation monitoring.
        """
        if cycle_id != self.current_cycle_id:
            self.logger.warning(f"⚠️  Cycle ID mismatch: Expected {self.current_cycle_id}, got {cycle_id}")
        
        timestamp_data = self.get_microsecond_timestamp()
        
        cycle_end_record = CaleonCycleTimestamp(
            cycle_id=cycle_id,
            cycle_type=self.current_cycle_type,
            timestamp_microseconds=timestamp_data['timestamp_microseconds'],
            stardate=timestamp_data['stardate'],
            operation='cycle_end',
            vault_operation=f"resolution:{final_resolution}" if final_resolution else None,
            drift_ns=timestamp_data['drift_ns']
        )
        
        self._log_cycle_event(cycle_end_record)
        
        # Calculate cycle duration and log for drift monitoring
        cycle_duration = self._calculate_cycle_duration(cycle_id)
        
        self.logger.info(f"🏁 CYCLE END [{cycle_id}] - Duration: {cycle_duration:.3f}ms - "
                        f"Final Resolution: {final_resolution} - "
                        f"Timestamp: {timestamp_data['timestamp_microseconds']:.3f}μs - "
                        f"Drift: {timestamp_data['drift_ns']:.2f}ns")
        
        # Reset current cycle tracking
        self.current_cycle_id = None
        self.current_cycle_type = None
        
        return {
            'cycle_id': cycle_id,
            'duration_ms': cycle_duration,
            'final_timestamp': timestamp_data,
            'drift_status': 'acceptable' if abs(timestamp_data['drift_ns']) < 1000 else 'warning'
        }
    
    def _calculate_cycle_duration(self, cycle_id: str) -> float:
        """Calculate duration of a cycle from start to end timestamps"""
        try:
            start_timestamp = None
            end_timestamp = None
            
            with open(self.cycle_log_path, 'r') as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        if record['cycle_id'] == cycle_id:
                            if record['operation'] == 'cycle_start':
                                start_timestamp = record['timestamp_microseconds']
                            elif record['operation'] == 'cycle_end':
                                end_timestamp = record['timestamp_microseconds']
                    except json.JSONDecodeError:
                        continue
            
            if start_timestamp and end_timestamp:
                return (end_timestamp - start_timestamp) / 1000.0  # Convert to milliseconds
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating cycle duration: {e}")
            return 0.0
    
    def _log_cycle_event(self, cycle_record: CaleonCycleTimestamp):
        """Log cycle event to timestamped audit trail"""
        try:
            with open(self.cycle_log_path, 'a') as f:
                f.write(json.dumps(asdict(cycle_record)) + '\n')
        except Exception as e:
            self.logger.error(f"❌ Error logging cycle event: {e}")
    
    def store_vault_entry(self, vault_type: str, entry_data: Dict[str, Any], 
                         cycle_id: Optional[str] = None) -> bool:
        """
        Store entry to specified vault with ISS timestamping.
        Implements immutable_core.txt requirement for ISS timestamping all vault entries.
        
        Args:
            vault_type: 'a_priori' or 'a_posteriori'
            entry_data: Data to store in vault
            cycle_id: Optional cycle ID for tracking
        """
        timestamp_data = self.get_microsecond_timestamp()
        
        # Add ISS timestamp metadata to entry
        timestamped_entry = {
            **entry_data,
            'iss_timestamp': timestamp_data,
            'iss_cycle_id': cycle_id,
            'iss_vault_type': vault_type,
            'iss_system': self.system_name
        }
        
        # Determine vault path
        vault_path = (self.a_priori_vault if vault_type == 'a_priori' 
                     else self.a_posteriori_vault)
        
        try:
            with open(vault_path, 'a') as f:
                f.write(json.dumps(timestamped_entry) + '\n')
            
            # Log vault storage operation
            vault_store_record = CaleonCycleTimestamp(
                cycle_id=cycle_id or 'NO_CYCLE',
                cycle_type=self.current_cycle_type or 'UNKNOWN',
                timestamp_microseconds=timestamp_data['timestamp_microseconds'],
                stardate=timestamp_data['stardate'],
                operation='vault_store',
                vault_operation=f"{vault_type}:stored",
                drift_ns=timestamp_data['drift_ns']
            )
            
            self._log_cycle_event(vault_store_record)
            
            self.logger.info(f"💾 VAULT STORE [{vault_type}] - Entry stored - "
                           f"Cycle: {cycle_id} - "
                           f"Timestamp: {timestamp_data['timestamp_microseconds']:.3f}μs")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error storing to {vault_type} vault: {e}")
            return False
    
    def get_drift_report(self) -> Dict[str, Any]:
        """Generate drift monitoring report for zero drift expectation"""
        try:
            drift_samples = []
            
            with open(self.cycle_log_path, 'r') as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        if record.get('drift_ns') is not None:
                            drift_samples.append(record['drift_ns'])
                    except json.JSONDecodeError:
                        continue
            
            if not drift_samples:
                return {'status': 'no_data', 'drift_status': 'unknown'}
            
            avg_drift = sum(drift_samples) / len(drift_samples)
            max_drift = max(drift_samples)
            min_drift = min(drift_samples)
            
            drift_status = 'excellent' if abs(avg_drift) < 100 else 'good' if abs(avg_drift) < 500 else 'warning'
            
            return {
                'status': 'calculated',
                'drift_status': drift_status,
                'average_drift_ns': avg_drift,
                'max_drift_ns': max_drift,
                'min_drift_ns': min_drift,
                'sample_count': len(drift_samples),
                'zero_drift_compliance': abs(avg_drift) < 1000  # Within 1μs tolerance
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error generating drift report: {e}")
            return {'status': 'error', 'drift_status': 'unknown'}
    
    def heartbeat(self) -> bool:
        """Enhanced heartbeat with drift monitoring"""
        try:
            drift_report = self.get_drift_report()
            
            self.logger.info(f"💓 ISS Heartbeat - Status: {self.status} - "
                           f"Drift: {drift_report.get('drift_status', 'unknown')} - "
                           f"Cycles: {self.cycle_counter}")
            
            return (self.status == "healthy" and 
                   drift_report.get('zero_drift_compliance', True))
                   
        except Exception as e:
            self.logger.error(f"❌ Heartbeat error: {e}")
            return False