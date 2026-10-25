"""Single-file wearable interpreter demo: python -m streamlit run app.py"""
from html import escape
from base64 import b64encode
from pathlib import Path

import streamlit as st

try:
    from streamlit.components.v2 import component as browser_component
except ImportError:
    browser_component = None

st.set_page_config(page_title="NativeLisans | Wearable Interpreter", page_icon="↔", layout="centered")

PLACES = ["Emergency department", "Imaging", "Transport", "Inpatient unit"]
LANGUAGES = ["English", "Spanish", "Arabic"]
SAMPLES = {
    "patient": {
        "English": "Where are we going?", "Arabic": "إلى أين نحن ذاهبون؟",
        "Spanish": "¿Adónde vamos?",
    },
    "staff": {
        "English": "Hello, I am your nurse.", "Arabic": "مرحباً، أنا الممرض",
        "Spanish": "Hola, soy su enfermero.",
    },
}


# The six MP3 recordings are in the same folder as this script.
AUDIO_DIR = Path(__file__).resolve().parent
AUDIO_FILES = {
    "staff": {
        "English": "HelloIamyourNurse_English.mp3",
        "Spanish": "HelloIamyourNurse_Spanish.mp3",
        "Arabic": "HelloIamyourNurse_Arabic.mp3",
    },
    "patient": {
        "English": "Where are we going_English.mp3",
        "Spanish": "Where are we going_Spanish.mp3",
        "Arabic": "Where are we going_Arabic.mp3",
    },
}



def recording_data_uri(role, language):
    """Load the recording directly from the same folder as this Python file."""
    audio = (AUDIO_DIR / AUDIO_FILES[role][language]).read_bytes()
    return "data:audio/mpeg;base64," + b64encode(audio).decode("ascii")


def reset():
    st.session_state.demo = {
        "mic": False, "location": 0, "speaker": "", "original": "", "translated": "",
        "original_language": "English", "translated_language": "Arabic",
        "note": "", "previous_location": None, "move_id": 0,
    }
    st.session_state.from_language = "English"
    st.session_state.to_language = "Arabic"


if "demo" not in st.session_state or "mic" not in st.session_state.demo:
    reset()

# Keep an existing demo usable when updating from the earlier language list.
if st.session_state.get("from_language") not in LANGUAGES or st.session_state.get("to_language") not in LANGUAGES:
    reset()


# Preserve an active conversation when loading this update.
st.session_state.demo.setdefault("previous_location", None)
st.session_state.demo.setdefault("move_id", 0)


def change_languages():
    d = st.session_state.demo
    if st.session_state.from_language == st.session_state.to_language:
        st.session_state.to_language = next(x for x in LANGUAGES if x != st.session_state.from_language)
    d.update(original="", translated="", speaker="", note="")


def press(action):
    d = st.session_state.demo
    d["speaking"] = action in SAMPLES and d["mic"]
    if d["speaking"]:
        d["speech_id"] = d.get("speech_id", 0) + 1
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
        d["move_id"] = d.get("move_id", 0) + 1
        if d["location"] == len(PLACES) - 1:
            d["location"] = 0
            d["previous_location"] = None
            d["note"] = "Journey restarted. The same wearable stays with the patient."
        else:
            d["previous_location"] = d["location"]
            d["location"] += 1
            d["note"] = "Same device. Same languages. Always with the patient!"


