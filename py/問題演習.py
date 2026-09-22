import streamlit as st
import sqlite3
import json
import os
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
    
    tab1, tab2 = st.tabs(["ログイン", "新規登録"])
    
    with tab1:
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
    
    with tab2:
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

# ---------- 問題用紙選択 ----------
PAPERS_ROOT = r"C:\Users\ngcsi\Desktop\Haruki\JLPTcalc\papers"
# ✅ THIS LINE reads ALL folder names inside "papers"
paper_list = [f for f in os.listdir(PAPERS_ROOT) 
              if os.path.isdir(os.path.join(PAPERS_ROOT, f))]

if not paper_list:
    st.warning("⚠️ papersフォルダに問題用紙を追加してください")
    st.stop()

# ✅ THIS LINE shows them in dropdown
selected_paper = st.selectbox("📖 問題用紙を選択", paper_list)

# ✅ THIS LINE builds the path = folder name + "info.json"
path = os.path.join(PAPERS_ROOT, selected_paper, "info.json")

with open(path, encoding="utf-8") as f:
    p = json.load(f)

st.subheader(f"📝 {p['name']}")

# ---------- 画面分割 ----------
col_left, col_right = st.columns([3, 1])

# ========== 左：問題PDF + 音声 ==========
with col_left:
    st.subheader("📄 問題用紙 & 🎧 聴解音声")
    max_page = len(p["page_guide"])
    page = st.number_input("ページ", min_value=1, max_value=max_page, value=1)
    st.caption(f"📍 {p['page_guide'][str(page)]}")

    
    
    # PDF表示
    pdf_path = os.path.join(PAPERS_ROOT, selected_paper, p["pdf"])
    if os.path.exists(pdf_path):
        pdf_viewer(pdf_path, pages_to_render=[page])
    
    # 音声再生
    audio_path = os.path.join(PAPERS_ROOT, selected_paper, p["audio"])
    if os.path.exists(audio_path):
        with open(audio_path, "rb") as af:
            st.audio(af.read(), format="audio/mp3")

# ========== 右：回答入力 ==========
with col_right:
    st.subheader("✍️ 回答を記入")
    ans = {}
    
    # --- 言語知識（文字・語彙）---
    with st.expander("📝 言語知識（文字・語彙）問題1～7", expanded=True):
        for q in ["Q1","Q2","Q3","Q4","Q5","Q6","Q7"]:
            ans[q] = st.radio(q, [1,2,3,4], horizontal=True, key=f"a_{q}")
    
    # --- 言語知識（文法）---
    with st.expander("📝 言語知識（文法）問題8～14"):
        for q in ["Q8","Q9","Q10","Q11","Q12","Q13","Q14"]:
            ans[q] = st.radio(q, [1,2,3,4], horizontal=True, key=f"a_{q}")
    
    # --- 読解 ---
    with st.expander("📖 読解 問題15～31"):
        for q in ["Q15","Q16","Q17","Q18","Q19","Q20",
                  "Q21","Q22","Q23","Q24","Q25",
                  "Q26","Q27","Q28","Q29","Q30","Q31"]:
            ans[q] = st.radio(q, [1,2,3,4], horizontal=True, key=f"a_{q}")
    
    # --- 聴解 ---
    with st.expander("👂 聴解 問題1～5"):
        for q in ["L1","L2","L3","L4","L5","L6",
                  "L7","L8","L9","L10","L11","L12",
                  "L13","L14","L15","L16","L17","L18",
                  "L19","L20","L21","L22","L23","L24","L25",
                  "L26","L27","L28","L29","L30","L31",
                  "L32","L33","L34"]:
            ans[q] = st.radio(q, [1,2,3,4], horizontal=True, key=f"a_{q}")
    
    # --- 採点実行 ---
    if st.button("📤 回答を送信して採点", type="primary", use_container_width=True):
        key = p["answer_key"]
        w = p["scoring_weights"]
        
        # 各部の点数計算
        goi = sum(w[q] for q in ["Q1","Q2","Q3","Q4","Q5","Q6","Q7"] if ans[q] == key[q])
        bunpou = sum(w[q] for q in ["Q8","Q9","Q10","Q11","Q12","Q13","Q14"] if ans[q] == key[q])
        dokkai = sum(w[q] for q in ["Q15","Q16","Q17","Q18","Q19","Q20",
                                      "Q21","Q22","Q23","Q24","Q25",
                                      "Q26","Q27","Q28","Q29","Q30","Q31"] if ans[q] == key[q])
        choukai = sum(w[q] for q in ["L1","L2","L3","L4","L5","L6",
                                      "L7","L8","L9","L10","L11","L12",
                                      "L13","L14","L15","L16","L17","L18",
                                      "L19","L20","L21","L22","L23","L24","L25",
                                      "L26","L27","L28","L29","L30","L31",
                                      "L32","L33","L34"] if ans[q] == key[q])
        
        gengo_total = goi + bunpou
        total = gengo_total + dokkai + choukai
        passed = total >= 100 and gengo_total >= 19 and dokkai >= 19 and choukai >= 19
        
        # 結果表示
        st.subheader("📊 採点結果")
        c1, c2, c3 = st.columns(3)
        c1.metric("📝 言語知識", f"{gengo_total:.1f}/59", "✅ 合格" if gengo_total>=19 else "⚠️ 19点以上必要")
        c2.metric("📖 読解", f"{dokkai:.1f}/60", "✅ 合格" if dokkai>=19 else "⚠️ 19点以上必要")
        c3.metric("👂 聴解", f"{choukai:.1f}/59", "✅ 合格" if choukai>=19 else "⚠️ 19点以上必要")
        
        st.divider()
        st.header(f"🎯 総合得点：{total:.1f}/180 — {'✅ 合格！' if passed else '❌ 不合格'}")
        
        # 履歴に保存
        conn = sqlite3.connect("jlpt.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO results 
            (username, paper_name, vocab_grammar, reading, listening, total, passed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (st.session_state.username, p["name"], gengo_total, dokkai, choukai, total, "合格" if passed else "不合格"))
        conn.commit()
        conn.close()
        st.success("✅ 履歴に保存しました！")

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
        - 📝 言語知識：{r[2]:.1f}/59
        - 📖 読解：{r[3]:.1f}/60
        - 👂 聴解：{r[4]:.1f}/59
        - 🎯 総合得点：**{r[5]:.1f}/180** — {'✅ 合格' if r[6]=="合格" else '❌ 不合格'}
        """)
        st.divider()
else:
    st.info("まだ練習履歴がありません。上から問題を解いてみましょう！")