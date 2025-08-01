# OBS WebSocket Setup Guide

## Step 1: Open OBS Studio
Launch OBS Studio on your Mac.

## Step 2: Enable WebSocket Server
1. In OBS, go to the menu bar: **Tools → WebSocket Server Settings**
2. Check the box: **"Enable WebSocket server"**
3. (Optional) Set a password - leave blank for testing
4. Note the Server Port (default: 4455)
5. Click **"OK"**

## Step 3: Create Test Scenes
Let's create some test scenes:
1. In the Scenes panel (bottom left), click the **+** button
2. Create these scenes:
   - "Main"
   - "Gaming" 
   - "Starting Soon"
   - "Be Right Back"

## Step 4: Add Test Sources
1. Select the "Main" scene
2. In Sources panel, click **+** and add:
   - **Display Capture** (to capture your screen)
   - **Audio Input Capture** (if you have a microphone)
   - **Text** (add some test text)

## Step 5: Test the Connection
Run our test script:
```bash
source venv/bin/activate
python test_connection.py
```

If you set a password:
```bash
python test_connection.py your_password_here
```

## Troubleshooting

### "Connection refused" error:
- Make sure OBS is running
- Check that WebSocket is enabled
- Verify the port number (default 4455)

### "Authentication failed" error:
- Check your password in OBS settings
- Try with no password first (leave field blank in OBS)

### Still having issues?
- Restart OBS after enabling WebSocket
- Check if any firewall is blocking port 4455
- Try connecting to 127.0.0.1 instead of localhost