AUDIO_JS = r"""
export default function ({ parentElement, data }) {
    const status = parentElement.querySelector("#voice_status");
    const retry = parentElement.querySelector("#audio_retry");
    if (typeof Audio === "undefined") {
        status.textContent = "Audio playback is not available in this browser.";
        return;
    }
    const manager = window.__nativeLisansRecordings || (window.__nativeLisansRecordings = {
        generation: 0, running: false, audio: new Audio(), message: "", timer: null,
        gap: null, config: null, retry: null
    });
    const audio = manager.audio;
    manager.retryButton = retry;
    manager.show = message => { manager.message = message; status.textContent = message; };
    retry.hidden = !manager.retry;
    retry.onclick = () => { if (manager.retry) manager.retry(); };
    function stop(message) {
        manager.generation++;
        clearTimeout(manager.timer);
        clearTimeout(manager.gap);
        audio.onplaying = audio.onended = audio.onerror = null;
        audio.pause();
        manager.running = false;
        manager.retry = null;
        manager.retryButton.hidden = true;
        manager.show(message);
    }
    const config = data.languages.join("|");
    if ((!data.enabled || !data.mic || (manager.config && manager.config !== config)) && (manager.running || manager.retry)) {
        stop("Audio stopped.");
    }
    manager.config = config;
    if (manager.running || manager.retry) status.textContent = manager.message;
    else if (!data.enabled) manager.show("Recorded audio is off.");
    else manager.show(data.mic ? "Recordings ready: original phrase, then translation." : "Press Speak on the device to begin.");

    function talk(role) {
        if (!data.enabled || !data.mic) return;
        stop("Starting recording…");
        const generation = manager.generation;
        const clips = data.conversations[role];
        if (!clips || clips.some(clip => !clip.src)) {
            manager.show("A recording is missing for this language pair.");
            return;
        }
        manager.running = true;
        function fail(message) {
            if (generation !== manager.generation) return;
            stop(message);
            manager.retry = () => talk(role);
            manager.retryButton.hidden = false;
        }
        function playAt(index) {
            if (generation !== manager.generation) return;
            if (index >= clips.length) {
                manager.running = false;
                manager.retry = null;
                manager.retryButton.hidden = true;
                manager.show("Finished playing.");
                return;
            }
            const clip = clips[index];
            audio.src = clip.src;
            audio.preload = "auto";
            audio.volume = 1;
            audio.onplaying = () => {
                if (generation !== manager.generation) return;
                clearTimeout(manager.timer);
                manager.show((clip.translation ? "Interpreter: " : (role === "staff" ? "Staff: " : "Patient: ")) + clip.language);
                if (clip.translation) {
                    document.querySelectorAll(".grille").forEach(el => {
                        el.style.animation = "none";
                        void el.offsetWidth;
                        el.style.animation = "speakerPulse 0.5s ease-in-out 4";
                    });
                }
            };
            audio.onended = () => {
                if (generation !== manager.generation) return;
                clearTimeout(manager.timer);
                manager.gap = setTimeout(() => playAt(index + 1), 300);
            };
            audio.onerror = () => fail("Could not play this recording. Check browser sound settings, then retry.");
            manager.timer = setTimeout(() => fail("Audio did not start. Enable browser sound, then retry."), 10000);
            try {
                const playing = audio.play();
                if (playing && typeof playing.catch === "function") {
                    playing.catch(error => fail(error.name === "NotAllowedError"
                        ? "The browser blocked audio. Click Retry audio below."
                        : "Could not play this recording. Click Retry audio below."));
                }
            } catch (error) {
                fail("Could not start audio. Click Retry audio below.");
            }
        }
        playAt(0);
    }

    function handleClick(event) {
        const button = event.target.closest && event.target.closest("button");
        if (!button || button.disabled) return;
        const label = button.textContent.trim().replace(/\s+/g, " ");
        if (label === "Patient speaks") talk("patient");
        else if (label === "Staff speaks") talk("staff");
        else if (label === "Stop" || label === "Reset") stop("Audio stopped.");
    }
    document.addEventListener("click", handleClick, true);
    return () => {
        // Keep the same unlocked audio element playing through Python reruns.
        document.removeEventListener("click", handleClick, true);
    };
}
"""

voice_bridge = browser_component(
    "native_lisans_recorded_audio",
    html='<p id="voice_status" role="status" aria-live="polite"></p><button id="audio_retry" hidden>Retry audio</button>',
    css="""p {font:12px Arial,sans-serif;line-height:1.5;color:#64795c;margin:0;}
button {margin-top:8px;padding:7px 12px;border:1px solid #cbd9c4;border-radius:9px;background:#e4eddf;color:#285541;cursor:pointer;}
button[hidden] {display:none;}""",
    js=AUDIO_JS,
) if browser_component else None


def spoken_audio_controls():
    if voice_bridge is None:
        st.caption("Update Streamlit to enable recorded audio. The visual demo still works.")
        return
    enabled = st.checkbox("Play recordings", value=True, key="read_aloud")
    staff, patient = st.session_state.from_language, st.session_state.to_language
    clips = {
        role: {language: recording_data_uri(role, language) for language in LANGUAGES}
        for role in AUDIO_FILES
    }
    conversations = {}
    for role, source, target in (("staff", staff, patient), ("patient", patient, staff)):
        conversations[role] = [
            {"src": clips[role][source], "language": source, "translation": False},
            {"src": clips[role][target], "language": target, "translation": True},
        ]
    voice_bridge(
        key="recorded_audio",
        data={"enabled": enabled, "mic": st.session_state.demo["mic"],
              "languages": [staff, patient], "conversations": conversations,
              "speech_id": st.session_state.demo.get("speech_id", 0)},
    )


