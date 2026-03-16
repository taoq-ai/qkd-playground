interface EveAlertProps {
  errorRate: number | null;
  eavesdropperDetected: boolean | null;
  protocol: string;
}

const THRESHOLDS: Record<string, number> = {
  bb84: 0.11,
  b92: 0.15,
  e91: 0.11,
};

export function EveAlert({ errorRate, eavesdropperDetected, protocol }: EveAlertProps) {
  if (errorRate === null || eavesdropperDetected === null) return null;

  const threshold = THRESHOLDS[protocol] ?? 0.11;
  const thresholdPct = (threshold * 100).toFixed(0);
  const ratePct = (errorRate * 100).toFixed(1);

  if (eavesdropperDetected) {
    return (
      <div className="eve-alert eve-alert-danger">
        <span className="eve-alert-icon">{"\u26a0\ufe0f"}</span>
        <div>
          <strong>Eavesdropping Detected!</strong>
          <p>
            Error rate {ratePct}% exceeds the {thresholdPct}% threshold. The shared key has been
            discarded to maintain security.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="eve-alert eve-alert-safe">
      <span className="eve-alert-icon">{"\u2705"}</span>
      <div>
        <strong>Channel Secure</strong>
        <p>
          Error rate {ratePct}% is below the {thresholdPct}% threshold. No eavesdropping detected.
        </p>
      </div>
    </div>
  );
}
