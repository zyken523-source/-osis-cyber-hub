
import streamlit as st
import phonenumbers
from phonenumbers import carrier, geocoder, number_type
import urllib.parse

st.set_page_config(
    page_title="OSIS Cyber Hub",
    page_icon="🕵️",
    layout="wide"
)

st.markdown("""
<style>
.stApp {background:#080d16;color:#e5f5ff}
h1,h2,h3 {color:#00e5ff !important}
.stButton button,.stLinkButton a {
    border:1px solid #00e5ff;
    border-radius:10px;
    width:100%;
}
[data-testid="stMetric"] {
    background:#111c2c;
    padding:15px;
    border-radius:12px;
    border:1px solid #18394d;
}
</style>
""", unsafe_allow_html=True)

st.title("🕵️ OSIS // CYBER HUB")
st.caption("PHONE INTELLIGENCE • SOCIAL FOOTPRINT • LOCATION")
st.info("Public OSINT only. Tidak mengakses akun privat atau GPS seseorang.")

# ==================================
# PHONE ANALYZER
# ==================================

def analyze_phone(raw, region="ID"):
    try:
        pn = phonenumbers.parse(raw, region)

        if not phonenumbers.is_possible_number(pn):
            return None, "Nomor tidak memungkinkan."

        if not phonenumbers.is_valid_number(pn):
            return None, "Nomor tidak valid."

        types = {
            0: "Fixed Line",
            1: "Mobile",
            2: "Fixed Line / Mobile",
            3: "Toll Free",
            4: "Premium Rate",
            5: "Shared Cost",
            6: "VoIP",
            7: "Personal Number",
            8: "Pager",
            9: "UAN",
            10: "Voicemail"
        }

        return {
            "E.164": phonenumbers.format_number(
                pn, phonenumbers.PhoneNumberFormat.E164
            ),
            "International": phonenumbers.format_number(
                pn, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            ),
            "National": phonenumbers.format_number(
                pn, phonenumbers.PhoneNumberFormat.NATIONAL
            ),
            "Country": geocoder.description_for_number(pn, "en") or "Unknown",
            "Carrier": carrier.name_for_number(pn, "en") or "Unknown",
            "Type": types.get(number_type(pn), "Unknown"),
            "Country Code": pn.country_code
        }, None

    except phonenumbers.NumberParseException as e:
        return None, str(e)


# ==================================
# PUBLIC SOCIAL SEARCH
# ==================================

def social_search(phone):
    q = urllib.parse.quote(f'"{phone}"')

    return {
        "Google": f"https://www.google.com/search?q={q}",
        "Instagram": f"https://www.google.com/search?q={q}+site%3Ainstagram.com",
        "Facebook": f"https://www.google.com/search?q={q}+site%3Afacebook.com",
        "TikTok": f"https://www.google.com/search?q={q}+site%3Atiktok.com",
        "LinkedIn": f"https://www.google.com/search?q={q}+site%3Alinkedin.com",
        "Telegram": f"https://www.google.com/search?q={q}+site%3At.me",
        "DuckDuckGo": f"https://html.duckduckgo.com/html/?q={q}",
        "Truecaller": "https://www.truecaller.com/"
    }


# ==================================
# LOCATION INFORMATION
# ==================================

def show_location(data):
    st.subheader("📍 LOCATION INTELLIGENCE")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Country / Region", data["Country"])

    with col2:
        st.metric("Country Code", "+" + str(data["Country Code"]))

    query = urllib.parse.quote(data["Country"])

    st.link_button(
        "🌍 OPEN GOOGLE MAPS",
        f"https://www.google.com/maps/search/?api=1&query={query}",
        use_container_width=True
    )

    st.caption(
        "Wilayah berdasarkan metadata nomor, bukan lokasi GPS."
    )


# ==================================
# MAIN DASHBOARD
# ==================================

st.divider()
st.subheader("📱 PHONE NUMBER ANALYZER")

phone = st.text_input(
    "Nomor HP",
    placeholder="08123456789"
)

region = st.selectbox(
    "Negara",
    ["ID", "MY", "SG", "US", "GB", "AU"]
)

if st.button("🚀 EXECUTE SCAN", use_container_width=True):

    if not phone.strip():
        st.warning("Masukkan nomor terlebih dahulu.")

    else:
        with st.spinner("Analyzing..."):
            result, error = analyze_phone(phone, region)

        if error:
            st.error(error)

        elif result:
            st.success("ANALYSIS COMPLETED")

            # PHONE INFORMATION
            st.header("📊 PHONE INFORMATION")

            c1, c2 = st.columns(2)

            with c1:
                st.metric("Carrier", result["Carrier"])
                st.metric("Number Type", result["Type"])

            with c2:
                st.metric("Country", result["Country"])
                st.code(result["E.164"])

            st.write("International Format:")
            st.code(result["International"])

            st.write("National Format:")
            st.code(result["National"])

            # LOCATION
            st.divider()
            show_location(result)

            # SOCIAL MEDIA
            st.divider()
            st.header("🌐 SOCIAL MEDIA FOOTPRINT")

            st.write(
                "Cari nomor pada sumber publik. "
                "Hasil pencarian bukan bukti kepemilikan akun."
            )

            links = social_search(result["E.164"])

            names = list(links.items())

            for i in range(0, len(names), 2):
                cols = st.columns(2)

                for j in range(2):
                    if i + j < len(names):
                        name, url = names[i + j]

                        with cols[j]:
                            st.link_button(
                                "🔎 " + name,
                                url,
                                use_container_width=True
                            )

            # REPORT
            st.divider()
            st.header("📄 ANALYSIS REPORT")

            st.json(result)

            report = "\n".join(
                f"{key}: {value}"
                for key, value in result.items()
            )

            st.download_button(
                "⬇️ DOWNLOAD REPORT",
                data=report,
                file_name="osis_report.txt",
                mime="text/plain",
                use_container_width=True
            )

st.divider()
st.caption("OSIS CYBER HUB | Public Information Research")
