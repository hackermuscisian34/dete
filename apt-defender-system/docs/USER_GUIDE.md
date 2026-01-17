# APT Defender - User Setup Guide

**For Non-Technical Users**

## 📦 What's in the Box

- 1× Raspberry Pi 4B (small green computer)
- 1× Power adapter
- 1× QR code card
- 1× USB stick (installer)
- 1× Quick start guide (this document)

## 🚀 Setup (5 Minutes)

### Step 1: Set Up the Raspberry Pi

1. **Plug in the Raspberry Pi**
   - Connect the power adapter to the Raspberry Pi
   - Plug into wall outlet
   - Connect ethernet cable to your router
   
2. **Wait for green LED**
   - The device will start automatically
   - Wait until the green LED blinks steadily (about 1 minute)
   - ✅ Ready when LED blinks once per second

### Step 2: Install on Your Computer

**Windows:**
1. Insert USB stick
2. Open "USB Drive" in File Explorer
3. Double-click `APTDefender-Setup.msi`
4. Click "Next" → "Install" → "Finish"
5. A code will appear on screen — **write it down**

**Mac:**
1. Insert USB stick
2. Open the USB drive
3. Double-click `APTDefender.pkg`
4. Follow the installer
5. A code will appear — **write it down**

### Step 3: Connect Your Phone

1. **Download the app**
   - iPhone: Search "APT Defender" in App Store
   - Android: Search "APT Defender" in Play Store

2. **Scan QR Code**
   - Open the app
   - Tap "Add Device"
   - Scan the QR code on the card you received
   
3. **Enter Pairing Code**
   - Type the code from your computer screen
   - Tap "Pair"
   
4. **✅ Done!**
   - You'll see your computer listed
   - Protection is now active

## 📱 Daily Use

### You Don't Have to Do Anything!

The system runs silently in the background. You'll only hear from it if there's a threat.

### If You Get an Alert

You'll receive a phone notification like:

```
🔴 APT Defender Alert
Threat detected on My Laptop
Tap to review →
```

**What to do:**

1. Open the alert
2. Read the plain-English explanation
3. Tap the big green "REMOVE THREAT" button
4. Done — you're protected

### Understanding Alerts

**What you'll see:**
- Clear explanation (no technical jargon)
- Risk level (HIGH, MEDIUM, LOW)
- One big action button

**Example:**
```
⚠️ THREAT DETECTED

A suspicious program tried to secretly
start with your computer. This is common
in malware.

File: startup_helper.exe
Risk: HIGH

[REMOVE THREAT 👍]
```

## 🎮 App Features

### Home Screen — Your Devices

Shows all protected computers with:
- 🟢 Green = Safe
- 🔴 Red = Threat Found
- ⚫ Gray = Offline

Tap any device to see details.

### Device Screen — Actions

Large buttons for:
- **Scan Now** — Check for threats right now
- **Lock** — Lock the computer screen
- **Block Network** — Disconnect from internet
- **Shutdown** — Turn off the computer

⚠️ **Warning Actions** (Yellow buttons):
- Use when something seems wrong
- Safe to use, won't harm your files

🚨 **Emergency Actions** (Red buttons):
- Use only for serious threats
- Will stop the computer to protect you

### Alerts Tab

See all security notifications in one place.
Tap any alert to see full details and take action.

## ❓ Common Questions

**Q: Will this slow down my computer?**  
A: No. The helper program uses less than 1% of your computer's resources.

**Q: What if I'm traveling?**  
A: The protection works anywhere. You can control it from your phone over the internet.

**Q: Can I turn it off?**  
A: Yes, but we don't recommend it. Open the app → Settings → Pause Protection.

**Q: What if my phone battery dies?**  
A: Protection continues automatically. You just can't see alerts until your phone charges.

**Q: How often does it scan?**  
A: Automatically every 24 hours, plus whenever you tap "Scan Now".

**Q: What happens to threats?**  
A: They're moved to a safe quarantine folder. You can restore them if it was a mistake.

## 🆘 Troubleshooting

### Computer Shows "Offline"

1. Make sure computer is powered on
2. Check that Raspberry Pi has power and ethernet
3. Restart the computer
4. If still offline, contact support

### Can't Scan QR Code

1. Make sure camera permission is allowed
2. Try better lighting
3. If QR code is damaged, contact support for a new one

### App Says "Cannot Connect"

1. Check your phone's internet connection
2. Make sure you're on WiFi (not cellular)
3. Make sure Raspberry Pi is powered on
4. Restart the app

## 📞 Support

**Email:** support@apt-defender.local  
**Phone:** +1 (555) 123-4567  
**Hours:** 24/7

Include in your message:
- Your device name (shown in app)
- What you were trying to do
- Screenshot if possible

## 🔒 Privacy

- All data stays on YOUR Raspberry Pi
- Nothing is sent to the cloud (unless you enable optional backup)
- We cannot see your files or data
- You own and control everything

## 📋 Maintenance

### Monthly:
- Check that Raspberry Pi LED is blinking
- Verify app shows device as "Online"

### Yearly:
- Check for system updates (app will notify you)

### That's It!

No cleaning, no manual scans, no complicated settings.

---

**Need Help?**  
Contact support any time — we're here to help, and questions are always welcome!
