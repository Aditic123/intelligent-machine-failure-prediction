import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import {
  ContactShadows,
  Float,
  OrbitControls,
  Environment,
} from "@react-three/drei";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Bell,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  Clock3,
  Cpu,
  Download,
  Gauge,
  LayoutDashboard,
  Menu,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Thermometer,
  Wrench,
  X,
  Zap,
} from "lucide-react";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

const DEFAULT_FORM = {
  machine_id: "MCH-001",
  machine_type: "M",
  air_temperature: 300,
  process_temperature: 310,
  rotational_speed: 1500,
  torque: 40,
  tool_wear: 100,
};

const NAV_ITEMS = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "assessment", label: "Machine Assessment", icon: SlidersHorizontal },
  { id: "history", label: "Prediction History", icon: Clock3 },
  { id: "analytics", label: "Analytics", icon: Activity },
];

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return String(value);

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function probabilityValue(record) {
  const value =
    record?.failure_probability_percent ??
    record?.failure_probability ??
    0;

  const number = Number(value);

  if (!Number.isFinite(number)) return 0;

  return number <= 1 ? number * 100 : number;
}

function isFailure(record) {
  const value = record?.prediction ?? record?.status;

  if (typeof value === "number") return value === 1;

  const normalized = String(value ?? "").toLowerCase();

  return (
    normalized === "1" ||
    normalized.includes("failure") ||
    normalized.includes("risk")
  );
}

/* ---------------- 3D MACHINE MODEL ---------------- */

function MachineModel() {
  const rotor = useRef();

  useFrame((state, delta) => {
    if (rotor.current) {
      rotor.current.rotation.x += delta * 0.8;
    }
  });

  return (
    <group rotation={[0.12, -0.35, 0]}>
      {/* Main machine body */}
      <mesh castShadow receiveShadow position={[0, 0, 0]}>
        <cylinderGeometry args={[1.05, 1.05, 2.6, 64]} />
        <meshStandardMaterial
          color="#29242e"
          metalness={0.85}
          roughness={0.3}
        />
      </mesh>

      {/* Front ring */}
      <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 0, 1.33]}>
        <torusGeometry args={[0.92, 0.1, 16, 64]} />
        <meshStandardMaterial
          color="#ff65b5"
          metalness={0.7}
          roughness={0.22}
          emissive="#8c164f"
          emissiveIntensity={0.55}
        />
      </mesh>

      {/* Front cover */}
      <mesh position={[0, 0, 1.34]}>
        <cylinderGeometry args={[0.83, 0.83, 0.13, 64]} />
        <meshStandardMaterial
          color="#17131c"
          metalness={0.9}
          roughness={0.25}
        />
      </mesh>

      {/* Rotor */}
      <group ref={rotor} position={[0, 0, 1.47]}>
        <mesh>
          <cylinderGeometry args={[0.18, 0.18, 0.3, 32]} />
          <meshStandardMaterial
            color="#ff75c5"
            metalness={0.8}
            roughness={0.2}
          />
        </mesh>

        {[0, 1, 2, 3, 4, 5].map((item) => (
          <mesh
            key={item}
            rotation={[0, 0, (Math.PI / 3) * item]}
            position={[
              Math.cos((Math.PI / 3) * item) * 0.48,
              Math.sin((Math.PI / 3) * item) * 0.48,
              0,
            ]}
          >
            <boxGeometry args={[0.72, 0.12, 0.12]} />
            <meshStandardMaterial
              color="#e9dce8"
              metalness={0.75}
              roughness={0.3}
            />
          </mesh>
        ))}
      </group>

      {/* Back cover */}
      <mesh position={[0, 0, -1.36]}>
        <cylinderGeometry args={[0.9, 0.9, 0.2, 48]} />
        <meshStandardMaterial
          color="#413747"
          metalness={0.85}
          roughness={0.35}
        />
      </mesh>

      {/* Machine base */}
      <mesh position={[0, -1.25, 0]}>
        <boxGeometry args={[2.5, 0.18, 1.5]} />
        <meshStandardMaterial color="#29232e" metalness={0.8} />
      </mesh>

      {/* Feet */}
      {[-0.8, 0.8].map((x) => (
        <mesh key={x} position={[x, -1.48, 0]}>
          <boxGeometry args={[0.3, 0.3, 0.9]} />
          <meshStandardMaterial color="#62566a" metalness={0.8} />
        </mesh>
      ))}

      {/* Top sensor */}
      <mesh position={[0, 1.25, 0]}>
        <cylinderGeometry args={[0.17, 0.17, 0.42, 24]} />
        <meshStandardMaterial
          color="#ff68b8"
          emissive="#a51b64"
          emissiveIntensity={0.6}
        />
      </mesh>

      {/* Side details */}
      {[-0.6, 0, 0.6].map((y) => (
        <mesh key={y} position={[1.02, y, 0]}>
          <boxGeometry args={[0.1, 0.12, 0.8]} />
          <meshStandardMaterial color="#746a7a" metalness={0.8} />
        </mesh>
      ))}
    </group>
  );
}

