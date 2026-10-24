"""NativeLisans bedside prototype. Run: python -m streamlit run bedside_app.py"""
from html import escape
from textwrap import wrap

import streamlit as st

st.set_page_config(page_title="NativeLisans | Bedside Companion", page_icon="↔", layout="centered")

LANGUAGES = ["English", "Spanish", "Arabic"]
PHRASES = {
    "staff": {
        "English": "Hello, I am your nurse.",
        "Spanish": "Hola, soy su enfermero.",
        "Arabic": "مرحباً، أنا الممرض",
    },
    "patient": {
        "English": "My head hurts me.",
        "Spanish": "Me duele la cabeza.",
        "Arabic": "رأسي يؤلمني",
    },
}


def reset():
    st.session_state.bedside = {"sequence": 0, "event": "", "exchange": None}
    st.session_state.staff_language = "English"
    st.session_state.patient_language = "Arabic"


if "bedside" not in st.session_state:
    reset()


def set_languages():
    if st.session_state.staff_language == st.session_state.patient_language:
        st.session_state.patient_language = next(x for x in LANGUAGES if x != st.session_state.staff_language)
    st.session_state.bedside.update(sequence=0, event="", exchange=None)


def hear(who):
    """Demo speech triggers activation directly; there is no manual start step."""
    d = st.session_state.bedside
    d["sequence"] += 1
    source, target = st.session_state.staff_language, st.session_state.patient_language
    if who == "patient":
        source, target = target, source
    d["exchange"] = {
        "speaker": who.title(), "source": source, "target": target,
        "original": PHRASES[who][source], "translation": PHRASES[who][target],
    }
    d["event"] = f"{who.title()} voice detected → activated automatically → interpreted into {target}."


