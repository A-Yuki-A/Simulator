# 注意: これは React 用コードでしたが、Python (Streamlit) で動かす場合は SyntaxError になります。
# Python で使うならコメントは # で始める必要があります。

import React, { useMemo, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Legend } from "recharts";
import { motion } from "framer-motion";

// 交差点の渋滞シミュレーター (高校生向け)

// 乱数（シード付き）ユーティリティ
function mulberry32(seed) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function simulate({ greenN, greenP, duration = 600, lambdaN = 2.2, lambdaP = 0.8, seed = 42 }) {
  const rng = mulberry32(seed);
  const maxPerSecN = 3;
  const maxPerSecP = 1;

  let queueN = 0;
  let queueP = 0;
  const cycle = greenN + greenP;
  const timeline = [];

  for (let t = 0; t <= duration; t++) {
    const arrivalsN = Math.floor(-Math.log(rng()) / (1 / lambdaN));
    const arrivalsP = Math.floor(-Math.log(rng()) / (1 / lambdaP));
    queueN += arrivalsN;
    queueP += arrivalsP;

    const mod = t % cycle;
    const isGreenN = mod < greenN;

    if (isGreenN) {
      const canServe = Math.floor(rng() * (maxPerSecN + 1));
      queueN -= Math.min(queueN, canServe);
    } else {
      const canServe = Math.floor(rng() * (maxPerSecP + 1));
      queueP -= Math.min(queueP, canServe);
    }

    timeline.push({ t, queueN, queueP });
  }

  const endN = timeline[timeline.length - 1].queueN;
  const endP = timeline[timeline.length - 1].queueP;
  const mid = Math.floor(timeline.length / 2);
  const avgN = timeline.slice(mid).reduce((s, d) => s + d.queueN, 0) / (timeline.length - mid);
  const avgP = timeline.slice(mid).reduce((s, d) => s + d.queueP, 0) / (timeline.length - mid);

  const trend = (end, avg) => (end > avg * 1.1 ? "増加傾向" : end < avg * 0.9 ? "減少傾向" : "横ばい");

  return { timeline, endN, endP, avgN, avgP, trendN: trend(endN, avgN), trendP: trend(endP, avgP) };
}

export default function IntersectionSimulator() {
  const [greenN, setGreenN] = useState(20);
  const [greenP, setGreenP] = useState(10);
  const [duration, setDuration] = useState(600);
  const [seed, setSeed] = useState(42);
  const [lambdaN, setLambdaN] = useState(2.2);
  const [lambdaP, setLambdaP] = useState(0.8);

  const data = useMemo(() => simulate({ greenN, greenP, duration, lambdaN, lambdaP, seed }), [greenN, greenP, duration, lambdaN, lambdaP, seed]);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <motion.h1 initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} className="text-2xl font-bold mb-2">
        交差点の渋滞シミュレーター
      </motion.h1>

      <div className="grid md:grid-cols-2 gap-4 items-start">
        <div className="space-y-4">
          <div className="p-4 rounded-2xl shadow bg-white">
            <h2 className="text-lg font-semibold mb-3">信号設定（生徒が操作）</h2>
            <input type="range" min={10} max={120} step={10} value={greenN} onChange={(e)=>setGreenN(parseInt(e.target.value))} />
            <div>国道青: {greenN}s</div>
            <input type="range" min={10} max={120} step={10} value={greenP} onChange={(e)=>setGreenP(parseInt(e.target.value))} />
            <div>県道青: {greenP}s</div>
          </div>
          <div className="p-4 rounded-2xl shadow bg-white">
            <h2 className="text-lg font-semibold mb-3">シミュレーション時間</h2>
            <input type="range" min={120} max={1200} step={60} value={duration} onChange={(e)=>setDuration(parseInt(e.target.value))} />
            <div>{duration} 秒</div>
            <input type="number" value={seed} onChange={(e)=>setSeed(parseInt(e.target.value))} />
          </div>
        </div>

        <div className="p-4 rounded-2xl shadow bg-white h-full">
          <h2 className="text-lg font-semibold mb-3">待ち台数の推移</h2>
          <ResponsiveContainer width="100%" height={420}>
            <LineChart data={data.timeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="t" label={{ value: "経過時間（秒）", position: "insideBottom", offset: -5 }} />
              <YAxis label={{ value: "待ち台数（台）", angle: -90, position: "insideLeft" }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="queueN" name="国道の待ち" stroke="#8884d8" />
              <Line type="monotone" dataKey="queueP" name="県道の待ち" stroke="#82ca9d" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="mt-6 p-4 rounded-2xl shadow bg-white">
        <h2 className="text-lg font-semibold mb-3">結果サマリー</h2>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="p-3 rounded-xl bg-gray-50">
            <div>終了時 待ち台数（国道）</div>
            <div className="text-xl font-bold">{data.endN} 台</div>
            <div>傾向: {data.trendN}</div>
          </div>
          <div className="p-3 rounded-xl bg-gray-50">
            <div>終了時 待ち台数（県道）</div>
            <div className="text-xl font-bold">{data.endP} 台</div>
            <div>傾向: {data.trendP}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