function MachineScene() {
  return (
    <Canvas
      camera={{ position: [4, 2.6, 5.5], fov: 38 }}
      shadows
      dpr={[1, 2]}
    >
      <ambientLight intensity={1.1} />
      <directionalLight
        position={[4, 6, 5]}
        intensity={2}
        castShadow
      />
      <pointLight position={[-4, 1, 2]} color="#ff4fa8" intensity={30} />
      <pointLight position={[3, -1, -3]} color="#8b4cff" intensity={20} />

      <Float speed={1.1} rotationIntensity={0.08} floatIntensity={0.2}>
        <MachineModel />
      </Float>

      <ContactShadows
        position={[0, -1.65, 0]}
        opacity={0.45}
        scale={6}
        blur={2}
      />

      <Environment preset="city" />
      <OrbitControls
        enableZoom={false}
        minPolarAngle={Math.PI / 3}
        maxPolarAngle={Math.PI / 1.8}
      />
    </Canvas>
  );
}

/* ---------------- REUSABLE COMPONENTS ---------------- */

function SectionHeading({ eyebrow, title, description, action }) {
  return (
    <div className="section-heading">
      <div>
        {eyebrow && <p className="section-eyebrow">{eyebrow}</p>}
        <h2>{title}</h2>
        {description && <p className="section-description">{description}</p>}
      </div>
      {action}
    </div>
  );
}

function MetricCard({ icon: Icon, label, value, unit, note, trend }) {
  return (
    <motion.div
      className="metric-card glass-panel"
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
    >
      <div className="metric-top">
        <div className="metric-icon">
          <Icon size={19} />
        </div>
        {trend && (
          <span className="metric-trend">
            <ArrowUpRight size={14} />
            {trend}
          </span>
        )}
      </div>

      <p className="metric-label">{label}</p>

      <div className="metric-value">
        {value}
        <span>{unit}</span>
      </div>

      <p className="metric-note">{note}</p>
    </motion.div>
  );
}

function StatusBadge({ failure }) {
  return (
    <span className={`status-badge ${failure ? "status-danger" : "status-safe"}`}>
      {failure ? <AlertTriangle size={13} /> : <CheckCircle2 size={13} />}
      {failure ? "Failure Risk" : "Normal"}
    </span>
  );
}

function EmptyState({ icon: Icon = Activity, title, description }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">
        <Icon size={25} />
      </div>
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;

  return (
    <div className="chart-tooltip">
      <p>{label}</p>
      <strong>{payload[0].value}%</strong>
    </div>
  );
}

/* ---------------- MAIN APPLICATION ---------------- */

