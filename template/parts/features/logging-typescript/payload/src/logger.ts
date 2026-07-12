const _levels = ["debug", "info", "warn", "error"] as const;
type Level = (typeof _levels)[number];

const activeLevel: Level = (process.env["LOG_LEVEL"] as Level) ?? "info";
const levelIndex = (l: Level): number => _levels.indexOf(l);

export function getLogger(name: string) {
  return {
    debug: (msg: string) => _log("debug", name, msg),
    info: (msg: string) => _log("info", name, msg),
    warn: (msg: string) => _log("warn", name, msg),
    error: (msg: string) => _log("error", name, msg),
  };
}

function _log(level: Level, name: string, msg: string): void {
  if (levelIndex(level) >= levelIndex(activeLevel)) {
    const ts = new Date().toISOString();
    console.log(`${ts} ${name} ${level.toUpperCase()} ${msg}`);
  }
}
