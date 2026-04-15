# 🚀 QUICK START GUIDE

## Get Started in 3 Steps!

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python run_local.py
```

### Step 3: Open Your Browser
Go to: **http://localhost:5000**

That's it! 🎉

---

## What You Get

✅ **Dashboard** with real-time metrics  
✅ **SQLite Database** with sample data  
✅ **Interactive Charts** showing trends  
✅ **Activity Feed** with recent events  
✅ **Modular Components** for easy customization  

---

## Common Commands

### Run the Dashboard
```bash
python run_local.py
```

### Database Management
```bash
# View database info
python db_manager.py info

# Reset database
python db_manager.py clear
python db_manager.py seed

# Backup database
python db_manager.py backup
```

---

## File Structure Overview

```
📦 Your Dashboard
├── 🐍 app.py              ← Main application
├── 🗄️ database.py         ← Database models
├── 🔧 db_manager.py       ← Database tools
├── ▶️ run_local.py        ← Easy starter
├── 📁 templates/
│   ├── dashboard.html     ← Main page
│   └── components/        ← Reusable parts
├── 💾 dashboard.db        ← Your data
└── 📖 README.md          ← Full documentation
```

---

## Need Help?

- Full documentation: `README.md`
- Database help: `python db_manager.py help`
- Issues? Check the Troubleshooting section in README.md

---

## Customize Your Dashboard

1. **Change colors**: Edit `templates/components/styles.css`
2. **Add metrics**: Modify `database.py` and seed data
3. **New components**: Create HTML files in `templates/components/`
4. **API changes**: Update `app.py`

Enjoy your dashboard! 📊✨
