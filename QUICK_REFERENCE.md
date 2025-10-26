# Quick Reference Card - Trading Chatbot System

## 🚀 Quick Start Commands

### Start Everything
```powershell
cd docker && docker-compose up -d && cd ..
```

### Check Health
```powershell
.\scripts\health_check.ps1
```

### Run Evaluation
```powershell
python eval_client_simple.py --limit 5
```

### View Logs
```powershell
cd docker && docker-compose logs -f app
```

### Stop Everything
```powershell
cd docker && docker-compose down && cd ..
```

---

## 📁 Project Structure

```
trade_system/
├── src/              # Application source
├── scripts/          # Operational scripts
├── frontend/         # Streamlit UI
├── docker/           # Docker configs
├── tests/            # Test suite
├── logs/             # Log files
└── docs/             # Documentation
```

---

## 🔧 Common Tasks

### Development
```powershell
# Start backend
cd docker; docker-compose up -d; cd ..

# Start frontend
cd frontend; .\START.bat

# Run tests
pytest tests/ -v

# Quick eval
python eval_client_simple.py --limit 5
```

### Deployment
```powershell
# Deploy to staging
.\scripts\deploy.ps1 -Environment staging

# Deploy to production
.\scripts\deploy.ps1 -Environment production

# Health check
.\scripts\health_check.ps1
```

### Troubleshooting
```powershell
# Check logs
cd docker; docker-compose logs -f app

# Restart services
cd docker; docker-compose restart app

# Rebuild
cd docker; docker-compose up --build -d

# Clean rebuild
cd docker; docker-compose down -v
docker system prune -a
docker-compose up --build -d
```

---

## 📊 Key Endpoints

- **API Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health
- **Chat:** POST http://localhost:8000/chat
- **Eval:** GET http://localhost:8000/evaluate/groundtruth
- **Metrics:** http://localhost:8000/metrics
- **Frontend:** http://localhost:8501
- **Langfuse:** http://localhost:3000

---

## 🔍 Health Check Quick Test

```powershell
# Backend
curl http://localhost:8000/health

# Chat test
$body = @{ message = "What is CSE?" } | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/chat -Method POST -Body $body -ContentType "application/json"

# Eval test
python eval_client_simple.py --limit 1
```

---

## 📝 File Locations

- **Config:** `src/config/settings.py`
- **Main App:** `src/main.py`
- **Data:** `src/data/` (faq.txt, policies.txt, etc.)
- **Ground Truth:** `src/data/ground_truth/test_qa_pairs.json`
- **Logs:** `logs/`
- **Scripts:** `scripts/`
- **Env File:** `.env`

---

## 🎯 Performance Metrics

- **Chat Latency:** ~8-10 sec (avg)
- **RAG Retrieval:** ~500ms (avg)
- **Keyword Match:** ~50-100ms (parallel)
- **Eval (31 cases):** ~3-5 min
- **Pass Rate:** ~90-95%

---

## 🔒 Security Checklist

Production Requirements:
- [ ] API authentication enabled
- [ ] HTTPS/TLS configured
- [ ] CORS origins restricted (not "*")
- [ ] Rate limiting configured
- [ ] Secrets in env vars
- [ ] Log aggregation setup
- [ ] Monitoring alerts active

---

## 📚 Documentation

- `README.md` - Complete setup guide
- `PRODUCTION_READINESS.md` - Production assessment
- `OPTIMIZATION_SUMMARY.md` - Change summary
- `EVALUATION_FIXED.md` - Evaluation guide
- `docker/READ.md` - Docker guide

---

## ⚡ Emergency Commands

### If system is down
```powershell
cd docker
docker-compose down
docker-compose up -d
.\scripts\health_check.ps1
```

### If database is corrupted
```powershell
cd docker
docker-compose down -v
docker-compose up -d
# Wait for services to start
python scripts/ingest_data_files.py
```

### If evaluation fails
```powershell
# Quick test
python eval_client_simple.py --limit 1

# Check backend
curl http://localhost:8000/health

# View logs
cd docker; docker-compose logs -f app
```

---

## 🎨 Color Codes in Logs

- 🟢 **Green (✅)** - Success
- 🔴 **Red (❌)** - Error/Failure
- 🟡 **Yellow (⚠️)** - Warning
- 🔵 **Blue (ℹ️)** - Info

---

## 💡 Tips

1. Always check health after deployment
2. Run quick eval (limit 5) for rapid validation
3. Monitor logs during first hour of deployment
4. Keep backups before major changes
5. Use scripts/ directory for custom tools
6. Document any manual configuration changes

---

## 🆘 Support

**Issues?**
1. Check `.\scripts\health_check.ps1`
2. Review logs: `cd docker && docker-compose logs -f`
3. See PRODUCTION_READINESS.md troubleshooting section
4. Check GitHub issues

**Quick Fixes:**
- Restart: `cd docker; docker-compose restart app`
- Rebuild: `cd docker; docker-compose up --build -d`
- Clean: `cd docker; docker-compose down -v; docker-compose up -d`

---

**Version:** 1.0.1  
**Last Updated:** October 26, 2025  
**Status:** ✅ Production Ready (pending security enhancements)
