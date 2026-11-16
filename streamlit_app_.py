"""Тестове за парамедици – Streamlit приложение.

Въпросите са в questions.json (по раздели). За нов въпрос добавете обект
в "questions" на съответния раздел:
  {"question": "...", "options": ["A", "B", "C", "D"], "answer": 0,
   "explanation": "...", "source": "..."}
"answer" е индексът на верния отговор (броене от 0).
"""

import json
import random
import time
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Тестове за парамедици", page_icon="🚑", layout="wide")

DATA_FILE = Path(__file__).parent / "questions.json"
LETTERS = ["А", "Б", "В", "Г", "Д", "Е"]


@st.cache_data
def load_sections():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


SECTIONS = load_sections()
BY_ID = {s["id"]: s for s in SECTIONS}
TOTAL_Q = sum(len(s["questions"]) for s in SECTIONS)

# ---------- стил ----------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Golos+Text:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, label { font-family: 'Golos Text', sans-serif !important; }
.band { height: 10px; border-radius: 3px; margin: 0 0 1.2rem 0;
  background: repeating-linear-gradient(-45deg, #E2620D 0 18px, #F08A3E 18px 36px); }
.hero h1 { font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0.2rem; }
.hero p { color: #4a5568; margin-top: 0; }
.secnum { font-weight: 700; color: #E2620D; font-size: 0.85rem; letter-spacing: 0.08em; }
.sectitle { font-weight: 600; font-size: 1.08rem; margin: 0.1rem 0 0.25rem 0; }
.secdesc { color: #5a6474; font-size: 0.9rem; min-height: 2.6em; }
.qtext { font-size: 1.25rem; font-weight: 600; line-height: 1.4; margin: 0.4rem 0 1rem 0; }
.fb { border-radius: 8px; padding: 0.9rem 1.1rem; margin: 0.8rem 0; border-left: 6px solid; }
.fb.ok { background: #e8f4ea; border-color: #2e7d32; }
.fb.bad { background: #fbe9e7; border-color: #c62828; }
.fb .src { display: inline-block; margin-top: 0.5rem; font-size: 0.8rem; color: #5a6474;
  background: rgba(20,33,61,0.06); padding: 0.15rem 0.5rem; border-radius: 4px; }
.verdict { font-size: 2.4rem; font-weight: 700; margin: 0; }
.tri { display:inline-block; padding: 0.2rem 0.7rem; border-radius: 4px; font-weight: 600; color: white; }
.tri.g { background: #2e7d32; } .tri.y { background: #c98a00; } .tri.r { background: #c62828; }
div[role=radiogroup] label p { font-size: 1.05rem; line-height: 1.5; }
div[role=radiogroup] { gap: 0.35rem; }
.foot { color: #6b7280; font-size: 0.82rem; margin-top: 2rem; border-top: 1px solid #e2ddd3; padding-top: 0.8rem; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------- състояние ----------
ss = st.session_state
ss.setdefault("view", "home")
ss.setdefault("quiz", None)
ss.setdefault("best", {})  # id на раздел -> най-добър резултат в %


def build_items(pairs):
    """pairs: списък от (id на раздел, индекс на въпрос). Разбърква въпроси и отговори."""
    pairs = list(pairs)
    random.shuffle(pairs)
    items = []
    for sid, qi in pairs:
        n = len(BY_ID[sid]["questions"][qi]["options"])
        perm = list(range(n))
        random.shuffle(perm)
        items.append({"sid": sid, "qi": qi, "perm": perm})
    return items


def start_quiz(title, pairs, mode, key):
    ss.quiz = {
        "uid": str(time.time()),
        "title": title,
        "key": key,          # id на раздел или "exam"
        "mode": mode,        # "practice" или "exam"
        "items": build_items(pairs),
        "idx": 0,
        "answers": [],       # избран оригинален индекс (или None)
        "checked": False,
        "started": time.time(),
    }
    ss.view = "quiz"


def section_pairs(s):
    """Случайни въпроси от раздела – толкова, колкото е избрано в страничната лента."""
    pairs = [(s["id"], i) for i in range(len(s["questions"]))]
    n = ss.get("per_quiz", 15)
    if n == "Всички" or n >= len(pairs):
        return pairs
    return random.sample(pairs, n)


def go_home():
    ss.view = "home"
    ss.quiz = None


def q_of(item):
    return BY_ID[item["sid"]]["questions"][item["qi"]]


# ---------- странична лента ----------
with st.sidebar:
    st.markdown("### 🚑 Разделите")
    st.select_slider("Въпроси в упражнение", options=[10, 15, 20, 25, "Всички"],
                     value=15, key="per_quiz",
                     help="При всеки опит се теглят различни случайни въпроси от раздела.")
    if st.button("Начало", use_container_width=True):
        go_home()
        st.rerun()
    for s in SECTIONS:
        best = ss.best.get(s["id"])
        label = f"{s['n']} · {s['title']}" + (f"  ({best}%)" if best is not None else "")
        if st.button(label, key=f"side_{s['id']}", use_container_width=True):
            start_quiz(s["title"], section_pairs(s), "practice", s["id"])
            st.rerun()
    st.caption(f"{TOTAL_Q} въпроса в {len(SECTIONS)} раздела")


# ---------- начален екран ----------
def view_home():
    st.markdown('<div class="band"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero"><h1>Тестове за парамедици</h1>'
        "<p>Упражнения по раздели и пробен изпит по анатомия, диагностично-терапевтичните "
        "протоколи (ДТПА), Наредба № 3/2017 „Спешна медицина“ и Наредба № 54/2026 за професията „Парамедик“.</p></div>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown("#### Пробен изпит")
        st.caption("Случайни въпроси от избраните раздели. Резултатът и обясненията се показват накрая.")
        c1, c2, c3 = st.columns([3, 1.4, 1])
        with c1:
            chosen = st.multiselect(
                "Раздели", options=[s["id"] for s in SECTIONS],
                default=[s["id"] for s in SECTIONS],
                format_func=lambda i: BY_ID[i]["title"],
            )
        pool = [(sid, i) for sid in chosen for i in range(len(BY_ID[sid]["questions"]))]
        with c2:
            n = st.number_input("Брой въпроси", min_value=1, max_value=max(1, len(pool)),
                                value=min(30, max(1, len(pool))), step=5)
        with c3:
            st.write("")
            st.write("")
            if st.button("Започни изпита", type="primary", disabled=not pool, use_container_width=True):
                start_quiz("Пробен изпит", random.sample(pool, int(n)), "exam", "exam")
                st.rerun()

    st.markdown("#### Упражнения по раздели")
    st.caption("Веднага след всеки отговор виждате дали е верен, обяснение и източник. "
               "Всеки опит тегли различни случайни въпроси – броя избирате в страничната лента.")
    cols = st.columns(3)
    for i, s in enumerate(SECTIONS):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(
                    f'<div class="secnum">РАЗДЕЛ {s["n"]}</div>'
                    f'<div class="sectitle">{s["title"]}</div>'
                    f'<div class="secdesc">{s["desc"]}</div>',
                    unsafe_allow_html=True,
                )
                best = ss.best.get(s["id"])
                st.progress((best or 0) / 100,
                            text=f"Най-добър резултат: {best}%" if best is not None else f"{len(s['questions'])} въпроса")
                if st.button("Започни", key=f"go_{s['id']}", use_container_width=True):
                    start_quiz(s["title"], section_pairs(s), "practice", s["id"])
                    st.rerun()

    st.markdown(
        '<div class="foot">Източници: Диагностично-терапевтични протоколи и алгоритми – приложение към '
        "Заповед № РД-01-326/05.06.2023 г. на МЗ; Наредба № 3 от 6.10.2017 г. за утвърждаване на "
        "медицински стандарт „Спешна медицина“ (ДВ, бр. 86/2017, изм. и доп. ДВ, бр. 41/2024); Наредба № 54 от 15.06.2026 г. за придобиване на квалификация по професията „Парамедик“ (ДВ, бр. 57/2026). Въпросите по анатомия са по обща "
        "анатомия и физиология. Учебно помагало – при разминаване важи актуалният нормативен текст.</div>",
        unsafe_allow_html=True,
    )


# ---------- тест ----------
def view_quiz():
    qz = ss.quiz
    items = qz["items"]
    idx = qz["idx"]
    item = items[idx]
    q = q_of(item)
    total = len(items)

    top1, top2 = st.columns([4, 1])
    with top1:
        st.markdown(f"**{qz['title']}** · {'изпит' if qz['mode'] == 'exam' else 'упражнение'}")
    with top2:
        if st.button("✕ Изход", use_container_width=True):
            go_home()
            st.rerun()
    st.progress(idx / total, text=f"Въпрос {idx + 1} от {total}")
    if qz["key"] not in BY_ID:
        st.caption(BY_ID[item["sid"]]["title"])

    st.markdown(f'<div class="qtext">{q["question"]}</div>', unsafe_allow_html=True)

    perm = item["perm"]
    labels = [f"{LETTERS[k]}) {q['options'][orig]}" for k, orig in enumerate(perm)]
    choice = st.radio("Изберете отговор", options=list(range(len(perm))),
                      format_func=lambda k: labels[k], index=None,
                      key=f"r_{qz['uid']}_{idx}", label_visibility="collapsed",
                      disabled=qz["checked"])
    chosen_orig = perm[choice] if choice is not None else None
    last = idx == total - 1

    if qz["mode"] == "practice":
        if not qz["checked"]:
            if st.button("Провери", type="primary", disabled=choice is None):
                qz["answers"].append(chosen_orig)
                qz["checked"] = True
                st.rerun()
        else:
            given = qz["answers"][idx]
            ok = given == q["answer"]
            correct_letter = LETTERS[perm.index(q["answer"])]
            head = "✓ Вярно." if ok else f"✗ Грешно. Верният отговор е {correct_letter}) {q['options'][q['answer']]}."
            st.markdown(
                f'<div class="fb {"ok" if ok else "bad"}"><b>{head}</b><br>{q["explanation"]}'
                f'<br><span class="src">Източник: {q["source"]}</span></div>',
                unsafe_allow_html=True,
            )
            if st.button("Към резултата →" if last else "Следващ въпрос →", type="primary"):
                advance(last)
    else:
        if st.button("Предай изпита" if last else "Следващ →", type="primary", disabled=choice is None):
            qz["answers"].append(chosen_orig)
            advance(last)


def advance(last):
    qz = ss.quiz
    if last:
        qz["finished"] = time.time()
        correct = sum(1 for it, a in zip(qz["items"], qz["answers"]) if a == q_of(it)["answer"])
        pct = round(100 * correct / len(qz["items"]))
        if qz["key"] in BY_ID:
            ss.best[qz["key"]] = max(pct, ss.best.get(qz["key"], 0))
        ss.view = "results"
    else:
        qz["idx"] += 1
        qz["checked"] = False
    st.rerun()


# ---------- резултати ----------
def view_results():
    qz = ss.quiz
    items, answers = qz["items"], qz["answers"]
    total = len(items)
    wrong = [(it, a) for it, a in zip(items, answers) if a != q_of(it)["answer"]]
    correct = total - len(wrong)
    pct = round(100 * correct / total)
    mins, secs = divmod(int(qz.get("finished", time.time()) - qz["started"]), 60)

    if pct >= 80:
        tri, txt = "g", "Отлично – код зелено"
    elif pct >= 60:
        tri, txt = "y", "Добре, има какво да се допълни – код жълто"
    else:
        tri, txt = "r", "Нужен е преговор – код червено"

    st.markdown('<div class="band"></div>', unsafe_allow_html=True)
    st.markdown(f"### {qz['title']} – резултат")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<p class="verdict">{pct}%</p><span class="tri {tri}">{txt}</span>', unsafe_allow_html=True)
    c2.metric("Верни отговори", f"{correct} / {total}")
    c3.metric("Време", f"{mins} мин {secs:02d} сек")

    b1, b2, b3 = st.columns(3)
    if wrong and b1.button("Повтори само грешните", type="primary", use_container_width=True):
        start_quiz(qz["title"] + " – грешни", [(it["sid"], it["qi"]) for it, _ in wrong], "practice", "retry")
        st.rerun()
    if b2.button("Нов опит", use_container_width=True):
        start_quiz(qz["title"], [(it["sid"], it["qi"]) for it in items], qz["mode"], qz["key"])
        st.rerun()
    if b3.button("Към разделите", use_container_width=True):
        go_home()
        st.rerun()

    if wrong:
        st.markdown(f"#### Грешни отговори ({len(wrong)})")
        for it, a in wrong:
            q = q_of(it)
            with st.expander(q["question"]):
                given = q["options"][a] if a is not None else "—"
                st.markdown(f"❌ **Вашият отговор:** {given}")
                st.markdown(f"✅ **Верен отговор:** {q['options'][q['answer']]}")
                st.markdown(q["explanation"])
                st.caption(f"Източник: {q['source']} · Раздел: {BY_ID[it['sid']]['title']}")
    else:
        st.success("Нито една грешка!")


if ss.view == "quiz" and ss.quiz:
    view_quiz()
elif ss.view == "results" and ss.quiz:
    view_results()
else:
    view_home()
