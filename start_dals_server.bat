@echo off
echo Starting Digital Asset Logistics System (DALS) Server...
echo.
echo This will start the server on http://localhost:8003
echo Press Ctrl+C to stop the server
echo.
cd /d "%~dp0"
python -c "
try:
    from iss_module.api.api import app
    print('✓ App imported successfully')
    print('✓ App has', len(app.routes), 'routes')
    import uvicorn
    print('✓ Starting server on http://127.0.0.1:8003')
    print('✓ Press Ctrl+C to stop')
    uvicorn.run(app, host='127.0.0.1', port=8003, log_level='info')
except Exception as e:
    print('✗ Error:', e)
    import traceback
    traceback.print_exc()
    pause
"
pause