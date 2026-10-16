import React, { useState, useEffect, useCallback } from 'react';
import { Cloud, Server, RefreshCw, Send, CheckCircle2, Clock, AlertCircle, ExternalLink } from 'lucide-react';
import KatexView from './KatexView';

export default function IBMCloudLiveView({
  alpha,
  beta,
}) {
  const [backends, setBackends] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedBackend, setSelectedBackend] = useState('ibm_kingston');
  const [submissionResult, setSubmissionResult] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [shots, setShots] = useState(1024);

  // Fetch live IBM Cloud status
  const fetchCloudStatus = useCallback(async () => {
    setIsLoading(true);
    try {
      const [resBackends, resJobs] = await Promise.all([
        fetch('/api/ibm/backends'),
        fetch('/api/ibm/jobs'),
      ]);
      if (resBackends.ok) {
        const data = await resBackends.json();
        if (data.backends) setBackends(data.backends);
      }
      if (resJobs.ok) {
        const data = await resJobs.json();
        if (data.jobs) setJobs(data.jobs);
      }
    } catch (err) {
      console.warn('Failed to load IBM cloud telemetry', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCloudStatus();
  }, [fetchCloudStatus]);

  // Submit job to real hardware
  const handleSubmitJob = async () => {
    setIsSubmitting(true);
    try {
      const res = await fetch('/api/ibm/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          alpha_real: alpha.real,
          alpha_imag: alpha.imag,
          beta_real: beta.real,
          beta_imag: beta.imag,
          shots,
          backend_name: selectedBackend,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setSubmissionResult(data);
        // Refresh job list
        fetchCloudStatus();
      } else {
        const errData = await res.json();
        alert(`IBM Cloud submission error: ${errData.detail || 'Failed to submit'}`);
      }
    } catch (err) {
      alert(`Submission network error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="card formal-card">
      <div className="card-header">
        <div className="header-title-group">
          <Cloud className="icon-formal" size={18} />
          <div>
            <h3 className="section-title">IBM Quantum Cloud Hardware (Live Telemetry & QPU Queue)</h3>
            <p className="section-subtitle">
              Connected to IBM Cloud Quantum Instance via CRN (Region: us-east / Washington DC)
            </p>
          </div>
        </div>

        <button
          className="btn btn-secondary btn-sm"
          onClick={fetchCloudStatus}
          disabled={isLoading}
        >
          <RefreshCw size={13} className={isLoading ? 'spin' : ''} />
          {isLoading ? 'Querying QPUs...' : 'Refresh Telemetry'}
        </button>
      </div>

      <div className="card-body">
        {/* Why Jobs Show "Pending" Callout */}
        <div className="info-callout mb-4" style={{ backgroundColor: 'rgba(27, 70, 140, 0.04)', borderColor: 'var(--b1)' }}>
          <div className="callout-header">
            <Clock size={16} className="text-b1" />
            <strong style={{ color: 'var(--b1)' }}>Why IBM Quantum Dashboard Shows "Pending Jobs":</strong>
          </div>
          <p className="callout-desc mt-1">
            Physical quantum processors (like <strong><code>ibm_kingston</code></strong>) reside in dilution refrigerators cooled to 15 millikelvin. Unlike software simulations, real hardware executes circuits sequentially in a global shared queue. When you submit a job to IBM Cloud, it shows as <strong>Pending / Queued</strong> until the physical QPU reaches your job.
          </p>
          <p className="callout-desc mt-1">
            In our app, you have both:
            <br />• <strong>Local Aer Engine:</strong> Computes the exact quantum math on your Mac in <strong>5 milliseconds</strong> (zero queue).
            <br />• <strong>Cloud Dispatch:</strong> Submits the transpiled ISA circuit directly to the real 156-qubit Heron r2 processor.
          </p>
        </div>

        {/* Live QPU Fleet Cards */}
        <h4 className="sub-panel-title mb-3">
          <Server size={15} /> Available Cloud QPUs & Real-Time Queue Depths
        </h4>

        <div className="outcome-cards-grid mb-4">
          {backends.map((b) => {
            const isSelected = selectedBackend === b.name;
            return (
              <div
                key={b.name}
                className={`outcome-card ${isSelected ? 'selected' : ''}`}
                onClick={() => setSelectedBackend(b.name)}
                style={{ cursor: 'pointer' }}
              >
                <div className="outcome-card-top">
                  <span className="outcome-bitstring" style={{ fontSize: '0.95rem' }}>{b.name}</span>
                  <span className="badge badge-success">Online</span>
                </div>

                <div className="qubit-owner" style={{ margin: '4px 0' }}>
                  Architecture: <strong>{b.processor_type}</strong> ({b.num_qubits} Qubits)
                </div>

                <div className="metric-box mt-2" style={{ padding: '6px 8px' }}>
                  <span className="metric-label">Cloud Queue Depth:</span>
                  <span className="metric-val" style={{ fontSize: '1rem', color: b.pending_jobs > 0 ? '#b45309' : '#059669' }}>
                    {b.pending_jobs} pending {b.pending_jobs === 1 ? 'job' : 'jobs'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Submit Circuit to Selected QPU */}
        <div className="branch-deepdive mb-4">
          <div className="deepdive-header">
            <h4 className="deepdive-title">
              Dispatch Teleportation Circuit to Physical QPU: <span className="text-b1">{selectedBackend}</span>
            </h4>
            <span className="badge badge-primary">SamplerV2 Dynamic Circuit</span>
          </div>

          <p className="stage-description-text">
            Transpile the current teleportation state <KatexView math="|\psi\rangle = \alpha|0\rangle + \beta|1\rangle" /> into native Heron basis gates (<code>cz, rz, sx, x</code>) with dynamic conditional feed-forward logic and submit to the physical processor queue.
          </p>

          <div className="sim-action-group mt-3" style={{ flexWrap: 'wrap', gap: '12px' }}>
            <div className="shots-selector">
              <span className="shots-label">Shots:</span>
              {[512, 1024, 4096].map((s) => (
                <button
                  key={s}
                  className={`btn-shot ${shots === s ? 'active' : ''}`}
                  onClick={() => setShots(s)}
                >
                  {s}
                </button>
              ))}
            </div>

            <button
              className="btn btn-primary"
              onClick={handleSubmitJob}
              disabled={isSubmitting}
            >
              <Send size={13} className={isSubmitting ? 'spin' : ''} />
              {isSubmitting ? 'Transpiling & Submitting...' : `Submit Job to ${selectedBackend}`}
            </button>
          </div>

          {/* Submission Feedback */}
          {submissionResult && (
            <div className="certificate-banner success mt-3">
              <div className="cert-icon">
                <CheckCircle2 size={24} className="text-success" />
              </div>
              <div className="cert-details">
                <div className="cert-status-tag">Job Queued on IBM Cloud</div>
                <h5 className="cert-title" style={{ fontSize: '0.92rem', fontFamily: 'monospace' }}>
                  Job ID: {submissionResult.job_id}
                </h5>
                <p className="cert-desc">{submissionResult.message}</p>
              </div>
            </div>
          )}
        </div>

        {/* Recent Jobs History */}
        <h4 className="sub-panel-title mb-2">Recent IBM Cloud Workloads</h4>
        <div className="formal-table-container">
          <table className="formal-table">
            <thead>
              <tr>
                <th>Job Identifier</th>
                <th>Target Backend</th>
                <th>Status</th>
                <th>Submitted Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr key={j.job_id}>
                  <td>
                    <span className="mono-pill" style={{ fontWeight: 600 }}>{j.job_id}</span>
                  </td>
                  <td><strong>{j.backend}</strong></td>
                  <td>
                    <span className={`badge ${j.status === 'DONE' ? 'badge-success' : 'badge-subtle'}`}>
                      {j.status}
                    </span>
                  </td>
                  <td>{j.created}</td>
                </tr>
              ))}
              {jobs.length === 0 && (
                <tr>
                  <td colSpan={4} style={{ textAlign: 'center', color: '#64748b' }}>
                    No recent cloud jobs found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
