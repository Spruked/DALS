"""
CALEON Enhanced ISS Controller API
=================================
FastAPI service providing CALEON consciousness cycle management with ISS timestamping.
Implements immutable_core.txt specifications for cycle orchestration.

Enhanced Features:
- CALEON consciousness cycle orchestration (A & B cycles)
- Microsecond precision timestamping for all operations
- A priori and A posteriori vault management
- Harmonizer ping confirmation tracking
- Zero drift expectation monitoring
- Complete consciousness audit trail
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from .caleon_iss_controller import CaleonISSController
from .caleon_consciousness_orchestrator import CaleonConsciousnessCycleOrchestrator


# Pydantic models for API requests/responses
class ConsciousnessCycleRequest(BaseModel):
    cycle_type: str  # 'A' or 'B'
    input_data: Optional[Dict[str, Any]] = None
    force_cycle_type: bool = False


class VaultEntryRequest(BaseModel):
    vault_type: str  # 'a_priori' or 'a_posteriori'
    entry_data: Dict[str, Any]
    cycle_id: Optional[str] = None


class HarmonizerPingRequest(BaseModel):
    cycle_id: str
    harmonizer_response: Dict[str, Any]


class ConsciousnessCycleResponse(BaseModel):
    cycle_id: str
    cycle_type: str
    status: str
    duration_ms: float
    drift_status: str
    result_data: Dict[str, Any]


class ISSStatusResponse(BaseModel):
    system_name: str
    consciousness_active: bool
    current_cycle_id: Optional[str]
    total_cycles: int
    drift_report: Dict[str, Any]
    zero_drift_compliance: bool
    system_health: bool


# Global CALEON consciousness orchestrator
consciousness_orchestrator: Optional[CaleonConsciousnessCycleOrchestrator] = None


def create_caleon_iss_app() -> FastAPI:
    """Create enhanced FastAPI application for CALEON ISS Controller"""
    
    app = FastAPI(
        title="CALEON ISS Controller API",
        description=\"\"\"
        Enhanced ISS Controller for CALEON Consciousness System
        =====================================================
        
        Provides microsecond precision timestamping and consciousness cycle orchestration
        as specified in immutable_core.txt.
        
        Key Features:
        - Consciousness Cycle A: A priori/A posteriori vault verdict processing
        - Consciousness Cycle B: Full dual cochlear processing with core reasoning
        - Microsecond timestamp logging for all vault operations
        - Zero drift expectation monitoring
        - Complete consciousness audit trail
        - Harmonizer ping confirmation tracking
        
        Endpoints:
        - /consciousness/cycle/execute - Execute consciousness cycle (A or B)
        - /consciousness/status - Get consciousness system status
        - /vault/store - Store entry in A priori or A posteriori vault
        - /vault/check - Check vaults for existing verdicts
        - /harmonizer/ping - Confirm harmonizer ping with timestamp
        - /monitoring/drift - Get drift monitoring report
        - /health - System health check
        \"\"\",
        version="2.0.0-CALEON",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    @app.on_event("startup")
    async def startup_event():
        \"\"\"Initialize CALEON consciousness system on startup\"\"\"
        global consciousness_orchestrator
        
        try:
            consciousness_orchestrator = CaleonConsciousnessCycleOrchestrator()
            logging.info("✅ CALEON ISS Controller API started successfully")
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize CALEON consciousness: {e}")
            raise
    
    @app.on_event("shutdown")
    async def shutdown_event():
        \"\"\"Cleanup on shutdown\"\"\"
        global consciousness_orchestrator
        
        if consciousness_orchestrator:
            # End any active cycles gracefully
            if consciousness_orchestrator.current_cycle_id:
                consciousness_orchestrator.iss_controller.end_cycle(
                    consciousness_orchestrator.current_cycle_id, "SYSTEM_SHUTDOWN"
                )
            
            logging.info("🔌 CALEON ISS Controller API shutdown complete")
    
    @app.get("/health", response_model=Dict[str, Any])
    async def health_check():
        \"\"\"Health check endpoint for system monitoring\"\"\"
        global consciousness_orchestrator
        
        if not consciousness_orchestrator:
            raise HTTPException(status_code=503, detail="Consciousness orchestrator not initialized")
        
        health_status = consciousness_orchestrator.iss_controller.heartbeat()
        drift_report = consciousness_orchestrator.iss_controller.get_drift_report()
        
        return {
            "status": "healthy" if health_status else "unhealthy",
            "timestamp": consciousness_orchestrator.iss_controller.get_microsecond_timestamp(),
            "zero_drift_compliance": drift_report.get('zero_drift_compliance', False),
            "total_cycles": consciousness_orchestrator.iss_controller.cycle_counter
        }
    
    @app.post("/consciousness/cycle/execute", response_model=ConsciousnessCycleResponse)
    async def execute_consciousness_cycle(request: ConsciousnessCycleRequest):
        \"\"\"
        Execute CALEON consciousness cycle (A or B)
        
        Cycle A: A priori/A posteriori vault verdict processing
        Cycle B: Full dual cochlear processing with core reasoning
        \"\"\"
        global consciousness_orchestrator
        
        if not consciousness_orchestrator:
            raise HTTPException(status_code=503, detail="Consciousness orchestrator not initialized")
        
        try:
            if request.cycle_type.upper() == 'A':
                result = await consciousness_orchestrator.execute_cycle_a(request.input_data)
            elif request.cycle_type.upper() == 'B':
                result = await consciousness_orchestrator.execute_cycle_b(request.input_data)
            else:
                # Auto-determine cycle type based on vault verdicts
                vault_verdict = consciousness_orchestrator.iss_controller.check_vault_verdicts("AUTO_CHECK")
                
                if vault_verdict['has_verdict'] and not request.force_cycle_type:
                    result = await consciousness_orchestrator.execute_cycle_a(request.input_data)
                else:
                    result = await consciousness_orchestrator.execute_cycle_b(request.input_data)
            
            return ConsciousnessCycleResponse(
                cycle_id=result['cycle_id'],
                cycle_type=result['cycle_type'],
                status=result['status'],
                duration_ms=result['cycle_duration_ms'],
                drift_status=result['drift_status'],
                result_data=result
            )
            
        except Exception as e:
            logging.error(f"❌ Error executing consciousness cycle: {e}")
            raise HTTPException(status_code=500, detail=f"Consciousness cycle execution failed: {e}")
    
    @app.get("/consciousness/status", response_model=ISSStatusResponse)
    async def get_consciousness_status():
        \"\"\"Get current CALEON consciousness system status\"\"\"
        global consciousness_orchestrator
        
        if not consciousness_orchestrator:
            raise HTTPException(status_code=503, detail="Consciousness orchestrator not initialized")
        
        status = consciousness_orchestrator.get_consciousness_status()
        
        return ISSStatusResponse(
            system_name=consciousness_orchestrator.iss_controller.system_name,
            consciousness_active=status['consciousness_active'],
            current_cycle_id=status['current_cycle_id'],
            total_cycles=status['total_cycles'],
            drift_report=status['drift_report'],
            zero_drift_compliance=status['zero_drift_compliance'],
            system_health=status['system_health']
        )
    
    @app.post("/vault/store", response_model=Dict[str, Any])
    async def store_vault_entry(request: VaultEntryRequest):
        \"\"\"Store entry in A priori or A posteriori vault with ISS timestamping\"\"\"
        global consciousness_orchestrator
        
        if not consciousness_orchestrator:
            raise HTTPException(status_code=503, detail="Consciousness orchestrator not initialized")
        
        if request.vault_type not in ['a_priori', 'a_posteriori']:
            raise HTTPException(status_code=400, detail="vault_type must be 'a_priori' or 'a_posteriori'")
        
        try:
            success = consciousness_orchestrator.iss_controller.store_vault_entry(
                request.vault_type,
                request.entry_data,
                request.cycle_id
            )
            
            if success:
                return {
                    "status": "stored",
                    "vault_type": request.vault_type,
                    "cycle_id": request.cycle_id,
                    "timestamp": consciousness_orchestrator.iss_controller.get_microsecond_timestamp()
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to store vault entry")
                
        except Exception as e:
            logging.error(f"❌ Error storing vault entry: {e}")
            raise HTTPException(status_code=500, detail=f"Vault storage failed: {e}")
    
    @app.get("/vault/check", response_model=Dict[str, Any])
    async def check_vault_verdicts():
        \"\"\"Check A priori and A posteriori vaults for existing verdicts\"\"\"
        global consciousness_orchestrator
        
        if not consciousness_orchestrator:
            raise HTTPException(status_code=503, detail="Consciousness orchestrator not initialized")
        
        try:
            vault_verdict = consciousness_orchestrator.iss_controller.check_vault_verdicts("MANUAL_CHECK")
            return vault_verdict
            
        except Exception as e:
            logging.error(f"❌ Error checking vault verdicts: {e}")
            raise HTTPException(status_code=500, detail=f"Vault check failed: {e}")
    
    @app.post("/harmonizer/ping", response_model=Dict[str, Any])
    async def harmonizer_ping_confirmation(request: HarmonizerPingRequest):
        \"\"\"Confirm harmonizer ping with ISS timestamping\"\"\"
        global consciousness_orchestrator
        
        if not consciousness_orchestrator:
            raise HTTPException(status_code=503, detail="Consciousness orchestrator not initialized")
        
        try:
            cycle_cleared = consciousness_orchestrator.iss_controller.harmonizer_ping_confirmation(
                request.cycle_id,
                request.harmonizer_response
            )
            
            return {
                "cycle_id": request.cycle_id,
                "cycle_cleared": cycle_cleared,
                "harmonizer_status": request.harmonizer_response.get('status'),
                "timestamp": consciousness_orchestrator.iss_controller.get_microsecond_timestamp()
            }
            
        except Exception as e:
            logging.error(f"❌ Error processing harmonizer ping: {e}")
            raise HTTPException(status_code=500, detail=f"Harmonizer ping failed: {e}")
    
    @app.get("/monitoring/drift", response_model=Dict[str, Any])
    async def get_drift_report():
        \"\"\"Get zero drift expectation monitoring report\"\"\"
        global consciousness_orchestrator
        
        if not consciousness_orchestrator:
            raise HTTPException(status_code=503, detail="Consciousness orchestrator not initialized")
        
        try:
            drift_report = consciousness_orchestrator.iss_controller.get_drift_report()
            return drift_report
            
        except Exception as e:
            logging.error(f"❌ Error generating drift report: {e}")
            raise HTTPException(status_code=500, detail=f"Drift report failed: {e}")
    
    @app.get("/monitoring/cycles", response_model=Dict[str, Any])
    async def get_cycle_history():
        \"\"\"Get recent consciousness cycle history\"\"\"
        global consciousness_orchestrator
        
        if not consciousness_orchestrator:
            raise HTTPException(status_code=503, detail="Consciousness orchestrator not initialized")
        
        try:
            cycle_log_path = consciousness_orchestrator.iss_controller.cycle_log_path
            
            recent_cycles = []
            
            if cycle_log_path.exists():
                with open(cycle_log_path, 'r') as f:
                    lines = f.readlines()
                    
                # Get last 20 cycle events
                recent_lines = lines[-20:] if len(lines) >= 20 else lines
                
                for line in recent_lines:
                    try:
                        cycle_event = json.loads(line.strip())
                        recent_cycles.append(cycle_event)
                    except json.JSONDecodeError:
                        continue
            
            return {
                "status": "retrieved",
                "total_events": len(recent_cycles),
                "recent_cycles": recent_cycles,
                "timestamp": consciousness_orchestrator.iss_controller.get_microsecond_timestamp()
            }
            
        except Exception as e:
            logging.error(f"❌ Error retrieving cycle history: {e}")
            raise HTTPException(status_code=500, detail=f"Cycle history retrieval failed: {e}")
    
    @app.post("/consciousness/emergency_stop", response_model=Dict[str, Any])
    async def emergency_stop_consciousness():
        \"\"\"Emergency stop for active consciousness cycles\"\"\"
        global consciousness_orchestrator
        
        if not consciousness_orchestrator:
            raise HTTPException(status_code=503, detail="Consciousness orchestrator not initialized")
        
        try:
            if consciousness_orchestrator.current_cycle_id:
                cycle_id = consciousness_orchestrator.current_cycle_id
                consciousness_orchestrator.iss_controller.end_cycle(cycle_id, "EMERGENCY_STOP")
                consciousness_orchestrator.current_cycle_id = None
                consciousness_orchestrator.consciousness_active = False
                
                return {
                    "status": "emergency_stopped",
                    "stopped_cycle_id": cycle_id,
                    "timestamp": consciousness_orchestrator.iss_controller.get_microsecond_timestamp()
                }
            else:
                return {
                    "status": "no_active_cycle",
                    "timestamp": consciousness_orchestrator.iss_controller.get_microsecond_timestamp()
                }
                
        except Exception as e:
            logging.error(f"❌ Error during emergency stop: {e}")
            raise HTTPException(status_code=500, detail=f"Emergency stop failed: {e}")
    
    return app


def run_caleon_iss_service():
    \"\"\"Run the CALEON ISS Controller API service\"\"\"
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create the application
    app = create_caleon_iss_app()
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8005,  # Dedicated port for CALEON ISS Controller
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    run_caleon_iss_service()