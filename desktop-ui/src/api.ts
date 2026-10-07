export type Room = { id: string; enabled: boolean; quality: string; url: string; name: string }
export type Settings = {
  output: string; format: string; interval: string; fps: string;
  proxyEnabled: boolean; proxy: string; soopUsername: string;
  hasSoopPassword: boolean; hasSoopCookie: boolean;
}
export type Snapshot = { rooms: Room[]; running: boolean; startedAt: number | null; settings: Settings }
export type LogLine = { id: number; time: string; text: string; level: string }
export type RoomDraft = Pick<Room, "enabled" | "quality" | "url" | "name">
export type SettingsDraft = Pick<Settings, "output" | "format" | "interval" | "fps" | "proxyEnabled" | "proxy" | "soopUsername"> & {
  soopPassword: string; soopCookie: string;
}

export const qualities = ["2K", "1080P", "720P", "540P", "360P", "240P"]
export const formats = ["ts", "mkv", "flv", "mp4", "mp3音頻", "m4a音頻"]
export const emptyRoom: RoomDraft = { enabled: true, quality: "1080P", url: "", name: "" }
export const emptySettings: SettingsDraft = {
  output: "", format: "ts", interval: "300", fps: "自動", proxyEnabled: false,
  proxy: "", soopUsername: "", soopPassword: "", soopCookie: "",
}

export async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, {
    method: body === undefined ? "GET" : "POST",
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = await response.json()
  if (!response.ok) throw new Error(data.error || data.message || "操作失敗")
  return data as T
}

export function roomLabel(room: Room, fallback = "未命名直播間"): string {
  if (room.name) return room.name
  try { return new URL(room.url).pathname.split("/").filter(Boolean)[0] || fallback }
  catch { return fallback }
}