st.markdown("""
<style>
.stApp {background:#f6f7f3;color:#254f40}
.block-container {max-width:820px;padding-top:1.8rem;padding-bottom:1rem}
.title {text-align:center;font:600 32px Arial,sans-serif;letter-spacing:-1px;color:#285541;margin:0 0 10px;padding:0}
.subtitle {text-align:center;font:10px Arial,sans-serif;letter-spacing:2px;color:#899786;margin:0}
.room-scene {width:100%;margin:0}
.room-scene svg {display:block;width:100%;height:auto;border-radius:24px}
.room-scene text {font-family:Arial,sans-serif}
.st-key-room_canvas {position:relative;container-type:inline-size;margin:22px auto 15px;gap:0!important}
.st-key-room_canvas > [data-testid="stVerticalBlock"] {gap:0!important}
.st-key-patient_button,.st-key-staff_button {position:absolute!important;z-index:3;transform:translateX(-50%);margin:0!important}
.st-key-patient_button {left:16%;top:33%;width:30%!important}
.st-key-staff_button {left:83%;top:12%;width:32%!important}
.st-key-room_canvas .stButton>button {min-height:36px;padding:7px 9px;border-radius:13px;box-shadow:0 3px 10px #355c3b12;background:#f8fbf4}
.st-key-room_canvas .stButton>button p {font-size:clamp(9px,1.6cqw,12px);line-height:1.3}
.st-key-room_canvas .stButton>button:hover {background:#e0eddb;border-color:#a1bc95}
@container(max-width:500px){.st-key-patient_button{top:24%}.st-key-staff_button{top:1%}.st-key-room_canvas .stButton>button{padding:5px;min-height:30px}}
.room {text-align:center;font:12px Arial,sans-serif;color:#788d72;margin:0 0 12px}
.ready {text-align:center;font:13px Arial,sans-serif;line-height:1.7;color:#587451;margin:0}
.hint {text-align:center;font:11px Arial,sans-serif;line-height:1.6;color:#91a088;margin:12px 0 0}
[data-testid="stSidebar"] {background:#eef2e8}
.stButton>button {width:100%;border-radius:12px;min-height:42px;background:#e4eddf;color:#285541;border-color:#cbd9c4}
@media(max-width:600px){.block-container{padding-top:1.2rem}.title{font-size:28px}.st-key-room_canvas{margin-top:15px}}
@media(prefers-reduced-motion:reduce){.device-ring,.voice-waves{animation-duration:0s!important}}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.subheader("Native-Lisans Device Language Configuration:")
    st.selectbox("Staff language", LANGUAGES, key="staff_language", on_change=set_languages)
    st.selectbox("Patient language", LANGUAGES, key="patient_language", on_change=set_languages)
    st.button("Reset demo", key="reset", on_click=reset)

d = st.session_state.bedside
sequence = d["sequence"]
animation = f"bedsidePulse{sequence} 0.5s ease-in-out 4" if sequence else "none"
speaker = d["exchange"]["speaker"] if d["exchange"] else ""
voice_animation = f"voiceFade{sequence} 2s ease-out forwards"
patient_style = f"animation:{voice_animation}" if speaker == "Patient" else "opacity:0"
nurse_style = f"animation:{voice_animation}" if speaker == "Staff" else "opacity:0"
device_reply = ""
if d["exchange"]:
    e = d["exchange"]
    lines = wrap(e["translation"], width=30, break_long_words=False, break_on_hyphens=False)
    code = {"English": "en", "Spanish": "es", "Arabic": "ar"}[e["target"]]
    direction = "rtl" if code == "ar" else "ltr"
    text_lines = ''.join(f'<tspan x="414" y="{197 + 22*i}">{escape(line)}</tspan>' for i, line in enumerate(lines))
    device_reply = f'''<g aria-label="Interpreter says: {escape(e['translation'], quote=True)}">
<rect x="279" y="153" width="270" height="77" rx="15" fill="#fcfef8" stroke="#a9c698" stroke-width="1.5"/>
<path d="M400 229L411 239L423 229" fill="#fcfef8" stroke="#a9c698" stroke-width="1.5"/>
<path d="M401 229H422" stroke="#fcfef8" stroke-width="3"/>
<text x="414" y="173" text-anchor="middle" fill="#7c9170" font-size="10">{escape(e['source'])} → {escape(e['target'])}</text>
<text text-anchor="middle" fill="#285541" font-size="17" lang="{code}" direction="{direction}">{text_lines}</text>
</g>'''
# A new animation name on each utterance restarts the two-second light pulse.
st.markdown(f"""
<style>
@keyframes bedsidePulse{sequence} {{
    0%,100% {{stroke:#bdcdb4;filter:drop-shadow(0 0 0 #91ce9100);}}
    50% {{stroke:#55ad70;filter:drop-shadow(0 0 7px #71bd79);}}
}}
@keyframes voiceFade{sequence} {{
    0%,100% {{opacity:0;}}
    15%,80% {{opacity:1;}}
}}
</style>
<h1 class="title">NativeLisans</h1>
<p class="subtitle">Prototype A: Bedside Companion</p>
""", unsafe_allow_html=True)

scene_markup = f"""
<div class="room-scene">
<svg viewBox="0 0 760 430" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Patient resting in a hospital bed on the left, a NativeLisans interpreter on the bedside table in the center, and a nurse standing in the doorway on the right">
<defs>
  <pattern id="mesh" width="4" height="4" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="0.65" fill="#8c9b80"/></pattern>
  <linearGradient id="deviceShade"><stop stop-color="#d1dcc6"/><stop offset=".45" stop-color="#f3f6ec"/><stop offset="1" stop-color="#c9d6bc"/></linearGradient>
</defs>
<rect width="760" height="430" rx="24" fill="#edf1e7"/>
<path d="M0 295H760V430H0Z" fill="#e0e6d7"/>
<path d="M0 295H760" stroke="#d3ddc9" stroke-width="3"/>
<rect x="51" y="52" width="178" height="111" rx="10" fill="#f8faf4" stroke="#d3ddc8" stroke-width="5"/>
<rect x="62" y="63" width="156" height="89" rx="5" fill="#dce9e6"/>
<path d="M140 63V152M62 107H218" stroke="#f8faf4" stroke-width="5"/>
<rect x="267" y="69" width="94" height="69" rx="7" fill="#fafbf6" stroke="#d5dfcb"/>
<path d="M289 104H304L312 88L324 117L332 104H341" fill="none" stroke="#a7b99b" stroke-width="3" stroke-linejoin="round"/>
<rect x="564" y="55" width="145" height="257" rx="5" fill="#bdcbb1"/>
<rect x="575" y="66" width="123" height="246" fill="#d0dbc6"/>
<path d="M698 66L725 87V310L698 312Z" fill="#f4f6ed" stroke="#b9c8ae" stroke-width="2"/>
<circle cx="713" cy="204" r="3" fill="#8f9f83"/>
<text x="636" y="46" text-anchor="middle" fill="#85957a" font-size="11" letter-spacing="1">DOORWAY</text>
<ellipse cx="210" cy="357" rx="158" ry="15" fill="#becbb2" opacity=".4"/>
<rect x="59" y="210" width="18" height="124" rx="8" fill="#a9bba0"/>
<rect x="72" y="283" width="268" height="24" rx="7" fill="#a9bba0"/>
<path d="M86 305V342M320 305V342" stroke="#9dae91" stroke-width="10"/>
<circle cx="86" cy="347" r="9" fill="#829678"/><circle cx="320" cy="347" r="9" fill="#829678"/>
<rect x="74" y="252" width="261" height="34" rx="13" fill="#fafbf5" stroke="#d4ddc9" stroke-width="2"/>
<rect x="79" y="230" width="65" height="31" rx="13" fill="#fffef9" transform="rotate(-12 111 245)"/>
<path d="M128 246Q143 215 174 231L201 262H123Z" fill="#c6d7cf"/>
<ellipse cx="109" cy="226" rx="24" ry="26" fill="#d6ac8d" transform="rotate(-18 109 226)"/>
<path d="M87 226Q78 203 102 199Q124 194 132 214Q109 205 91 225Z" fill="#706353"/>
<path d="M116 221L122 220" stroke="#725d4b" stroke-width="2" stroke-linecap="round"/>
<path d="M129 233Q126 237 122 235" fill="none" stroke="#a7745f" stroke-width="2"/>
<path d="M166 232Q190 236 214 246L323 245Q337 246 339 264V279H153Z" fill="#a8c7b2"/>
<path d="M177 247Q215 253 248 251" fill="none" stroke="#bfd8c4" stroke-width="3"/>
<path d="M153 239L177 247L190 244" fill="none" stroke="#d6ac8d" stroke-width="10" stroke-linecap="round"/>
<path d="M327 253V308" stroke="#a9bba0" stroke-width="11" stroke-linecap="round"/>
<path d="M127 291H284M137 280V303M274 280V303" stroke="#dce5d5" stroke-width="6" stroke-linecap="round"/>
<g class="voice-waves" style="{patient_style}" fill="none" stroke="#5a9b6b" stroke-width="3" stroke-linecap="round">
  <path d="M141 218Q151 226 143 236M150 210Q168 227 153 244"/>
</g>
<ellipse cx="414" cy="351" rx="65" ry="10" fill="#becbb2" opacity=".45"/>
<path d="M368 289H457V339H368Z" fill="#c9bfa4"/>
<path d="M376 338V351M448 338V351" stroke="#b4aa8e" stroke-width="6"/>
<rect x="359" y="279" width="107" height="13" rx="5" fill="#ded4b9"/>
<path d="M377 314H446" stroke="#b6ab8d" stroke-width="2"/>
<path d="M405 302H419" stroke="#f1ebda" stroke-width="3" stroke-linecap="round"/>
<g transform="translate(376 237)">
  <path d="M0 9Q0 0 36 0Q72 0 72 9V31Q72 44 36 44Q0 44 0 31Z" fill="url(#deviceShade)" stroke="#b6c7aa"/>
  <ellipse cx="36" cy="9" rx="36" ry="11" fill="#eff4e6" stroke="#d6e0c9"/>
  <ellipse class="device-ring" cx="36" cy="8" rx="33" ry="9" fill="none" stroke="#bdcdb4" stroke-width="2.5" style="animation:{animation}"/>
  <rect x="9" y="22" width="54" height="12" rx="5" fill="url(#mesh)"/>
  <text x="36" y="40" font-size="5" text-anchor="middle" fill="#6f8561">NativeLisans</text>
</g>
<text x="413" y="376" text-anchor="middle" fill="#748768" font-size="11">Bedside interpreter</text>
<ellipse cx="630" cy="320" rx="43" ry="9" fill="#aebfa2" opacity=".4"/>
<path d="M615 244L611 306M640 244L647 306" stroke="#42705d" stroke-width="18" stroke-linecap="round"/>
<path d="M611 306L598 311M647 306L660 311" stroke="#41584d" stroke-width="13" stroke-linecap="round"/>
<path d="M605 181Q628 171 651 184L653 249H604Z" fill="#719c85"/>
<path d="M619 181L629 194L639 181" fill="none" stroke="#c5d9cd" stroke-width="3"/>
<path d="M610 192L587 213L565 208" fill="none" stroke="#719c85" stroke-width="15" stroke-linecap="round"/>
<path d="M565 208L554 204" stroke="#bf8e6d" stroke-width="11" stroke-linecap="round"/>
<path d="M649 192L663 226L657 246" fill="none" stroke="#719c85" stroke-width="14" stroke-linecap="round"/>
<path d="M657 246L655 252" stroke="#bf8e6d" stroke-width="10" stroke-linecap="round"/>
<rect x="635" y="203" width="12" height="17" rx="2" fill="#eaf1e6"/>
<path d="M637 207H645M637 211H642" stroke="#9db5a0" stroke-width="1.5"/>
<path d="M621 168V181Q629 188 636 179V167" fill="#bf8e6d"/>
<ellipse cx="629" cy="148" rx="22" ry="26" fill="#bf8e6d"/>
<path d="M607 150Q600 119 625 119Q654 114 654 148L645 136Q623 140 614 133Z" fill="#594e45"/>
<circle cx="649" cy="125" r="11" fill="#594e45"/>
<path d="M614 148H619M624 164Q630 167 634 163" fill="none" stroke="#7e5544" stroke-width="2" stroke-linecap="round"/>
<g class="voice-waves" style="{nurse_style}" fill="none" stroke="#5a9b6b" stroke-width="3" stroke-linecap="round">
  <path d="M598 145Q589 154 597 164M588 137Q571 155 587 173"/>
</g>
{device_reply}
</svg>
</div>
"""
with st.container(key="room_canvas"):
    st.markdown(scene_markup, unsafe_allow_html=True)
    with st.container(key="patient_button"):
        st.button(
            f'Patient: “{PHRASES["patient"][st.session_state.patient_language]}”',
            key="patient",
            on_click=hear,
            args=("patient",),
            use_container_width=True,
        )
    with st.container(key="staff_button"):
        st.button(f'Staff: “{PHRASES["staff"][st.session_state.staff_language]}”', key="staff", on_click=hear, args=("staff",), use_container_width=True)

st.markdown(f"""
<p class="room">Patient Room · {escape(st.session_state.staff_language)} ↔ {escape(st.session_state.patient_language)}</p>
<p class="hint">Click the button above a person to speak. The bedside device interprets.<br>Simulated speech and translation; the bubble represents spoken output.</p>
""", unsafe_allow_html=True)
