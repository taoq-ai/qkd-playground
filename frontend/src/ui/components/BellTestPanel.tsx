import { useCallback, useState } from "react";
import type { BellTestCorrelation, BellTestResponse } from "../../adapters";
import { runBellTest } from "../../adapters";

const TSIRELSON = 2 * Math.sqrt(2);
const CLASSICAL_LIMIT = 2;

interface Preset {
  label: string;
  aliceAngles: [number, number];
  bobAngles: [number, number];
}

const PRESETS: Preset[] = [
  {
    label: "Maximum Violation",
    aliceAngles: [0, 45],
    bobAngles: [22.5, 67.5],
  },
  {
    label: "Classical (Aligned)",
    aliceAngles: [0, 0],
    bobAngles: [0, 0],
  },
  {
    label: "Zero Correlation",
    aliceAngles: [0, 0],
    bobAngles: [45, 45],
  },
];

function CorrelationCard({ corr }: { corr: BellTestCorrelation }) {
  const color = Math.abs(corr.correlation) > 0.5 ? "var(--accent)" : "var(--foreground-secondary)";
  return (
    <div className="bell-corr-card">
      <div className="bell-corr-angles">
        E({corr.alice_angle}&deg;, {corr.bob_angle}&deg;)
      </div>
      <div className="bell-corr-value" style={{ color }}>
        {corr.correlation.toFixed(3)}
      </div>
    </div>
  );
}

