@echo off
echo Activating conda environment...
call conda activate haiper_api
echo Setting Tesseract Path...
SET TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
cd /d D:\Projects\haiper_api
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 2
