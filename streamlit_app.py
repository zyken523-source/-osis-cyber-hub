
import streamlit as st
import phonenumbers
from phonenumbers import carrier, geocoder, number_type

st.set_page_config(
    page_title="OSIS Cyber Hub",
    page_icon="🕵️",
    layout="wide"
)

st.title("🕵️ OSIS // Cyber Hub")
st.caption("Phone Number Intelligence & Validation")

st.info(
    "Mode aman: analisis format dan metadata nomor "
    "tanpa mengakses API internal platform."
)

phone = st.text_input(
    "Masukkan nomor HP",
    placeholder="08123456789"
)

region = st.selectbox(
    "Wilayah nomor",
    ["ID", "MY", "SG", "US"]
)

def analyze_phone(raw_phone, region):
    try:
        parsed = phonenumbers.parse(raw_phone, region)

        if not phonenumbers.is_possible_number(parsed):
            return None, "Nomor tidak mungkin digunakan."

        if not phonenumbers.is_valid_number(parsed):
            return None, "Nomor tidak valid menurut metadata."

        phone_type = number_type(parsed)

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

        result = {
            "E.164": phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            ),
            "International": phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.INTERNATIONAL
            ),
            "National": phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.NATIONAL
            ),
            "Country": geocoder.description_for_number(
                parsed, "en"
            ) or "Unknown",
            "Carrier": carrier.name_for_number(
                parsed, "en"
            ) or "Unknown",
            "Type": types.get(phone_type, "Unknown"),
            "Country Code": parsed.country_code
        }

        return result, None

    except phonenumbers.NumberParseException as error:
        return None, str(error)

if st.button("🚀 ANALYZE NUMBER", use_container_width=True):

    if not phone.strip():
        st.warning("Masukkan nomor terlebih dahulu.")

    else:
        with st.spinner("Menganalisis nomor..."):

            result, error = analyze_phone(phone, region)

        if error:
            st.error(error)

        elif result:
            st.success("Analisis nomor berhasil!")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Country Code", result["Country Code"])
                st.metric("Carrier", result["Carrier"])
                st.metric("Number Type", result["Type"])

            with col2:
                st.metric("Country", result["Country"])
                st.code(result["E.164"])
                st.write("**International:**")
                st.code(result["International"])

            st.divider()

            st.subheader("📊 Number Intelligence")

            st.json(result)

            st.caption(
                "Catatan: Informasi operator berasal dari "
                "metadata dan tidak selalu menunjukkan "
                "operator aktif saat ini."
            )

            st.success("Selesai.")

st.divider()
st.caption("OSIS Cyber Hub | Educational OSINT Tool")
