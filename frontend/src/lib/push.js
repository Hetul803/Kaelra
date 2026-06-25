import { api } from "./api";
import { getDeviceId } from "./device";

// Web Push helper — subscribe the browser to Kaelra's notifications (VAPID).

export function pushSupported() {
  return (
    typeof window !== "undefined" &&
    "serviceWorker" in navigator &&
    "PushManager" in window &&
    "Notification" in window
  );
}

function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = window.atob(base64);
  const arr = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
  return arr;
}

export async function getPushState() {
  if (!pushSupported()) return { supported: false, permission: "unsupported", subscribed: false };
  let subscribed = false;
  try {
    const reg = await navigator.serviceWorker.getRegistration();
    if (reg) {
      const sub = await reg.pushManager.getSubscription();
      subscribed = !!sub;
    }
  } catch (e) {
    /* ignore */
  }
  return { supported: true, permission: Notification.permission, subscribed };
}

export async function enablePush() {
  if (!pushSupported()) throw new Error("unsupported");
  const reg = await navigator.serviceWorker.register("/sw.js");
  await navigator.serviceWorker.ready;
  const permission = await Notification.requestPermission();
  if (permission !== "granted") throw new Error("denied");
  const { data } = await api.get("/push/vapid-public-key");
  let sub = await reg.pushManager.getSubscription();
  if (!sub) {
    sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(data.public_key),
    });
  }
  await api.post("/push/subscribe", { subscription: sub.toJSON(), device_id: getDeviceId() });
  return true;
}

export async function disablePush() {
  if (!pushSupported()) return;
  const reg = await navigator.serviceWorker.getRegistration();
  if (!reg) return;
  const sub = await reg.pushManager.getSubscription();
  if (sub) {
    try {
      await api.post("/push/unsubscribe", { endpoint: sub.endpoint });
    } catch (e) {
      /* ignore */
    }
    await sub.unsubscribe();
  }
}

export async function sendTestPush() {
  const { data } = await api.post("/push/test");
  return data;
}
