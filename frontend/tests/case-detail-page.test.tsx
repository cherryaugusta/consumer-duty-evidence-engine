import { screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { CaseDetailPage } from "../src/features/cases/CaseDetailPage";
import { renderWithProviders } from "./test-utils";

vi.mock("../src/api/cases", () => ({
  getCase: vi.fn(),
  getCaseClaims: vi.fn(),
  getCaseEvidenceLinks: vi.fn(),
  getCaseAssessments: vi.fn(),
  getCaseRecommendation: vi.fn(),
  getCaseAuditEvents: vi.fn(),
  getCaseArtifacts: vi.fn(),
  getArtifactSections: vi.fn(),
}));

import {
  getArtifactSections,
  getCase,
  getCaseArtifacts,
  getCaseAssessments,
  getCaseAuditEvents,
  getCaseClaims,
  getCaseEvidenceLinks,
  getCaseRecommendation,
} from "../src/api/cases";

const mockedGetCase = vi.mocked(getCase);
const mockedGetCaseClaims = vi.mocked(getCaseClaims);
const mockedGetCaseEvidenceLinks = vi.mocked(getCaseEvidenceLinks);
const mockedGetCaseAssessments = vi.mocked(getCaseAssessments);
const mockedGetCaseRecommendation = vi.mocked(getCaseRecommendation);
const mockedGetCaseAuditEvents = vi.mocked(getCaseAuditEvents);
const mockedGetCaseArtifacts = vi.mocked(getCaseArtifacts);
const mockedGetArtifactSections = vi.mocked(getArtifactSections);

describe("CaseDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockedGetCase.mockResolvedValue({
      id: "case-1",
      reference_code: "CDEE-20260329-0001",
      title: "Unclear fee wording complaint",
      status: "needs_review",
      review_status: "unassigned",
      priority: "high",
      case_type: "complaint_review",
      correlation_id: "corr-1",
      latest_eval_run_id: "eval-run-1",
      eval_case_id: "eval-case-1",
      degraded_mode_active: true,
      created_at: "2026-03-29T10:00:00Z",
      updated_at: "2026-03-29T11:00:00Z",
      summary_snapshot: {},
    });

    mockedGetCaseClaims.mockResolvedValue([
      {
        id: "claim-1",
        case: "case-1",
        claim_type: "unclear_fee",
        claim_text: "Customer says the monthly fee was unclear.",
        normalized_claim_text: "monthly fee unclear",
        source_section: "section-1",
        extraction_confidence: 0.91,
        schema_valid: true,
        extraction_version: "v1",
        created_at: "2026-03-29T10:01:00Z",
      },
    ]);

    mockedGetCaseEvidenceLinks.mockResolvedValue([
      {
        id: "link-1",
        case: "case-1",
        claim: "claim-1",
        outcome: "consumer_understanding",
        section: "section-1",
        link_type: "supporting",
        rationale: "Fee explanation text cited.",
        score: 0.84,
      },
    ]);

    mockedGetCaseAssessments.mockResolvedValue({
      assessments: [
        {
          id: "assessment-1",
          case: "case-1",
          claim: "claim-1",
          outcome: "consumer_understanding",
          status: "weak_support",
          confidence: 0.66,
          requires_review: true,
          assessment_reason: "Fee wording is ambiguous.",
          rules_triggered: [],
          model_version: "rules-v1",
          created_at: "2026-03-29T10:03:00Z",
        },
      ],
      contradictions: [
        {
          id: "contradiction-1",
          case: "case-1",
          claim: "claim-1",
          primary_section: "section-1",
          secondary_section: "section-2",
          contradiction_type: "statement_conflict",
          severity: "high",
          reason: "Script wording conflicts with disclosure.",
          created_at: "2026-03-29T10:04:00Z",
        },
      ],
    });

    mockedGetCaseRecommendation.mockResolvedValue({
      id: "recommendation-1",
      case: "case-1",
      recommended_action: "review",
      recommended_priority: "high",
      executive_summary: "Escalate for analyst review because support is weak.",
      structured_rationale: {},
      confidence: 0.61,
      citation_count: 2,
      model_version: "mock-structured-v1",
      prompt_version: null,
      prompt_version_name: null,
      prompt_version_label: null,
      created_at: "2026-03-29T10:05:00Z",
    });

    mockedGetCaseAuditEvents.mockResolvedValue([
      {
        id: "audit-1",
        case: "case-1",
        event_type: "case.created",
        actor_type: "system",
        actor_id: null,
        correlation_id: "corr-1",
        payload: { status: "new" },
        created_at: "2026-03-29T10:00:00Z",
      },
    ]);

    mockedGetCaseArtifacts.mockResolvedValue([
      {
        id: "artifact-1",
        case: "case-1",
        artifact_type: "disclosure",
        filename: "fee-disclosure.pdf",
        mime_type: "application/pdf",
        source_channel: "seeded_demo",
        storage_path: "/tmp/fee-disclosure.pdf",
        sha256_checksum: "abc123",
        parse_status: "parsed",
        parse_error_code: null,
        text_length: 1200,
        uploaded_at: "2026-03-29T10:02:00Z",
      },
    ]);

    mockedGetArtifactSections.mockResolvedValue([
      {
        id: "section-1",
        artifact: "artifact-1",
        section_index: 1,
        heading: "Fees",
        text: "Monthly fee wording appears in small print.",
        page_number: 2,
      },
    ]);
  });

  it("renders claims, assessments, recommendation, artifacts, and audit events", async () => {
    renderWithProviders(<CaseDetailPage />, {
      route: "/cases/case-1",
      path: "/cases/:id",
    });

    expect(await screen.findByText("CDEE-20260329-0001")).toBeInTheDocument();
    expect(screen.getByText("Unclear fee wording complaint")).toBeInTheDocument();

    expect(screen.getByText("Status: needs_review")).toBeInTheDocument();
    expect(screen.getByText("Review: unassigned")).toBeInTheDocument();
    expect(screen.getByText("Priority: high")).toBeInTheDocument();
    expect(screen.getByText("Degraded: yes")).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: "Claims" })).toBeInTheDocument();
    expect(
      screen.getByText("Customer says the monthly fee was unclear."),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", { name: "Assessments" }),
    ).toBeInTheDocument();
    expect(screen.getByText("weak_support")).toBeInTheDocument();
    expect(screen.getByText("Fee wording is ambiguous.")).toBeInTheDocument();

    expect(
      screen.getByRole("heading", { name: "Contradictions" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Script wording conflicts with disclosure."),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", { name: "Recommendation" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Action:/)).toBeInTheDocument();
    expect(
      screen.getByText("Escalate for analyst review because support is weak."),
    ).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: "Artifacts" })).toBeInTheDocument();
    expect(screen.getByText("fee-disclosure.pdf")).toBeInTheDocument();
    expect(
      screen.getByText("No sections found for selected artifact."),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", { name: "Audit Events" }),
    ).toBeInTheDocument();
    expect(screen.getByText("case.created")).toBeInTheDocument();

    await waitFor(() => {
      expect(mockedGetCase).toHaveBeenCalledWith("case-1");
      expect(mockedGetCaseClaims).toHaveBeenCalledWith("case-1");
      expect(mockedGetCaseEvidenceLinks).toHaveBeenCalledWith("case-1");
      expect(mockedGetCaseAssessments).toHaveBeenCalledWith("case-1");
      expect(mockedGetCaseRecommendation).toHaveBeenCalledWith("case-1");
      expect(mockedGetCaseAuditEvents).toHaveBeenCalledWith("case-1");
      expect(mockedGetCaseArtifacts).toHaveBeenCalledWith("case-1");
      expect(mockedGetArtifactSections).toHaveBeenCalledWith("artifact-1");
    });
  });

  it("shows eval linkage when eval ids are present", async () => {
    renderWithProviders(<CaseDetailPage />, {
      route: "/cases/case-1",
      path: "/cases/:id",
    });

    expect(
      await screen.findByRole("heading", { name: "Eval linkage" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Eval case ID:/)).toBeInTheDocument();
    expect(screen.getByText(/Latest eval run ID:/)).toBeInTheDocument();
  });
});