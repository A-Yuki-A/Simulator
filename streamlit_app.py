import React, { useMemo, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Legend } from "recharts";
import { motion } from "framer-motion";

/**
 * 交差点の渋滞シミュレーター（高校生向け）
 * - 国道と県道がクロスする単一路線の信号制御
 * - 生徒が操作できるのは「各道路の青信号の長さ（10秒単位）」のみ
 * - 到着台数はランダム（ポアソン到着）
 * - 青信号中の処理台数もランダム（1秒あたりの上限まで）
 *
 * 仕様（問題設定に合わせて調整可能）
 * - 国道の処理能力: 10秒で最大30台 → 1秒あたり最大3台
 * - 県道の処理能力: 10秒で最大10台 → 1秒あたり最大1台
 * - 信号は交互制御: 国道→県道→国道…（全赤は無し）
 * - 生徒は国道・県道それぞれの青信号時間（10秒ステップ）を設定
 * - シミュレーション時間は既定10分（600秒）
 * - 到着率（平均到着台数/秒）は教師用の「詳細設定」で変更可
 */

// 乱数（シード付き）ユーティリティ
function mulberry32(seed) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ポアソン乱数（Knuth法）
function poisson(lambda, rng) {
  const L = Math.exp(-lambda);
  let k = 0;
  let p = 1;
  do {
    k++;
    p *= rng();
  } while (p > L);
  return k - 1;
}

// 区間 [min, max] の整数乱数
function randInt(min, max, rng) {
  return Math.floor(rng() * (max - min + 1)) + min;
}

function simulate({
  greenN, // 国道の青時間（秒）
  greenP, // 県道の青時間（秒）
  duration = 600, // 総シミュレーション秒数
  lambdaN = 2.2, // 国道到着率（台/秒）
  lambdaP = 0.8, // 県道到着率（台/秒）
  seed = 42,
}) {
  const rng = mulberry32(seed);
  const maxPerSecN = 3; // 国道 1秒最大3台
  const maxPerSecP = 1; // 県道 1秒最大1台

  let queueN = 0; // 国道の待ち台数
  let queueP = 0; // 県道の待ち台数

  const cycle = greenN + greenP; // 交互信号のサイクル

  const timeline = [];

  for (let t = 0; t <= duration; t++) {
    // 1. 到着（ランダム）
    const arrivalsN = poisson(lambdaN, rng);
    const arrivalsP = poisson(lambdaP, rng);
    queueN += arrivalsN;
    queueP += arrivalsP;

    // 2. 信号の状態（t 時点でどちらが青か）
    const mod = t % cycle;
    const isGreenN = mod < greenN; // 先に国道を青、次に県道を青とする

    // 3. 処理（青の側だけ、1秒あたりの上限までランダム処理）
    if (isGreenN) {
      const canServe = randInt(0, maxPerSecN, rng);
      const served = Math.min(queueN, canServe);
      queueN -= served;
    } else {
      const canServe = randInt(0, maxPerSecP, rng);
      const served = Math.min(queueP, canServe);
      queueP -= served;
    }

    timeline.push({
      t,
      queueN,
      queueP,
      green: isGreenN ? "国道=青 / 県道=赤" : "国道=赤 / 県道=青",
      arrivalsN,
      arrivalsP,
    });
  }

  const endN = timeline[timeline.length - 1].queueN;
  const endP = timeline[timeline.length - 1].queueP;

  // 混雑評価（単純）：終了時の待ち台数と中盤の平均を比較
  const mid = Math.floor(timeline.length / 2);
  const avgN = timeline.slice(mid).reduce((s, d) => s + d.queueN, 0) / (timeline.length - mid);
  const avgP = timeline.slice(mid).reduce((s, d) => s + d.queueP, 0) / (timeline.length - mid);

  const trendN = endN > avgN * 1.1 ? "増加傾向（渋滞気味）" : endN < avgN * 0.9 ? "減少傾向" : "横ばい";
  const trendP = endP > avgP * 1.1 ? "増加傾向（渋滞気味）" : endP < avgP * 0.9 ? "減少傾向" : "横ばい";

  return { timeline, endN, endP, avgN, avgP, trendN, trendP };
}

