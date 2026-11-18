import streamlit as st
import asyncio
import httpx
import phonenumbers
from phonenumbers import carrier
import urllib.parse
import re

st.set_page_config(page_title="OSIS Cyber Hub", page_icon="🕵️‍♂️", layout="wide")

st.title("🕵️‍♂️ OSIS // Cyber Hub")
st.write("Pemetaan Nomor HP ke Akun & GetContact OSINT")

async def check_whatsapp(client, info):
    try:
        r = await client.post("https://v.whatsapp.net/v2/exist", data={"cc": info["cc"], "in": info["national"]}, headers={"User-Agent": "WhatsApp/2.24.6.77"})
        if "exists=true" in r.text: return "Registered"
        if "exists=false" in r.text: return "Not Registered"
    except: pass
    return "Unknown"

async def check_instagram(client, info):
    try:
        r = await client.post("https://i.instagram.com/api/v1/accounts/check_phone_number/", data={"phone_number": info["e164"]}, headers={"X-IG-App-ID": "936619743392459"})
        if "phone_number_taken" in r.text: return "Registered"
        if '"status":"ok"' in r.text: return "Not Registered"
    except: pass
    return "Unknown"

async def run_scan(raw_phone):
    try:
        pn = phonenumbers.parse(raw_phone, "ID")
        info = {
            "e164": phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164),
            "noplus": f"{pn.country_code}{pn.national_number}",
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

phone = st.text_input("Masukkan Nomor HP (contoh: 08123456789 atau +628123456789)", "")

if st.button("🚀 Execute Scan", use_container_width=True):
    if not phone:
        st.warning("Masukkan nomor dulu bree!")
    else:
        with st.spinner("Sedang memindai platform..."):
            result = asyncio.run(run_scan(phone))
            
            if result:
                st.success(f"Berhasil scan: {result['e164']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Carrier:** {result['carrier']}")
                with col2:
                    st.info(f"**E164:** {result['e164']}")
                
                st.subheader("📱 Platform Footprint")
                st.write(f"**WhatsApp:** {result['WhatsApp']}")
                st.write(f"**Instagram:** {result['Instagram']}")
                
                st.subheader("🔍 Dork Queries (GetContact OSINT)")
                st.write("Klik link di bawah ini untuk mencari nama pemilik nomor di Google:")
                
                q1 = urllib.parse.quote(f'"{result["e164"]}" OR "{result["noplus"]}"')
                st.markdown(f"- [Cari Jejak Umum di Google](https://www.google.com/search?q={q1})")
                
                q2 = urllib.parse.quote(f'site:facebook.com OR site:linkedin.com "{result["noplus"]}"')
                st.markdown(f"- [Cari Sosial Media di Google](https://www.google.com/search?q={q2})")
                
            else:
                st.error("Format nomor tidak valid!")