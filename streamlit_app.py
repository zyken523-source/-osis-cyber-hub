import streamlit as st
import asyncio
import httpx
import phonenumbers
from phonenumbers import carrier
import urllib.parse

st.set_page_config(page_title="OSIS Cyber Hub", page_icon="🕵️‍♂️", layout="wide")

st.title("🕵️‍♂️ OSIS // Cyber Hub")
st.write("Pemetaan Nomor HP & GetContact OSINT (Bypass Edition)")

async def check_whatsapp(client, info):
    try:
        r = await client.post("https://v.whatsapp.net/v2/exist", data={"cc": info["cc"], "in": info["national"]}, headers={"User-Agent": "WhatsApp/2.24.6.77"})
        if "exists=true" in r.text: return "Registered"
        if "exists=false" in r.text: return "Not Registered"
    except: pass
    return "Unknown (IP Server Diblokir)"

async def check_instagram(client, info):
    try:
        r = await client.post("https://i.instagram.com/api/v1/accounts/check_phone_number/", data={"phone_number": info["e164"]}, headers={"X-IG-App-ID": "936619743392459"})
        if "phone_number_taken" in r.text: return "Registered"
        if '"status":"ok"' in r.text: return "Not Registered"
    except: pass
    return "Unknown (IP Server Diblokir)"

async def run_scan(raw_phone):
    try:
        pn = phonenumbers.parse(raw_phone, "ID")
        # Bikin berbagai format penulisan nomor
        e164 = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)
        intl = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        natl = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.NATIONAL)
        
        info = {
            "e164": e164,
            "intl": intl, # +62 857-2020-3576
            "natl": natl, # 0857-2020-3576
            "cc": str(pn.country_code),
            "national": str(pn.national_number),
            "carrier": carrier.name_for_number(pn, "en") or "Unknown"
        }
    except:
        return None

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        wa, ig = await asyncio.gather(
            check_whatsapp(client, info),
            check_instagram(client, info)
        )
    
    info["WhatsApp"] = wa
    info["Instagram"] = ig
    return info

phone = st.text_input("Masukkan Nomor HP (contoh: 08123456789)", "")

if st.button("🚀 Execute Scan", use_container_width=True):
    if not phone:
        st.warning("Masukkan nomor dulu bree!")
    else:
        with st.spinner("Sedang memindai..."):
            result = asyncio.run(run_scan(phone))
            
            if result:
                st.success(f"Berhasil scan: {result['e164']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Carrier:** {result['carrier']}")
                with col2:
                    st.info(f"**Format:** {result['intl']}")
                
                st.subheader("📱 Platform Footprint (via API Internal)")
                st.write(f"**WhatsApp:** {result['WhatsApp']}")
                st.write(f"**Instagram:** {result['Instagram']}")
                st.caption("*Catatan: 'Unknown' wajar terjadi di server gratis karena IP diblokir oleh WhatsApp/IG.*")
                
                st.divider()
                st.subheader("🔍 Dork Queries (GetContact OSINT)")
                st.write("Klik tombol di bawah ini untuk mencari jejak nama pemilik nomor:")
                
                # Link DuckDuckGo HTML (lebih gampang nembus)
                q_umum = urllib.parse.quote(f'"{result["e164"]}" OR "{result["natl"]}" OR "{result["intl"]}"')
                st.markdown(f"👉 **[Cari Jejak Umum (DuckDuckGo)](https://html.duckduckgo.com/html/?q={q_umum})**")
                
                # Link Google Facebook/LinkedIn
                q_sosmed = urllib.parse.quote(f'site:facebook.com OR site:linkedin.com "{result["natl"]}" OR "{result["intl"]}"')
                st.markdown(f"👉 **[Cari Sosial Media (Google)](https://www.google.com/search?q={q_sosmed})**")
                
                # Link Truecaller (Manual)
                q_true = result["e164"].replace("+", "")
                st.markdown(f"👉 **[Cek Truecaller (Manual)](https://www.truecaller.com/search/id/{q_true})**")
                
            else:
                st.error("Format nomor tidak valid!")