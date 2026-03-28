import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  getArtifactSections,
  getCase,
  getCaseArtifacts,
  getCaseAssessments,
  getCaseAuditEvents,
  getCaseClaims,
  getCaseEvidenceLinks,
  getCaseRecommendation,
} from "../../api/cases";

export function CaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [selectedArtifactId, setSelectedArtifactId] = useState<string>("");

  const caseQuery = useQuery({
    queryKey: ["case", id],
    queryFn: () => getCase(id!),
    enabled: Boolean(id),
  });

  const claimsQuery = useQuery({
    queryKey: ["case-claims", id],
    queryFn: () => getCaseClaims(id!),
    enabled: Boolean(id),
  });

  const evidenceQuery = useQuery({
    queryKey: ["case-evidence", id],
    queryFn: () => getCaseEvidenceLinks(id!),
    enabled: Boolean(id),
  });

  const assessmentsQuery = useQuery({
    queryKey: ["case-assessments", id],
    queryFn: () => getCaseAssessments(id!),
    enabled: Boolean(id),
  });

  const recommendationQuery = useQuery({
    queryKey: ["case-recommendation", id],
    queryFn: () => getCaseRecommendation(id!),
    enabled: Boolean(id),
  });

  const auditQuery = useQuery({
    queryKey: ["case-audit", id],
    queryFn: () => getCaseAuditEvents(id!),
    enabled: Boolean(id),
  });

  const artifactsQuery = useQuery({
    queryKey: ["case-artifacts", id],
    queryFn: () => getCaseArtifacts(id!),
    enabled: Boolean(id),
  });

  const selectedArtifact = useMemo(() => {
    const artifacts = artifactsQuery.data ?? [];
    if (!artifacts.length) {
      return null;
    }

    if (selectedArtifactId) {
      return artifacts.find((item) => item.id === selectedArtifactId) ?? artifacts[0];
    }

    return artifacts[0];
  }, [artifactsQuery.data, selectedArtifactId]);

  const sectionsQuery = useQuery({
    queryKey: ["artifact-sections", selectedArtifact?.id],
    queryFn: () => getArtifactSections(selectedArtifact!.id),
    enabled: Boolean(selectedArtifact?.id),
  });

  if (!id) {
    return <div className="panel error-panel">Missing case id.</div>;
  }

  if (caseQuery.isLoading) {
    return <div className="panel">Loading case…</div>;
  }

  if (caseQuery.isError || !caseQuery.data) {
    return (
      <div className="panel error-panel">
        Failed to load case.
        <pre>{String(caseQuery.error)}</pre>
      </div>
    );
  }

  const reviewCase = caseQuery.data;
  const claims = claimsQuery.data ?? [];
  const evidenceLinks = evidenceQuery.data ?? [];
  const assessments = assessmentsQuery.data?.assessments ?? [];
  const contradictions = assessmentsQuery.data?.contradictions ?? [];
  const recommendation = recommendationQuery.data;
  const auditEvents = auditQuery.data ?? [];
  const artifacts = artifactsQuery.data ?? [];
  const sections = sectionsQuery.data ?? [];

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <Link to="/" className="back-link">
            ← Back to cases
          </Link>
          <h2>{reviewCase.reference_code}</h2>
          <p>{reviewCase.title}</p>
        </div>
        <div className="header-grid">
          <div className="stat-chip">Status: {reviewCase.status}</div>
          <div className="stat-chip">Review: {reviewCase.review_status}</div>
          <div className="stat-chip">Priority: {reviewCase.priority}</div>
          <div className="stat-chip">
            Degraded: {reviewCase.degraded_mode_active ? "yes" : "no"}
          </div>
        </div>
      </div>

      <div className="panel-grid">
        <section className="panel">
          <h3>Claims</h3>
          {claims.length === 0 ? (
            <p>No claims found.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Text</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {claims.map((claim) => (
                  <tr key={claim.id}>
                    <td>{claim.claim_type}</td>
                    <td>{claim.claim_text}</td>
                    <td>{claim.extraction_confidence}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="panel">
          <h3>Evidence Links</h3>
          {evidenceLinks.length === 0 ? (
            <p>No evidence links found.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Claim</th>
                  <th>Outcome</th>
                  <th>Link Type</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {evidenceLinks.map((link) => (
                  <tr key={link.id}>
                    <td>{link.claim}</td>
                    <td>{link.outcome}</td>
                    <td>{link.link_type}</td>
                    <td>{String(link.score ?? "")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="panel">
          <h3>Assessments</h3>
          {assessments.length === 0 ? (
            <p>No assessments found.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Confidence</th>
                  <th>Requires Review</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                {assessments.map((assessment) => (
                  <tr key={assessment.id}>
                    <td>{assessment.status}</td>
                    <td>{assessment.confidence}</td>
                    <td>{assessment.requires_review ? "yes" : "no"}</td>
                    <td>{assessment.assessment_reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="panel">
          <h3>Contradictions</h3>
          {contradictions.length === 0 ? (
            <p>No contradictions found.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Severity</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                {contradictions.map((item) => (
                  <tr key={item.id}>
                    <td>{item.contradiction_type}</td>
                    <td>{item.severity}</td>
                    <td>{item.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="panel">
          <h3>Recommendation</h3>
          {!recommendation ? (
            <p>Recommendation not ready.</p>
          ) : (
            <div className="stack">
              <div>
                <strong>Action:</strong> {recommendation.recommended_action}
              </div>
              <div>
                <strong>Priority:</strong> {recommendation.recommended_priority}
              </div>
              <div>
                <strong>Confidence:</strong> {recommendation.confidence}
              </div>
              <div>
                <strong>Citations:</strong> {recommendation.citation_count}
              </div>
              <div>
                <strong>Model:</strong> {recommendation.model_version}
              </div>
              <div>
                <strong>Summary:</strong>
                <p>{recommendation.executive_summary}</p>
              </div>
            </div>
          )}
        </section>

        <section className="panel">
          <h3>Artifacts</h3>
          {artifacts.length === 0 ? (
            <p>No artifacts found.</p>
          ) : (
            <>
              <select
                value={selectedArtifact?.id ?? ""}
                onChange={(e) => setSelectedArtifactId(e.target.value)}
                className="select-input"
              >
                {artifacts.map((artifact) => (
                  <option key={artifact.id} value={artifact.id}>
                    {artifact.filename} ({artifact.artifact_type})
                  </option>
                ))}
              </select>

              <table className="data-table">
                <thead>
                  <tr>
                    <th>Filename</th>
                    <th>Type</th>
                    <th>Parse Status</th>
                    <th>Uploaded</th>
                  </tr>
                </thead>
                <tbody>
                  {artifacts.map((artifact) => (
                    <tr key={artifact.id}>
                      <td>{artifact.filename}</td>
                      <td>{artifact.artifact_type}</td>
                      <td>{artifact.parse_status}</td>
                      <td>{new Date(artifact.uploaded_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <h4>Sections</h4>
              {sections.length === 0 ? (
                <p>No sections found for selected artifact.</p>
              ) : (
                <div className="stack">
                  {sections.map((section) => (
                    <div key={section.id} className="section-card">
                      <div className="section-meta">
                        <strong>Section {section.section_index}</strong>
                        {section.heading ? <span>{section.heading}</span> : null}
                        {section.page_number ? <span>Page {section.page_number}</span> : null}
                      </div>
                      <p>{section.text}</p>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </section>

        <section className="panel">
          <h3>Audit Events</h3>
          {auditEvents.length === 0 ? (
            <p>No audit events found.</p>
          ) : (
            <div className="stack">
              {auditEvents.map((event) => (
                <div key={event.id} className="timeline-item">
                  <div className="timeline-title">{event.event_type}</div>
                  <div className="timeline-meta">
                    <span>{event.actor_type}</span>
                    <span>{new Date(event.created_at).toLocaleString()}</span>
                  </div>
                  <pre className="json-block">
                    {JSON.stringify(event.payload, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}