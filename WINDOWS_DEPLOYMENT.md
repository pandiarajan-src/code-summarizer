# Windows Deployment Guide for Code Summarizer

This guide provides multiple options for deploying the Code Summarizer application on Windows machines.

## Prerequisites

1. **Python 3.12 or higher**
   - Download from: https://www.python.org/downloads/
   - During installation, CHECK "Add Python to PATH"

2. **Git** (for cloning the repository)
   - Download from: https://git-scm.com/download/win

3. **OpenAI API Key**
   - Get from: https://platform.openai.com/api-keys

## Option 1: Simple Script Deployment (Recommended)

This is the easiest method that runs both API and Frontend without Docker.

### Method A: Using Batch Script

1. **Clone the repository:**
   ```cmd
   git clone https://github.com/your-repo/code-summarizer.git
   cd code-summarizer
   ```

2. **Run the deployment script:**
   ```cmd
   deploy-windows.bat
   ```

3. **Follow the prompts:**
   - The script will check for Python
   - Create/edit .env file for API key
   - Install dependencies
   - Start both servers

4. **Access the application:**
   - Frontend: http://localhost:8080
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### **External Access (From Other Machines)**

To access from other machines on your network:

1. **Configure Windows Firewall** (Run as Administrator):
   ```cmd
   setup_firewall.bat
   ```

2. **Find your machine's IP address**:
   ```cmd
   ipconfig
   ```
   Look for "IPv4 Address" under your network adapter.

3. **Access from other machines**:
   - Frontend: http://YOUR_IP_ADDRESS:8080
   - API: http://YOUR_IP_ADDRESS:8000

4. **Test external access**:
   ```cmd
   python test_external_access.py
   ```

### Method B: Using Python Script

1. **Run the Python deployment script:**
   ```cmd
   python deploy_windows.py
   ```

2. **The script will:**
   - Check all prerequisites
   - Setup environment
   - Install dependencies
   - Start servers
   - Open browser automatically

## Option 2: Manual Deployment

If the scripts don't work, follow these manual steps:

### Step 1: Setup Environment

1. **Create .env file:**
   ```cmd
   copy .env.example .env
   notepad .env
   ```

2. **Add your OpenAI API key:**
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

### Step 2: Install Dependencies

Choose one method:

**Using uv (faster):**
```cmd
# Install uv
powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"

# Install dependencies
uv sync --frozen --no-dev
```

**Using pip (standard):**
```cmd
# Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn[standard] openai tiktoken click python-multipart pyyaml pydantic pydantic-settings
```

### Step 3: Start the API Server

Open a new Command Prompt and run:
```cmd
cd path\to\code-summarizer
set PYTHONPATH=app
python -m uvicorn app.api_main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 4: Start the Frontend Server

Open another Command Prompt and run:
```cmd
cd path\to\code-summarizer\frontend
python -m http.server 8080
```

### Step 5: Access the Application

Open your browser and go to:
- Frontend: http://localhost:8080
- API Documentation: http://localhost:8000/docs

## Option 3: Docker Desktop (If Available)

If you have Docker Desktop for Windows installed:

### Fix for Docker Issues

1. **Ensure line endings are correct:**
   ```cmd
   git config --global core.autocrlf input
   git clone https://github.com/your-repo/code-summarizer.git
   cd code-summarizer
   ```

2. **Build with fixes:**
   ```cmd
   docker-compose -f docker-compose.single.yml build --no-cache
   docker-compose -f docker-compose.single.yml up
   ```

3. **Access at:**
   - Frontend: http://localhost
   - API: http://localhost/api

## Option 4: Windows Service Installation

For production deployment as Windows services:

### Using NSSM (Non-Sucking Service Manager)

1. **Download NSSM:**
   - From: https://nssm.cc/download
   - Extract to a folder

2. **Install API as service:**
   ```cmd
   nssm install CodeSummarizerAPI
   # In the GUI:
   # Path: C:\Python312\python.exe
   # Arguments: -m uvicorn app.api_main:app --host 127.0.0.1 --port 8000
   # Startup directory: C:\path\to\code-summarizer
   # Environment: PYTHONPATH=app
   ```

3. **Install Frontend as service:**
   ```cmd
   nssm install CodeSummarizerFrontend
   # In the GUI:
   # Path: C:\Python312\python.exe
   # Arguments: -m http.server 8080
   # Startup directory: C:\path\to\code-summarizer\frontend
   ```

4. **Start services:**
   ```cmd
   nssm start CodeSummarizerAPI
   nssm start CodeSummarizerFrontend
   ```

## Troubleshooting

### Common Issues and Solutions

#### 1. "Python not found"
- Ensure Python is installed and added to PATH
- Restart Command Prompt after installation
- Try: `py --version` instead of `python --version`

#### 2. "Port already in use"
- Kill existing processes:
  ```cmd
  # Find process on port 8000
  netstat -ano | findstr :8000
  # Kill process (replace PID with actual number)
  taskkill /F /PID [PID]
  ```

#### 3. "Module not found" errors
- Ensure you're in the correct directory
- Check PYTHONPATH is set: `set PYTHONPATH=app`
- Reinstall dependencies

#### 4. "OPENAI_API_KEY not set"
- Check .env file exists and contains valid key
- No spaces around the = sign
- No quotes unless the key contains special characters

#### 5. Frontend can't connect to API
- Ensure API is running first
- Check Windows Firewall isn't blocking ports
- Try accessing API directly: http://localhost:8000/api/health

### Windows Firewall Configuration

If you need to access from other machines on network:

1. **Open Windows Defender Firewall**
2. **Click "Advanced settings"**
3. **Inbound Rules → New Rule**
4. **Port → TCP → Specific ports: 8000, 8080**
5. **Allow the connection**
6. **Apply to all profiles**
7. **Name: "Code Summarizer"**

### Performance Optimization

For better performance on Windows:

1. **Exclude from antivirus scanning:**
   - Add code-summarizer folder to Windows Defender exclusions
   - Speeds up file operations

2. **Use SSD:**
   - Place project on SSD for faster file I/O

3. **Increase Python thread pool:**
   ```cmd
   set PYTHONTHREADS=4
   ```

## Quick Start Commands

```cmd
# Clone repository
git clone https://github.com/your-repo/code-summarizer.git
cd code-summarizer

# Quick setup and run
copy .env.example .env
notepad .env
# Add your API key and save

# Run deployment
python deploy_windows.py
# OR
deploy-windows.bat
```

## Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Ensure all prerequisites are installed
3. Try the manual deployment method
4. Check API logs in the command window for errors
5. Verify your OpenAI API key is valid

## Notes

- The application runs on ports 8000 (API) and 8080 (Frontend)
- Both servers must be running for full functionality
- Close Command Prompt windows or use Ctrl+C to stop servers
- For production use, consider the Windows Service option