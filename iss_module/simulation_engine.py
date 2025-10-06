"""
DALS Phase 1 - Simulation Engine
Generates realistic telemetry data for testing CertSig, Caleon, and ISS modules
"""

import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import aiohttp
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger("DALS.Simulator")

@dataclass
class SimulationConfig:
    """Configuration for telemetry simulation"""
    base_url: str = "http://127.0.0.1:8003"
    event_rate: float = 2.0  # Events per second
    burst_probability: float = 0.1  # 10% chance of burst
    burst_multiplier: int = 5  # 5x events during burst
    duration_seconds: Optional[int] = None  # None = infinite
    stress_test_mode: bool = False  # High-volume testing
    
    # Module-specific settings
    certsig_mint_rate: float = 0.5  # Mints per second
    caleon_reasoning_rate: float = 1.0  # Reasoning cycles per second
    iss_pulse_rate: float = 1.047  # Hz (ISS chronometer frequency)


class TelemetrySimulator:
    """Advanced telemetry simulation engine for Phase 1 testing"""
    
    def __init__(self, config: SimulationConfig = None):
        self.config = config or SimulationConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = False
        self.stats = {
            "events_generated": 0,
            "certsig_mints": 0,
            "caleon_cycles": 0,
            "iss_pulses": 0,
            "errors": 0,
            "start_time": None
        }
        
        # Realistic data pools for generation
        self.nft_types = ["K-NFT", "L-NFT", "M-NFT", "N-NFT", "O-NFT", "P-NFT", 
                         "Q-NFT", "R-NFT", "S-NFT", "T-NFT", "U-NFT", "V-NFT", "X-NFT"]
        
        self.reasoning_sequences = [
            "aesop_003_10247", "harmony_cycle_002", "drift_calibration_045",
            "symbolic_resonance_021", "gepetto_fusion_007", "axiom_validation_189",
            "coherence_matrix_134", "glyph_processing_092", "neural_pathway_256"
        ]
        
        self.blockchain_networks = ["ethereum", "polygon", "arbitrum", "base", "optimism"]
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def generate_certsig_telemetry(self) -> Dict[str, Any]:
        """Generate realistic CertSig mint telemetry"""
        nft_type = random.choice(self.nft_types)
        token_id = f"ALPHA-{random.randint(100000, 999999):06d}"
        blockchain = random.choice(self.blockchain_networks)
        
        # Simulate mint success/failure rates
        status = "minted" if random.random() > 0.05 else "failed"
        
        telemetry = {
            "token_id": token_id,
            "nft_type": nft_type,
            "status": status,
            "timestamp_iso": datetime.utcnow().isoformat() + "Z",
            "stardate_iss": f"-{297238 + random.uniform(-1, 1):.1f}",
            "royalty_amount": round(random.uniform(5.0, 50.0), 2),
            "transaction_hash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
            "mint_duration_ms": random.randint(200, 2000),
            "blockchain_network": blockchain,
            "gas_used": random.randint(21000, 150000),
            "mint_fee": round(random.uniform(0.001, 0.01), 6),
            "validation_layers": random.randint(15, 20),
            "metadata_size_bytes": random.randint(1024, 8192)
        }
        
        return telemetry
    
    def generate_caleon_telemetry(self) -> Dict[str, Any]:
        """Generate realistic Caleon AI telemetry"""
        sequence_id = random.choice(self.reasoning_sequences)
        
        # Simulate drift variance - usually stable, occasionally fluctuates
        base_drift = 0.023
        drift_variance = random.uniform(-0.005, 0.005) if random.random() > 0.8 else random.uniform(-0.0005, 0.0005)
        drift_score = max(0.001, base_drift + drift_variance)
        
        harmonizer_verdict = "Stable" if drift_score < 0.05 else "Fluctuating" if drift_score < 0.1 else "Unstable"
        
        telemetry = {
            "sequence_id": f"{sequence_id}_{random.randint(10000, 99999)}",
            "drift_score": round(drift_score, 6),
            "harmonizer_verdict": harmonizer_verdict,
            "reasoning_cycles": random.randint(64, 512),
            "logs_processed": random.randint(1000, 50000),
            "memory_usage": round(random.uniform(0.4, 0.9), 3),
            "cpu_load": round(random.uniform(0.1, 0.7), 3),
            "timestamp_iso": datetime.utcnow().isoformat() + "Z",
            "symbolic_coherence": round(random.uniform(90.0, 99.9), 2),
            "neural_pathways_active": random.randint(128, 1024),
            "glyph_resonance_hz": round(random.uniform(40.0, 60.0), 2),
            "axiom_validation_score": round(random.uniform(0.85, 1.0), 4)
        }
        
        return telemetry
    
    def generate_iss_pulse(self) -> Dict[str, Any]:
        """Generate realistic ISS chronometer pulse"""
        now = datetime.utcnow()
        
        # Calculate various timestamp formats
        julian_day = 2440588.0 + (time.time() / 86400.0)  # Julian Day Number
        stardate = -297238 + random.uniform(-0.1, 0.1)  # TNG-era stardate with slight variance
        
        # Simulate temporal accuracy - very precise but not perfect
        phase_variance = random.uniform(-0.001, 0.001)
        signal_strength = min(1.0, max(0.95, 1.0 + phase_variance))
        
        telemetry = {
            "timestamp_iso": now.isoformat() + "Z",
            "timestamp_julian": round(julian_day, 6),
            "timestamp_epoch": int(time.time()),
            "stardate_iss": f"{stardate:.1f}",
            "phase": f"cycle-{random.randint(1, 100)}",
            "signal_strength": round(signal_strength, 6),
            "temporal_drift_ppm": round(random.uniform(-1.0, 1.0), 3),
            "chronon_frequency_hz": round(1.047 + random.uniform(-0.001, 0.001), 6),
            "anchor_stability": round(random.uniform(99.5, 99.99), 2),
            "interplanetary_offset_cycles": round(random.uniform(-0.0001, 0.0001), 7),
            "quantum_uncertainty": round(random.uniform(0.0001, 0.001), 6)
        }
        
        return telemetry
    
    async def send_telemetry(self, endpoint: str, data: Dict[str, Any]) -> bool:
        """Send telemetry data to DALS API"""
        try:
            url = f"{self.config.base_url}/api/v1{endpoint}"
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    return True
                else:
                    logger.warning(f"Telemetry send failed: {response.status} - {await response.text()}")
                    return False
        except Exception as e:
            logger.error(f"Error sending telemetry to {endpoint}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def generate_burst_activity(self):
        """Generate burst of activity across all modules"""
        logger.info("🌋 Generating activity burst...")
        
        burst_tasks = []
        burst_size = self.config.burst_multiplier * 3  # 3 modules
        
        for _ in range(burst_size):
            # Randomly choose module for burst event
            module_choice = random.choice(["certsig", "caleon", "iss"])
            
            if module_choice == "certsig":
                data = self.generate_certsig_telemetry()
                task = self.send_telemetry("/mint/telemetry", data)
            elif module_choice == "caleon":
                data = self.generate_caleon_telemetry() 
                task = self.send_telemetry("/caleon/telemetry", data)
            else:  # iss
                data = self.generate_iss_pulse()
                task = self.send_telemetry("/iss/pulse", data)
                
            burst_tasks.append(task)
            
        # Execute burst in parallel
        results = await asyncio.gather(*burst_tasks, return_exceptions=True)
        successful = sum(1 for r in results if r is True)
        
        logger.info(f"📊 Burst completed: {successful}/{len(burst_tasks)} successful")
    
    async def run_simulation(self):
        """Main simulation loop"""
        logger.info(f"🚀 Starting DALS telemetry simulation - Rate: {self.config.event_rate} events/sec")
        
        self.running = True
        self.stats["start_time"] = time.time()
        
        last_certsig = 0
        last_caleon = 0
        last_iss = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Check for burst activity
                if random.random() < self.config.burst_probability:
                    await self.generate_burst_activity()
                
                # Generate CertSig mints
                if current_time - last_certsig >= (1.0 / self.config.certsig_mint_rate):
                    data = self.generate_certsig_telemetry()
                    await self.send_telemetry("/mint/telemetry", data)
                    self.stats["certsig_mints"] += 1
                    last_certsig = current_time
                
                # Generate Caleon reasoning cycles
                if current_time - last_caleon >= (1.0 / self.config.caleon_reasoning_rate):
                    data = self.generate_caleon_telemetry()
                    await self.send_telemetry("/caleon/telemetry", data)
                    self.stats["caleon_cycles"] += 1
                    last_caleon = current_time
                
                # Generate ISS pulses
                if current_time - last_iss >= (1.0 / self.config.iss_pulse_rate):
                    data = self.generate_iss_pulse()
                    await self.send_telemetry("/iss/pulse", data)
                    self.stats["iss_pulses"] += 1
                    last_iss = current_time
                
                self.stats["events_generated"] = (self.stats["certsig_mints"] + 
                                                 self.stats["caleon_cycles"] + 
                                                 self.stats["iss_pulses"])
                
                # Sleep to maintain event rate
                await asyncio.sleep(1.0 / self.config.event_rate)
                
                # Check duration limit
                if (self.config.duration_seconds and 
                    current_time - self.stats["start_time"] >= self.config.duration_seconds):
                    logger.info(f"⏰ Simulation duration completed: {self.config.duration_seconds}s")
                    break
                    
            except asyncio.CancelledError:
                logger.info("🛑 Simulation cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Simulation error: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(1)  # Brief pause on error
        
        self.running = False
        await self.print_final_stats()
    
    async def print_final_stats(self):
        """Print simulation statistics"""
        duration = time.time() - self.stats["start_time"]
        
        logger.info("📊 === SIMULATION STATISTICS ===")
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info(f"Total Events: {self.stats['events_generated']}")
        logger.info(f"CertSig Mints: {self.stats['certsig_mints']}")
        logger.info(f"Caleon Cycles: {self.stats['caleon_cycles']}")
        logger.info(f"ISS Pulses: {self.stats['iss_pulses']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Event Rate: {self.stats['events_generated']/duration:.2f} events/sec")
        logger.info("================================")
    
    def stop(self):
        """Stop the simulation"""
        self.running = False


# Convenience functions for different simulation scenarios

async def run_basic_simulation(duration_minutes: int = 5):
    """Run basic telemetry simulation for testing"""
    config = SimulationConfig(
        duration_seconds=duration_minutes * 60,
        event_rate=2.0
    )
    
    async with TelemetrySimulator(config) as simulator:
        await simulator.run_simulation()


async def run_stress_test(duration_minutes: int = 2):
    """Run high-volume stress test simulation"""
    config = SimulationConfig(
        duration_seconds=duration_minutes * 60,
        event_rate=20.0,  # 20 events per second
        burst_probability=0.3,  # 30% chance of burst
        burst_multiplier=10,
        stress_test_mode=True,
        certsig_mint_rate=5.0,  # 5 mints per second
        caleon_reasoning_rate=10.0,  # 10 cycles per second
        iss_pulse_rate=5.0  # 5 Hz
    )
    
    async with TelemetrySimulator(config) as simulator:
        await simulator.run_simulation()


async def run_burst_demo():
    """Demonstrate burst activity generation"""
    config = SimulationConfig(
        duration_seconds=30,
        event_rate=1.0,
        burst_probability=0.5,  # 50% chance of burst
        burst_multiplier=8
    )
    
    async with TelemetrySimulator(config) as simulator:
        await simulator.run_simulation()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run basic simulation
    print("🎲 Starting DALS Phase 1 Telemetry Simulation...")
    print("🔗 Make sure DALS server is running on http://127.0.0.1:8003")
    print("📊 Dashboard: http://127.0.0.1:8003/")
    
    try:
        asyncio.run(run_basic_simulation(duration_minutes=3))
    except KeyboardInterrupt:
        print("\n🛑 Simulation stopped by user")