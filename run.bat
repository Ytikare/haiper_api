@echo off
echo Activating conda environment...
call conda activate haiper_api
echo Changing to drive D:
d:
echo Changing to haiper_api project directory...
cd Projects\haiper_api

echo Setting Tesseract Path...
SET TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe

echo Starting uvicorn server with 2 workers...
uvicorn app:app --workers 2
echo Server stopped.
pause