export default function IntersectionSimulator() {
  const [greenN, setGreenN] = useState(20); // 国道の青（10秒単位）
  const [greenP, setGreenP] = useState(10); // 県道の青（10秒単位）
  const [duration, setDuration] = useState(600);
  const [seed, setSeed] = useState(42);

  // 詳細設定（教師用）
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [lambdaN, setLambdaN] = useState(2.2);
  const [lambdaP, setLambdaP] = useState(0.8);

  const data = useMemo(
    () =>
      simulate({
        greenN, greenP, duration, lambdaN, lambdaP, seed,
      }),
    [greenN, greenP, duration, lambdaN, lambdaP, seed]
  );

  const cycle = greenN + greenP;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <motion.h1 initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} className="text-2xl font-bold mb-2">
        交差点の渋滞シミュレーター
      </motion.h1>
      <p className="text-sm text-gray-600 mb-4">
        生徒は<strong>国道・県道の青信号の長さ（10秒単位）</strong>だけを調整します。<br />
        国道は 10秒で最大30台（≒1秒最大3台）、県道は 10秒で最大10台（≒1秒最大1台）流せます。到着台数・処理台数は毎秒ランダムです。
      </p>

      <div className="grid md:grid-cols-2 gap-4 items-start">
        <div className="space-y-4">
          <div className="p-4 rounded-2xl shadow bg-white">
            <h2 className="text-lg font-semibold mb-3">信号設定（生徒が操作）</h2>
            <label className="block text-sm mb-1">国道の青時間（秒）</label>
            <input type="range" min={10} max={120} step={10} value={greenN} onChange={(e)=>setGreenN(parseInt(e.target.value))} className="w-full" />
            <div className="text-right text-sm">{greenN} 秒</div>

            <label className="block text-sm mt-4 mb-1">県道の青時間（秒）</label>
            <input type="range" min={10} max={120} step={10} value={greenP} onChange={(e)=>setGreenP(parseInt(e.target.value))} className="w-full" />
            <div className="text-right text-sm">{greenP} 秒</div>

            <div className="mt-3 text-sm text-gray-600">サイクル長：<strong>{cycle} 秒</strong>（国道→県道の順に青）</div>
          </div>

          <div className="p-4 rounded-2xl shadow bg-white">
            <h2 className="text-lg font-semibold mb-3">シミュレーション</h2>
            <label className="block text-sm mb-1">総時間（秒）</label>
            <input type="range" min={120} max={1200} step={60} value={duration} onChange={(e)=>setDuration(parseInt(e.target.value))} className="w-full" />
            <div className="text-right text-sm">{duration} 秒</div>

            <label className="block text-sm mt-3 mb-1">乱数シード</label>
            <input type="number" value={seed} onChange={(e)=>setSeed(parseInt(e.target.value || "0"))} className="w-full border rounded px-2 py-1" />

            <button onClick={()=>{ /* 値変更で自動再計算のため空 */ }} className="mt-3 px-4 py-2 rounded-2xl shadow bg-black text-white">
              シミュレーション実行
            </button>

            <button onClick={()=>setShowAdvanced(v=>!v)} className="ml-2 px-4 py-2 rounded-2xl border">
              {showAdvanced ? "詳細設定を隠す" : "詳細設定（教師用）"}
            </button>

            {showAdvanced && (
              <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <label className="block mb-1">国道の平均到着率 λ<sub>N</sub>（台/秒）</label>
                  <input type="number" step="0.1" min="0" value={lambdaN} onChange={(e)=>setLambdaN(parseFloat(e.target.value || "0"))} className="w-full border rounded px-2 py-1" />
                </div>
                <div>
                  <label className="block mb-1">県道の平均到着率 λ<sub>P</sub>（台/秒）</label>
                  <input type="number" step="0.1" min="0" value={lambdaP} onChange={(e)=>setLambdaP(parseFloat(e.target.value || "0"))} className="w-full border rounded px-2 py-1" />
                </div>
                <p className="col-span-2 text-gray-500">
                  ※ λ は「1秒あたり平均で何台到着するか」。既定は λ<sub>N</sub>=2.2, λ<sub>P</sub>=0.8。
                </p>
              </div>
            )}
          </div>

          <div className="p-4 rounded-2xl shadow bg-white">
            <h2 className="text-lg font-semibold mb-3">結果サマリー</h2>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="p-3 rounded-xl bg-gray-50">
                <div className="text-gray-600">終了時 待ち台数（国道）</div>
                <div className="text-xl font-bold">{data.endN} 台</div>
                <div className="text-gray-600">傾向: {data.trendN}</div>
              </div>
              <div className="p-3 rounded-xl bg-gray-50">
                <div className="text-gray-600">終了時 待ち台数（県道）</div>
                <div className="text-xl font-bold">{data.endP} 台</div>
                <div className="text-gray-600">傾向: {data.trendP}</div>
              </div>
              <div className="p-3 rounded-xl bg-gray-50">
                <div className="text-gray-600">後半平均（国道）</div>
                <div className="text-xl font-bold">{data.avgN.toFixed(1)} 台</div>
              </div>
              <div className="p-3 rounded-xl bg-gray-50">
                <div className="text-gray-600">後半平均（県道）</div>
                <div className="text-xl font-bold">{data.avgP.toFixed(1)} 台</div>
              </div>
            </div>
            <p className="mt-3 text-sm text-gray-600">
              ヒント：終了時の待ち台数が小さく、かつ後半平均より減っていれば渋滞は緩和方向です。どちらかの待ちが増え続ける場合は、その道路の青を長くする/サイクルを短くするなどを試しましょう。
            </p>
          </div>
        </div>

        <div className="p-4 rounded-2xl shadow bg-white h-full">
          <h2 className="text-lg font-semibold mb-3">待ち台数の推移</h2>
          <ResponsiveContainer width="100%" height={420}>
            <LineChart data={data.timeline} margin={{ top: 10, right: 24, bottom: 10, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="t" label={{ value: "経過時間（秒）", position: "insideBottom", offset: -5 }} />
              <YAxis label={{ value: "待ち台数（台）", angle: -90, position: "insideLeft" }} />
              <Tooltip formatter={(v, n) => [v, n === "queueN" ? "国道の待ち" : n === "queueP" ? "県道の待ち" : n]} />
              <Legend />
              <Line type="monotone" dataKey="queueN" name="国道の待ち" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="queueP" name="県道の待ち" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>

          <div className="mt-4 text-sm text-gray-600">
            信号状態（凡例）: 国道と県道は交互に青になります。サイクル = 国道 {greenN}s → 県道 {greenP}s。
          </div>
        </div>
      </div>

      <div className="mt-6 p-4 rounded-2xl shadow bg-white">
        <h2 className="text-lg font-semibold mb-2">授業での使い方の例</h2>
        <ol className="list-decimal ml-6 space-y-1 text-sm text-gray-700">
          <li>最初は同じ配分（例: 国道20s・県道20s）で実行し、どちらが渋滞しやすいかを観察。</li>
          <li>国道の待ちが増えるなら国道を長く、県道の待ちが増えるなら県道を長くして再実行。</li>
          <li>サイクルを短く（例: 20s+10s→10s+10s）すると応答が速くなり、極端に長いと片側がため込みやすいことを確認。</li>
          <li>詳細設定で到着率 λ を変えると、イベント日や通勤時間帯のような混雑も再現できます。</li>
        </ol>
      </div>
    </div>
  );
}
