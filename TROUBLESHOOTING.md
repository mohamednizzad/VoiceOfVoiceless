# VoiceAccess Troubleshooting Guide

## Common Issues and Solutions

### 1. AssemblyAI Model Deprecated Error

**Error Message:**
```
Model deprecated. See docs for new model information: https://www.assemblyai.com/docs/speech-to-text/universal-streaming
```

**Solution:**
```bash
# Run the fix script
python fix_assemblyai.py

# Or manually update AssemblyAI
pip install --upgrade assemblyai
```

**What was fixed:**
- Updated to latest AssemblyAI SDK version
- Added fallback connection logic
- Improved error handling for deprecated models
- Added automatic fallback to mock service

### 2. Audio Input Overflow

**Error Message:**
```
Audio callback status: input overflow
```

**Solution:**
This is now handled automatically with:
- Reduced chunk size (512 samples instead of 1024)
- Increased buffer size (8192 instead of 4096)
- Better queue management with overflow handling
- Low-latency audio settings

**Manual fixes if needed:**
```python
# In .env file, adjust these settings:
AUDIO_CHUNK_SIZE=256  # Even smaller chunks
BUFFER_SIZE=16384     # Larger buffer
```

### 3. Connection Issues

**Symptoms:**
- "Not currently recording" messages
- WebSocket connection errors
- Frequent disconnections

**Solutions:**

1. **Check API Key:**
   ```bash
   # Verify your .env file has:
   ASSEMBLYAI_API_KEY=your_actual_api_key_here
   ```

2. **Test API Key:**
   ```python
   import assemblyai as aai
   aai.settings.api_key = "your_key"
   # Should not raise an error
   ```

3. **Network Issues:**
   - Check firewall settings
   - Try different network connection
   - Disable VPN if using one

### 4. Installation Issues

**sounddevice installation fails:**
```bash
# Try these alternatives:
pip install sounddevice --no-cache-dir
# Or use conda:
conda install -c conda-forge python-sounddevice
# Or use the fallback:
# The app will automatically use simulation mode
```

**General installation issues:**
```bash
# Use the automated installer:
python install_dependencies.py

# Or minimal installation:
pip install -r requirements-minimal.txt
```

### 5. Performance Issues

**High CPU Usage:**
- Close unnecessary applications
- Reduce audio quality in settings
- Use smaller chunk sizes

**High Memory Usage:**
- Restart the application periodically
- Clear transcript history
- Reduce buffer sizes

**High Latency:**
- Check network connection
- Reduce audio chunk size
- Close bandwidth-heavy applications

### 6. Accessibility Issues

**Text too small:**
- Use the font size slider in sidebar
- Enable "Large Text Mode"
- Adjust browser zoom level

**Poor contrast:**
- Enable "High Contrast Mode"
- Try different color themes
- Adjust monitor brightness

**Keyboard navigation not working:**
- Make sure focus is not in input fields
- Use Tab to navigate between elements
- Try the keyboard shortcuts:
  - Space: Start/Stop recording
  - S: Go to settings
  - H: Open help

### 7. Mock/Simulation Mode

**When does it activate:**
- No API key provided
- API connection fails
- Model deprecated errors
- Audio hardware issues

**Features available in mock mode:**
- ✅ All UI features
- ✅ Simulated transcription
- ✅ Sentiment analysis demo
- ✅ Tone detection demo
- ✅ Performance monitoring
- ✅ Accessibility features
- ❌ Real audio input

### 8. Debugging Steps

**Enable debug logging:**
```python
# Add to .env file:
DEBUG_MODE=True
LOG_LEVEL=DEBUG
```

**Check system requirements:**
```bash
python --version  # Should be 3.8+
pip list | grep assemblyai  # Check version
pip list | grep streamlit   # Check version
```

**Test components individually:**
```bash
# Test audio:
python -c "import sounddevice; print('Audio OK')"

# Test AssemblyAI:
python -c "import assemblyai; print('AssemblyAI OK')"

# Test Streamlit:
python -c "import streamlit; print('Streamlit OK')"
```

### 9. Getting Help

**Check logs:**
- Look at the terminal output when running the app
- Check the `logs/` directory if it exists
- Enable debug mode for more detailed logs

**Gather information:**
- Python version
- Operating system
- Error messages (full stack trace)
- Steps to reproduce the issue

**Resources:**
- [AssemblyAI Documentation](https://www.assemblyai.com/docs/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Project GitHub Repository](your-repo-link)

### 10. Quick Fixes Summary

**For immediate testing:**
```bash
# 1. Update AssemblyAI
pip install --upgrade assemblyai

# 2. Run the app
streamlit run app.py

# 3. If issues persist, use mock mode by removing API key temporarily
```

**For production use:**
```bash
# 1. Run the comprehensive fix
python fix_assemblyai.py

# 2. Verify all dependencies
python install_dependencies.py

# 3. Test with your API key
streamlit run app.py
```

The application is designed to be resilient and will automatically fall back to simulation mode if real-time transcription isn't available, ensuring you can always test and demonstrate the features.