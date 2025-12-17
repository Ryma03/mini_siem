# Quick Start Guide - Enhanced Mini SIEM

## ✨ What's New

Your Mini SIEM now has:
1. ✅ **Real-time Dashboard** - Live alert updates with WebSockets
2. ✅ **Interactive Charts** - 4 different analytics visualizations
3. ✅ **Advanced Search** - Filter by IP, signature, severity, date range

---

## 🚀 How to Run (3 Steps)

### **Step 1: Install Enhanced Libraries** (if needed)
```powershell
cd C:\Users\LENOVO\Desktop\python\mini_siem
pip install flask-socketio python-socketio python-engineio plotly pandas
```

### **Step 2: Start Alert Generator** (Terminal 1)
```powershell
cd C:\Users\LENOVO\Desktop\python\mini_siem
python siem_orchestrator.py --mock
```

You should see:
```
2025-12-13 10:30:00 - __main__ - INFO - Starting Mini SIEM...
2025-12-13 10:30:00 - __main__ - INFO - Alert stored: SQL Injection Attempt from 192.168.x.x [ID: 1]
```

### **Step 3: Start Web Server** (Terminal 2)
```powershell
cd C:\Users\LENOVO\Desktop\python\mini_siem
python app/main_enhanced.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * WebSocket support enabled
 * Press CTRL+C to quit
```

### **Step 4: Open Dashboard**
```
http://localhost:5000
```

---

## 📊 New Pages

### **1. Real-time Dashboard** (`/`)
- Live alert updates (no refresh needed!)
- 4 interactive charts
- Statistics that update automatically
- Green pulsing indicator shows system is live

**Features:**
- Alerts appear automatically as they're generated
- Charts update with new data
- Statistics refresh every 30 seconds
- All data visualization in real-time

### **2. Advanced Search** (`/search`)
- Search by source IP
- Search by attack signature
- Filter by severity level
- Filter by date range
- Combine multiple filters

**Example Searches:**
```
Find SQL Injection alerts:
→ Search Type: Signature
→ Query: SQL Injection
→ Severity: Any

Find alerts from specific IP:
→ Search Type: Source IP
→ Query: 192.168.1.100
→ Date: Last 7 days

Find critical alerts:
→ Severity: CRITICAL
→ Date From: 2025-12-01
→ Date To: 2025-12-13
```

### **3. Analytics Dashboard** (`/analytics`)
- **Alert Timeline**: Shows alerts per day (last 7 days)
- **Severity Distribution**: Pie chart of alert types
- **Top 10 Attacking IPs**: Which IPs are most active
- **Top 10 Signatures**: Most common attack signatures

**How to use:**
1. Click on chart to interact
2. Hover for exact values
3. Right-click to download as PNG
4. Zoom and pan with mouse

---

## 🎯 Usage Examples

### **Example 1: Monitor Attacks in Real-time**
1. Open dashboard at `http://localhost:5000`
2. Keep page open in background
3. New alerts appear automatically
4. No refresh needed!

### **Example 2: Find and Block Attacking IP**
1. Go to `/search`
2. Enter IP in "Search Query"
3. Set "Search Type" to "Source IP"
4. Click "Search"
5. Click "Block IP" button on results
6. Confirm block

### **Example 3: Analyze Attack Trends**
1. Go to `/analytics`
2. Look at "Alert Timeline" chart
3. Identify peak attack times
4. Check "Top 10 Attacking IPs"
5. Review "Attack Signatures"

### **Example 4: Multi-Filter Search**
1. Go to `/search`
2. Fill in:
   - Search Type: Source IP
   - Severity: HIGH
   - Date From: 2025-12-01
   - Date To: 2025-12-13
3. Click "Search"
4. See only high-severity alerts from that IP in that date range

---

## 📊 Chart Explanations

### **Alert Timeline**
**What it shows:** How many alerts occur each day
**Why it matters:** Spot attack patterns
- Sudden spike = possible attack
- Consistent baseline = normal activity
- Weekend patterns = can identify human-driven attacks

### **Severity Distribution**
**What it shows:** Pie chart of alert severity levels
**Why it matters:** Understand threat landscape
- High % CRITICAL = serious threats
- Mostly LOW = probably scanning
- Mixed = varied threat types

### **Top 10 Attacking IPs**
**What it shows:** Which IPs generate most alerts
**Why it matters:** Identify repeat attackers
- Top IPs = priority for blocking
- Patterns = organized attacks
- New IPs = reconnaissance

