"""Single-file wearable interpreter demo: python -m streamlit run app.py"""
from html import escape

import streamlit as st

st.set_page_config(page_title="NativeLisans | Wearable Interpreter", page_icon="↔", layout="centered")

PLACES = ["Emergency department", "Imaging", "Transport", "Inpatient unit"]
LANGUAGES = ["English", "Spanish", "Arabic"]
SAMPLES = {
    "patient": {
        "English": "Where are we going?", "Arabic": "إلى أين نحن ذاهبون؟",
        "Spanish": "¿Adónde vamos?",
    },
    "staff": {
        "English": "Hello, I am your nurse.", "Arabic": "مرحباً، أنا الممرض المسؤول عن رعايتك.",
        "Spanish": "Hola, soy su enfermero.",
    },
}


def reset():
    st.session_state.demo = {
        "mic": False, "location": 0, "speaker": "", "original": "", "translated": "",
        "original_language": "English", "translated_language": "Arabic",
        "note": "",
    }
    st.session_state.from_language = "English"
    st.session_state.to_language = "Arabic"


if "demo" not in st.session_state or "mic" not in st.session_state.demo:
    reset()

# Keep an existing demo usable when updating from the earlier language list.
if st.session_state.get("from_language") not in LANGUAGES or st.session_state.get("to_language") not in LANGUAGES:
    reset()


def change_languages():
    d = st.session_state.demo
    if st.session_state.from_language == st.session_state.to_language:
        st.session_state.to_language = next(x for x in LANGUAGES if x != st.session_state.from_language)
    d.update(original="", translated="", speaker="", note="")


def press(action):
    d = st.session_state.demo
    if action == "mic":
        d["mic"] = not d["mic"]
        d["note"] = ""
    elif action in SAMPLES and d["mic"]:
        source, target = st.session_state.from_language, st.session_state.to_language
        if action == "patient":
            source, target = target, source
        d.update(speaker=action.title(), original=SAMPLES[action][source], translated=SAMPLES[action][target],
                 original_language=source, translated_language=target)
        d["note"] = ""
    elif action == "move":
        d["location"] = (d["location"] + 1) % len(PLACES)
        d["note"] = "Same device. Same languages. Always with the patient!"


st.markdown("""
<style>
.stApp {background:#f6f7f3;color:#204b40}
.block-container {max-width:390px;padding-top:1.8rem;padding-bottom:1rem}
.page-title {text-align:center;font:600 32px Arial,sans-serif;letter-spacing:-1px;color:#285541;margin:0 0 10px;padding:0}
.label {text-align:center;font:10px Arial,sans-serif;letter-spacing:2px;color:#8b988c;margin-bottom:8px}
.lanyard {width:145px;height:105px;margin:0 auto -16px;position:relative;z-index:1;pointer-events:none}
.lanyard svg {display:block;width:100%;height:100%;overflow:visible}
.st-key-wearable {background:#fcfdf8;border:1px solid #dfe5d9;border-radius:38px;
padding:22px!important;box-shadow:0 14px 32px #254b3412;max-width:300px;margin:0 auto 12px}
.clip {width:48px;height:9px;border-radius:8px;background:#cbd5bc;margin:0 auto 13px}
.screen {background:#edf2e6;border-radius:18px;padding:20px 14px;min-height:220px;
display:flex;flex-direction:column;justify-content:center;gap:18px;text-align:center}
.status {font:10px Arial,sans-serif;letter-spacing:.5px;color:#7d8e77}
.status.listening {color:#2d7753}
.pair {font:12px Arial,sans-serif;color:#4c6b50}
.phrase {font:18px Arial,sans-serif;line-height:1.5;color:#214a3b}
.phrase[lang="ar"] {font:20px Tahoma,Arial,sans-serif;line-height:1.5}
.original {color:#7a8d77;font-size:12px!important}
.idle {font:18px Arial,sans-serif;line-height:1.5;color:#91a08a}
.grille {width:76px;height:19px;border-radius:12px;margin:9px auto 0;
background:radial-gradient(circle,#8b9985 1px,transparent 1.5px) 0 0 / 6px 6px}
.brand {text-align:center;font:9px Arial,sans-serif;letter-spacing:1.2px;color:#9ba795;margin:7px 0 0}
.place {text-align:center;font:11px Arial,sans-serif;color:#7b8c78;margin:3px 0 12px}
.stButton>button,[data-testid="stPopover"]>button {width:100%;border-radius:12px;min-height:42px;padding:8px!important;border-color:#dce4d5;background:#fcfdf8;color:#45634a}
.st-key-wearable button p {font-size:12px!important}
.st-key-wearable [data-testid="stBaseButton-primary"] {background:#2d604c;color:#fff;border-color:#2d604c}
.st-key-wearable [data-testid="stHorizontalBlock"] {gap:8px;flex-wrap:nowrap}
.st-key-wearable [data-testid="stColumn"] {min-width:0!important;flex:1 1 0!important}
.st-key-device_controls {width:100%!important;max-width:220px;margin-left:auto!important;margin-right:auto!important;align-self:center}
.st-key-device_controls [data-testid="stHorizontalBlock"] {justify-content:center;align-items:center;gap:12px}
.st-key-device_controls [data-testid="stPopover"] {width:100%}
.st-key-device_controls button {justify-content:center;text-align:center}
.stButton > button,
[data-testid="stPopover"] > button,
.st-key-wearable [data-testid="stBaseButton-primary"] {
    background-color: #e4eddf;
    color: #285541;
    border-color: #cbd9c4;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 class="page-title">Native Lisans</h1>
<div class="label">PROTOTYPE C: WEARABLE INTERPRETER</div>
<div class="lanyard"><svg viewBox="0 0 180 140" role="img" aria-label="Green neck lanyard attached to the wearable">
<path d="M90 113 C68 89 28 43 34 21 C40 1 140 1 146 21 C152 43 112 89 90 113 Z" fill="none" stroke="#386451" stroke-width="13" stroke-linejoin="round"/>
<path d="M90 113 C68 89 28 43 34 21 C40 1 140 1 146 21 C152 43 112 89 90 113 Z" fill="none" stroke="#8da995" stroke-width="1.5" stroke-dasharray="2 5"/>
<rect x="81" y="105" width="18" height="17" rx="4" fill="#294e40"/>
<rect x="85" y="120" width="10" height="17" rx="4" fill="none" stroke="#9ca89c" stroke-width="3"/>
</svg></div>
""", unsafe_allow_html=True)