function SGauge({ sValue }: { sValue: number }) {
  // Scale: 0 to 3 (slightly beyond Tsirelson bound)
  const maxScale = 3.0;
  const absS = Math.abs(sValue);
  const pct = Math.min(absS / maxScale, 1) * 100;
  const classicalPct = (CLASSICAL_LIMIT / maxScale) * 100;
  const tsirelsonPct = (TSIRELSON / maxScale) * 100;
  const isQuantum = absS > CLASSICAL_LIMIT;

  return (
    <div className="bell-gauge">
      <div className="bell-gauge-labels">
        <span>0</span>
        <span>S = |{sValue.toFixed(3)}|</span>
        <span>{maxScale}</span>
      </div>
      <div className="bell-gauge-track">
        <div
          className="bell-gauge-marker bell-gauge-classical"
          style={{ left: `${classicalPct}%` }}
          title="Classical limit (S = 2)"
        />
        <div
          className="bell-gauge-marker bell-gauge-tsirelson"
          style={{ left: `${tsirelsonPct}%` }}
          title={`Tsirelson's bound (S = 2\u221A2)`}
        />
        <div
          className={`bell-gauge-fill ${isQuantum ? "bell-gauge-quantum" : "bell-gauge-classic"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="bell-gauge-legend">
        <span className="bell-legend-classical">Classical limit (S = 2)</span>
        <span className="bell-legend-tsirelson">Tsirelson (S = 2&radic;2)</span>
      </div>
    </div>
  );
}

export function BellTestPanel() {
  const [aliceA, setAliceA] = useState(0);
  const [aliceAPrime, setAliceAPrime] = useState(45);
  const [bobB, setBobB] = useState(22.5);
  const [bobBPrime, setBobBPrime] = useState(67.5);
  const [numTrials, setNumTrials] = useState(1000);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BellTestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRun = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runBellTest([aliceA, aliceAPrime], [bobB, bobBPrime], numTrials);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Bell test failed");
    } finally {
      setLoading(false);
    }
  }, [aliceA, aliceAPrime, bobB, bobBPrime, numTrials]);

  const applyPreset = useCallback((preset: Preset) => {
    setAliceA(preset.aliceAngles[0]);
    setAliceAPrime(preset.aliceAngles[1]);
    setBobB(preset.bobAngles[0]);
    setBobBPrime(preset.bobAngles[1]);
    setResult(null);
  }, []);

  const isQuantum = result !== null && Math.abs(result.s_value) > CLASSICAL_LIMIT;

  return (
    <div className="bell-test-panel">
      <h2>CHSH Bell Inequality Test</h2>
      <p className="bell-description">
        Explore Bell&apos;s theorem by choosing measurement angles for Alice and Bob. Entangled
        quantum particles can produce correlations (S &gt; 2) that are impossible classically.
      </p>

      <div className="bell-presets">
        {PRESETS.map((p) => (
          <button key={p.label} className="btn btn-secondary" onClick={() => applyPreset(p)}>
            {p.label}
          </button>
        ))}
      </div>

      <div className="bell-angles-grid">
        <div className="bell-angle-group">
          <h3>Alice&apos;s Angles</h3>
          <div className="form-group">
            <label htmlFor="alice-a">a (degrees)</label>
            <input
              id="alice-a"
              type="range"
              min={0}
              max={180}
              step={0.5}
              value={aliceA}
              onChange={(e) => setAliceA(Number(e.target.value))}
            />
            <span className="range-value">{aliceA}&deg;</span>
          </div>
          <div className="form-group">
            <label htmlFor="alice-a-prime">a&apos; (degrees)</label>
            <input
              id="alice-a-prime"
              type="range"
              min={0}
              max={180}
              step={0.5}
              value={aliceAPrime}
              onChange={(e) => setAliceAPrime(Number(e.target.value))}
            />
            <span className="range-value">{aliceAPrime}&deg;</span>
          </div>
        </div>
        <div className="bell-angle-group">
          <h3>Bob&apos;s Angles</h3>
          <div className="form-group">
            <label htmlFor="bob-b">b (degrees)</label>
            <input
              id="bob-b"
              type="range"
              min={0}
              max={180}
              step={0.5}
              value={bobB}
              onChange={(e) => setBobB(Number(e.target.value))}
            />
            <span className="range-value">{bobB}&deg;</span>
          </div>
          <div className="form-group">
            <label htmlFor="bob-b-prime">b&apos; (degrees)</label>
            <input
              id="bob-b-prime"
              type="range"
              min={0}
              max={180}
              step={0.5}
              value={bobBPrime}
              onChange={(e) => setBobBPrime(Number(e.target.value))}
            />
            <span className="range-value">{bobBPrime}&deg;</span>
          </div>
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="num-trials-bell">Trials per angle pair</label>
        <input
          id="num-trials-bell"
          type="range"
          min={100}
          max={5000}
          step={100}
          value={numTrials}
          onChange={(e) => setNumTrials(Number(e.target.value))}
        />
        <span className="range-value">{numTrials}</span>
      </div>

      <button className="btn btn-primary" onClick={handleRun} disabled={loading}>
        {loading ? "Running\u2026" : "Run Bell Test"}
      </button>

      {error && <div className="error-banner">{error}</div>}

      {result && (
        <div className="bell-results">
          <div className={`bell-s-display ${isQuantum ? "bell-s-quantum" : "bell-s-classical"}`}>
            <span className="bell-s-label">CHSH S value</span>
            <span className="bell-s-value">{result.s_value.toFixed(4)}</span>
            <span className="bell-s-verdict">
              {isQuantum
                ? "Quantum violation! S > 2 rules out local hidden variables."
                : "No violation. Correlations are within classical bounds (S \u2264 2)."}
            </span>
          </div>

          <SGauge sValue={result.s_value} />

          <h3>Correlations</h3>
          <div className="bell-corr-grid">
            {result.correlations.map((c, i) => (
              <CorrelationCard key={i} corr={c} />
            ))}
          </div>

          <div className="bell-formula">
            S = E(a,b) - E(a,b&apos;) + E(a&apos;,b) + E(a&apos;,b&apos;) = (
            {result.correlations[0].correlation.toFixed(3)}) - (
            {result.correlations[1].correlation.toFixed(3)}) + (
            {result.correlations[2].correlation.toFixed(3)}) + (
            {result.correlations[3].correlation.toFixed(3)}) ={" "}
            <strong>{result.s_value.toFixed(3)}</strong>
          </div>

          <div className="bell-info">
            <h4>What does this mean?</h4>
            <p>
              In 1964, John Bell showed that any local hidden variable theory must satisfy S &le; 2.
              Quantum mechanics predicts that entangled particles can reach S = 2&radic;2 &asymp;
              2.828 (Tsirelson&apos;s bound). When S &gt; 2, we have direct evidence that the
              correlations cannot be explained by any classical theory &mdash; the particles are
              genuinely entangled.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
