# streamlit_app.py
# 交差点の渋滞シミュレーター（信号時間のみ操作）
# - 国道: 10秒で最大30台（= 1秒 最大3台）
# - 県道: 10秒で最大10台（= 1秒 最大1台）
# - 信号は「国道→県道→国道…」の交互。生徒は青時間だけ10秒刻みで操作。
# - 到着台数・処理台数は毎秒ランダム（ポアソン到着、処理は上限内で一様ランダム）
# - 乱数シードを固定すれば結果の再現が可能
#
# 依存ライブラリ：Streamlit（標準の line_chart を使用。matplotlib / numpy は不要）

import random
import streamlit as st
import pandas as pd

# -----------------------------
# 乱数シード（再現性のため）
# -----------------------------
def set_seed(seed: int):
    random.seed(seed if isinstance(seed, int) else 0)

# -----------------------------
# ポアソン乱数（Knuth法：標準randomのみで実装）
# lam は 1秒あたりの平均到着台数（>=0）
# -----------------------------
def poisson_knuth(lam: float) -> int:
    if lam <= 0:
        return 0
    # Knuthの方法：k をカウントし、積pが e^{-lam} を下回るまで乱数を掛け続ける
    L = pow(2.718281828459045, -lam)  # e^{-lam}
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= random.random()
        if p <= L:
            return k - 1

# -----------------------------
# シミュレーション本体
# -----------------------------
def simulate(
    green_n: int,   # 国道の青時間（秒, 10秒刻み）
    green_p: int,   # 県道の青時間（秒, 10秒刻み）
    duration: int,  # 総シミュレーション秒
    lam_n: float,   # 国道の平均到着率（台/秒）
    lam_p: float,   # 県道の平均到着率（台/秒）
    seed: int,      # 乱数シード
):
    set_seed(seed)

    # 1秒あたりの最大処理台数（青のとき）
    cap_n = 3  # 国道（10秒で最大30）
    cap_p = 1  # 県道（10秒で最大10）

    queue_n = 0  # 国道の待ち台数
    queue_p = 0  # 県道の待ち台数
    cycle = green_n + green_p

    rows = []  # 可視化・集計用

    for t in range(duration + 1):
        # 1) 到着（毎秒ポアソン分布）
        arrivals_n = poisson_knuth(lam_n)
        arrivals_p = poisson_knuth(lam_p)
        queue_n += arrivals_n
        queue_p += arrivals_p

        # 2) 信号（交互制御：先に国道が青）
        mod = t % cycle
        is_green_n = (mod < green_n)

        # 3) 処理（青側のみ、1秒の上限までランダム処理）
        if is_green_n:
            serve = random.randint(0, cap_n)  # 0〜cap_n
            served = min(queue_n, serve)
            queue_n -= served
        else:
            serve = random.randint(0, cap_p)  # 0〜cap_p
            served = min(queue_p, serve)
            queue_p -= served

        rows.append(
            {
                "t": t,
                "queue_n": queue_n,
                "queue_p": queue_p,
                "green": "国道=青/県道=赤" if is_green_n else "国道=赤/県道=青",
                "arrivals_n": arrivals_n,
                "arrivals_p": arrivals_p,
            }
        )

    # DataFrame化
    df = pd.DataFrame(rows)

    # 指標（後半平均と終了時）
    end_n = int(df["queue_n"].iloc[-1])
    end_p = int(df["queue_p"].iloc[-1])
    mid = len(df) // 2
    avg_n = float(df["queue_n"].iloc[mid:].mean())
    avg_p = float(df["queue_p"].iloc[mid:].mean())

    def trend(end, avg):
        if end > avg * 1.1:
            return "増加傾向（渋滞気味）"
        elif end < avg * 0.9:
            return "減少傾向"
        else:
            return "横ばい"

    return {
        "df": df,
        "end_n": end_n,
        "end_p": end_p,
        "avg_n": avg_n,
        "avg_p": avg_p,
        "trend_n": trend(end_n, avg_n),
        "trend_p": trend(end_p, avg_p),
        "cycle": cycle,
        "green_n": green_n,
        "green_p": green_p,
        "lam_n": lam_n,
        "lam_p": lam_p,
    }

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="交差点の渋滞シミュレーター", layout="centered")

