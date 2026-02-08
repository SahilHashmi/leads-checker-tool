# Leads Checker Pro - Desktop Application

Enterprise-level email verification tool that checks emails against MongoDB databases.

## Features

- 🚀 **High Performance** - Multi-threaded processing with 50 concurrent checks
- 🎨 **Modern UI** - Enterprise-level dark theme interface
- 🔒 **Secure** - No data transmitted externally, all processing is local
- 📊 **Real-time Stats** - Live progress tracking and statistics
- 💾 **Export Results** - Save fresh leads to file

## Installation

### Option 1: Run from Source

1. Create virtual environment:
```bash
cd desktop-app
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

### Option 2: Build Standalone .exe

1. Install dependencies (if not done):
```bash
pip install -r requirements.txt
```

2. Build the executable:
```bash
python build.py
```

3. Find the executable at: `dist/LeadsCheckerPro.exe`

## Usage

1. **Configure Databases** - Enter MongoDB connection URLs and database names in the sidebar
2. **Connect** - Click "Connect All" to establish database connections
3. **Select File** - Browse and select a .txt or .csv file containing emails
4. **Start Check** - Click "Start Check" to begin verification
5. **Export** - Export fresh (non-leaked) emails to a file

## Database Configuration

The application connects to 7 VPS databases:

| VPS | Domains | Default Database |
|-----|---------|------------------|
| VPS2 | A-G | email_A_G |
| VPS3 | H-N | email_H_N |
| VPS4 | O-U | email_O_U |
| VPS5 | V-Z | email_V_Z |
| VPS6 | gmail.com | email_gmail |
| VPS7 | hotmail.com | email_hotmail |
| VPS8 | yahoo.com, aol.com | email_yahoo_aol |

## System Requirements

- Windows 10/11
- 4GB RAM minimum
- MongoDB databases accessible

## Security

- All processing happens locally on your machine
- No data is sent to external servers
- Database credentials are not stored permanently