d = st.session_state.demo
status = "● Listening" if d["mic"] else "Mic off"
original = translated = ""
if d["translated"]:
    for field, language_field, cls in (("original", "original_language", "original"), ("translated", "translated_language", "")):
        code = {"Arabic": "ar", "English": "en", "Spanish": "es"}[d[language_field]]
        direction = "rtl" if code == "ar" else "ltr"
        tag = f'<div class="phrase {cls}" lang="{code}" dir="{direction}">{escape(d[field])}</div>'
        if field == "original":
            original = tag
        else:
            translated = tag
else:
    translated = '<div class="idle">Listening…</div>' if d["mic"] else '<div class="idle">Ready when you are</div>'

with st.container(key="wearable"):
    st.markdown(f'''<div class="clip"></div><div class="screen">
    <div class="status {"listening" if d["mic"] else ""}">{status}</div>
    <div class="pair">{escape(st.session_state.from_language)} ↔ {escape(st.session_state.to_language)}</div>
    {translated}{original}</div>''', unsafe_allow_html=True)
    with st.container(key="device_controls"):
        language_button, mic_button = st.columns(2)
        with language_button:
            with st.popover("Choose Language:", use_container_width=True):
                st.selectbox("Staff language", LANGUAGES, key="from_language", on_change=change_languages)
                st.selectbox("Patient language", LANGUAGES, key="to_language", on_change=change_languages)
        with mic_button:
            st.button("Stop" if d["mic"] else "Speak", key="mic", on_click=press, args=("mic",),
                      type="primary" if d["mic"] else "secondary", help="Turn the microphone on or off for either person (simulated).")
    st.markdown('<div class="grille" role="img" aria-label="Speaker grille"></div><div class="brand">NativeLisans</div>', unsafe_allow_html=True)

st.markdown(f'<div class="place">{PLACES[d["location"]]}</div>', unsafe_allow_html=True)
a, b = st.columns(2)
with a:
    with st.popover("Try demo", use_container_width=True):
        st.caption("Press Speak on the device, then choose a sample.")
        st.button("Patient speaks", key="patient", disabled=not d["mic"], on_click=press, args=("patient",))
        st.button("Staff speaks", key="staff", disabled=not d["mic"], on_click=press, args=("staff",))
        st.button("Reset", key="reset", on_click=reset)
        st.caption("Speech and translation are simulated.")
with b:
    st.button("Move patient Location →", key="move", on_click=press, args=("move",))
if d["note"]:
    st.caption(d["note"])
