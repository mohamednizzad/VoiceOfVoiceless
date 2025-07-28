# Windows Setup Guide for VoiceAccess

## Quick Start (Recommended)

### Option 1: Automatic Installation
1. **Run the Python installer:**
   ```bash
   python install_dependencies.py
   ```

2. **Add your AssemblyAI API key to `.env`:**
   ```
   ASSEMBLYAI_API_KEY=your_api_key_here
   ```

3. **Run the application:**
   ```bash
   streamlit run app.py
   ```

### Option 2: Minimal Installation
If you're having issues with dependencies, use the minimal requirements:

```bash
pip install -r requirements-minimal.txt
```

### Option 3: Manual Installation
Install packages one by one:

```bash
pip install streamlit assemblyai sounddevice numpy python-dotenv pandas plotly psutil requests
```

## Troubleshooting

### Audio Issues
If you get audio-related errors:

1. **Try installing sounddevice separately:**
   ```bash
   pip install sounddevice
   ```

2. **If sounddevice fails, the app will automatically use simulation mode** - you'll see mock transcription data for testing.

3. **For real audio on Windows, you might need:**
   - Microsoft Visual C++ Build Tools
   - Or try: `pip install sounddevice --no-cache-dir`

### Common Windows Issues

#### 1. "Microsoft Visual C++ 14.0 is required"
- Install Microsoft C++ Build Tools from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Or install Visual Studio Community

#### 2. "Failed building wheel for [package]"
- Try: `pip install --upgrade pip setuptools wheel`
- Then retry the installation

#### 3. "Permission denied" errors
- Run Command Prompt as Administrator
- Or use: `pip install --user [package]`

#### 4. Python not found
- Install Python from: https://python.org
- Make sure to check "Add Python to PATH" during installation

## Testing Without Audio

The app includes a **simulation mode** that works without any audio hardware:

1. If audio libraries fail to install, the app automatically uses simulation
2. You'll see mock transcription data for testing the UI
3. All features work except real audio input

## Getting Your AssemblyAI API Key

1. Go to: https://www.assemblyai.com/
2. Sign up for a free account
3. Get $50 in free credits
4. Copy your API key to the `.env` file

## Verification

To verify everything is working:

1. **Check Python version:**
   ```bash
   python --version
   ```
   (Should be 3.8 or higher)

2. **Test basic imports:**
   ```bash
   python -c "import streamlit, assemblyai, numpy; print('Basic imports OK')"
   ```

3. **Test audio (optional):**
   ```bash
   python -c "import sounddevice; print('Audio OK')"
   ```

## Running the App

Once everything is installed:

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Features Available

- ✅ Real-time transcription (with AssemblyAI API key)
- ✅ Sentiment analysis
- ✅ Tone detection  
- ✅ Accessibility features
- ✅ Performance monitoring
- ✅ High contrast mode
- ✅ Scalable text
- 🔄 Audio input (requires sounddevice or uses simulation)

## Need Help?

1. Check the error messages in the terminal
2. Try the minimal installation first
3. Use simulation mode for testing without audio
4. Make sure your AssemblyAI API key is correct

The app is designed to work even with limited dependencies - you can test all the UI features in simulation mode!