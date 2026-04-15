cd API
python -m venv .venv
.venv\Scripts\activate    
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
python app.py

cd API
.venv\Scripts\activate    
python app.py


cd UI
npm install
npm run dev