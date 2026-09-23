import type { StationObservation } from "@/lib/cwaObservations";

function fmt(v: number | null, digits = 1): string {
  return v === null || v === undefined ? "--" : v.toFixed(digits);
}

function formatTime(iso: string | null): string {
  if (!iso) return "--";
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}/${pad(d.getMonth() + 1)}/${pad(d.getDate())} 下午${pad(d.getHours())}:${pad(
    d.getMinutes()
  )}`;
}

interface Props {
  station: StationObservation;
  onRefresh: () => void;
}

export default function StationDetailCard({ station, onRefresh }: Props) {
  return (
    <div className="w-[280px] rounded-2xl border border-white/10 bg-black/70 p-4 text-white shadow-2xl backdrop-blur-md">
      <div className="mb-2 flex items-center gap-1.5">
        <span>📍</span>
        <div>
          <div className="text-base font-bold">{station.name}</div>
          <div className="text-[11px] text-white/50">
            {station.county}
            {station.town}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm">
        <div className="flex items-center gap-1.5 rounded-lg bg-white/5 px-2.5 py-1.5">
          🌡️ {fmt(station.temp)}°C
        </div>
        <div className="flex items-center gap-1.5 rounded-lg bg-white/5 px-2.5 py-1.5">
          💧 {fmt(station.humidity, 0)}%
        </div>
        <div className="flex items-center gap-1.5 rounded-lg bg-white/5 px-2.5 py-1.5">
          🌧️ {fmt(station.rain)} mm
        </div>
        <div className="flex items-center gap-1.5 rounded-lg bg-white/5 px-2.5 py-1.5">
          🌬️ {fmt(station.windSpeed)} m/s
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between text-[11px] text-white/50">
        <span>更新於 {formatTime(station.obsTime)}</span>
        <button onClick={onRefresh} className="rounded-lg bg-white/10 px-2 py-1 text-white hover:bg-white/20">
          ↻ 更新資料
        </button>
      </div>
    </div>
  );
}
