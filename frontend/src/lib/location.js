import { api } from "./api";

// Location tracking — Kaelra builds her own timeline from browser geolocation
// (Google Maps Timeline has no public API). Opt-in; pings every few minutes.

const KEY = "kaelra_location";
let _timer = null;

export function locationSupported() {
  return typeof navigator !== "undefined" && "geolocation" in navigator;
}

export function isLocationEnabled() {
  return typeof localStorage !== "undefined" && localStorage.getItem(KEY) === "1";
}

function sendCurrent() {
  return new Promise((resolve) => {
    if (!locationSupported()) return resolve(false);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          await api.post("/location/ping", {
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
            accuracy: pos.coords.accuracy,
          });
          resolve(true);
        } catch (e) {
          resolve(false);
        }
      },
      () => resolve(false),
      { enableHighAccuracy: false, maximumAge: 120000, timeout: 15000 }
    );
  });
}

export async function enableLocation() {
  if (!locationSupported()) throw new Error("unsupported");
  const ok = await sendCurrent();
  if (!ok) throw new Error("denied");
  localStorage.setItem(KEY, "1");
  startTracking();
  return true;
}

export function disableLocation() {
  localStorage.removeItem(KEY);
  if (_timer) { clearInterval(_timer); _timer = null; }
}

export function startTracking() {
  if (!isLocationEnabled() || !locationSupported()) return;
  sendCurrent();
  if (_timer) return;
  _timer = setInterval(sendCurrent, 5 * 60 * 1000);
}
