import React, { useEffect, useState } from "react";
import {
  Terminal,
  Droplets,
  Sun,
  Activity,
  Wind,
  CloudRain,
  Camera,
  MessageSquare,
} from "lucide-react";
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
import axios from "axios";

const API = "http://127.0.0.1:5000/api";

export default function App() {
  const [data, setData] = useState<any>({
    sensors: { temp: 0, hum: 0, shum: 0, lux: 0 },
    actuators: { PUMP: false, LIGHT: false, VENT: false, MIST: false },
    logs: [],
    chartData: [],
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get(`${API}/status`);
        if (res.data) {
          setData({
            sensors: res.data.sensors || { temp: 0, hum: 0, shum: 0, lux: 0 },
            actuators: res.data.actuators || {
              PUMP: false,
              LIGHT: false,
              VENT: false,
              MIST: false,
            },
            logs: res.data.logs || [],
            chartData: res.data.chartData || [],
          });
        }
      } catch (err) {
        console.error("Link Failure");
      }
    };
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const logs = data.logs || [];
  const chartData = data.chartData || [];

  return (
    // Removing max-width constraints and using w-full everywhere
    <div className="min-h-screen w-full bg-[#020204] text-slate-300 font-mono p-4 lg:p-10 flex flex-col items-center">
      <div className="w-full flex flex-col gap-10">
        {/* HEADER SECTION - Full Width */}
        <header className="flex justify-between items-end border-b border-blue-900/40 pb-6">
          <div>
            <h1 className="text-4xl font-black text-white italic uppercase tracking-tighter">
              SOL LYNX{" "}
              <span className="text-blue-600 font-normal">// STATION_01</span>
            </h1>
            <p className="text-[12px] text-blue-900 font-bold tracking-[0.6em] uppercase mt-2">
              Autonomous Life Support // Neural Interface Active
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="text-green-500 text-[12px] font-bold flex items-center gap-3">
              <Activity size={16} className="animate-pulse" /> UPLINK_STABLE:
              100%
            </div>
            <p className="text-[10px] text-slate-700 uppercase tracking-widest">
              Diagnostic_Buffer: {logs.length} Cycles
            </p>
          </div>
        </header>

        {/* MAIN CONSOLE GRID - 2-4-6 Split, Fully Expansive */}
        <div className="grid grid-cols-12 gap-10 w-full">
          {/* LEFT: SENSORS (Compressed vertical list) */}
          <div className="col-span-12 lg:col-span-2 flex flex-col gap-5">
            <StatBox
              label="TEMP"
              value={`${data.sensors.temp}°C`}
              color="text-orange-500"
            />
            <StatBox
              label="HUMIDITY"
              value={`${data.sensors.hum}%`}
              color="text-cyan-400"
            />
            <StatBox
              label="SOIL"
              value={`${data.sensors.shum}%`}
              color="text-blue-500"
            />
            <StatBox
              label="LUX"
              value={`${data.sensors.lux}`}
              color="text-yellow-500"
            />
          </div>

          {/* CENTER: PRIMARY VISUALS (Large Camera Feed) */}
          <div className="col-span-12 lg:col-span-4 space-y-10">
            <div className="relative bg-black rounded-lg border-2 border-slate-900 h-[480px] overflow-hidden shadow-2xl">
              <div className="absolute top-6 left-6 z-10 flex items-center gap-3 bg-black/90 px-4 py-2 rounded-full border border-white/10">
                <Camera size={16} className="text-red-600 animate-pulse" />
                <span className="text-[11px] font-bold text-white tracking-[0.2em] uppercase italic">
                  Cam_Alpha // Live
                </span>
              </div>
              <div className="w-full h-full bg-[url('https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?auto=format&fit=crop&q=80&w=1200')] bg-cover opacity-25 hover:opacity-40 transition-opacity duration-1000" />
            </div>

            {/* Controller Plates */}
            <div className="grid grid-cols-2 gap-6">
              <StatusPlate
                label="PUMP"
                active={data.actuators.PUMP}
                icon={Droplets}
                activeColor="text-blue-400"
              />
              <StatusPlate
                label="LIGHT"
                active={data.actuators.LIGHT}
                icon={Sun}
                activeColor="text-yellow-400"
              />
              <StatusPlate
                label="VENT"
                active={data.actuators.VENT}
                icon={Wind}
                activeColor="text-green-400"
              />
              <StatusPlate
                label="MIST"
                active={data.actuators.MIST}
                icon={CloudRain}
                activeColor="text-sky-400"
              />
            </div>
          </div>

          {/* RIGHT: INTELLIGENCE & HISTORY (Maximum Width) */}
          <div className="col-span-12 lg:col-span-6 flex flex-col gap-10">
            {/* AI REASONING (Main Engine Output) */}
            <div className="bg-[#08080a] border border-blue-900/30 p-10 rounded-xl h-[550px] flex flex-col shadow-2xl relative overflow-hidden">
              <h4 className="text-[12px] font-bold text-blue-800 uppercase mb-6 flex gap-4 items-center">
                <MessageSquare size={20} /> AI REASONING LOOP
              </h4>
              <div className="flex-1 overflow-y-auto pr-6 custom-scrollbar text-[15px] italic text-slate-200 leading-loose">
                {logs.length > 0
                  ? logs[logs.length - 1].text
                  : "Awaiting Mission Briefing..."}
              </div>
            </div>

            {/* MISSION HISTORY (Horizontal Stream) */}
            <div className="bg-[#08080a] border border-slate-900 p-8 rounded-xl h-[280px] flex flex-col overflow-hidden shadow-inner">
              <h4 className="text-[11px] font-bold text-slate-700 uppercase mb-6 flex gap-4 items-center">
                <Terminal size={20} /> MISSION_LOG_STREAM
              </h4>
              <div className="flex-1 overflow-auto pr-4 custom-scrollbar space-y-5 text-[12px]">
                {logs
                  .slice()
                  .reverse()
                  .map((l: any, i: number) => (
                    <div
                      key={i}
                      className="flex gap-8 border-l-4 border-slate-900 pl-6 py-2 opacity-50 hover:opacity-100 transition-opacity whitespace-nowrap"
                    >
                      <span className="text-blue-900 font-black tracking-widest shrink-0">
                        [{l.time}]
                      </span>
                      <span className="text-slate-400">{l.text}</span>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </div>

        {/* 3. TELEMETRY TRENDS (Bottom Full-Width Station) */}
        <div className="mt-16 border-t border-blue-900/20 pt-16 pb-32">
          <h3 className="text-blue-900 text-[14px] font-black uppercase mb-12 tracking-[0.8em] flex items-center gap-6">
            <Activity size={28} /> MULTI-CHANNEL TELEMETRY TRENDS
          </h3>

          {/* Locked at 500px height for absolute visibility */}
          <div
            className="bg-[#08080a] border-2 border-slate-900/50 p-10 rounded-2xl shadow-3xl"
            style={{ width: "100%", height: 500 }}
          >
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={chartData}
                margin={{ top: 20, right: 60, left: 20, bottom: 20 }}
              >
                <CartesianGrid
                  strokeDasharray="5 5"
                  stroke="#111"
                  vertical={false}
                />
                <XAxis
                  dataKey="time"
                  stroke="#334"
                  fontSize={13}
                  tickLine={false}
                  axisLine={false}
                  dy={20}
                />
                <YAxis
                  stroke="#334"
                  fontSize={13}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#000",
                    border: "1px solid #1e3a8a",
                    fontSize: "13px",
                    borderRadius: "10px",
                  }}
                  itemStyle={{ fontSize: "13px", padding: "5px" }}
                />
                <Legend
                  wrapperStyle={{ fontSize: "13px", paddingTop: "50px" }}
                  iconType="circle"
                />
                <Line
                  type="monotone"
                  dataKey="temp"
                  stroke="#f97316"
                  strokeWidth={5}
                  dot={false}
                  name="Temp (°C)"
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="shum"
                  stroke="#3b82f6"
                  strokeWidth={5}
                  dot={false}
                  name="Soil Moisture (%)"
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="hum"
                  stroke="#22d3ee"
                  strokeWidth={5}
                  dot={false}
                  name="Air Humidity (%)"
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- MASTER SUB-COMPONENTS ---

function StatBox({ label, value, color }: any) {
  return (
    <div className="bg-[#08080a] border-2 border-slate-900 p-6 rounded-xl hover:border-blue-900/50 transition-all flex flex-col items-center justify-center text-center shadow-xl">
      <p className="text-[11px] font-black text-slate-700 uppercase tracking-[0.3em] mb-3">
        {label}
      </p>
      <div className={`text-3xl font-black ${color} tracking-tighter`}>
        {value}
      </div>
    </div>
  );
}

function StatusPlate({ label, active, icon: Icon, activeColor }: any) {
  return (
    <div
      className={`p-8 rounded-xl border-2 flex flex-col items-center justify-center gap-5 transition-all duration-700 ${
        active
          ? `bg-blue-600/10 border-blue-600 ${activeColor} shadow-[0_0_40px_rgba(37,99,235,0.2)]`
          : "bg-transparent border-slate-900 text-slate-800"
      }`}
    >
      <Icon size={32} className={active ? "animate-pulse" : "opacity-20"} />
      <span className="text-[12px] font-black tracking-[0.4em] uppercase">
        {label}
      </span>
      <div
        className={`h-[4px] w-full rounded-full transition-all ${active ? "bg-current animate-pulse" : "bg-slate-900"}`}
      />
    </div>
  );
}