def room_art(location):
    """Self-contained room illustrations: no image files or downloads needed."""
    rooms = [
        ("#f2ebe5", "#dfd7ca", '''
<rect x="60" y="76" width="350" height="64" rx="12" fill="#fcf6f0"/>
<path d="M93 96V120M81 108H105" stroke="#ba6c60" stroke-width="9"/>
<text x="126" y="117" fill="#976f64" font-size="22">EMERGENCY</text>
<path d="M45 170H450" stroke="#b6c4b5" stroke-width="9" stroke-linecap="round"/>
<path d="M58 180H187V556H58Z" fill="#cadbcf"/>
<path d="M72 180V550M102 180V550M132 180V550M163 180V550" stroke="#b5cebf" stroke-width="5"/>
<rect x="248" y="197" width="135" height="108" rx="12" fill="#f8f8ee" stroke="#c9cfbd" stroke-width="5"/>
<rect x="261" y="210" width="109" height="77" rx="6" fill="#78938d"/>
<path d="M272 251H293L301 230L312 267L323 245H359" fill="none" stroke="#cfebcc" stroke-width="3"/>
<path d="M315 307V395" stroke="#b5beaf" stroke-width="8"/>
<ellipse cx="268" cy="643" rx="191" ry="19" fill="#c9c8ba" opacity=".4"/>
<rect x="98" y="495" width="345" height="50" rx="15" fill="#fdfbf5" stroke="#d6d9c9" stroke-width="3"/>
<rect x="112" y="474" width="86" height="30" rx="12" fill="#fffef9"/>
<path d="M207 486H421Q443 486 443 510V530H200Z" fill="#b5cbbc"/>
<path d="M93 448V569M446 491V569M98 555H446" stroke="#a4b7a6" stroke-width="12" stroke-linecap="round"/>
<path d="M132 563V616M405 563V616" stroke="#a4b7a6" stroke-width="10"/>
<circle cx="132" cy="624" r="14" fill="#8b9f8e"/><circle cx="405" cy="624" r="14" fill="#8b9f8e"/>
<rect x="865" y="228" width="244" height="330" rx="12" fill="#e7e2d5" stroke="#cfccbb" stroke-width="4"/>
<path d="M885 300H1089M885 366H1089M885 432H1089" stroke="#c7c6b6" stroke-width="3"/>
<path d="M968 330H1011M968 395H1011M968 462H1011" stroke="#f9f7ef" stroke-width="5" stroke-linecap="round"/>
<rect x="896" y="177" width="58" height="49" rx="7" fill="#f9f7ec"/>
<path d="M925 188V215M912 201H938" stroke="#b98275" stroke-width="5"/>
<path d="M1057 120V204M1040 120H1074" stroke="#adb8a5" stroke-width="6"/>
<rect x="1043" y="135" width="28" height="42" rx="6" fill="#d6e5df"/>
'''),
        ("#e7eff2", "#d4e0e3", '''
<rect x="70" y="70" width="300" height="64" rx="12" fill="#f5fafb"/>
<text x="106" y="111" fill="#7b9aa3" font-size="25" letter-spacing="3">IMAGING</text>
<ellipse cx="295" cy="665" rx="213" ry="22" fill="#b4c9cc" opacity=".4"/>
<rect x="165" y="421" width="250" height="215" rx="37" fill="#c4d6d9"/>
<ellipse cx="291" cy="369" rx="183" ry="198" fill="#f7faf8" stroke="#c3d5d8" stroke-width="13"/>
<ellipse cx="291" cy="369" rx="119" ry="137" fill="#cbdce0" stroke="#e4ecec" stroke-width="17"/>
<ellipse cx="291" cy="369" rx="88" ry="106" fill="#829fa8"/>
<path d="M167 260Q195 205 246 195" fill="none" stroke="#bad7ce" stroke-width="8" stroke-linecap="round"/>
<circle cx="399" cy="392" r="8" fill="#b2cbbd"/>
<circle cx="398" cy="418" r="6" fill="#d4e1e0"/>
<path d="M286 455L526 548L500 579L265 484Z" fill="#f9fbf8" stroke="#beced1" stroke-width="4"/>
<path d="M466 567V655M501 575V655" stroke="#b2c7cb" stroke-width="12"/>
<rect x="893" y="269" width="180" height="139" rx="13" fill="#f5f8f5" stroke="#c6d5d6" stroke-width="5"/>
<rect x="908" y="284" width="150" height="104" rx="6" fill="#829da2"/>
<circle cx="983" cy="335" r="37" fill="#bfcccb"/><circle cx="983" cy="335" r="24" fill="#8fa9ad"/>
<path d="M983 407V475" stroke="#b4c7cb" stroke-width="10"/>
<rect x="859" y="474" width="255" height="21" rx="7" fill="#bdcfd1"/>
<path d="M884 495V657M1088 495V657" stroke="#b7c9cc" stroke-width="12"/>
'''),
        ("#e8eef0", "#d4dfe0", '''
<path d="M0 0L493 225V530L0 800Z" fill="#e2e9e6"/>
<path d="M1200 0L707 225V530L1200 800Z" fill="#dce6e5"/>
<rect x="493" y="225" width="214" height="305" fill="#d2dfe0"/>
<path d="M0 800L493 530H707L1200 800Z" fill="#d4dfde"/>
<path d="M150 800L535 530M1050 800L665 530M0 657H1200" stroke="#c0cfcd" stroke-width="3"/>
<path d="M0 0L493 225H707L1200 0Z" fill="#f5f7f1"/>
<path d="M245 58H955L878 96H323Z" fill="#fffef5"/>
<path d="M399 140H801L764 162H436Z" fill="#fffef5"/>
<path d="M77 164L235 207V589L77 677Z" fill="#b6c8c4"/>
<path d="M91 185L219 219V576L91 644Z" fill="#cbdad5"/>
<path d="M297 233L384 257V510L297 558Z" fill="#c2d2cd"/>
<path d="M1123 164L965 207V589L1123 677Z" fill="#afc4c1"/>
<path d="M1109 185L981 219V576L1109 644Z" fill="#c4d5d2"/>
<path d="M903 233L816 257V510L903 558Z" fill="#bbcecb"/>
<path d="M0 455L477 391M1200 455L723 391" stroke="#a9bfb8" stroke-width="11"/>
<rect x="64" y="48" width="315" height="71" rx="12" fill="#f3f6ed"/>
<text x="86" y="92" fill="#7a9690" font-size="25" letter-spacing="2">TRANSPORT →</text>
<rect x="1015" y="241" width="63" height="43" rx="4" fill="#e7eee3"/>
<path d="M1031 261H1061M1052 252L1062 261L1052 270" fill="none" stroke="#88a29a" stroke-width="4"/>
'''),
        ("#eaf0e2", "#dcdcca", '''
<rect x="68" y="70" width="335" height="65" rx="12" fill="#f8faf2"/>
<text x="99" y="112" fill="#839372" font-size="24" letter-spacing="2">INPATIENT UNIT</text>
<rect x="849" y="94" width="287" height="222" rx="10" fill="#f7f9f0" stroke="#cbd8bf" stroke-width="8"/>
<rect x="862" y="107" width="261" height="196" rx="5" fill="#d6e7e9"/>
<path d="M993 108V303M862 205H1123" stroke="#f5f8ed" stroke-width="8"/>
<path d="M917 302Q980 261 1047 302" fill="#c6dacb"/>
<rect x="50" y="212" width="37" height="370" rx="13" fill="#bac9ab"/>
<rect x="80" y="480" width="370" height="60" rx="17" fill="#fbfcf5" stroke="#d2dcc4" stroke-width="4"/>
<rect x="92" y="453" width="95" height="39" rx="15" fill="#fffef9"/>
<path d="M203 468H424Q451 468 451 493V527H196Z" fill="#bfd0ae"/>
<path d="M73 550H459M83 550V615M439 550V615" stroke="#a7b894" stroke-width="13" stroke-linecap="round"/>
<circle cx="83" cy="624" r="13" fill="#91a47e"/><circle cx="439" cy="624" r="13" fill="#91a47e"/>
<path d="M145 565H376M157 545V580M365 545V580" stroke="#e1e9d6" stroke-width="8" stroke-linecap="round"/>
<rect x="882" y="439" width="141" height="140" rx="6" fill="#d9cdb1"/>
<rect x="873" y="426" width="159" height="17" rx="5" fill="#e7dcc5"/>
<path d="M892 505H1013M938 473H967" stroke="#bdaf92" stroke-width="4"/>
<path d="M1083 561V399M1083 462L1052 422M1083 438L1110 396" stroke="#91a47f" stroke-width="5"/>
<ellipse cx="1042" cy="415" rx="19" ry="35" fill="#adbf98" transform="rotate(-35 1042 415)"/>
<ellipse cx="1116" cy="387" rx="19" ry="35" fill="#a4b98c" transform="rotate(33 1116 387)"/>
<ellipse cx="1083" cy="383" rx="19" ry="34" fill="#b2c59d"/>
<path d="M1054 550H1112L1102 613H1064Z" fill="#c6bda1"/>
'''),
    ]
    wall, floor, details = rooms[location]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800">
