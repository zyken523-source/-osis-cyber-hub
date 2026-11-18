import asyncio
import httpx
import phonenumbers
from phonenumbers import carrier, geocoder, timezone as pn_tz, number_type, PhoneNumberType
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import urllib.parse
import re

app = FastAPI()

# --- HTML UI DISISIPKAN LANGSUNG DI SINI ---
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="id" class="dark">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSIS // Cyber Hub</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&display=swap');
        body { font-family: 'Fira Code', monospace; background-color: #050505; color: #00ff41; }
        .neon-btn { background: transparent; border: 1px solid #00ff41; transition: all 0.2s; }
        .neon-btn:hover { background: #00ff41; color: #000; box-shadow: 0 0 20px #00ff41; }
        .terminal-box { background: #0a0a0a; border: 1px solid #1a1a1a; }
        ::-webkit-scrollbar { width: 8px; } ::-webkit-scrollbar-track { background: #000; } ::-webkit-scrollbar-thumb { background: #00ff41; }
    </style>
</head>
<body class="min-h-screen p-6">
    <div class="max-w-6xl mx-auto">
        <header class="flex items-center justify-between mb-8 border-b border-green-900 pb-4">
            <h1 class="text-3xl font-bold tracking-widest text-glow">OSIS // CYBER HUB</h1>
        </header>
        <div class="terminal-box p-6 rounded-lg mb-8">
            <label class="block text-sm mb-2 text-green-500">TARGET PHONE NUMBER</label>
            <div class="flex flex-col md:flex-row gap-4">
                <input type="text" id="phoneInput" placeholder="+6281234567890" class="flex-1 bg-black border border-green-800 p-3 text-green-400 focus:outline-none focus:border-green-500">
                <button onclick="startScan()" id="scanBtn" class="neon-btn px-8 py-3 font-bold uppercase tracking-wider">Execute Scan</button>
            </div>
        </div>
        <div id="results" class="hidden grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-6">
                <div class="terminal-box p-4 rounded"><h2 class="text-lg border-b border-green-900 pb-2 mb-3 text-green-300">>> Target Info</h2><ul id="targetInfo" class="text-sm space-y-1 text-gray-300"></ul></div>
                <div class="terminal-box p-4 rounded"><h2 class="text-lg border-b border-green-900 pb-2 mb-3 text-green-300">>> Name Trace (GetContact)</h2><div id="nameTrace" class="text-sm text-gray-300">Menganalisis...</div></div>
            </div>
            <div class="space-y-6">
                <div class="terminal-box p-4 rounded"><h2 class="text-lg border-b border-green-900 pb-2 mb-3 text-green-300">>> Platform Footprint</h2><div id="osisResults" class="grid grid-cols-2 gap-2 text-sm"></div></div>
                <div class="terminal-box p-4 rounded"><h2 class="text-lg border-b border-green-900 pb-2 mb-3 text-green-300">>> Dork Queries</h2><div id="dorkResults" class="space-y-2 text-xs"></div></div>
            </div>
        </div>
    </div>
    <script>
        async function startScan() {
            const phone = document.getElementById('phoneInput').value;
            if (!phone) return alert("Masukkan nomor!");
            const btn = document.getElementById('scanBtn');
            btn.innerText = "SCANNING..."; btn.disabled = true;
            document.getElementById('results').classList.add('hidden');
            try {
                const res = await fetch('/api/scan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone: phone }) });
                const data = await res.json();
                if(data.error) { alert(data.error); return; }
                renderResults(data); document.getElementById('results').classList.remove('hidden');
            } catch (e) { alert("Error: " + e.message); } finally { btn.innerText = "Execute Scan"; btn.disabled = false; }
        }
        function renderResults(data) {
            const info = data.info;
            document.getElementById('targetInfo').innerHTML = `<li><span class="text-green-600">E164:</span> ${info.e164}</li><li><span class="text-green-600">Valid:</span> ${info.valid}</li><li><span class="text-green-600">Carrier:</span> ${info.carrier}</li><li><span class="text-green-600">Region:</span> ${info.region}</li>`;
            const trace = data.name_trace;
            if (trace.length > 0) {
                let html = `<ul class="space-y-2">`;
                trace.forEach(n => { html += `<li class="border-b border-gray-800 pb-1 text-yellow-400 font-bold">${n}</li>`; });
                document.getElementById('nameTrace').innerHTML = html + `</ul>`;
            } else { document.getElementById('nameTrace').innerHTML = `<span class="text-gray-500">Tidak ada nama yang terdeteksi.</span>`; }
            const osisDiv = document.getElementById('osisResults'); osisDiv.innerHTML = '';
            data.osis_results.forEach(r => {
                const isReg = r.status === 'registered'; const badge = isReg ? 'bg-green-900 text-green-300' : 'bg-gray-800 text-gray-400';
                osisDiv.innerHTML += `<div class="flex items-center justify-between p-2 bg-black border border-gray-800 rounded"><span class="uppercase text-xs">${r.platform}</span><span class="px-2 py-1 text-[10px] rounded ${badge}">${r.status}</span></div>`;
            });
            const dorkDiv = document.getElementById('dorkResults'); dorkDiv.innerHTML = '';
            for (const [key, query] of Object.entries(data.dorks)) { dorkDiv.innerHTML += `<div class="bg-black p-2 border border-gray-800 rounded"><span class="text-green-600 uppercase font-bold">[${key}]</span><div class="text-gray-400 break-all mt-1">${query}</div></div>`; }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_CONTENT

class ScanRequest(BaseModel):
    phone: str

# --- LOGIKA OSINT & CHECKER ---
def get_phone_info(raw_phone):
    try:
        pn = phonenumbers.parse(raw_phone, "ID")
        return {
            "e164": phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164),
            "noplus": f"{pn.country_code}{pn.national_number}",
            "cc": str(pn.country_code),
            "national": str(pn.national_number),
            "valid": phonenumbers.is_valid_number(pn),
            "carrier": carrier.name_for_number(pn, "en") or "Unknown",
            "region": phonenumbers.region_code_for_number(pn) or "Unknown"
        }
    except:
        return None

async def check_whatsapp(client, info):
    try:
        r = await client.post("https://v.whatsapp.net/v2/exist", data={"cc": info["cc"], "in": info["national"]}, headers={"User-Agent": "WhatsApp/2.24.6.77"})
        if "exists=true" in r.text: return "registered"
        if "exists=false" in r.text: return "not_registered"
    except: pass
    try:
        r = await client.get(f"https://wa.me/{info['noplus']}")
        if "Phone number shared via url is invalid" in r.text: return "not_registered"
        if r.status_code == 200: return "registered"
    except: pass
    return "unknown"

async def check_instagram(client, info):
    try:
        r = await client.post("https://i.instagram.com/api/v1/accounts/check_phone_number/", data={"phone_number": info["e164"]}, headers={"X-IG-App-ID": "936619743392459"})
        if "phone_number_taken" in r.text: return "registered"
        if '"status":"ok"' in r.text: return "not_registered"
    except: pass
    return "unknown"

async def trace_name(client, info):
    queries = [f'"{info["e164"]}" OR "{info["noplus"]}" ("nama" OR "name")', f'"{info["e164"]}" site:facebook.com OR site:linkedin.com']
    found = []
    for q in queries:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"
        try:
            r = await client.get(url)
            matches = re.findall(r'<a rel="nofollow" class="result__a" href="([^"]+)">(.*?)</a>', r.text)
            for _, title in matches:
                clean_title = re.sub('<[^>]+>', '', title)
                if info["noplus"] in clean_title or info["e164"] in clean_title:
                    name = re.split(r'[-|,]', clean_title)[0].strip()
                    if 2 < len(name) < 30 and not any(c.isdigit() for c in name):
                        found.append(name)
        except: pass
    return list(set(found))[:3] # Ambil 3 nama unik

@app.post("/api/scan")
async def api_scan(req: ScanRequest):
    info = get_phone_info(req.phone)
    if not info: return {"error": "Format nomor tidak valid"}

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        wa, ig, names = await asyncio.gather(
            check_whatsapp(client, info),
            check_instagram(client, info),
            trace_name(client, info)
        )

    return {
        "info": info,
        "osis_results": [
            {"platform": "WhatsApp", "status": wa},
            {"platform": "Instagram", "status": ig},
        ],
        "name_trace": names,
        "dorks": {
            "umum": f'"{info["e164"]}" | "{info["noplus"]}"',
            "sosmed": f'site:linkedin.com OR site:facebook.com "{info["noplus"]}"'
        }
}
