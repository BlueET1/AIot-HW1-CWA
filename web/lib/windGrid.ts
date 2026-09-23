// Coarse wind vector grid over Taiwan, built from Open-Meteo's free batched
// forecast API (no key, up to 1000 locations per request). Grid data is
// ordered row-major, north -> south, west -> east (row 0 = northernmost).

export interface WindGridHeader {
  lo1: number;
  la1: number; // northernmost latitude (row 0)
  lo2: number;
  la2: number; // southernmost latitude (last row)
  nx: number;
  ny: number;
  dx: number;
  dy: number; // positive; latitude decreases as row index increases
}

export interface WindGridData {
  header: WindGridHeader;
  u: number[]; // eastward component, m/s
  v: number[]; // northward component, m/s
}

const BBOX = { lo1: 118.8, lo2: 122.5, la1: 26.2, la2: 21.4 }; // la1 > la2 (north -> south)
const STEP = 0.3;

function buildGridPoints(): { lats: number[]; lons: number[]; nx: number; ny: number } {
  const lons: number[] = [];
  for (let lon = BBOX.lo1; lon <= BBOX.lo2 + 1e-6; lon += STEP) lons.push(Number(lon.toFixed(3)));
  const lats: number[] = [];
  for (let lat = BBOX.la1; lat >= BBOX.la2 - 1e-6; lat -= STEP) lats.push(Number(lat.toFixed(3)));
  return { lats, lons, nx: lons.length, ny: lats.length };
}

export async function fetchWindGrid(): Promise<WindGridData> {
  const { lats, lons, nx, ny } = buildGridPoints();

  const latParam: number[] = [];
  const lonParam: number[] = [];
  for (const lat of lats) {
    for (const lon of lons) {
      latParam.push(lat);
      lonParam.push(lon);
    }
  }

  const url =
    `https://api.open-meteo.com/v1/forecast?` +
    `latitude=${latParam.join(",")}&longitude=${lonParam.join(",")}` +
    `&current=wind_speed_10m,wind_direction_10m&wind_speed_unit=ms&timezone=UTC`;

  const res = await fetch(url, { next: { revalidate: 1800 } });
  if (!res.ok) {
    throw new Error(`Open-Meteo wind API responded ${res.status}`);
  }
  const data = await res.json();
  const list: Array<{ current?: { wind_speed_10m?: number; wind_direction_10m?: number } }> =
    Array.isArray(data) ? data : [data];

  const u: number[] = new Array(nx * ny).fill(0);
  const v: number[] = new Array(nx * ny).fill(0);

  list.forEach((entry, i) => {
    const speed = entry.current?.wind_speed_10m ?? 0;
    const dirDeg = entry.current?.wind_direction_10m ?? 0;
    const dirRad = (dirDeg * Math.PI) / 180;
    // Meteorological direction = where wind comes FROM; flip to get the
    // vector the wind blows TOWARD, which is what the particle sim needs.
    u[i] = -speed * Math.sin(dirRad);
    v[i] = -speed * Math.cos(dirRad);
  });

  return {
    header: {
      lo1: BBOX.lo1,
      la1: BBOX.la1,
      lo2: lons[nx - 1],
      la2: lats[ny - 1],
      nx,
      ny,
      dx: STEP,
      dy: STEP,
    },
    u,
    v,
  };
}

/** Bilinear-interpolated wind vector (u, v in m/s) at an arbitrary lon/lat. */
export function sampleWind(grid: WindGridData, lon: number, lat: number): [number, number] {
  const { header, u, v } = grid;
  const { lo1, la1, nx, ny, dx, dy } = header;

  const fx = (lon - lo1) / dx;
  const fy = (la1 - lat) / dy; // rows increase southward

  if (fx < 0 || fx > nx - 1 || fy < 0 || fy > ny - 1) return [0, 0];

  const x0 = Math.floor(fx);
  const x1 = Math.min(x0 + 1, nx - 1);
  const y0 = Math.floor(fy);
  const y1 = Math.min(y0 + 1, ny - 1);
  const tx = fx - x0;
  const ty = fy - y0;

  const idx = (yy: number, xx: number) => yy * nx + xx;
  const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

  const u00 = u[idx(y0, x0)];
  const u10 = u[idx(y0, x1)];
  const u01 = u[idx(y1, x0)];
  const u11 = u[idx(y1, x1)];
  const v00 = v[idx(y0, x0)];
  const v10 = v[idx(y0, x1)];
  const v01 = v[idx(y1, x0)];
  const v11 = v[idx(y1, x1)];

  const uTop = lerp(u00, u10, tx);
  const uBot = lerp(u01, u11, tx);
  const vTop = lerp(v00, v10, tx);
  const vBot = lerp(v01, v11, tx);

  return [lerp(uTop, uBot, ty), lerp(vTop, vBot, ty)];
}
