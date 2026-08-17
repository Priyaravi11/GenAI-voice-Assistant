# QUICK START - GET RUNNING IN 5 MINUTES

## 1️⃣ GET GEMINI API KEY (2 minutes)

Go to: https://aistudio.google.com/

Click "Get API Key" → "Create API Key"

Copy the key (looks like: `AIzaSy...`)

## 2️⃣ SETUP BACKEND (2 minutes)

**Terminal 1:**
```bash
cd C:\PROJECTS\GenAI-voice-Assistant
python -m venv venv
venv\Scripts\activate
pip install -r backend/requirements.txt
```

## 3️⃣ CREATE .ENV FILE (1 minute)

```bash
copy .env.example .env
```

Edit `.env` and add your key:
```
GEMINI_API_KEY=AIzaSy...
```

## 4️⃣ START BACKEND (1 minute)

```bash
uvicorn backend.app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 5️⃣ START FRONTEND (1 minute)

**Terminal 2:**
```bash
cd frontend
npm install
npm run dev
```

You should see:
```
VITE v6.4.3  ready in 342 ms
  ➜  Local:   http://localhost:5173/
```

## 6️⃣ OPEN IN BROWSER

Go to: **http://localhost:5173**

## 7️⃣ TEST AUDIO

1. Click microphone icon
2. Say something: "What's my bill?"
3. Gemini will respond with audio + text
4. Done! ✅

---

## WHAT YOU HAVE RUNNING

```
Frontend:       http://localhost:5173
Backend:        http://localhost:8000
API Docs:       http://localhost:8000/docs
WebSocket:      ws://localhost:8000/ws/voice/{sessionId}
```

## FEATURES ENABLED

✅ Real-time audio streaming (Gemini Live)
✅ Text queries
✅ Knowledge base (RAG)
✅ Telecom tools (mock data)
✅ Multi-language support
✅ Voice response

## OPTIONAL (Can Add Later)

⚠️ MongoDB - for persistent data
⚠️ Redis - for caching
⚠️ JWT Auth - for security
⚠️ Docker - for deployment

## TROUBLESHOOTING

**"Port 8000 in use?"**
```bash
uvicorn backend.app.main:app --port 8001
```

**"Microphone not working?"**
- Check browser permission
- Must use localhost (not IP)
- Or use HTTPS

**"API key not found?"**
- Edit .env again
- Restart backend

**"Can't hear audio?"**
- Check browser volume
- Check system volume
- Check microphone connected

## FULL DOCUMENTATION

- Setup guide: `NO_DOCKER_GUIDE.md`
- Component guide: `REQUIRED_VS_OPTIONAL.md`
- Deployment guide: `DEPLOYMENT_GUIDE.md`
- Full summary: `IMPLEMENTATION_SUMMARY.md`

## STOP EVERYTHING

Press `Ctrl+C` in both terminals.

That's it! Everything saves to disk automatically.

---

## NEXT TIME YOU START

```bash
# Terminal 1
cd C:\PROJECTS\GenAI-voice-Assistant
venv\Scripts\activate
uvicorn backend.app.main:app --reload

# Terminal 2
cd frontend
npm run dev

# Open browser
http://localhost:5173
```

No reinstalling, no setup - everything already done!

---

## EXPECTED OUTPUT

### Backend
```
MongoDB connection warning: localhost:27017...
Embedding model loaded successfully.
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Frontend
```
VITE v6.4.3  ready in 342 ms
  ➜  Local:   http://localhost:5173/
```

### Browser
```
Frontend loads at localhost:5173
Shows voice interface
Ready to accept audio input
```

## THAT'S IT!

You now have a fully functional multilingual voice assistant with real-time audio streaming.

Enjoy! 🎉
