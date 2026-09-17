import React, { useState } from 'react';
import useFetch from './hooks/useFetch';
import HitlList from './components/HitlList';

const SidebarItem = ({ icon, label, active, onClick }) => (
  <div
    onClick={onClick}
    style={{
      padding: '8px 12px',
      cursor: 'pointer',
      borderRadius: '6px',
      fontSize: '13px',
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      backgroundColor: active ? 'var(--bindu-void-3)' : 'transparent',
      color: active ? 'var(--bindu-shunya)' : 'var(--bindu-shunya-4)',
      transition: 'all 0.2s var(--bindu-ease)',
      border: active ? '1px solid rgba(250,248,242,0.1)' : '1px solid transparent'
    }}
  >
    <span style={{ fontSize: '16px' }}>{icon}</span>
    {label}
  </div>
);

// StatCard component (unchanged)
const StatCard = ({ label, value, trend }) => (
  <div className="card-panel" style={{ minWidth: '200px', flex: 1 }}>
    <div style={{ color: 'var(--bindu-shunya-4)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>{label}</div>
    <div style={{ fontSize: '24px', fontWeight: '600', fontFamily: 'var(--bindu-font-display)', color: 'var(--bindu-shunya)' }}>{value}</div>
    <div style={{ fontSize: '11px', color: trend.startsWith('+') ? 'var(--bindu-raga-teal)' : 'var(--bindu-raga-red)', marginTop: '4px' }}>
      {trend} vs last 24h
    </div>
  </div>
);

// Opportunity Table component
const OpportunityTable = ({ opportunities }) => {
  if (!opportunities) return null;
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
      <thead>
        <tr style={{ borderBottom: '1px solid rgba(250,248,242,0.1)', color: 'var(--bindu-shunya-4)' }}>
          <th style={{ padding: '12px 8px' }}>Company</th>
          <th style={{ padding: '12px 8px' }}>Match %</th>
          <th style={{ padding: '12px 8px' }}>Source</th>
          <th style={{ padding: '12px 8px' }}>Status</th>
        </tr>
      </thead>
      <tbody>
        {opportunities.map((opp, i) => (
          <tr key={i} style={{ borderBottom: '1px solid rgba(250,248,242,0.03)' }}>
            <td style={{ padding: '12px 8px', fontWeight: '500' }}>{opp.company_name}</td>
            <td style={{ padding: '12px 8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ width: '40px', height: '4px', background: 'var(--bindu-void-4)', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ width: opp.match_score + '%', height: '100%', background: 'var(--bindu-raga-teal)' }}></div>
                </div>
                {opp.match_score}
              </div>
            </td>
            <td style={{ padding: '12px 8px' }}><span>{opp.source_platform}</span></td>
            <td style={{ padding: '12px 8px' }}>
              <span style={{ background: opp.status === 'READY' ? 'rgba(0,221,170,0.1)' : 'rgba(250,248,242,0.05)', color: opp.status === 'READY' ? 'var(--bindu-raga-teal)' : 'var(--bindu-shunya-4)' }}>{opp.status}</span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};


// Companies Map (simplified as a list for now)
const CompaniesMap = ({ companies }) => {
  if (!companies) return null;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {companies.map((c, i) => (
        <div key={i} style={{ padding: '12px', borderRadius: '8px', background: 'rgba(250,248,242,0.03)', borderLeft: '3px solid var(--bindu-raga-teal)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span style={{ fontSize: '13px', fontWeight: '500' }}>{c.name}</span>
            <span style={{ fontSize: '11px', color: 'var(--bindu-shunya-4)' }}>{c.source_platform}</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--bindu-shunya-3)' }}>
            {c.domain} • {c.region} • {c.funding_stage || 'N/A'} • {c.company_size || 'N/A'} employees
          </div>
        </div>
      ))}
    </div>
  );
};

// Signals Feed component
const SignalsFeed = ({ signals }) => {
  if (!signals) return null;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {signals.map((sig, i) => (
        <div key={i} style={{ padding: '12px', borderRadius: '8px', background: 'rgba(250,248,242,0.03)', borderLeft: '3px solid ' + (sig.type === 'signal' ? 'var(--bindu-raga-teal)' : 'var(--bindu-void-4)') }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span style={{ fontSize: '10px', color: 'var(--bindu-shunya-4)' }}>{new Date(sig.time).toLocaleTimeString()}</span>
            <span style={{ fontSize: '10px', color: sig.type === 'signal' ? 'var(--bindu-raga-teal)' : 'var(--bindu-shunya-4)', textTransform: 'uppercase' }}>{sig.type}</span>
          </div>
          <div style={{ fontSize: '12px', lineHeight: '1.5' }}>{sig.message}</div>
        </div>
      ))}
    </div>
  );
};

// Main App component
const App = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [deploying, setDeploying] = useState(false);

  // Fetch data for each tab as needed
  const { data: metricsData, loading: metricsLoading, error: metricsError } = useFetch('/metrics');
  const { data: opportunitiesData, loading: opportunitiesLoading, error: opportunitiesError } = useFetch('/opportunities');
  const { data: companiesData, loading: companiesLoading, error: companiesError } = useFetch('/companies');
  const { data: signalsData, loading: signalsLoading, error: signalsError } = useFetch('/signals');

  const handleDeploy = async () => {
    setDeploying(true);
    try {
      const res = await fetch(apiBase + '/deploy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: 'all sources' })
      });
      if (!res.ok) throw new Error("'Deploy failed: ' + res.status");
      const result = await res.json();
      alert("'Deployment queued: ' + result.note");
    } catch (err) {
      alert("'Deployment error: ' + err.message");
    } finally {
      setDeploying(false);
    }
  };

  // Determine which data to show based on activeTab
  let tabContent;
  switch (activeTab) {
    case 'dashboard':
      tabContent = (
        <>
          <div className="spectrum-bar" style={{ marginBottom: '24px' }}></div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '24px' }}>
            <div>
              <h1 style={{ margin: 0, fontSize: '32px', fontWeight: '600', color: 'var(--bindu-shunya)' }}>Intelligence Surface</h1>
              <p style={{ margin: '8px 0 0 0', color: 'var(--bindu-shunya-4)', fontSize: '14px' }}>Autonomous discovery and lead enrichment metrics.</p>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <div style={{ padding: '4px 12px', background: 'var(--bindu-void-3)', borderRadius: '4px', fontSize: '12px', border: '1px solid rgba(250,248,242,0.1)' }}>
                Last sync: 2m ago
              </div>
            </div>
          </div>
          {/* Stats Grid */}
          <div style={{ display: 'flex', gap: '20px', marginBottom: '32px' }}>
            {!metricsLoading && metricsData ? (
              <>
                <StatCard label="Leads Discovered" value={metricsData.leads_discovered.value.toLocaleString()} trend={'+' + metricsData.leads_discovered.trend + '%'} />
                <StatCard label="Enrichment Rate" value={metricsData.enrichment_rate.value + '%'} trend={'+' + metricsData.enrichment_rate.trend + '%'} />
                                 <StatCard label="Active Signals" value={metricsData.active_signals.value} trend={"+" + (metricsData.active_signals.trend >= 0 ? "+" : "") + metricsData.active_signals.trend + "%"} />
                <StatCard label="Conversion Prob." value={metricsData.conversion_prob.value + '%'} trend={'+' + metricsData.conversion_prob.trend + '%'} />
              </>
            ) : (
              <div style={{ flex: 1, minWidth: '200px', textAlign: 'center', padding: '20px', color: 'var(--bindu-shunya-4)' }}>
                Loading metrics...
              </div>
            )}
          </div>
          {/* Main Data Area */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px', flex: 1 }}>
            <div className="card-panel" style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3 style={{ margin: 0, fontSize: '18px' }}>High-Intent Opportunities</h3>
                <button
                  onClick={() => setActiveTab('map')}
                  style={{
                    background: 'transparent',
                    color: 'var(--bindu-shunya-4)',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '12px',
                    padding: '0'
                  }}
                >
                  View All →
                </button>
              </div>
              {!opportunitiesLoading && opportunitiesData ? (
                <OpportunityTable opportunities={opportunitiesData.items || opportunitiesData} />
              ) : (
                <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--bindu-shunya-4)' }}>
                  Loading opportunities...
                </div>
              )}
            </div>
            <div className="card-panel" style={{ background: 'var(--bindu-void-1)' }}>
              <h3 style={{ margin: '0 0 20px 0', fontSize: '18px' }}>Live Signal Feed</h3>
              {!signalsLoading && signalsData ? (
                <SignalsFeed signals={signalsData.items || signalsData} />
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--bindu-shunya-4)' }}>
                  Loading signals...
                </div>
              )}
            </div>
          </div>
        </>
      );
      break;

    case 'map':
      tabContent = (
        <>
          <div className="spectrum-bar" style={{ marginBottom: '24px' }}></div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <h1 style={{ margin: 0, fontSize: '24px', fontWeight: '600', color: 'var(--bindu-shunya)' }}>Opportunity Map</h1>
            <button
              onClick={() => setActiveTab('dashboard')}
              style={{
                background: 'transparent',
                color: 'var(--bindu-shunya-4)',
                border: 'none',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              ← Back to Dashboard
            </button>
          </div>
          {!companiesLoading && companiesData ? (
            <CompaniesMap companies={companiesData.items || companiesData} />
          ) : (
            <div style={{ minHeight: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--bindu-shunya-4)' }}>
              Loading companies...
            </div>
          )}
        </>
      );
      break;

    case 'pipeline':
      tabContent = (
        <>
          <div className="spectrum-bar" style={{ marginBottom: '24px' }}></div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <h1 style={{ margin: 0, fontSize: '24px', fontWeight: '600', color: 'var(--bindu-shunya)' }}>Enrichment Pipeline</h1>
            <button
              onClick={() => setActiveTab('dashboard')}
              style={{
                background: 'transparent',
                color: 'var(--bindu-shunya-4)',
                border: 'none',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              ← Back to Dashboard
            </button>
          </div>
          <div style={{ background: 'var(--bindu-void-1)', borderRadius: '8px', padding: '24px' }}>
            <p style={{ color: 'var(--bindu-shunya-4)', marginBottom: '16px' }}>
              View the status of companies as they move through the enrichment pipeline (Apollo → LinkedIn → Manual).
            </p>
            {/* Pipeline stages would go here - for now show a placeholder */}
            <div style={{ display: 'flex', gap: '16px' }}>
              <div style={{ flex: 1, background: 'var(--bindu-void-3)', padding: '16px', borderRadius: '6px' }}>
                <h4 style={{ margin: '0 0 12px 0', color: 'var(--bindu-shunya)' }}>Pending</h4>
                <div style={{ color: 'var(--bindu-shunya-3)' }}>0 companies</div>
              </div>
              <div style={{ flex: 1, background: 'var(--bindu-void-3)', padding: '16px', borderRadius: '6px' }}>
                <h4 style={{ margin: '0 0 12px 0', color: 'var(--bindu-shunya)' }}>Enriching</h4>
                <div style={{ color: 'var(--bindu-shunya-3)' }}>0 companies</div>
              </div>
              <div style={{ flex: 1, background: 'var(--bindu-void-3)', padding: '16px', borderRadius: '6px' }}>
                <h4 style={{ margin: '0 0 12px 0', color: 'var(--bindu-shunya)' }}>Ready</h4>
                <div style={{ color: 'var(--bindu-shunya-3)' }}>0 companies</div>
              </div>
            </div>
          </div>
        </>
      );
      break;

    case 'signals':
      tabContent = (
        <>
          <div className="spectrum-bar" style={{ marginBottom: '24px' }}></div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <h1 style={{ margin: 0, fontSize: '24px', fontWeight: '600', color: 'var(--bindu-shunya)' }}>Signal Monitor</h1>
            <button
              onClick={() => setActiveTab('dashboard')}
              style={{
                background: 'transparent',
                color: 'var(--bindu-shunya-4)',
                border: 'none',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              ← Back to Dashboard
            </button>
          </div>
          {!signalsLoading && signalsData ? (
            <SignalsFeed signals={signalsData.items || signalsData} />
          ) : (
            <div style={{ minHeight: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--bindu-shunya-4)' }}>
              Loading signals...
            </div>
          )}
        </>
      );
      break;

    case 'settings':
      tabContent = (
        <>
          <div className="spectrum-bar" style={{ marginBottom: '24px' }}></div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <h1 style={{ margin: 0, fontSize: '24px', fontWeight: '600', color: 'var(--bindu-shunya)' }}>System Config</h1>
            <button
              onClick={() => setActiveTab('dashboard')}
              style={{
                background: 'transparent',
                color: 'var(--bindu-shunya-4)',
                border: 'none',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              ← Back to Dashboard
            </button>
          </div>
          <div className="card-panel" style={{ background: 'var(--bindu-void-1)' }}>
            <h3 style={{ margin: '0 0 20px 0', fontSize: '18px' }}>API Status</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' }}>
              <div>
                <div style={{ fontSize: '12px', color: 'var(--bindu-shunya-4)', marginBottom: '4px' }}>Metrics API</div>
                <div style={{ fontSize: '14px', fontWeight: '500', color: metricsLoading ? 'var(--bindu-shunya-3)' : metricsError ? 'var(--bindu-raga-red)' : 'var(--bindu-raga-teal)' }}>
                  {metricsLoading ? 'loading' : metricsError ? 'error' : 'ok'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '12px', color: 'var(--bindu-shunya-4)', marginBottom: '4px' }}>Opportunities API</div>
                <div style={{ fontSize: '14px', fontWeight: '500', color: opportunitiesLoading ? 'var(--bindu-shunya-3)' : opportunitiesError ? 'var(--bindu-raga-red)' : 'var(--bindu-raga-teal)' }}>
                  {opportunitiesLoading ? 'loading' : opportunitiesError ? 'error' : 'ok'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '12px', color: 'var(--bindu-shunya-4)', marginBottom: '4px' }}>Companies API</div>
                <div style={{ fontSize: '14px', fontWeight: '500', color: companiesLoading ? 'var(--bindu-shunya-3)' : companiesError ? 'var(--bindu-raga-red)' : 'var(--bindu-raga-teal)' }}>
                  {companiesLoading ? 'loading' : companiesError ? 'error' : 'ok'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '12px', color: 'var(--bindu-shunya-4)', marginBottom: '4px' }}>Signals API</div>
                <div style={{ fontSize: '14px', fontWeight: '500', color: signalsLoading ? 'var(--bindu-shunya-3)' : signalsError ? 'var(--bindu-raga-red)' : 'var(--bindu-raga-teal)' }}>
                  {signalsLoading ? 'loading' : signalsError ? 'error' : 'ok'}
                </div>
              </div>
            </div>
          </div>
        </>
      );
      break;

    case 'hitl':
      tabContent = (
        <>
          <div className="spectrum-bar" style={{ marginBottom: '24px' }}></div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <h1 style={{ margin: 0, fontSize: '24px', fontWeight: '600', color: 'var(--bindu-shunya)' }}>HITL Approvals</h1>
            <span style={{ fontSize: '12px', color: 'var(--bindu-shunya-4)' }}>Review generated outreach messages before they are sent.</span>
          </div>
          <div className="card-panel" style={{ background: 'var(--bindu-void-1)' }}>
            <HitlList />
          </div>
        </>
      );
      break;

    default:
      tabContent = <div>Loading...</div>;
  }

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', background: 'var(--bindu-void)' }}>
      {/* Sidebar */}
      <div style={{ width: '240px', background: 'var(--bindu-void-1)', borderRight: '1px solid rgba(250,248,242,0.06)', display: 'flex', flexDirection: 'column', padding: '20px 12px' }}>
        <div style={{ fontSize: '20px', fontFamily: 'var(--bindu-font-display)', fontWeight: '700', marginBottom: '32px', paddingLeft: '12px', color: 'var(--bindu-shunya)' }}>
          INTERCEPTOR<span style={{ color: 'var(--bindu-raga-teal)' }}>.Q</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <SidebarItem icon="🎯" label="Command Center" active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
          <SidebarItem icon="🔍" label="Opportunity Map" active={activeTab === 'map'} onClick={() => setActiveTab('map')} />
          <SidebarItem icon="⚡" label="Enrichment Pipeline" active={activeTab === 'pipeline'} onClick={() => setActiveTab('pipeline')} />
          <SidebarItem icon="📡" label="Signal Monitor" active={activeTab === 'signals'} onClick={() => setActiveTab('signals')} />
          <SidebarItem icon="📋" label="HITL" active={activeTab === 'hitl'} onClick={() => setActiveTab('hitl')} />
          <SidebarItem icon="⚙️" label="System Config" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
        </div>
        <div style={{ marginTop: 'auto', padding: '12px', background: 'var(--bindu-void-3)', borderRadius: '8px', border: '1px solid rgba(250,248,242,0.05)' }}>
          <div style={{ fontSize: '11px', color: 'var(--bindu-shunya-4)', marginBottom: '8px' }}>SYSTEM STATUS</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}>
            <span className="status-dot"></span>
            <span>All Nodes Active</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <nav style={{ height: '44px', background: 'rgba(8,11,18,0.95)', backdropFilter: 'var(--bindu-glass-blur)', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px' }}>
          <div style={{ fontSize: '13px', color: 'var(--bindu-shunya-3)' }}>
            {activeTab === 'dashboard'
              ? 'Command Center / Overview'
              : 'Command Center / ' + activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
          </div>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              className="btn-primary"
              onClick={handleDeploy}
              disabled={deploying}
              style={{ opacity: deploying ? 0.7 : 1 }}
            >
              {deploying ? 'Deploying...' : 'Deploy Agent'}
            </button>
          </div>
        </nav>

        <div style={{ flex: 1, overflowY: 'auto', padding: '32px', gap: '32px', display: 'flex', flexDirection: 'column' }}>
          {tabContent}
        </div>
      </div>
    </div>
  );
};

export default App;