import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  Terminal,
  Zap,
  Droplets,
  Sun,
  Activity,
  Wind,
  CloudRain,
  Camera,
  Scan,
  MessageSquare,
} from "lucide-react";
import axios from "axios";

const API = "http://127.0.0.1:5000/api";

export default function App() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      axios
        .get(`${API}/status`)
        .then((res) => setData(res.data))
        .catch(() => {});
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const sendCmd = (code: string) => axios.post(`${API}/cmd`, { code });

  if (!data)
    return (
      <div className="h-screen bg-black flex items-center justify-center text-blue-500 font-mono animate-pulse">
        SYNCING WITH LYNX VISUAL RECON...
      </div>
    );

  return (
    <div className="min-h-screen bg-[#020203] text-slate-400 font-mono p-6">
      {/* HEADER */}
      <header className="flex justify-between items-center border-b border-blue-900/20 pb-4 mb-8">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tighter">
            SOL LYNX{" "}
            <span className="text-blue-600 font-light">// MISSION CONTROL</span>
          </h1>
          <p className="text-[9px] text-blue-900 font-bold tracking-[0.3em] uppercase">
            Sector: 7G // Greenhouse Alpha
          </p>
        </div>
        <div className="flex gap-6 items-center">
          <div className="text-[10px]">
            <span className="text-slate-600">UPTIME:</span> 01:14:22:09
          </div>
          <div className="text-green-500 text-[10px] font-bold flex items-center gap-2">
            <Activity size={12} className="animate-pulse" /> LINK: ACTIVE
          </div>
        </div>
      </header>

      {/* MAIN MISSION GRID */}
      <div className="grid grid-cols-12 gap-6">
        {/* LEFT COLUMN: TELEMETRY */}
        <div className="col-span-12 lg:col-span-3 space-y-4">
          <StatCard
            label="TEMP"
            value={`${data.sensors.temp}°C`}
            color="text-orange-500"
          />
          <StatCard
            label="HUMIDITY"
            value={`${data.sensors.hum}%`}
            color="text-cyan-400"
          />
          <StatCard
            label="SOIL"
            value={`${data.sensors.shum}%`}
            color="text-blue-500"
          />
          <StatCard
            label="LUMENS"
            value={`${data.sensors.lux}lx`}
            color="text-yellow-500"
          />
        </div>

        {/* CENTER COLUMN: CAMERA & ACTUATORS */}
        <div className="col-span-12 lg:col-span-5 space-y-6">
          {/* CAMERA BOX */}
          <div className="relative bg-slate-900 aspect-video rounded border border-slate-800 overflow-hidden group">
            <div className="absolute top-2 left-2 z-10 flex items-center gap-2 bg-black/50 px-2 py-1 rounded">
              <Camera size={12} className="text-red-500 animate-pulse" />
              <span className="text-[9px] font-bold text-white uppercase tracking-widest">
                CAM_01 // IR_ENABLED
              </span>
            </div>
            {/* Simulated Scanning Line */}
            <motion.div
              animate={{ top: ["0%", "100%", "0%"] }}
              transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
              className="absolute left-0 w-full h-[1px] bg-blue-500/30 z-10 shadow-[0_0_10px_#3b82f6]"
            />
            <div className="w-full h-full bg-[url('https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?auto=format&fit=crop&q=80&w=800')] bg-cover opacity-40 grayscale group-hover:grayscale-0 transition-all duration-700" />
            <div className="absolute inset-0 bg-blue-500/5 mix-blend-overlay" />
          </div>

          {/* ACTUATORS */}
          <div className="grid grid-cols-4 gap-3">
            <ControlBtn
              label="PUMP"
              active={data.actuators.PUMP}
              on={() => sendCmd("31")}
              off={() => sendCmd("30")}
              icon={Droplets}
            />
            <ControlBtn
              label="LITE"
              active={data.actuators.LIGHT}
              on={() => sendCmd("21")}
              off={() => sendCmd("20")}
              icon={Sun}
            />
            <ControlBtn
              label="VENT"
              active={data.actuators.VENT}
              on={() => sendCmd("51")}
              off={() => sendCmd("50")}
              icon={Wind}
            />
            <ControlBtn
              label="MIST"
              active={data.actuators.MIST}
              on={() => sendCmd("41")}
              off={() => sendCmd("40")}
              icon={CloudRain}
            />
          </div>
        </div>

        {/* RIGHT COLUMN: INTELLIGENCE */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          {/* LLM RESPONSE WINDOW */}
          <div className="bg-blue-950/10 border border-blue-900/20 rounded p-4 h-[250px] flex flex-col">
            <div className="flex items-center gap-2 text-blue-500 text-[10px] font-bold tracking-widest uppercase mb-3">
              <MessageSquare size={14} /> AI Reasoning Engine
            </div>
            <div className="flex-1 text-[11px] text-slate-300 italic leading-relaxed overflow-y-auto custom-scrollbar">
              {data.logs.length > 0
                ? data.logs[data.logs.length - 1].text
                : "Awaiting next diagnostic cycle..."}
            </div>
          </div>

          {/* MISSION LOG */}
          <div className="bg-black border border-slate-900 rounded p-4 h-[250px] flex flex-col">
            <div className="flex items-center gap-2 text-slate-600 text-[10px] font-bold tracking-widest uppercase mb-3">
              <Terminal size={14} /> Mission Log
            </div>
            <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar">
              {data.logs
                .slice(0, -1)
                .reverse()
                .map((log: any, i: number) => (
                  <div
                    key={i}
                    className="text-[10px] flex gap-3 opacity-50 hover:opacity-100 transition-opacity"
                  >
                    <span className="text-blue-900 shrink-0">[{log.time}]</span>
                    <span className="truncate">{log.text}</span>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- SUB-COMPONENTS ---
function StatCard({ label, value, color }: any) {
  return (
    <div className="bg-black border border-slate-900 p-4 hover:border-blue-900/30 transition-all group">
      <p className="text-[8px] font-bold text-slate-600 uppercase tracking-[0.2em] mb-1">
        {label}
      </p>
      <div
        className={`text-2xl font-bold tracking-tighter ${color} group-hover:pl-2 transition-all`}
      >
        {value}
      </div>
    </div>
  );
}

function ControlBtn({ label, active, on, off, icon: Icon }: any) {
  return (
    <button
      onClick={active ? off : on}
      className={`p-3 rounded border flex flex-col items-center gap-2 transition-all ${active ? "bg-blue-600/10 border-blue-600 text-blue-500" : "bg-transparent border-slate-900 text-slate-800"}`}
    >
      <Icon size={16} className={active ? "animate-pulse" : "opacity-20"} />
      <span className="text-[8px] font-black tracking-tighter uppercase">
        {label}
      </span>
    </button>
  );
}
function MissionAnalytics({ chartData }: { chartData: any[] }) {
  return (
    <div className="mt-8 bg-[#08080a] border border-blue-900/10 rounded-sm p-6 h-[400px]">
      <div className="flex items-center gap-2 text-blue-900 text-[10px] font-bold tracking-widest uppercase mb-6">
        <Activity size={14} /> Environmental Trend Analysis
      </div>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={chartData}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#1e293b"
            vertical={false}
          />
          <XAxis
            dataKey="time"
            stroke="#475569"
            fontSize={10}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="#475569"
            fontSize={10}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#020203",
              border: "1px solid #1e3a8a",
              fontSize: "10px",
            }}
            itemStyle={{ fontSize: "10px" }}
          />
          <Legend wrapperStyle={{ fontSize: "10px", paddingTop: "20px" }} />
          <Line
            type="monotone"
            dataKey="temp"
            stroke="#f97316"
            strokeWidth={2}
            dot={false}
            name="Temp (°C)"
            animationDuration={300}
          />
          <Line
            type="monotone"
            dataKey="shum"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            name="Soil (%)"
            animationDuration={300}
          />
          <Line
            type="monotone"
            dataKey="hum"
            stroke="#22d3ee"
            strokeWidth={2}
            dot={false}
            name="Humidity (%)"
            animationDuration={300}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// In your main App() return, add this at the bottom:
// <MissionAnalytics chartData={data.chartData} />