### **Top 10 Signatures**
**What it shows:** Most common attack types
**Why it matters:** Know your vulnerabilities
- Popular = your systems are targets
- Rare = newer attack methods
- Trends = emerging threats

---

## ⚙️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+Shift+R` | Hard refresh (clear cache) |
| `F12` | Open developer console |
| Right-click on chart | Download as PNG |

---

## 🔌 Real-time Features Explained

### **How WebSocket Works**
1. Your browser connects to server
2. When new alert arrives, server broadcasts it
3. Your page receives update instantly
4. Alert appears in table with animation
5. No page refresh needed!

### **What Updates in Real-time**
- ✅ Alert table (new rows appear)
- ✅ Total alerts count
- ✅ Unique IPs count
- ✅ Correlation count
- ❌ Charts (update every 30 seconds)

---

## 📈 Performance Tips

### **For Faster Charts:**
- Clear old alerts: `python -c "from core.database import DatabaseManager; DatabaseManager().clear_old_alerts(7)"`
- Reduce data: Charts only use last 1000 alerts
- Disable other tabs: Reduces server load

### **For Faster Search:**
- Use date filters: Narrow down to relevant period
- Start with IP search: Usually faster than signature
- Combine filters: Reduces result set

### **For Real-time Dashboard:**
- Close unused tabs: Reduces WebSocket connections
- Modern browser: Better performance with Chrome/Edge
- Good internet: Smoother updates

---

## 🐛 Troubleshooting

### **Charts not showing**
```powershell
# Clear browser cache with Ctrl+Shift+R
# If still not working, check if you have alerts:
python -c "from core.database import DatabaseManager; print(DatabaseManager().get_alert_count())"
```

### **Real-time updates not working**
```powershell
# Make sure you're using main_enhanced.py, not main.py
# Check browser console (F12) for WebSocket errors
# Verify port 5000 is not blocked by firewall
```

### **Search returning no results**
```powershell
# Try searching without filters first
# Check that orchestrator is still running and generating alerts
# Look at /api/stats to see total alert count
```

### **Page loads slowly**
```powershell
# Too many alerts in database (> 10,000)
# Clear old alerts: python -c "from core.database import DatabaseManager; DatabaseManager().clear_old_alerts(7)"
# Restart web server
```

---

## 📞 Support

### **Check Logs:**
```powershell
# View application logs
type mini_siem.log

# Or in real-time
Get-Content -Path mini_siem.log -Tail 20 -Wait
```

### **Common Issues:**
| Issue | Solution |
|-------|----------|
| Port 5000 in use | Kill process or use different port in main_enhanced.py |
| WebSocket fails | Use modern browser (Chrome, Edge, Firefox) |
| Charts blank | Ensure alerts exist in database |
| Search slow | Use date filters to narrow results |

---

## 🎓 Learning Resources

### **Understanding the Architecture:**
```
Real-time Flow:
    Orchestrator → New Alert
         ↓
    Database → Insert Alert
         ↓
    Flask Server → WebSocket Emit
         ↓
    Your Browser → Receive & Display
```

### **File Locations:**
```
Main App:     app/main_enhanced.py
Templates:    app/templates/
Database:     data/alerts.db
Logs:         mini_siem.log
Config:       config.py
```

---

## 🚀 Next Steps

1. **Explore the Dashboard** - Click around, try different pages
2. **Test Real-time Updates** - Watch alerts appear live
3. **Try Advanced Search** - Find specific alerts
4. **Check Analytics** - Understand your threat landscape
5. **Block Malicious IPs** - Use the Block IP feature
6. **Review Charts** - Export data for reports

---

## 💡 Pro Tips

1. **Keep Dashboard Open** - Best way to see attacks as they happen
2. **Use Date Filters** - Faster searches with narrower date ranges
3. **Export Charts** - Right-click charts to save analysis as PNG
4. **Combine Filters** - Use multiple criteria for precise results
5. **Check Statistics** - See trend summaries at a glance

---

## 📋 Checklists

### **Daily Check:**
- [ ] Open dashboard `/`
- [ ] Review new alerts
- [ ] Check `/analytics` for trends
- [ ] Block any suspicious IPs
- [ ] Document findings

### **Weekly Review:**
- [ ] Analyze alert patterns
- [ ] Review top attacking IPs
- [ ] Check most common signatures
- [ ] Generate report (export charts)
- [ ] Share with team

---

**Version:** 2.0 (Enhanced)  
**Ready to go!** 🎉

Any questions? Check the browser console (F12) for error messages!
