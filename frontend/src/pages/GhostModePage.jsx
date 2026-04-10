import GhostChat from "../components/GhostChat";
import GhostAdminPanel from "../components/GhostAdminPanel";

export default function GhostModePage() {
  return (
    <div style={styles.page}>
      <div style={styles.banner}>
        <div style={styles.bannerTitle}>👻 GHOST MODE</div>
        <div style={styles.bannerSub}>AI Honeypot System — Trap & Track Malicious Users</div>
      </div>
      <div style={styles.grid}>
        <div style={styles.left}>
          <div style={styles.label}>HONEYPOT INTERFACE (seen by target)</div>
          <GhostChat username={"attacker_" + Math.floor(Math.random() * 99)} />
        </div>
        <div style={styles.right}>
          <GhostAdminPanel />
        </div>
      </div>
    </div>
  );
}

const styles = {
  page: { padding: 24, background: "#050509", minHeight: "100vh", fontFamily: "'Courier New', monospace" },
  banner: { marginBottom: 28, padding: "20px 28px", background: "linear-gradient(135deg, #0d0010, #1a0005)", border: "1px solid #ff003333", borderRadius: 12 },
  bannerTitle: { color: "#ff4466", fontSize: 28, fontWeight: "bold", letterSpacing: 4, textShadow: "0 0 30px #ff004488" },
  bannerSub: { color: "#884466", fontSize: 13, marginTop: 6, letterSpacing: 1 },
  grid: { display: "flex", gap: 24, flexWrap: "wrap" },
  left: { display: "flex", flexDirection: "column", gap: 10 },
  right: { flex: 1, minWidth: 600 },
  label: { color: "#ff003366", fontSize: 11, letterSpacing: 2, marginBottom: 6 },
};