<rect width="1200" height="800" fill="{wall}"/>
<path d="M0 535H1200V800H0Z" fill="{floor}"/>
<path d="M0 535H1200" stroke="#bac8b8" stroke-width="3" opacity=".35"/>
<g font-family="Arial,sans-serif">{details}</g></svg>'''


def room_background(location):
    image = b64encode(room_art(location).encode("utf-8")).decode("ascii")
    st.markdown(f'''<style>
.stApp {{
    background-color:#edf1e8;
    background-image:linear-gradient(#f6f7f31a,#f6f7f31a),url("data:image/svg+xml;base64,{image}");
    background-size:cover;background-position:center;background-repeat:no-repeat;background-attachment:fixed;
}}
.block-container {{background:rgba(246,247,243,.84);box-shadow:0 0 50px 30px rgba(246,247,243,.62);}}
[data-testid="stSidebar"] {{background:#f1f5ec;}}
</style>''', unsafe_allow_html=True)


def patient_journey(d):
    """Show the patient and pendant travelling between the four care settings."""
    points = [27, 113, 199, 285]
    current = d["location"]
    previous = d.get("previous_location")
    start = current if previous is None else previous
    move_id = d.get("move_id", 0)
    animation = f"patientTravel{move_id} 1.4s ease-in-out both" if previous is not None else "none"
    steps = []
    labels = [("Emergency", "department"), ("Imaging", ""), ("Transport", ""), ("Inpatient", "unit")]
    for i, (first, second) in enumerate(labels):
        color = "#285541" if i == current else "#91a08a"
        weight = "700" if i == current else "400"
        fill = "#4d8961" if i <= current else "#d7e0d0"
        steps.append(
            f'<circle cx="{points[i]}" cy="43" r="4" fill="{fill}"/>'
            f'<text x="{points[i]}" y="64" text-anchor="middle" fill="{color}" font-size="9.5" font-weight="{weight}">'
            f'<tspan x="{points[i]}">{first}</tspan>'
            f'<tspan x="{points[i]}" dy="11">{second}</tspan></text>'
        )
    if previous is None:
        heading = f'Patient in <strong>{escape(PLACES[current])}</strong>'
    else:
        heading = f'{escape(PLACES[previous])} <span class="journey-arrow">→</span> <strong>{escape(PLACES[current])}</strong>'
    st.markdown(f"""
<style>
@keyframes patientTravel{move_id} {{
    from {{transform:translate({points[start]}px,0px);}}
    to {{transform:translate({points[current]}px,0px);}}
}}
</style>
<div class="journey-card">
  <div class="journey-heading">{heading}</div>
  <svg viewBox="0 0 312 83" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The patient and wearable move together. Current location: {escape(PLACES[current], quote=True)}">
    <path d="M27 43H285" fill="none" stroke="#dce5d4" stroke-width="3"/>
    <path d="M27 43H{points[current]}" fill="none" stroke="#9ab38d" stroke-width="3"/>
    {''.join(steps)}
    <g style="transform:translate({points[current]}px,0px);animation:{animation}">
      <circle cx="0" cy="9" r="6" fill="#ca9c7b"/>
      <path d="M-6 7Q-6 0 0 1Q7 0 6 8Q0 4-6 7" fill="#726858"/>
      <path d="M-7 19Q0 15 7 19L10 35H-10Z" fill="#769b87"/>
      <path d="M-7 21L-12 29M7 21L12 29" fill="none" stroke="#ca9c7b" stroke-width="3" stroke-linecap="round"/>
      <path d="M-4 35V40M4 35V40" stroke="#597563" stroke-width="3" stroke-linecap="round"/>
      <path d="M-4 20L0 26L4 20" fill="none" stroke="#f9fcf5" stroke-width="1.5"/>
      <rect x="-3" y="25" width="6" height="8" rx="2" fill="#e3efd5" stroke="#335e46" stroke-width=".7"/>
      <path d="M-1.5 28H1.5" stroke="#739568" stroke-width=".8"/>
    </g>
  </svg>
  <div class="journey-caption">Patient + wearable travel together</div>
</div>
""", unsafe_allow_html=True)

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
.st-key-wearable [data-testid="stColumn"] {min-width:0!important;}
.st-key-device_controls {width:100%!important;max-width:220px;margin-left:auto!important;margin-right:auto!important;align-self:center}
.st-key-device_controls [data-testid="stHorizontalBlock"] {justify-content:center;align-items:center;gap:12px}
.st-key-device_controls [data-testid="stPopover"] {width:100%}
.st-key-device_controls button {justify-content:center;text-align:center}
.grille.speaking {
    animation: speakerPulse 0.5s ease-in-out 4;
}

@keyframes speakerPulse {
    0%, 100% {
        background-color: transparent;
        box-shadow: none;
    }
    50% {
        background-color: #a8dfa8;
        box-shadow:
            0 0 0 5px #91ce9160,
            0 0 0 10px #91ce9125;
    }
}
.stButton > button,
[data-testid="stPopover"] > button,
.st-key-wearable [data-testid="stBaseButton-primary"] {
    background-color: #e4eddf;
    color: #285541;
    border-color: #cbd9c4;
}
.journey-card {background:#fcfdf8;border:1px solid #dbe5d1;border-radius:16px;padding:12px 8px 9px;margin:0 0 8px}
.journey-heading {text-align:center;font:11px Arial,sans-serif;color:#7b8d73;margin:0 0 7px;line-height:1.4}
.journey-heading strong {color:#285541;font-size:13px}
.journey-arrow {color:#4d8961;margin:0 5px}
.journey-card svg {display:block;width:100%;height:auto;overflow:visible;font-family:Arial,sans-serif}
.journey-caption {text-align:center;font:9px Arial,sans-serif;color:#8b9d80;letter-spacing:.4px;margin-top:0}
@media(prefers-reduced-motion:reduce){.journey-card svg g{animation:none!important}.grille.speaking{animation:none!important}}
</style>
""", unsafe_allow_html=True)

room_background(st.session_state.demo["location"])

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
        language_button, mic_button = st.columns([2, 1])
        with language_button:
            with st.popover("Choose Language:", use_container_width=True):
                st.selectbox("Staff language", LANGUAGES, key="from_language", on_change=change_languages)
                st.selectbox("Patient language", LANGUAGES, key="to_language", on_change=change_languages)
        with mic_button:
            st.button("Stop" if d["mic"] else "Speak", key="mic", on_click=press, args=("mic",),
                      type="primary" if d["mic"] else "secondary", help="Turn the microphone on or off for either person (simulated).")
    speaker_class = (
        "speaking"
        if d.get("speaking") and d["mic"] and d["translated"]
        else ""
    )

    with st.container(key=f"speaker_{d.get('speech_id', 0)}"):
        st.markdown(
            f'<div class="grille {speaker_class}" '
            'role="img" aria-label="Speaker grille"></div>'
            '<div class="brand">NativeLisans</div>',
            unsafe_allow_html=True,
        )
patient_journey(d)

st.button(
    "Move patient Location →" if d["location"] < len(PLACES) - 1 else "Restart patient journey ↺",
    key="move",
    on_click=press,
    args=("move",),
    use_container_width=True,
)
a, b = st.columns(2)
with a:
    with st.sidebar:
        st.subheader("Try demo")
        st.caption("Press Speak on the device, then choose a sample.")
        st.button("Patient speaks", key="patient", disabled=not d["mic"], on_click=press, args=("patient",))
        st.button("Staff speaks", key="staff", disabled=not d["mic"], on_click=press, args=("staff",))
        spoken_audio_controls()
        st.button("Reset", key="reset", on_click=reset)
        st.caption("Your recorded clips play the original phrase, then its translation. No microphone recording.")
    
if d["note"]:
    st.caption(d["note"])
