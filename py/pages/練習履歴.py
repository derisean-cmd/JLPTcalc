import streamlit as st
import sqlite3
import pandas as pd
import os


def to_num(x):
    try:
        return float(x)
    except:
        return 0.0
    
# ---------- Page Setup ----------
st.set_page_config(
    page_title="練習履歴",
    layout="wide"
)


# ---------- Login Check ----------
if "username" not in st.session_state or not st.session_state.username:
    st.warning("⚠️ 先にログインしてください")
    st.stop()

# ---------- Title ----------
st.title("📋 練習履歴")
st.divider()

# ---------- Filter Dropdown ----------
filter_mode = st.selectbox(
    "📂 表示切替",
    options=["すべて表示", "アクティブのみ", "アーカイブ済みのみ"],
    index=1  # Default = show active only
)

# ========== Database connection - Load Data ==========
conn = sqlite3.connect("jlpt.db")  # ✅ Defined BEFORE use
c = conn.cursor()
# ---------- Build filter condition ----------
if filter_mode == "アクティブのみ":
    condition = "AND is_archived = 0"
elif filter_mode == "アーカイブ済みのみ":
    condition = "AND is_archived = 1"
else:
    condition = ""  # Show everything

# ---------- Load data with filter ----------
c.execute(f"""
    SELECT rowid, paper_name, date, vocab_grammar, reading, listening, total, passed, is_archived
    FROM results 
    WHERE username=? {condition}
    ORDER BY date DESC
""", (st.session_state.username,))
rows = c.fetchall()
conn.close()

if not rows:
    st.info("まだ練習履歴がありません。問題演習で挑戦してみましょう！")
    st.stop()

# ---------- Display Results ----------
# ---------- Build Table Data ----------
table_data = []
for r in rows:
    rec_id, paper_name_raw, date_str, vg, read, listen, total, passed, archived = r
    
    # Format date
    display_date = str(date_str).split(" ")[0]
    
    # Clean paper name
    paper_name = paper_name_raw.replace(" N1 日本語能力試験", "")
    paper_name = paper_name.replace(" N1 日本語能力試験", "")

    # Convert scores 
    vg_num = to_num(vg)
    read_num = to_num(read)
    listen_num = to_num(listen)
    total_num = to_num(total)
    
    # Status
    status = "✅ 合格" if passed == "合格" else "❌ 不合格"
    
    table_data.append({
        "Date": display_date,
        "Paper": paper_name,
        "Knowledge (Vocab/Grammar)": f"{vg_num:.1f}/60",
        "Reading": f"{read_num:.1f}/60",
        "Listening": f"{listen_num:.1f}/60",
        "Total": f"{total_num:.1f}/180",
        "Status": status
    })

# ---------- Display Proper Table ----------
df = pd.DataFrame(table_data)
st.dataframe(
    df,
    width="stretch",
    hide_index=True,
    column_config={
        "Date": st.column_config.TextColumn("Date", width="small"),
        "Paper": st.column_config.TextColumn("Paper", width="medium"),
        "Knowledge (Vocab/Grammar)": st.column_config.TextColumn("Knowledge (Vocab/Grammar) /60", width="medium"),
        "Reading": st.column_config.TextColumn("Reading /60", width="medium"),
        "Listening": st.column_config.TextColumn("Listening /60", width="medium"),
        "Total": st.column_config.TextColumn("Total /180", width="small"),
        "Status": st.column_config.TextColumn("Status", width="small")
    }
)

st.divider()
# --------- ARCHIVE BUTTON ---------
st.subheader("🛠️ 操作")

for r in rows:
    rec_id = r[0]
    paper = r[1]
    date_short = str(r[2]).split(" ")[0]
    is_archived = r[8]
    
    c1, c2, c3 = st.columns([4, 2, 1])
    with c1:
        st.write(f"**{paper}** — {date_short}")
    
    with c2:
        if not is_archived:
            if st.button(f"📁 アーカイブ", key=f"arc_{rec_id}"):
                import sqlite3
                conn = sqlite3.connect("jlpt.db")
                c = conn.cursor()
                c.execute("UPDATE results SET is_archived = 1 WHERE rowid = ?", (rec_id,))
                conn.commit()
                conn.close()
                st.rerun()
        else:
            if st.button(f"↩️ 戻す", key=f"unarc_{rec_id}"):
                import sqlite3
                conn = sqlite3.connect("jlpt.db")
                c = conn.cursor()
                c.execute("UPDATE results SET is_archived = 0 WHERE rowid = ?", (rec_id,))
                conn.commit()
                conn.close()
                st.rerun()
    
    with c3:
        # Only show DELETE button if record is archived
        if is_archived:
            if st.button(f"🗑️", key=f"del_{rec_id}"):
                if "confirm_del" not in st.session_state or st.session_state.confirm_del != rec_id:
                    st.session_state.confirm_del = rec_id
                    st.warning("⚠️ もう一度 🗑️ を押すと完全削除")
                else:
                    import sqlite3
                    conn = sqlite3.connect("jlpt.db")
                    c = conn.cursor()
                    c.execute("DELETE FROM results WHERE rowid = ?", (rec_id,))
                    conn.commit()
                    conn.close()
                    st.session_state.confirm_del = None
                    st.rerun()
        # If active → nothing shows here ✅

# ---------- Quick Summary Below ----------
col1, col2 = st.columns(2)
with col1:
    st.metric("📝 受験回数", len(rows))
with col2:
    passed_count = sum(1 for r in rows if r[7] == "合格")
    st.metric("✅ 合格", passed_count)
