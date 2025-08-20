# streamlit_app.py
# 交差点の渋滞シミュレーター（高校生向け）/ Streamlit

import random
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path  # ← Path を使うので必須

# === フォント設定（日本語フォントがあれば使用） ===
# プロジェクト内に font/SourceHanCodeJP-Regular.otf を置くと確実
fp = Path("font/SourceHanCodeJP-Regular.otf")
if fp.exists():
    fm.fontManager.addfont(str(fp))
    plt.rcParams["font.family"] = "Source Han Code JP"
else:
    # マシンにある日本語フォントにフォールバック
    for name in ["Noto Sans JP", "Noto Sans CJK JP", "IPAexGothic",
                 "Yu Gothic", "Hiragino Sans", "Meiryo"]:
        try:
            fm.findfont(fm.FontProperties(family=name), fallback_to_default=False)
            plt.rcParams["font.family"] = name
            break
        except Exception:
            pass
# マイナス記号の文字化け対策
plt.rcParams["axes.unicode_minus"] = False

# -----------------------------
# 乱数シード設定
# -----------------------------
def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)

# -----------------------------
# ポアソン乱数（車の到着台数）
# -----------------------------
def poisson(lam: float) -> int:
    return np.random.poisson(lam)

# -----------------------------
# シミュレーション本体
# -----------------------------
def simulate(green_n, green_p, duration, lam_n, lam_p, seed):
    set_seed(seed)

    cap_n = 2  # 国道: 1秒で最大2台
    cap_p = 1  # 県道: 1秒で最大1台

    queue_n, queue_p = 0, 0
    cycle = green_n + green_p
    timeline = []

    for t in range(duration + 1):
        # 到着（1秒あたり平均 lam のポアソン到着）
        arrivals_n = poisson(lam_n)
        arrivals_p = poisson(lam_p)
        queue_n += arrivals_n
        queue_p += arrivals_p

        # 信号制御（先に国道が青）
        mod = t % cycle
        is_green_n = mod < green_n

        if is_green_n:
            served = min(queue_n, random.randint(0, cap_n))
            queue_n -= served
        else:
            served = min(queue_p, random.randint(0, cap_p))
            queue_p -= served

        timeline.append({"t": t, "queue_n": queue_n, "queue_p": queue_p})

    # 結果まとめ
    end_n = timeline[-1]["queue_n"]
    end_p = timeline[-1]["queue_p"]
    mid = len(timeline) // 2
    avg_n = sum(d["queue_n"] for d in timeline[mid:]) / (len(timeline) - mid)
    avg_p = sum(d["queue_p"] for d in timeline[mid:]) / (len(timeline) - mid)

    def trend(end, avg):
        if end > avg * 1.1:
            return "増加傾向（渋滞気味）"
        elif end < avg * 0.9:
            return "減少傾向"
        else:
            return "横ばい"

    return {
        "timeline": timeline,
        "end_n": end_n,
        "end_p": end_p,
        "avg_n": avg_n,
        "avg_p": avg_p,
        "trend_n": trend(end_n, avg_n),
        "trend_p": trend(end_p, avg_p),
        "cycle": cycle,
    }

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="交差点の渋滞シミュレーター", layout="centered")

st.title("交差点の渋滞シミュレーター")
st.caption("国道=10秒で最大20台（1秒 最大2台）、県道=10秒で最大10台（1秒 最大1台）。")

# ▼ λ の既定値（国道2.0, 県道1.0）を session_state から取得／なければ設定
# ▼ λ の既定値（10秒あたりの安全目安：国道6台、県道1.5台）
lam_n_default = 0.60  # 国道: 10秒で6台
lam_p_default = 0.15  # 県道: 10秒で1.5台

# session_state 初期化
if "lam_n" not in st.session_state:
    st.session_state["lam_n"] = lam_n_default
if "lam_p" not in st.session_state:
    st.session_state["lam_p"] = lam_p_default

lam_n = float(st.session_state["lam_n"])
lam_p = float(st.session_state["lam_p"])

# 左: 生徒用設定 / 右: グラフ
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("信号設定")
    green_n = st.slider("国道の青時間（秒）", 10, 120, 20, step=10)
    green_p = st.slider("県道の青時間（秒）", 10, 120, 10, step=10)
    duration = st.slider("シミュレーション時間（秒）", 120, 1200, 600, step=60)
    seed = st.number_input("乱数シード", value=42, step=1)
    st.divider()
    show_sample = st.checkbox("サンプルグラフ（練習用）を表示", value=False)

with col2:
    # 右列にグラフ（λは session_state の値を使用）
    result = simulate(green_n, green_p, duration, lam_n, lam_p, int(seed))
    st.subheader("待ち台数の推移")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot([d["t"] for d in result["timeline"]],
            [d["queue_n"] for d in result["timeline"]], label="国道の待ち")
    ax.plot([d["t"] for d in result["timeline"]],
            [d["queue_p"] for d in result["timeline"]], label="県道の待ち")
    ax.set_title("待ち台数の推移（シミュレーション）")
    ax.set_xlabel("経過時間（秒）")
    ax.set_ylabel("待ち台数（台）")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5)
    st.pyplot(fig)

    if show_sample:
        st.subheader("サンプルグラフ（練習用）")
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.plot([0, 1, 2], [0, 1, 0], label="国道の待ち")
        ax2.set_title("待ち台数の推移（サンプル）")
        ax2.set_xlabel("経過時間（秒）")
        ax2.set_ylabel("待ち台数（台）")
        ax2.legend()
        ax2.grid(True, linestyle="--", alpha=0.5)
        st.pyplot(fig2)

# -----------------------------
# 結果サマリー
# -----------------------------
st.subheader("結果まとめ")
c1, c2, c3, c4 = st.columns(4)
c1.metric("終了時 待ち（国道）", f"{result['end_n']} 台")
c2.metric("終了時 待ち（県道）", f"{result['end_p']} 台")
c3.metric("後半平均（国道）", f"{result['avg_n']:.1f} 台")
c4.metric("後半平均（県道）", f"{result['avg_p']:.1f} 台")
st.write(f"傾向: 国道 {result['trend_n']} ／ 県道 {result['trend_p']}")

# -----------------------------
# 詳細設定（教師用） ー サマリーの下に配置
# -----------------------------
with st.expander("詳細設定（教師用）", expanded=False):
    st.markdown("λ（ラムダ）は **1秒あたり平均で到着する台数** です。")

    col1, col2 = st.columns([3, 2])
    with col1:
        lam_n_input = st.number_input(
            "国道の平均到着率 λN（台/秒）",
            key="lam_n",
            value=float(st.session_state["lam_n"]),
            step=0.1,
            format="%.1f",
        )
    with col2:
        st.write(f"➡ 約 {lam_n_input*10:.1f} 台 / 10秒")

    col3, col4 = st.columns([3, 2])
    with col3:
        lam_p_input = st.number_input(
            "県道の平均到着率 λP（台/秒）",
            key="lam_p",
            value=float(st.session_state["lam_p"]),
            step=0.1,
            format="%.1f",
        )
    with col4:
        st.write(f"➡ 約 {lam_p_input*10:.1f} 台 / 10秒")

    st.caption("※ 入力を変更すると即時に再計算され、グラフとサマリーに反映されます。")
