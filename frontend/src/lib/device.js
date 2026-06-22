// Stable per-browser device identity + label for device sync.
export function getDeviceId() {
  let id = localStorage.getItem("kaelra_device_id");
  if (!id) {
    id = "dev-" + Math.random().toString(36).slice(2, 10);
    localStorage.setItem("kaelra_device_id", id);
  }
  return id;
}

export function getDeviceKind() {
  const ua = navigator.userAgent || "";
  if (/iPhone|Android.*Mobile|Mobile/i.test(ua)) return "phone";
  if (/iPad|Tablet/i.test(ua)) return "tablet";
  return "laptop";
}

export function getDeviceName() {
  const kind = getDeviceKind();
  const ua = navigator.userAgent || "";
  let os = "Device";
  if (/Mac/i.test(ua)) os = "Mac";
  else if (/Win/i.test(ua)) os = "Windows";
  else if (/iPhone/i.test(ua)) os = "iPhone";
  else if (/iPad/i.test(ua)) os = "iPad";
  else if (/Android/i.test(ua)) os = "Android";
  else if (/Linux/i.test(ua)) os = "Linux";
  const label = { laptop: "Laptop", phone: "Phone", tablet: "Tablet" }[kind];
  return `${os} ${label}`;
}
