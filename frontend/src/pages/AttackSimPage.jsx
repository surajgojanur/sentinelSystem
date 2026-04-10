import AttackSimulator from "../components/AttackSimulator";

export default function AttackSimPage() {
  return (
    <div style={{ padding: 24, background: "#050509", minHeight: "100vh" }}>
      <div style={styles.banner}>
        <div style={styles.title}>🪤 SECURITY TESTING LAB</div>
        <div style={styles.sub}>Honeypot Attack Simulation Environment — Authorized Testing Only</div>
        <div style={styles.pill}>CONTROLLED ENVIRONMENT</div>
      </div>
      <AttackSimulator />
    </div>
  );
}

const styles = {
  banner: { marginBottom: 28, padding: "20px 28px", background: "linear-gradient(135deg, #040010, #0a0520)", border: "1px solid #aa00ff33", borderRadius: 12, fontFamily: "'Courier New', monospace" },
  title: { color: "#cc44ff", fontSize: 26, fontWeight: "bold", letterSpacing: 3, textShadow: "0 0 20px #aa00ff66" },
  sub: { color: "#664488", fontSize: 13, marginTop: 6 },
  pill: { display: "inline-block", marginTop: 10, background: "#aa00ff22", color: "#aa44ff", border: "1px solid #aa00ff44", borderRadius: 20, padding: "3px 14px", fontSize: 11, letterSpacing: 2 },
};