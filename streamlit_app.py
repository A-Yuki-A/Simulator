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
    green_n = st.slider("国道の青時間（秒）", 10, 120, 20, step=5)
    green_p = st.slider("県道の青時間（秒）", 10, 120, 10, step=5)
    duration = st.slider("シミュレーション時間（秒）", 120, 1200, 600, step=60)
    seed = st.number_input("乱数シード", value=42, step=1)

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
def _limits(green_n, green_p, mode="random"):
    """渋滞しない上限λ（台/秒）を返す。mode='random'は現行仕様（randintの揺れあり）。"""
    cycle = green_n + green_p
    if cycle == 0:
        return 0.0, 0.0
    if mode == "random":
        # 国道は青のとき平均1台/秒、県道は0.5台/秒 処理できるという仮定
        fn, fp = 1.0, 0.5
    else:  # 'deterministic' に切り替えると、毎秒きっちり cap を流すモデル
        fn, fp = 2.0, 1.0
    return fn * green_n / cycle, fp * green_p / cycle

def _judge(lam, limit):
    """λが上限に対してどのくらいかを判定（適正/注意/過多）"""
    if limit <= 0:
        return "—", "?", 0.0
    ratio = lam / limit
    if ratio <= 0.9:
        return "適正", "✅", ratio
    elif ratio <= 1.0:
        return "注意（限界付近）", "⚠️", ratio
    else:
        return "過多（増加傾向）", "🛑", ratio

with st.expander("詳細設定（教師用）", expanded=False):
    st.markdown("λ（ラムダ）は **1秒あたり平均で到着する台数**")

    # --- 渋滞しない上限（現行=揺れありモデル）を計算 ---
    # 揺れなしモデルにしたい場合は 'mode="deterministic"' に変更
    ln_limit, lp_limit = _limits(green_n, green_p, mode="random")

    # 入力（横並び）＋ 10秒換算の表示
    col1, col2 = st.columns([3, 2])
    with col1:
        lam_n_input = st.number_input(
            "国道の平均到着率 λN（台/秒）",
            key="lam_n",
            value=float(st.session_state.get("lam_n", lam_n)),
            step=0.01,
            format="%.2f",
        )
    with col2:
        st.write(f"➡ 約 **{lam_n_input*10:.1f} 台 / 10秒**")

    col3, col4 = st.columns([3, 2])
    with col3:
        lam_p_input = st.number_input(
            "県道の平均到着率 λP（台/秒）",
            key="lam_p",
            value=float(st.session_state.get("lam_p", lam_p)),
            step=0.01,
            format="%.2f",
        )
    with col4:
        st.write(f"➡ 約 **{lam_p_input*10:.1f} 台 / 10秒**")

    # 判定表示（目安＆現在値の比較）
    st.divider()
    st.markdown("### λの目安（渋滞しない上限値）")
    st.write(
        f"- 国道の上限: **λN ≤ {ln_limit:.2f}**（10秒あたり **{ln_limit*10:.1f} 台**）\n"
        f"- 県道の上限: **λP ≤ {lp_limit:.2f}**（10秒あたり **{lp_limit*10:.1f} 台**）"
    )

    jn, icon_n, r_n = _judge(lam_n_input, ln_limit)
    jp, icon_p, r_p = _judge(lam_p_input, lp_limit)

    st.markdown("### 現在の設定の判定")
    st.write(
        f"- 国道: **λN = {lam_n_input:.2f}** → {icon_n} **{jn}** "
        f"(上限比 {r_n*100:.0f}%)"
    )
    st.write(
        f"- 県道: **λP = {lam_p_input:.2f}** → {icon_p} **{jp}** "
        f"(上限比 {r_p*100:.0f}%)"
    )

    st.caption(
        "※ 目安：上限の90%以下=適正、90〜100%=注意、100%超=過多（長期的に待ちが増えやすい）。\n"
        "※ 揺れなしモデル（毎秒きっちり捌く）に変えると上限値が上がります。"
    )
