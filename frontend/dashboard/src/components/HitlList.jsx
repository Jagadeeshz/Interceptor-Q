import React, { useState } from "react";
import useFetch from "../hooks/useFetch";

const HitlList = () => {
  const { data: hitlList, loading, error, refetch } = useFetch("/hitl/pending");
  const [busy, setBusy] = useState(null);

  const decide = async (hitlId, action) => {
    setBusy(hitlId);
    try {
      const res = await fetch(`/api/hitl/${action}/${hitlId}`, { method: "POST" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      refetch();
    } catch (err) {
      alert(`Failed to ${action} HITL item: ${err.message}`);
    } finally {
      setBusy(null);
    }
  };

  if (loading) return <p>Loading HITL items...</p>;
  if (error) return <p>Error loading HITL items: {error}</p>;

  return (
    <div>
      <h3 style={{ margin: "0 0 16px 0" }}>Pending HITL Items</h3>
      {!hitlList || hitlList.length === 0 ? (
        <p style={{ color: "var(--bindu-shunya-4)" }}>No pending items.</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {hitlList.map((item) => (
            <li
              key={item.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "16px",
                marginBottom: "8px",
                padding: "12px 16px",
                background: "rgba(250,248,242,0.03)",
                border: "1px solid rgba(250,248,242,0.06)",
                borderRadius: "8px",
              }}
            >
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: "500" }}>
                  {item.company_name || `Company #${item.company_id}`} –{" "}
                  {item.contact_name || `Contact #${item.contact_id}`}
                </div>
                <div
                  style={{
                    fontSize: "12px",
                    color: "var(--bindu-shunya-3)",
                    marginTop: "4px",
                    lineHeight: "1.5",
                  }}
                >
                  {item.message_text}
                </div>
              </div>
              <button
                className="btn-primary"
                disabled={busy === item.id}
                onClick={() => decide(item.id, "approve")}
              >
                Approve
              </button>
              <button
                disabled={busy === item.id}
                onClick={() => decide(item.id, "reject")}
                style={{
                  padding: "8px 14px",
                  borderRadius: "6px",
                  border: "1px solid rgba(250,248,242,0.15)",
                  background: "transparent",
                  color: "var(--bindu-shunya-3)",
                  cursor: "pointer",
                  fontSize: "13px",
                }}
              >
                Reject
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default HitlList;