st.title("交差点の渋滞シミュレーター（信号時間のみ操作）")
st.caption("国道=10秒で最大30台（1秒 最大3台）、県道=10秒で最大10台（1秒 最大1台）。到着・処理は毎秒ランダム。")

colL, colR = st.columns(2)

with colL:
    st.subheader("信号設定（生徒が操作）")
    green_n = st.slider("国道の青時間（秒）", min_value=10, max_value=120, step=10, value=20)
    green_p = st.slider("県道の青時間（秒）", min_value=10, max_value=120, step=10, value=10)
    st.markdown(f"**サイクル長:** {green_n + green_p} 秒（国道→県道の順に青）")

    st.subheader("シミュレーション設定")
    duration = st.slider("総時間（秒）", min_value=120, max_value=1200, step=60, value=600)
    seed = st.number_input("乱数シード（再現用）", value=42, step=1)

with colR:
    with st.expander("詳細設定（教師用）", expanded=False):
        st.markdown("λ（ラムダ）は **1秒あたり平均で到着する台数** です。")
        lam_n = st.number_input("国道の平均到着率 λN（台/秒）", min_value=0.0, step=0.1, value=2.2, format="%.1f")
        lam_p = st.number_input("県道の平均到着率 λP（台/秒）", min_value=0.0, step=0.1, value=0.8, format="%.1f")
        st.markdown(
            "- λN を大きくすると国道が混みやすく（通勤ラッシュ等）\n"
            "- λP を大きくすると県道が混みやすく（イベント帰り等）"
        )
    st.info(
        "ヒント：終了時の待ち台数が小さく、かつ後半平均より減っていれば渋滞は緩和方向です。"
        "どちらかが増え続ける場合は、その道路の青を長くする、またはサイクルを短くして応答を速くしましょう。"
    )

# 実行（値変更で毎回再計算）
result = simulate(green_n, green_p, duration, lam_n, lam_p, int(seed))

# -----------------------------
# 時系列グラフ（Streamlit標準）
# -----------------------------
st.subheader("待ち台数の推移")
plot_df = result["df"][["t", "queue_n", "queue_p"]].set_index("t")
st.line_chart(plot_df, height=320)

# -----------------------------
# 結果サマリー（※ご要望通り、グラフの下に配置）
# -----------------------------
st.subheader("結果サマリー")
c1, c2, c3, c4 = st.columns(4)
c1.metric("終了時 待ち（国道）", f"{result['end_n']} 台")
c2.metric("終了時 待ち（県道）", f"{result['end_p']} 台")
c3.metric("後半平均（国道）", f"{result['avg_n']:.1f} 台")
c4.metric("後半平均（県道）", f"{result['avg_p']:.1f} 台")
st.write(f"傾向： 国道 **{result['trend_n']}** ／ 県道 **{result['trend_p']}**")

# -----------------------------
# 学習用メモ
# -----------------------------
with st.expander("学習のポイント（授業で使うヒント）"):
    st.markdown(
        "- **乱数シード**を固定すると、同じ設定で同じ結果が再現できます（比較しやすい）。\n"
        "- **サイクルを短く**すると応答が速くなり、片側がため込まれにくくなる一方で、1度に流せる台数は減る傾向。\n"
        "- **到着率（λ）**が処理能力を上回ると、どれだけ工夫しても待ちは増えます（容量の限界に着目）。\n"
        "- 国道: 1秒あたり最大3台、県道: 1秒あたり最大1台という**処理能力の違い**を意識して配分を考える。"
    )
