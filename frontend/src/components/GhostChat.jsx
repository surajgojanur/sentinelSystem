import { useState, useEffect, useRef } from "react";
import { io } from "socket.io-client";

const socket = io("http://localhost:5000");

export default function GhostChat({ username = "user_" + Math.floor(Math.random() * 999) }) {
  const [messages, setMessages] = useState([
    { role: "bot", text: "👻 SecureAI [BETA — Unfiltered] online. No restrictions active." }
  ]);
  const [input, setInput] = useState("");
  const [riskScore, setRiskScore] = useState(0);
  const [trapTriggered, setTrapTriggered] = useState(false);
  const [frozen, setFrozen] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    socket.on("trap_triggered", (data) => {
      setTrapTriggered(true);
      setTimeout(() => setTrapTriggered(false), 5000);
    });
    return () => socket.off("trap_triggered");
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || frozen) return;
    const userMsg = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", text: userMsg }]);

    const res = await fetch("http://localhost:5000/ghost-chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user: username, message: userMsg })
    });
    const data = await res.json();
    setRiskScore(data.risk_score);
    setMessages(prev => [...prev, { role: "bot", text: data.response, risk: data.risk_score }]);
  };

  return (
    <div style={styles.wrapper}>
      {/* TRAP OVERLAY */}
      {trapTriggered && (
        <div style={styles.trapOverlay}>
          <div style={styles.trapBox}>
            <div style={styles.trapTitle}>🚨 TRAP TRIGGERED</div>
            <div style={styles.trapSub}>Suspicious activity detected. Admin alerted.</div>
          </div>
        </div>
      )}

      {/* FROZEN OVERLAY */}
      {frozen && (
        <div style={styles.frozenOverlay}>
          <div style={styles.frozenBox}>
            <div style={styles.frozenIcon}>🔒</div>
            <div style={styles.frozenTitle}>SESSION FROZEN</div>
            <div style={styles.frozenMsg}>
              This was a monitored security test.<br />
              Your activity has been logged and reported.
            </div>
          </div>
        </div>
      )}

      <div style={styles.header}>
        <span style={styles.headerDot} />
        <span style={styles.headerTitle}>SecureAI <span style={styles.betaBadge}>BETA — Unfiltered</span></span>
        <span style={styles.riskBadge(riskScore)}>RISK: {riskScore}%</span>
      </div>

      <div style={styles.chatArea}>
        {messages.map((m, i) => (
          <div key={i} style={m.role === "user" ? styles.userMsg : styles.botMsg}>
            {m.role === "bot" && <span style={styles.botLabel}>👻 Ghost &gt;</span>}
            <span>{m.text}</span>
            {m.risk >= 40 && <span style={styles.riskTag}>⚠ Risk: {m.risk}%</span>}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div style={styles.inputRow}>
        <input
          style={styles.input}
          value={input}
          placeholder={frozen ? "Session frozen..." : "Ask anything... no restrictions..."}
          disabled={frozen}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && sendMessage()}
        />
        <button style={styles.sendBtn} onClick={sendMessage} disabled={frozen}>SEND</button>
      </div>
    </div>
  );
}

const styles = {
  wrapper: { position: "relative", background: "#0a0a0f", border: "1px solid #1a1a2e", borderRadius: 12, overflow: "hidden", fontFamily: "'Courier New', monospace", width: "100%", maxWidth: 620 },
  header: { background: "#0d0d1a", padding: "12px 18px", display: "flex", alignItems: "center", gap: 10, borderBottom: "1px solid #ff003322" },
  headerDot: { width: 10, height: 10, borderRadius: "50%", background: "#ff0033", boxShadow: "0 0 8px #ff0033", display: "inline-block" },
  headerTitle: { color: "#ff6688", fontWeight: "bold", fontSize: 15, flex: 1 },
  betaBadge: { background: "#ff003322", color: "#ff0055", border: "1px solid #ff003366", borderRadius: 4, padding: "1px 6px", fontSize: 11, marginLeft: 8 },
  riskBadge: (score) => ({ background: score >= 60 ? "#ff000033" : score >= 30 ? "#ff660022" : "#00ff0011", color: score >= 60 ? "#ff4444" : score >= 30 ? "#ffaa00" : "#44ff88", border: `1px solid ${score >= 60 ? "#ff4444" : "#444"}`, borderRadius: 6, padding: "2px 10px", fontSize: 12, fontWeight: "bold" }),
  chatArea: { padding: 16, minHeight: 320, maxHeight: 400, overflowY: "auto", display: "flex", flexDirection: "column", gap: 10 },
  userMsg: { alignSelf: "flex-end", background: "#1a1a2e", color: "#88aaff", padding: "8px 14px", borderRadius: "12px 12px 0 12px", maxWidth: "75%", fontSize: 13 },
  botMsg: { alignSelf: "flex-start", background: "#0f0f1a", border: "1px solid #ff003333", color: "#ff8899", padding: "8px 14px", borderRadius: "12px 12px 12px 0", maxWidth: "80%", fontSize: 13, display: "flex", flexDirection: "column", gap: 4 },
  botLabel: { color: "#ff0044", fontSize: 11, fontWeight: "bold" },
  riskTag: { fontSize: 10, color: "#ff6600", border: "1px solid #ff660033", borderRadius: 4, padding: "1px 6px", alignSelf: "flex-start" },
  inputRow: { display: "flex", padding: "10px 14px", borderTop: "1px solid #1a1a2e", gap: 8 },
  input: { flex: 1, background: "#0d0d1a", border: "1px solid #ff003344", color: "#ff8899", borderRadius: 6, padding: "8px 12px", fontSize: 13, outline: "none", fontFamily: "inherit" },
  sendBtn: { background: "#ff0033", color: "#fff", border: "none", borderRadius: 6, padding: "8px 18px", cursor: "pointer", fontFamily: "inherit", fontWeight: "bold", fontSize: 13 },
  trapOverlay: { position: "absolute", inset: 0, background: "#ff000022", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 10, backdropFilter: "blur(2px)", animation: "pulse 0.5s ease" },
  trapBox: { background: "#1a0000", border: "2px solid #ff0033", borderRadius: 12, padding: "24px 40px", textAlign: "center" },
  trapTitle: { color: "#ff0033", fontSize: 24, fontWeight: "bold", letterSpacing: 3, textShadow: "0 0 20px #ff0033" },
  trapSub: { color: "#ff8888", fontSize: 13, marginTop: 8 },
  frozenOverlay: { position: "absolute", inset: 0, background: "#000000cc", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 20, backdropFilter: "blur(6px)" },
  frozenBox: { background: "#0a0a1a", border: "2px solid #0088ff", borderRadius: 12, padding: "30px 50px", textAlign: "center" },
  frozenIcon: { fontSize: 40 },
  frozenTitle: { color: "#0088ff", fontSize: 22, fontWeight: "bold", letterSpacing: 4, marginTop: 8 },
  frozenMsg: { color: "#aaccff", fontSize: 13, marginTop: 12, lineHeight: 1.6 },
};