@echo off
setlocal
cd /d "%~dp0"

echo Starting NLAMS portals...
start "NLAMS - Integration Service" cmd /k "cd /d "%~dp0integration" && python app.py"

start "NLAMS - LAO" cmd /k "cd /d "%~dp0internal\NLAMS-Final-Submission-Fixed-LAO-RR\LAO" && set NLAMS_PORT=5004 && python app.py"
start "NLAMS - RR Officer" cmd /k "cd /d "%~dp0internal\NLAMS-Final-Submission-Fixed-LAO-RR\RR" && set NLAMS_PORT=5003 && python app.py"
start "NLAMS - Grievance Officer" cmd /k "cd /d "%~dp0internal\Grievance_Officer_Portal_SIH_26016_V4" && set NLAMS_PORT=5002 && python app.py"
start "NLAMS - Landowner" cmd /k "cd /d "%~dp0internal\Landowner_Portal_SIH_26016_V2" && set NLAMS_PORT=5005 && python app.py"
start "NLAMS - Revenue Officer" cmd /k "cd /d "%~dp0internal\NLAMS_Revenue_Officer_FIXED\NLAMS_Revenue_Officer_FIXED" && set NLAMS_PORT=5006 && python app.py"
start "NLAMS - Advanced/Admin" cmd /k "cd /d "%~dp0internal\NLAMS_Advanced_Pro_Portal_Fixed\NLAMS_Advanced_Pro_Portal" && set NLAMS_PORT=5007 && python app.py"
start "NLAMS - Project Agency" cmd /k "cd /d "%~dp0internal\NLAMS_Project_Fixed_Updated" && set NLAMS_PORT=5008 && python app.py"

start "NLAMS - Survey GIS Officer" cmd /k "cd /d "%~dp0internal\NLAMS_Survey_GIS_Officer_Prototype_geo_evidence_fixed_v2\nlams_work" && if not exist node_modules (npm install) && npm run dev -- --host 127.0.0.1 --port 5173"

start "NLAMS Gateway" cmd /k "cd /d "%~dp0gateway" && python -m http.server 8000 --bind 127.0.0.1"

timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:8000

echo.
echo NLAMS Gateway: http://127.0.0.1:8000
endlocal
