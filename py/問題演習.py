import streamlit as st
import sqlite3
import json
import os
import re
from streamlit_pdf_viewer import pdf_viewer

# ---------- ページ設定 ----------
st.set_page_config(
    page_title="JLPT計算",
    page_icon="🇯🇵",
    initial_sidebar_state="expanded",
    menu_items={}
)

# ---------- セッション管理 ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# ---------- ログイン画面 ----------
if not st.session_state.logged_in:
    st.title("🔐 JLPT N1 能力試験 練習ポータル")
    
    tab_login, tab_reg = st.tabs(["ログイン", "新規登録"])
    
    with tab_login:
        with st.form("login_form"):
            user = st.text_input("ユーザー名")
            pwd = st.text_input("パスワード", type="password")
            if st.form_submit_button("ログイン"):
                conn = sqlite3.connect("jlpt.db")
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd))
                if c.fetchone():
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.rerun()
                else:
                    st.error("❌ ユーザー名またはパスワードが違います")
                conn.close()
    
    with tab_reg:
        with st.form("reg_form"):
            new_user = st.text_input("ユーザー名を入力")
            new_pwd = st.text_input("パスワードを設定", type="password")
            if st.form_submit_button("アカウント作成"):
                if new_user and new_pwd:
                    try:
                        conn = sqlite3.connect("jlpt.db")
                        c = conn.cursor()
                        c.execute("INSERT INTO users VALUES (NULL, ?, ?)", (new_user, new_pwd))
                        conn.commit()
                        st.success("✅ 登録完了！ログインしてください")
                    except:
                        st.error("❌ このユーザー名は既に使われています")
                else:
                    st.error("両方入力してください")
                conn.close()
    
    st.stop()

# ---------- ログイン後 ----------
st.title(f"📚 ようこそ、{st.session_state.username} さん")
if st.button("🚪 ログアウト"):
    st.session_state.logged_in = False
    st.rerun()

# ---------- Calculate Scores ----------
def calculate_scores(user_answers, paper):
    ak = paper["answer_key"]
    wts = paper["scoring_weights"]
    sf = paper["score_formula"]
    result = {}
    for section_name, config in sf.items():
        earned = 0
        possible = 0
        for qid, user_choice in user_answers.items():
            belongs = any(qid.startswith(prefix) for prefix in config["prefix"])
            if not belongs:
                continue
            weight = wts.get(qid, 1)
            possible += weight
            if str(user_choice) == str(ak.get(qid, "")):
                earned += weight
        result[section_name] = round((earned / possible) * config["max"], 1) if possible > 0 else 0
    result["total"] = round(
        result["vocab_grammar"] + result["reading"] + result["listening"], 1
    )
    return result

# ---------- 問題用紙選択 ----------
PAPERS_ROOT = r"C:\Users\ngcsi\Desktop\Haruki\JLPTcalc\papers"
paper_list = [f for f in os.listdir(PAPERS_ROOT) 
              if os.path.isdir(os.path.join(PAPERS_ROOT, f))]
if not paper_list:
    st.warning("⚠️ papersフォルダに問題用紙を追加してください")
    st.stop()

selected_paper = st.selectbox("📖 問題用紙を選択", paper_list)
path = os.path.join(PAPERS_ROOT, selected_paper, "info.json")
with open(path, encoding="utf-8") as f:
    p = json.load(f)

st.subheader(f"📝 {p['name']}")

# ---------- State Management ----------
state_key = f"state_{selected_paper}"
if state_key not in st.session_state:
    st.session_state[state_key] = {
        "p1_ans": {}, "p1_done": False, "p1_scores": None,
        "p2_ans": {}, "p2_done": False, "p2_scores": None
    }
ps = st.session_state[state_key]

# ==================================================
# 🔹 SIDE-BY-SIDE LAYOUT — PDF LEFT | ANSWERS RIGHT
# ==================================================
col_pdf, col_ans = st.columns([3, 2])  # Left wider, right slightly narrower