export default function App() {
  const [activePage, setActivePage] = useState("overview");
  const [history, setHistory] = useState([]);
  const [backendOnline, setBackendOnline] = useState(false);
  const [modelStatus, setModelStatus] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [formData, setFormData] = useState(DEFAULT_FORM);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [mobileMenu, setMobileMenu] = useState(false);

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/model-status`);

      if (!response.ok) {
        throw new Error("Backend status request failed");
      }

      const data = await response.json();

      setModelStatus(data);
      setBackendOnline(true);
    } catch {
      setBackendOnline(false);
      setModelStatus(null);
    }
  };

  const fetchHistory = async () => {
    setHistoryLoading(true);

    try {
      const response = await fetch(`${API_BASE}/history?limit=100`);

      if (!response.ok) {
        throw new Error("Unable to fetch prediction history");
      }

      const data = await response.json();

      const records = Array.isArray(data)
        ? data
        : data.history || data.predictions || data.records || [];

      setHistory(records);
      setBackendOnline(true);
    } catch {
      setHistory([]);
      setBackendOnline(false);
    } finally {
      setHistoryLoading(false);
    }
  };

  const refreshData = async () => {
    await Promise.all([fetchStatus(), fetchHistory()]);
  };

  useEffect(() => {
    refreshData();
  }, []);

  const totalPredictions = history.length;
  const failureCount = history.filter(isFailure).length;
  const normalCount = totalPredictions - failureCount;

  const averageRisk =
    totalPredictions > 0
      ? history.reduce((sum, item) => sum + probabilityValue(item), 0) /
        totalPredictions
      : 0;

  const latestRecord = history[0] || null;

  const chartHistory = useMemo(() => {
    return [...history]
      .slice(0, 12)
      .reverse()
      .map((item, index) => ({
        name: `#${index + 1}`,
        probability: Number(probabilityValue(item).toFixed(1)),
      }));
  }, [history]);

  const distributionData = [
    { name: "Normal", value: normalCount, color: "#ff70ba" },
    { name: "Failure", value: failureCount, color: "#8b5cf6" },
  ];

  const machineTypeData = ["L", "M", "H"].map((type) => {
    const records = history.filter(
      (item) => item.machine_type === type
    );

    return {
      type: `Type ${type}`,
      normal: records.filter((item) => !isFailure(item)).length,
      failure: records.filter(isFailure).length,
    };
  });

  const filteredHistory = history.filter((item) => {
    const matchesSearch =
      String(item.machine_id || "")
        .toLowerCase()
        .includes(search.toLowerCase()) ||
      String(item.machine_type || "")
        .toLowerCase()
        .includes(search.toLowerCase());

    const matchesFilter =
      filter === "all" ||
      (filter === "failure" && isFailure(item)) ||
      (filter === "normal" && !isFailure(item));

    return matchesSearch && matchesFilter;
  });

  const updateForm = (key, value) => {
    setFormData((previous) => ({
      ...previous,
      [key]: value,
    }));
  };

  const handlePrediction = async (event) => {
    event.preventDefault();
    setError("");
    setResult(null);

    if (
      Number(formData.process_temperature) <
      Number(formData.air_temperature)
    ) {
      setError(
        "Process temperature cannot be lower than air temperature."
      );
      return;
    }

    setSubmitting(true);

    try {
      const payload = {
        machine_id: formData.machine_id,
        machine_type: formData.machine_type,
        air_temperature: Number(formData.air_temperature),
        process_temperature: Number(formData.process_temperature),
        rotational_speed: Number(formData.rotational_speed),
        torque: Number(formData.torque),
        tool_wear: Number(formData.tool_wear),
      };

      const response = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || data.message || "Prediction request failed."
        );
      }

      setResult(data);
      await fetchHistory();
    } catch (err) {
      setError(
        err.message ||
          "Unable to connect to the prediction server."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const exportHistory = () => {
    if (!history.length) return;

    const columns = [
      "id",
      "machine_id",
      "timestamp",
      "machine_type",
      "air_temperature",
      "process_temperature",
      "rotational_speed",
      "torque",
      "tool_wear",
      "prediction",
      "failure_probability",
    ];

    const rows = history.map((record) =>
      columns
        .map((column) => {
          const value = String(record[column] ?? "");
          return `"${value.replaceAll('"', '""')}"`;
        })
        .join(",")
    );

    const csv = [columns.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = "machine_prediction_history.csv";
    link.click();

    URL.revokeObjectURL(url);
  };

  const pageTitle =
    NAV_ITEMS.find((item) => item.id === activePage)?.label || "Overview";

  const goTo = (page) => {
    setActivePage(page);
    setMobileMenu(false);
  };

  return (
    <div className="quanta-app">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <div className="ambient ambient-three" />

      {/* SIDEBAR */}

      <AnimatePresence>
        {mobileMenu && (
          <motion.div
            className="mobile-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setMobileMenu(false)}
          />
        )}
      </AnimatePresence>

      <aside className={`sidebar ${mobileMenu ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-symbol">
            <Cpu size={22} />
          </div>
          <div>
            <h1>INDUSTRIA<span> AI</span></h1>
            <p>MACHINE INTELLIGENCE</p>
          </div>

          <button
            className="mobile-close"
            onClick={() => setMobileMenu(false)}
          >
            <X size={19} />
          </button>
        </div>

        <div className="workspace-label">WORKSPACE</div>

        <nav className="navigation">
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              className={`nav-item ${activePage === id ? "active" : ""}`}
              onClick={() => goTo(id)}
            >
              <Icon size={19} />
              <span>{label}</span>
              {activePage === id && <ChevronRight size={15} />}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="system-status glass-panel">
            <div className="system-status-heading">
              <span className={`status-dot ${backendOnline ? "online" : ""}`} />
              SYSTEM STATUS
            </div>

            <h3>{backendOnline ? "System Connected" : "Server Offline"}</h3>
            <p>
              {backendOnline
                ? "Prediction API is reachable"
                : "Start the backend server to continue"}
            </p>
          </div>

          <div className="profile">
            <div className="profile-avatar">IA</div>
            <div className="profile-info">
              <strong>Machine Intelligence</strong>
              <span>AI Monitoring System</span>
            </div>
            <Settings size={17} className="profile-settings" />
          </div>
        </div>
      </aside>

      {/* MAIN AREA */}

      <main className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="mobile-menu-button"
              onClick={() => setMobileMenu(true)}
            >
              <Menu size={21} />
            </button>

            <div className="breadcrumb">
              <span>Workspace</span>
              <ChevronRight size={15} />
              <strong>{pageTitle}</strong>
            </div>
          </div>

          <div className="topbar-actions">
            <div className="live-indicator">
              <span className={`status-dot ${backendOnline ? "online" : ""}`} />
              {backendOnline ? "API CONNECTED" : "API OFFLINE"}
            </div>

            <button
              className="icon-button"
              onClick={refreshData}
              title="Refresh data"
            >
              <RefreshCw size={17} />
            </button>

            <button className="icon-button notification-button" title="Notifications">
              <Bell size={18} />
              <span />
            </button>

            <div className="top-avatar">AI</div>
          </div>
        </header>

        <div className="dashboard-content">
          <AnimatePresence mode="wait">
            {activePage === "overview" && (
              <motion.div
                key="overview"
                className="page-content"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
              >
                <SectionHeading
                  eyebrow="INTELLIGENT MACHINE MONITORING"
                  title="Machine Overview"
                  description="A centralized view of your machine health and predictive maintenance insights."
                  action={
                    <button
                      className="primary-button"
                      onClick={() => goTo("assessment")}
                    >
                      <Zap size={17} />
                      New Assessment
                    </button>
                  }
                />

                <div className="overview-grid">
                  {/* 3D MACHINE */}

                  <section className="machine-card glass-panel">
                    <div className="card-heading">
                      <div>
                        <p className="card-kicker">LIVE MACHINE MODEL</p>
                        <h3>Industrial Motor</h3>
                      </div>

                      <span className="machine-tag">
                        <span className="status-dot online" />
                        3D VIEW
                      </span>
                    </div>

                    <div className="machine-scene">
                      <div className="scene-glow" />
                      <MachineScene />

                      <div className="scene-label scene-label-left">
                        <span>MODEL</span>
                        <strong>AI4I 2020</strong>
                      </div>

                      <div className="scene-label scene-label-right">
                        <span>ROTATION</span>
                        <strong>360° VIEW</strong>
                      </div>
                    </div>

                    <div className="machine-footer">
                      <div>
                        <span className="footer-label">LATEST MACHINE ID</span>
                        <strong>{latestRecord?.machine_id || "MCH-001"}</strong>
                      </div>

                      <div>
                        <span className="footer-label">LAST ASSESSMENT</span>
                        <strong>
                          {latestRecord
                            ? formatDate(latestRecord.timestamp)
                            : "No assessment yet"}
                        </strong>
                      </div>

                      <button
                        className="text-button"
                        onClick={() => goTo("assessment")}
                      >
                        Assess <ChevronRight size={15} />
                      </button>
                    </div>
                  </section>

                  {/* HEALTH CARD */}

                  <section className="health-card glass-panel">
                    <div className="card-heading">
                      <div>
                        <p className="card-kicker">MACHINE CONDITION</p>
                        <h3>Health Snapshot</h3>
                      </div>
                      <ShieldCheck size={21} className="pink-icon" />
                    </div>

                    <div className="health-score">
                      <div className="score-ring">
                        <div className="score-inner">
                          <span>
                            {latestRecord
                              ? Math.max(
                                  0,
                                  Math.round(100 - probabilityValue(latestRecord))
                                )
                              : "—"}
                          </span>
                          <small>/ 100</small>
                        </div>
                      </div>

                      <div className="score-caption">
                        <strong>
                          {latestRecord
                            ? isFailure(latestRecord)
                              ? "Attention Required"
                              : "Normal Condition"
                            : "Awaiting Data"}
                        </strong>
                        <span>
                          {latestRecord
                            ? "Based on latest prediction"
                            : "Run an assessment to view health"}
                        </span>
                      </div>
                    </div>

                    <div className="health-divider" />

                    <div className="status-row">
                      <div className="status-row-icon">
                        <Activity size={17} />
                      </div>
                      <div className="status-row-text">
                        <strong>Prediction Records</strong>
                        <span>Stored assessments</span>
                      </div>
                      <strong>{totalPredictions}</strong>
                    </div>

                    <div className="status-row">
                      <div className="status-row-icon">
                        <CheckCircle2 size={17} />
                      </div>
                      <div className="status-row-text">
                        <strong>Normal Predictions</strong>
                        <span>Classified as normal</span>
                      </div>
                      <strong>{normalCount}</strong>
                    </div>

                    <div className="status-row">
                      <div className="status-row-icon warning-icon">
                        <AlertTriangle size={17} />
                      </div>
                      <div className="status-row-text">
                        <strong>Failure Predictions</strong>
                        <span>Classified as failure</span>
                      </div>
                      <strong>{failureCount}</strong>
                    </div>

                    <button
                      className="secondary-button full-button"
                      onClick={() => goTo("history")}
                    >
                      View All Records <ChevronRight size={16} />
                    </button>
                  </section>
                </div>

                {/* METRICS */}

                <div className="metrics-heading">
                  <div>
                    <p className="card-kicker">PERFORMANCE MONITORING</p>
                    <h3>System Metrics</h3>
                  </div>
                  <span className="sample-label">Based on stored predictions</span>
                </div>

                <div className="metrics-grid">
                  <MetricCard
                    icon={Activity}
                    label="Total Assessments"
                    value={totalPredictions}
                    unit=""
                    note="Total stored records"
                  />

                  <MetricCard
                    icon={CheckCircle2}
                    label="Normal Results"
                    value={normalCount}
                    unit=""
                    note="Normal classifications"
                  />

                  <MetricCard
                    icon={AlertTriangle}
                    label="Failure Results"
                    value={failureCount}
                    unit=""
                    note="Failure classifications"
                  />

                  <MetricCard
                    icon={Gauge}
                    label="Average Failure Probability"
                    value={averageRisk.toFixed(1)}
                    unit="%"
                    note="Average across stored records"
                  />
                </div>

                {/* OVERVIEW CHARTS */}

                <div className="charts-grid overview-charts">
                  <section className="chart-panel glass-panel">
                    <div className="card-heading">
                      <div>
                        <p className="card-kicker">PREDICTION TREND</p>
                        <h3>Failure Probability</h3>
                      </div>
                      <span className="chart-period">Latest 12 records</span>
                    </div>

                    {chartHistory.length ? (
                      <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={chartHistory}>
                            <defs>
                              <linearGradient
                                id="riskGradient"
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="1"
                              >
                                <stop
                                  offset="0%"
                                  stopColor="#ff64b5"
                                  stopOpacity={0.35}
                                />
                                <stop
                                  offset="100%"
                                  stopColor="#ff64b5"
                                  stopOpacity={0}
                                />
                              </linearGradient>
                            </defs>

                            <CartesianGrid
                              stroke="#ffffff10"
                              vertical={false}
                            />

                            <XAxis
                              dataKey="name"
                              stroke="#82798a"
                              tickLine={false}
                              axisLine={false}
                            />

                            <YAxis
                              domain={[0, 100]}
                              stroke="#82798a"
                              tickLine={false}
                              axisLine={false}
                            />

                            <Tooltip content={<ChartTooltip />} />

                            <Area
                              type="monotone"
                              dataKey="probability"
                              stroke="#ff70ba"
                              strokeWidth={2.5}
                              fill="url(#riskGradient)"
                              activeDot={{ r: 5 }}
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    ) : (
                      <EmptyState
                        title="No prediction data yet"
                        description="Complete your first machine assessment to generate the trend chart."
                      />
                    )}
                  </section>

                  <section className="chart-panel glass-panel">
                    <div className="card-heading">
                      <div>
                        <p className="card-kicker">CLASSIFICATION</p>
                        <h3>Prediction Distribution</h3>
                      </div>
                    </div>

                    {totalPredictions ? (
                      <>
                        <div className="donut-container">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie
                                data={distributionData}
                                dataKey="value"
                                nameKey="name"
                                innerRadius={65}
                                outerRadius={92}
                                paddingAngle={5}
                                stroke="none"
                              >
                                {distributionData.map((entry) => (
                                  <Cell
                                    key={entry.name}
                                    fill={entry.color}
                                  />
                                ))}
                              </Pie>
                              <Tooltip />
                            </PieChart>
                          </ResponsiveContainer>

                          <div className="donut-center">
                            <strong>{totalPredictions}</strong>
                            <span>Records</span>
                          </div>
                        </div>

                        <div className="chart-legend">
                          <span>
                            <i className="legend-pink" />
                            Normal <strong>{normalCount}</strong>
                          </span>
                          <span>
                            <i className="legend-purple" />
                            Failure <strong>{failureCount}</strong>
                          </span>
                        </div>
                      </>
                    ) : (
                      <EmptyState
                        title="No records available"
                        description="The distribution will appear after predictions are saved."
                      />
                    )}
                  </section>
                </div>

                <div className="dashboard-footer">
                  <span>INDUSTRIA AI · PREDICTIVE MAINTENANCE SYSTEM</span>
                  <span>Model: Random Forest Classifier</span>
                </div>
              </motion.div>
            )}

            {/* ASSESSMENT PAGE */}

            {activePage === "assessment" && (
              <motion.div
                key="assessment"
                className="page-content"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
              >
                <SectionHeading
                  eyebrow="PREDICTIVE MAINTENANCE"
                  title="Machine Assessment"
                  description="Enter the machine operating parameters to evaluate its failure risk."
                />

                <div className="assessment-layout">
                  <section className="page-panel glass-panel">
                    <div className="panel-title">
                      <div className="panel-title-icon">
                        <SlidersHorizontal size={20} />
                      </div>
                      <div>
                        <h3>Operating Parameters</h3>
                        <p>Provide the current machine readings</p>
                      </div>
                    </div>

                    <form
                      className="assessment-form"
                      onSubmit={handlePrediction}
                    >
                      <div className="form-group full-width">
                        <label>Machine ID</label>
                        <input
                          type="text"
                          value={formData.machine_id}
                          onChange={(event) =>
                            updateForm("machine_id", event.target.value)
                          }
                          placeholder="Enter machine ID"
                          required
                        />
                      </div>

                      <div className="form-group full-width">
                        <label>Machine Type</label>
                        <div className="machine-type-options">
                          {["L", "M", "H"].map((type) => (
                            <button
                              type="button"
                              key={type}
                              className={
                                formData.machine_type === type
                                  ? "type-option selected"
                                  : "type-option"
                              }
                              onClick={() => updateForm("machine_type", type)}
                            >
                              <span>Type {type}</span>
                              <small>
                                {type === "L"
                                  ? "Low"
                                  : type === "M"
                                    ? "Medium"
                                    : "High"}
                              </small>
                            </button>
                          ))}
                        </div>
                      </div>

                      <div className="form-group">
                        <label>
                          <Thermometer size={15} />
                          Air Temperature
                        </label>
                        <div className="input-with-unit">
                          <input
                            type="number"
                            min="250"
                            max="350"
                            step="0.1"
                            value={formData.air_temperature}
                            onChange={(event) =>
                              updateForm("air_temperature", event.target.value)
                            }
                            required
                          />
                          <span>K</span>
                        </div>
                        <small>Range: 250–350 K</small>
                      </div>

                      <div className="form-group">
                        <label>
                          <Thermometer size={15} />
                          Process Temperature
                        </label>
                        <div className="input-with-unit">
                          <input
                            type="number"
                            min="250"
                            max="400"
                            step="0.1"
                            value={formData.process_temperature}
                            onChange={(event) =>
                              updateForm(
                                "process_temperature",
                                event.target.value
                              )
                            }
                            required
                          />
                          <span>K</span>
                        </div>
                        <small>Range: 250–400 K</small>
                      </div>

                      <div className="form-group">
                        <label>
                          <Zap size={15} />
                          Rotational Speed
                        </label>
                        <div className="input-with-unit">
                          <input
                            type="number"
                            min="500"
                            max="3000"
                            step="1"
                            value={formData.rotational_speed}
                            onChange={(event) =>
                              updateForm("rotational_speed", event.target.value)
                            }
                            required
                          />
                          <span>RPM</span>
                        </div>
                        <small>Range: 500–3000 RPM</small>
                      </div>

                      <div className="form-group">
                        <label>
                          <Gauge size={15} />
                          Torque
                        </label>
                        <div className="input-with-unit">
                          <input
                            type="number"
                            min="1"
                            max="100"
                            step="0.1"
                            value={formData.torque}
                            onChange={(event) =>
                              updateForm("torque", event.target.value)
                            }
                            required
                          />
                          <span>Nm</span>
                        </div>
                        <small>Range: 1–100 Nm</small>
                      </div>

                      <div className="form-group full-width">
                        <label>
                          <Wrench size={15} />
                          Tool Wear
                        </label>
                        <div className="input-with-unit">
                          <input
                            type="number"
                            min="0"
                            max="300"
                            step="1"
                            value={formData.tool_wear}
                            onChange={(event) =>
                              updateForm("tool_wear", event.target.value)
                            }
                            required
                          />
                          <span>Minutes</span>
                        </div>
                        <small>Range: 0–300 minutes</small>
                      </div>

                      {error && (
                        <div className="message-box error-message">
                          <AlertTriangle size={17} />
                          {error}
                        </div>
                      )}

                      <button
                        className="primary-button form-submit"
                        type="submit"
                        disabled={submitting || !backendOnline}
                      >
                        {submitting ? (
                          <>
                            <RefreshCw className="spin-icon" size={17} />
                            Analysing Machine...
                          </>
                        ) : (
                          <>
                            <Zap size={17} />
                            Run AI Assessment
                          </>
                        )}
                      </button>

                      {!backendOnline && (
                        <p className="server-warning">
                          Backend is offline. Start your FastAPI server first.
                        </p>
                      )}
                    </form>
                  </section>

                  {/* RESULT PANEL */}

                  <section className="result-column">
                    <div className="result-info-card glass-panel">
                      <div className="result-info-icon">
                        <Cpu size={22} />
                      </div>
                      <p className="card-kicker">AI PREDICTION ENGINE</p>
                      <h3>Random Forest Classifier</h3>
                      <p>
                        The model evaluates six machine parameters and
                        predicts whether the current operating condition
                        indicates a normal state or potential failure.
                      </p>

                      <div className="model-detail">
                        <span>Model Type</span>
                        <strong>Random Forest</strong>
                      </div>
                      <div className="model-detail">
                        <span>Input Features</span>
                        <strong>6 Parameters</strong>
                      </div>
                      <div className="model-detail">
                        <span>Dataset</span>
                        <strong>AI4I 2020</strong>
                      </div>
                    </div>

                    <div className="prediction-result glass-panel">
                      <div className="card-heading">
                        <div>
                          <p className="card-kicker">ASSESSMENT OUTPUT</p>
                          <h3>Prediction Result</h3>
                        </div>
                        <Activity size={20} className="pink-icon" />
                      </div>

                      {result ? (
                        <div className="result-content">
                          <div
                            className={`result-status ${
                              isFailure(result) ||
                              String(result.status || "")
                                .toLowerCase()
                                .includes("failure")
                                ? "result-failure"
                                : "result-normal"
                            }`}
                          >
                            {isFailure(result) ? (
                              <AlertTriangle size={27} />
                            ) : (
                              <CheckCircle2 size={27} />
                            )}

                            <div>
                              <span>MODEL CLASSIFICATION</span>
                              <h2>
                                {isFailure(result)
                                  ? "Failure Risk Detected"
                                  : "Normal Condition"}
                              </h2>
                            </div>
                          </div>

                          <div className="result-probability">
                            <span>Failure Probability</span>
                            <strong>
                              {Number(
                                result.failure_probability_percent ??
                                  probabilityValue(result)
                              ).toFixed(2)}
                              %
                            </strong>
                          </div>

                          <div className="probability-track">
                            <div
                              className="probability-fill"
                              style={{
                                width: `${Math.min(
                                  100,
                                  probabilityValue(result)
                                )}%`,
                              }}
                            />
                          </div>

                          <div className="result-grid">
                            <div>
                              <span>Machine ID</span>
                              <strong>
                                {result.machine_id || formData.machine_id}
                              </strong>
                            </div>
                            <div>
                              <span>Prediction Time</span>
                              <strong>
                                {formatDate(result.timestamp)}
                              </strong>
                            </div>
                          </div>

                          <p className="result-note">
                            This output is a model prediction based on the
                            supplied parameters. It is not a substitute for
                            physical machine inspection.
                          </p>

                          <button
                            className="secondary-button full-button"
                            onClick={() => goTo("history")}
                          >
                            View Prediction History
                            <ChevronRight size={16} />
                          </button>
                        </div>
                      ) : (
                        <EmptyState
                          icon={Gauge}
                          title="Ready for Assessment"
                          description="Submit the operating parameters to view the model's prediction and failure probability."
                        />
                      )}
                    </div>
                  </section>
                </div>
              </motion.div>
            )}

            {/* HISTORY PAGE */}

            {activePage === "history" && (
              <motion.div
                key="history"
                className="page-content"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
              >
                <SectionHeading
                  eyebrow="RECORD MANAGEMENT"
                  title="Prediction History"
                  description="Review and filter the machine assessments stored in your database."
                  action={
                    <button
                      className="secondary-button"
                      onClick={exportHistory}
                      disabled={!history.length}
                    >
                      <Download size={16} />
                      Export CSV
                    </button>
                  }
                />

                <div className="history-summary">
                  <div className="history-summary-card glass-panel">
                    <span>Total Records</span>
                    <strong>{totalPredictions}</strong>
                  </div>
                  <div className="history-summary-card glass-panel">
                    <span>Normal</span>
                    <strong className="pink-text">{normalCount}</strong>
                  </div>
                  <div className="history-summary-card glass-panel">
                    <span>Failure</span>
                    <strong className="purple-text">{failureCount}</strong>
                  </div>
                </div>

                <section className="history-panel glass-panel">
                  <div className="history-toolbar">
                    <div>
                      <h3>All Assessments</h3>
                      <p>{filteredHistory.length} records found</p>
                    </div>

                    <div className="history-controls">
                      <div className="search-box">
                        <Search size={16} />
                        <input
                          type="text"
                          placeholder="Search machine ID..."
                          value={search}
                          onChange={(event) => setSearch(event.target.value)}
                        />
                      </div>

                      <select
                        value={filter}
                        onChange={(event) => setFilter(event.target.value)}
                      >
                        <option value="all">All Results</option>
                        <option value="normal">Normal</option>
                        <option value="failure">Failure</option>
                      </select>

                      <button
                        className="icon-button"
                        onClick={fetchHistory}
                        title="Refresh history"
                      >
                        <RefreshCw size={17} />
                      </button>
                    </div>
                  </div>

                  {historyLoading ? (
                    <EmptyState
                      icon={RefreshCw}
                      title="Loading records"
                      description="Fetching prediction history from the database."
                    />
                  ) : filteredHistory.length ? (
                    <div className="table-wrapper">
                      <table className="history-table">
                        <thead>
                          <tr>
                            <th>Machine ID</th>
                            <th>Date & Time</th>
                            <th>Type</th>
                            <th>Air Temp.</th>
                            <th>Process Temp.</th>
                            <th>Speed</th>
                            <th>Torque</th>
                            <th>Tool Wear</th>
                            <th>Probability</th>
                            <th>Result</th>
                          </tr>
                        </thead>

                        <tbody>
                          {filteredHistory.map((record, index) => (
                            <tr key={record.id ?? index}>
                              <td>
                                <strong className="machine-id-cell">
                                  {record.machine_id || "—"}
                                </strong>
                              </td>
                              <td>{formatDate(record.timestamp)}</td>
                              <td>{record.machine_type || "—"}</td>
                              <td>{record.air_temperature ?? "—"} K</td>
                              <td>{record.process_temperature ?? "—"} K</td>
                              <td>{record.rotational_speed ?? "—"}</td>
                              <td>{record.torque ?? "—"} Nm</td>
                              <td>{record.tool_wear ?? "—"}</td>
                              <td>
                                {probabilityValue(record).toFixed(2)}%
                              </td>
                              <td>
                                <StatusBadge failure={isFailure(record)} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <EmptyState
                      icon={Search}
                      title="No matching records"
                      description="No records match your current search or filter."
                    />
                  )}
                </section>
              </motion.div>
            )}

            {/* ANALYTICS PAGE */}

            {activePage === "analytics" && (
              <motion.div
                key="analytics"
                className="page-content"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
              >
                <SectionHeading
                  eyebrow="DATA INSIGHTS"
                  title="Machine Analytics"
                  description="Explore prediction patterns and machine classification trends from saved assessment records."
                  action={
                    <button className="secondary-button" onClick={fetchHistory}>
                      <RefreshCw size={16} />
                      Refresh Analytics
                    </button>
                  }
                />

                <div className="analytics-metrics">
                  <MetricCard
                    icon={Activity}
                    label="Total Predictions"
                    value={totalPredictions}
                    note="All saved assessments"
                  />
                  <MetricCard
                    icon={CheckCircle2}
                    label="Normal Results"
                    value={normalCount}
                    note="Normal classifications"
                  />
                  <MetricCard
                    icon={AlertTriangle}
                    label="Failure Results"
                    value={failureCount}
                    note="Failure classifications"
                  />
                  <MetricCard
                    icon={Gauge}
                    label="Average Risk"
                    value={averageRisk.toFixed(1)}
                    unit="%"
                    note="Mean failure probability"
                  />
                </div>

                <div className="analytics-charts">
                  <section className="chart-panel glass-panel">
                    <div className="card-heading">
                      <div>
                        <p className="card-kicker">MACHINE DISTRIBUTION</p>
                        <h3>Results by Machine Type</h3>
                      </div>
                    </div>

                    {totalPredictions ? (
                      <div className="chart-container large-chart">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart
                            data={machineTypeData}
                            barGap={10}
                          >
                            <CartesianGrid
                              stroke="#ffffff10"
                              vertical={false}
                            />
                            <XAxis
                              dataKey="type"
                              stroke="#8a8291"
                              axisLine={false}
                              tickLine={false}
                            />
                            <YAxis
                              allowDecimals={false}
                              stroke="#8a8291"
                              axisLine={false}
                              tickLine={false}
                            />
                            <Tooltip
                              contentStyle={{
                                background: "#17121d",
                                border: "1px solid #ffffff20",
                                borderRadius: "12px",
                                color: "#fff",
                              }}
                            />
                            <Bar
                              dataKey="normal"
                              name="Normal"
                              fill="#ff70ba"
                              radius={[6, 6, 0, 0]}
                            />
                            <Bar
                              dataKey="failure"
                              name="Failure"
                              fill="#8b5cf6"
                              radius={[6, 6, 0, 0]}
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    ) : (
                      <EmptyState
                        title="No machine data"
                        description="Machine type comparison will appear after assessments."
                      />
                    )}
                  </section>

                  <section className="chart-panel glass-panel">
                    <div className="card-heading">
                      <div>
                        <p className="card-kicker">CLASSIFICATION SHARE</p>
                        <h3>Normal vs Failure</h3>
                      </div>
                    </div>

                    {totalPredictions ? (
                      <>
                        <div className="donut-container analytics-donut">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie
                                data={distributionData}
                                dataKey="value"
                                nameKey="name"
                                innerRadius={68}
                                outerRadius={100}
                                paddingAngle={5}
                                stroke="none"
                              >
                                {distributionData.map((entry) => (
                                  <Cell
                                    key={entry.name}
                                    fill={entry.color}
                                  />
                                ))}
                              </Pie>
                              <Tooltip />
                            </PieChart>
                          </ResponsiveContainer>

                          <div className="donut-center">
                            <strong>{totalPredictions}</strong>
                            <span>Total</span>
                          </div>
                        </div>

                        <div className="chart-legend">
                          <span>
                            <i className="legend-pink" />
                            Normal <strong>{normalCount}</strong>
                          </span>
                          <span>
                            <i className="legend-purple" />
                            Failure <strong>{failureCount}</strong>
                          </span>
                        </div>
                      </>
                    ) : (
                      <EmptyState
                        title="No classification data"
                        description="Run a prediction to generate the distribution."
                      />
                    )}
                  </section>

                  <section className="chart-panel glass-panel full-chart">
                    <div className="card-heading">
                      <div>
                        <p className="card-kicker">RISK ANALYSIS</p>
                        <h3>Failure Probability Trend</h3>
                      </div>
                      <span className="chart-period">Latest 12 records</span>
                    </div>

                    {chartHistory.length ? (
                      <div className="chart-container large-chart">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={chartHistory}>
                            <defs>
                              <linearGradient
                                id="analyticsGradient"
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="1"
                              >
                                <stop
                                  offset="0%"
                                  stopColor="#a56aff"
                                  stopOpacity={0.4}
                                />
                                <stop
                                  offset="100%"
                                  stopColor="#a56aff"
                                  stopOpacity={0}
                                />
                              </linearGradient>
                            </defs>
                            <CartesianGrid
                              stroke="#ffffff10"
                              vertical={false}
                            />
                            <XAxis
                              dataKey="name"
                              stroke="#8a8291"
                              axisLine={false}
                              tickLine={false}
                            />
                            <YAxis
                              domain={[0, 100]}
                              stroke="#8a8291"
                              axisLine={false}
                              tickLine={false}
                            />
                            <Tooltip content={<ChartTooltip />} />
                            <Area
                              type="monotone"
                              dataKey="probability"
                              stroke="#b58aff"
                              strokeWidth={2.5}
                              fill="url(#analyticsGradient)"
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    ) : (
                      <EmptyState
                        title="No trend data available"
                        description="Your probability trend will appear here after predictions."
                      />
                    )}
                  </section>
                </div>

                <div className="analytics-note glass-panel">
                  <CircleHelp size={19} />
                  <p>
                    Analytics are calculated from the prediction records
                    currently stored in your database. Empty charts indicate
                    that no corresponding assessment data is available yet.
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}