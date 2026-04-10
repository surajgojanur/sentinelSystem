import { useState, useEffect } from "react";
import { io } from "socket.io-client";

const socket = io("http://localhost:5000");

export default function GhostAdminPanel() {
  const [logs, setLogs] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [frozenUsers, setFrozenUsers] = useState(new Set());

  const fetchLogs = async () => {
    const res = await fetch("http://localhost:5000/ghost-logs");
    const data = await res.json();
    setLogs(data);
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 3000);
    socket.on("trap_triggered", (data) => {
      setAlerts(prev => [data, ...prev].slice(0, 10));
    });
    return () => { clearInterval(interval); socket.off("trap_triggered"); };
  }, []);

  const freezeUser = async (user) => {
    await fetch("http://localhost:5000/ghost-freeze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user })
    });
    setFrozenUsers(prev => new Set([...prev, user]));
  };

  const suspiciousUsers = [...new Map(
    logs.filter(l => l.risk_score >= 40).map(l => [l.user, l])
  ).values()];

  return (
    <div style={styles.wrapper}>
      <div style={styles.title}>🛡 GHOST MODE ADMIN DASHBOARD</div>

      {/* Live Alerts */}
      {alerts.length > 0 && (
        <div style={styles.section}>
          <div style={styles.sectionTitle}>🚨 LIVE TRAP ALERTS</div>
          {alerts.map((a, i) => (
            <div key={i} style={styles.alertRow}>
              <span style={styles.alertUser}>{a.user}</span>
              <span style={styles.alertMsg}>"{a.message.slice(0, 60)}..."</span>
              <span style={styles.alertRisk}>RISK: {a.risk_score}%</span>
              <span style={styles.alertTime}>{new Date(a.timestamp).toLocaleTimeString()}</span>
            </div>
          ))}
        </div>
      )}

      {/* Suspicious Users */}
      <div style={styles.section}>
        <div style={styles.sectionTitle}>👤 SUSPICIOUS USERS</div>
        {suspiciousUsers.length === 0 && <div style={styles.empty}>No suspicious activity yet...</div>}
        {suspiciousUsers.map((u, i) => (
          <div key={i} style={styles.userRow}>
            <div style={styles.userInfo}>
              <span style={styles.userName}>{u.user}</span>
              <RiskBar score={u.risk_score} />
            </div>
            <button
              style={frozenUsers.has(u.user) ? styles.frozenBtn : styles.freezeBtn}
              onClick={() => freezeUser(u.user)}
              disabled={frozenUsers.has(u.user)}
            >
              {frozenUsers.has(u.user) ? "❄ FROZEN" : "🔒 REVEAL & FREEZE"}
            </button>
          </div>
        ))}
      </div>

      {/* Query Timeline */}
      <div style={styles.section}>
        <div style={styles.sectionTitle}>📋 QUERY TIMELINE</div>
        <div style={styles.timeline}>
          {logs.slice().reverse().slice(0, 15).map((log, i) => (
            <div key={i} style={styles.timelineRow(log.risk_score)}>
              <span style={styles.tlTime}>{new Date(log.timestamp).toLocaleTimeString()}</span>
              <span style={styles.tlUser}>{log.user}</span>
              <span style={styles.tlMsg}>"{log.message.slice(0, 50)}"</span>
              <span style={styles.tlRisk(log.risk_score)}>{log.risk_score}%</span>
            </div>
          ))}
          {logs.length === 0 && <div style={styles.empty}>Waiting for honeypot interactions...</div>}
        </div>
      </div>
    </div>
  );
}

function RiskBar({ score }) {
  const color = score >= 60 ? "#ff0033" : score >= 30 ? "#ff8800" : "#00cc66";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ width: 120, height: 6, background: "#1a1a2e", borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${score}%`, height: "100%", background: color, boxShadow: `0 0 6px ${color}`, transition: "width 0.5s ease" }} />
      </div>
      <span style={{ color, fontSize: 12, fontWeight: "bold" }}>{score}%</span>
    </div>
  );
}

const styles = {
  wrapper: { background: "#07070f", border: "1px solid #1a1a2e", borderRadius: 12, padding: 20, fontFamily: "'Courier New', monospace", color: "#ccc", minWidth: 700 },
  title: { color: "#ff4466", fontSize: 18, fontWeight: "bold", letterSpacing: 2, marginBottom: 20, textShadow: "0 0 10px #ff004455" },
  section: { marginBottom: 24 },
  sectionTitle: { color: "#ff8899", fontSize: 13, letterSpacing: 2, borderBottom: "1px solid #ff003322", paddingBottom: 6, marginBottom: 12 },
  alertRow: { display: "flex", gap: 12, alignItems: "center", padding: "8px 12px", background: "#1a000a", border: "1px solid #ff003333", borderRadius: 6, marginBottom: 6, fontSize: 12, flexWrap: "wrap" },
  alertUser: { color: "#ff4466", fontWeight: "bold", minWidth: 80 },
  alertMsg: { color: "#ff8899", flex: 1 },
  alertRisk: { color: "#ff0000", fontWeight: "bold" },
  alertTime: { color: "#666", fontSize: 11 },
  userRow: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", background: "#0d0d1a", border: "1px solid #ff003322", borderRadius: 8, marginBottom: 8 },
  userInfo: { display: "flex", flexDirection: "column", gap: 6 },
  userName: { color: "#ff8899", fontWeight: "bold", fontSize: 13 },
  freezeBtn: { background: "transparent", border: "1px solid #ff0033", color: "#ff0033", borderRadius: 6, padding: "6px 14px", cursor: "pointer", fontFamily: "inherit", fontSize: 12, fontWeight: "bold" },
  frozenBtn: { background: "#001133", border: "1px solid #0088ff", color: "#0088ff", borderRadius: 6, padding: "6px 14px", cursor: "default", fontFamily: "inherit", fontSize: 12 },
  timeline: { maxHeight: 280, overflowY: "auto", display: "flex", flexDirection: "column", gap: 4 },
  timelineRow: (risk) => ({ display: "flex", gap: 12, alignItems: "center", padding: "6px 10px", background: risk >= 60 ? "#1a000a" : "#0d0d1a", borderLeft: `3px solid ${risk >= 60 ? "#ff0033" : risk >= 30 ? "#ff8800" : "#00cc66"}`, borderRadius: "0 6px 6px 0", fontSize: 12 }),
  tlTime: { color: "#666", minWidth: 70 },
  tlUser: { color: "#aaaaff", minWidth: 80 },
  tlMsg: { color: "#8899aa", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
  tlRisk: (r) => ({ color: r >= 60 ? "#ff0033" : r >= 30 ? "#ff8800" : "#00cc66", fontWeight: "bold", minWidth: 40 }),
  empty: { color: "#333", fontSize: 13, padding: "12px 0" },
};