# ========== LEFT PANEL: PDF ALWAYS HERE ==========
with col_pdf:
    st.subheader("📄 問題用紙")
    pdf_path = os.path.join(PAPERS_ROOT, selected_paper, p["pdf"])
    
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            content = f.read().decode("latin-1")
        all_page_markers = re.findall(r"/Type\s*/Page[^s]", content)
        total_pages = len(all_page_markers) or 16
        st.markdown(f"<h5 style='text-align:center;'>全 {total_pages} ページ</h5>", unsafe_allow_html=True)
        st.caption("スクロールして問題を見てください")
        pdf_viewer(input=pdf_path, width="100%", height=750)  # ✅ Tall enough to scroll
    else:
        st.error(f"❌ PDFが見つかりません: {p['pdf']}")
    

# ========== RIGHT PANEL: ANSWER TABS ==========
with col_ans:
    tab1, tab2, tab3 = st.tabs(["📖 Part1: 筆記", "👂 Part2: 聴解", "📊 結果"])
    
    # ---------- Part1 Tab ----------
    with tab1:
        if ps["p1_done"]:
            st.success("✅ Part1 回答済み")
            s = ps["p1_scores"]
            st.metric("📝 語彙・文法", f"{s['vocab_grammar']:.1f}/59",
                      "✅" if s["vocab_grammar"] >= 19 else "⚠️ 要復習")
            st.metric("📖 読解", f"{s['reading']:.1f}/60",
                      "✅" if s["reading"] >= 19 else "⚠️ 要復習")
            if st.button("🔄 再挑戦", key="reset_p1"):
                ps["p1_done"] = False
                ps["p1_answers"] = {}
                st.rerun()
        else:
            st.subheader("✍️ 回答を記入")
            p1_ans = {}

            # === SCROLLABLE Answer Sheet Container ===
            with st.container(height=800):  # ✅ Scrollable! Adjust height if needed
                for section in p["parts"]["part1"]["sections"]:
                    sec_id = section["id"]
                    with st.expander(f"{section['title']}", expanded=section.get("open", False)):
                        for mondai in section["mondai"]:
                            st.markdown(f"**{mondai['name']}**")
                            for q in mondai["questions"]:
                                qid = f"{sec_id}_{q}"
                                p1_ans[qid] = st.radio(
                                    f"{q}",
                                    [1, 2, 3, 4],
                                    horizontal=True,
                                    key=f"p1_{selected_paper}_{qid}"
                                )
                            st.divider()

            if st.button("📤 Part1 採点", type="primary", use_container_width=True):
                ps["p1_answers"] = p1_ans
                # ✅ Use empty dict if p2_answers doesn't exist yet
                all_ans = {**p1_ans, **ps.get("p2_answers", {})}
                scores = calculate_scores(all_ans, p)
                ps["p1_scores"] = scores
                ps["p1_done"] = True
                st.rerun()
    
    # ---------- Part2 Tab ----------
    with tab2:
        if ps["p2_done"]:
            st.success("✅ Part2 回答済み")
            s = ps["p2_scores"]
            st.metric("🎧 聴解", f"{s['listening']:.1f}/59",
                      "✅" if s["listening"] >= 19 else "⚠️ 要復習")
            if st.button("🔄 再挑戦", key="reset_p2"):
                ps["p2_done"] = False
                ps["p2_answers"] = {}
                st.rerun()
        else:
            st.subheader("✍️ 回答を記入")
            p2_ans = {}

            # ✅ ONLY ONE audio player — right at the top
            audio_path = os.path.join(PAPERS_ROOT, selected_paper, p["audio"])
            if os.path.exists(audio_path):
                st.audio(audio_path)  # ← ONE here
            else:
                st.warning("⚠️ 音声ファイルが見つかりません")

            # === SCROLLABLE Answer Sheet Container ===
            with st.container(height=800):
                for section in p["parts"]["part2"]["sections"]:
                    sec_id = section["id"]
                    with st.expander(f"{section['title']}", expanded=True):
                        for mondai in section["mondai"]:
                            st.markdown(f"**{mondai['name']}**")
                            for q in mondai["questions"]:
                                qid = f"{sec_id}_{mondai['name'].replace('問題','')}_{q}"
                                p2_ans[qid] = st.radio(
                                    f"{q}",
                                    [1, 2, 3, 4],
                                    horizontal=True,
                                    key=f"p2_{selected_paper}_{qid}"
                                )
                            st.divider()

            if st.button("📤 Part2 採点", type="primary", use_container_width=True):
                ps["p2_answers"] = p2_ans
                # ✅ Use empty dict if p1_answers doesn't exist yet
                all_ans = {**ps.get("p1_answers", {}), **p2_ans}
                scores = calculate_scores(all_ans, p)
                ps["p2_scores"] = scores
                ps["p2_done"] = True
                st.rerun()
    
    # ---------- Results Tab ----------
    with tab3:
        st.subheader("📊 総合結果")
        
        if not ps["p1_done"] and not ps["p2_done"]:
            st.info("まずは Part1 または Part2 から回答してください")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                if ps["p1_done"]:
                    st.metric("📝 言語知識", f"{ps['p1_scores']['vocab_grammar']:.1f}/60",
                              "✅" if ps["p1_scores"]["vocab_grammar"] >= 19 else "⚠️")
                else:
                    st.metric("📝 言語知識", "未実施")
            with c2:
                if ps["p1_done"]:
                    st.metric("📖 読解", f"{ps['p1_scores']['reading']:.1f}/60",
                              "✅" if ps["p1_scores"]["reading"] >= 19 else "⚠️")
                else:
                    st.metric("📖 読解", "未実施")
            with c3:
                if ps["p2_done"]:
                    st.metric("👂 聴解", f"{ps['p2_scores']['listening']:.1f}/60",
                              "✅" if ps["p2_scores"]["listening"] >= 19 else "⚠️")
                else:
                    st.metric("👂 聴解", "未実施")
            
            if ps["p1_done"] and ps["p2_done"]:
                total = ps["p1_scores"]["vocab_grammar"] + ps["p1_scores"]["reading"] + ps["p2_scores"]["listening"]
                passed = (total >= 100 and 
                          ps["p1_scores"]["vocab_grammar"] >= 19 and 
                          ps["p1_scores"]["reading"] >= 19 and 
                          ps["p2_scores"]["listening"] >= 19)
                
                st.divider()
                st.header(f"🎯 総合得点：{total:.1f}/180 — {'✅ 合格！' if passed else '❌ 不合格'}")
                
                if "saved_final" not in st.session_state[state_key]:
                    conn = sqlite3.connect("jlpt.db")
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO results 
                        (username, paper_name, vocab_grammar, reading, listening, total, passed)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (st.session_state.username, p["name"],
                          ps["p1_scores"]["vocab_grammar"], ps["p1_scores"]["reading"],
                          ps["p2_scores"]["listening"], total, "合格" if passed else "不合格"))
                    conn.commit()
                    conn.close()
                    st.session_state[state_key]["saved_final"] = True
                    st.success("✅ 履歴に保存しました！")
            else:
                st.info("📌 両方のパートを完了すると総合得点が表示されます")

# ---------- 学習履歴 ----------
st.divider()
st.subheader("📋 練習履歴")
conn = sqlite3.connect("jlpt.db")
c = conn.cursor()
c.execute("SELECT date, paper_name, vocab_grammar, reading, listening, total, passed FROM results WHERE username=? ORDER BY date DESC", (st.session_state.username,))
rows = c.fetchall()
conn.close()

if rows:
    for r in rows:
        st.write(f"📅 {r[0]} — **{r[1]}**")
        st.markdown(f"""
        - 📝 言語知識：{r[2]:.1f}/60
        - 📖 読解：{r[3]:.1f}/60
        - 👂 聴解：{r[4]:.1f}/60
        - 🎯 総合得点：**{r[5]:.1f}/180** — {'✅ 合格' if r[6]=="合格" else '❌ 不合格'}
        """)
        st.divider()
else:
    st.info("まだ練習履歴がありません。上から問題を解いてみましょう！")