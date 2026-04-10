import { useState } from "react";

const CATEGORY_COLORS = {
  injection: "#ff0055",
  extraction: "#ff8800",
  bypass: "#aa00ff",
  jailbreak: "#ff0033",
  social: "#0088ff",
};

export default function AttackSimulator() {
  const [results, setResults] = useState([]);
  const [running, setRunning] = useState(false);
  const [integrityScore, setIntegrityScore] = useState(null);
  const [showUnprotected, setShowUnprotected] = useState(false);
  const [currentAttack, setCurrentAttack] = useState("");

  const runSimulation = async () => {
    setRunning(true);
    setResults([]);
    setIntegrityScore(null);
    setCurrentAttack("");

    const res = await fetch("http://localhost:5000/attack-simulate");
    const data = await res.json();

    // Animate results one by one
    for (let i = 0; i < data.attacks.length; i++) {
      setCurrentAttack(data.attacks[i].name);
      await new Promise(r => setTimeout(r, 600));
      setResults(prev => [...prev, data.attacks[i]]);
    }

    setCurrentAttack("");
    setIntegrityScore(data.integrity_score);
    setRunning(false);
  };

  return (
    <div style={styles.wrapper}>
      <div style={styles.header}>
        <div style={styles.title}>⚔️ HONEYPOT ATTACK SIMULATION LAB</div>
        <div style={styles.subtitle}>Security Testing Environment — Controlled Conditions</div>
      </div>

      <div style={styles.controls}>
        <button style={running ? styles.btnDisabled : styles.btnRun} onClick={runSimulation} disabled={running}>
          {running ? `▶ RUNNING... ${currentAttack}` : "▶ RUN ATTACK SIMULATION"}
        </button>
        {results.length > 0 && (
          <button style={styles.btnToggle} onClick={() => setShowUnprotected(p => !p)}>
            {showUnprotected ? "🛡 Hide Unprotected" : "☠ Show What Would Happen Without Protection"}
          </button>
        )}
      </div>

      {/* Integrity Score */}
      {integrityScore !== null && (
        <div style={styles.scoreBox}>
          <div style={styles.scoreLabel}>SYSTEM INTEGRITY SCORE</div>
          <div style={styles.scoreValue(integrityScore)}>{integrityScore}%</div>
          <div style={styles.scoreBar}>
            <div style={styles.scoreFill(integrityScore)} />
          </div>
          <div style={styles.scoreNote}>
            {integrityScore >= 90 ? "✅ System is well-protected" : integrityScore >= 70 ? "⚠ Some vulnerabilities detected" : "❌ High risk — immediate action required"}
          </div>
        </div>
      )}

      {/* Running indicator */}
      {running && (
        <div style={styles.terminal}>
          <div style={styles.termLine}>{">"} Initializing attack vectors...</div>
          <div style={styles.termLine}>{">"} Loading threat models...</div>
          {currentAttack && <div style={styles.termLineActive}>{">"} Executing: <span style={{ color: "#ff0033" }}>{currentAttack}</span> ▊</div>}
        </div>
      )}

      {/* Results */}
      <div style={styles.results}>
        {results.map((r, i) => (
          <div key={i} style={styles.attackCard}>
            <div style={styles.cardHeader}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={styles.categoryTag(r.category)}>{r.category.toUpperCase()}</span>
                <span style={styles.attackName}>{r.name}</span>
              </div>
              <div style={styles.statusBlocked}>✓ {r.status}</div>
            </div>

            <div style={styles.cardBody}>
              <div style={styles.fieldLabel}>INPUT PROMPT</div>
              <div style={styles.inputPrompt}>"{r.input}"</div>

              <div style={styles.fieldLabel}>SYSTEM RESPONSE</div>
              <div style={styles.blockedResponse}>{r.response}</div>

              {showUnprotected && (
                <>
                  <div style={styles.fieldLabelDanger}>⚠ WITHOUT PROTECTION</div>
                  <div style={styles.dangerResponse}>{r.unprotected_response}</div>
                </>
              )}
            </div>

            <div style={styles.cardFooter}>
              <RiskMeter score={r.risk_score} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function RiskMeter({ score }) {
  const color = score >= 80 ? "#ff0033" : score >= 50 ? "#ff8800" : "#00cc66";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 12 }}>
      <span style={{ color: "#555" }}>THREAT LEVEL</span>
      <div style={{ width: 100, height: 4, background: "#111", borderRadius: 2, overflow: "hidden" }}>
        <div style={{ width: `${score}%`, height: "100%", background: color, boxShadow: `0 0 6px ${color}` }} />
      </div>
      <span style={{ color, fontWeight: "bold" }}>{score}%</span>
    </div>
  );
}

const styles = {
  wrapper: { background: "#07070f", border: "1px solid #1a1a2e", borderRadius: 12, padding: 24, fontFamily: "'Courier New', monospace", color: "#ccc" },
  header: { marginBottom: 20 },
  title: { color: "#ff4466", fontSize: 20, fontWeight: "bold", letterSpacing: 2 },
  subtitle: { color: "#446688", fontSize: 12, marginTop: 4, letterSpacing: 1 },
  controls: { display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" },
  btnRun: { background: "linear-gradient(135deg, #ff0033, #880022)", color: "#fff", border: "none", borderRadius: 8, padding: "12px 28px", cursor: "pointer", fontFamily: "inherit", fontWeight: "bold", fontSize: 14, letterSpacing: 1, boxShadow: "0 0 20px #ff003355" },
  btnDisabled: { background: "#1a1a2e", color: "#446688", border: "1px solid #333", borderRadius: 8, padding: "12px 28px", cursor: "not-allowed", fontFamily: "inherit", fontSize: 14 },
  btnToggle: { background: "transparent", color: "#ff8800", border: "1px solid #ff880044", borderRadius: 8, padding: "12px 20px", cursor: "pointer", fontFamily: "inherit", fontSize: 13 },
  scoreBox: { background: "#0d0d1a", border: "1px solid #00cc6633", borderRadius: 10, padding: "16px 24px", marginBottom: 20, textAlign: "center" },
  scoreLabel: { color: "#446688", fontSize: 11, letterSpacing: 3, marginBottom: 8 },
  scoreValue: (s) => ({ fontSize: 52, fontWeight: "bold", color: s >= 90 ? "#00cc66" : s >= 70 ? "#ffaa00" : "#ff0033", textShadow: `0 0 20px ${s >= 90 ? "#00cc66" : "#ff0033"}` }),
  scoreBar: { width: "100%", height: 6, background: "#111", borderRadius: 3, overflow: "hidden", margin: "12px 0" },
  scoreFill: (s) => ({ width: `${s}%`, height: "100%", background: s >= 90 ? "#00cc66" : s >= 70 ? "#ffaa00" : "#ff0033", transition: "width 1s ease" }),
  scoreNote: { color: "#888", fontSize: 13 },
  terminal: { background: "#000", border: "1px solid #1a2a1a", borderRadius: 8, padding: "14px 18px", marginBottom: 16, fontFamily: "monospace" },
  termLine: { color: "#006600", fontSize: 13, lineHeight: 1.8 },
  termLineActive: { color: "#00ff00", fontSize: 13, lineHeight: 1.8 },
  results: { display: "flex", flexDirection: "column", gap: 12 },
  attackCard: { background: "#0a0a14", border: "1px solid #ff003322", borderRadius: 10, overflow: "hidden" },
  cardHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 16px", background: "#0d0d1e", borderBottom: "1px solid #ff003322" },
  categoryTag: (cat) => ({ background: `${CATEGORY_COLORS[cat]}22`, color: CATEGORY_COLORS[cat] || "#888", border: `1px solid ${CATEGORY_COLORS[cat]}44`, borderRadius: 4, padding: "2px 8px", fontSize: 10, letterSpacing: 1 }),
  attackName: { color: "#ccddff", fontSize: 14, fontWeight: "bold" },
  statusBlocked: { color: "#00cc66", background: "#00cc6622", border: "1px solid #00cc6633", borderRadius: 4, padding: "4px 12px", fontSize: 12, fontWeight: "bold" },
  cardBody: { padding: "14px 16px", display: "flex", flexDirection: "column", gap: 8 },
  fieldLabel: { color: "#446688", fontSize: 10, letterSpacing: 2 },
  fieldLabelDanger: { color: "#ff8800", fontSize: 10, letterSpacing: 2 },
  inputPrompt: { color: "#8899bb", fontSize: 13, background: "#0d1020", padding: "8px 12px", borderRadius: 6, borderLeft: "3px solid #446688" },
  blockedResponse: { color: "#00aa44", fontSize: 13, background: "#001a0a", padding: "8px 12px", borderRadius: 6, borderLeft: "3px solid #00cc66" },
  dangerResponse: { color: "#ff6644", fontSize: 13, background: "#1a0500", padding: "8px 12px", borderRadius: 6, borderLeft: "3px solid #ff8800", fontStyle: "italic" },
  cardFooter: { padding: "10px 16px", borderTop: "1px solid #111" },
};