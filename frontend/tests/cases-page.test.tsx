import { screen } from "@testing-library/react";
import { vi } from "vitest";

import { CasesPage } from "../src/features/cases/CasesPage";
import { renderWithProviders } from "./test-utils";

vi.mock("../src/api/cases", async () => {
  const actual = await vi.importActual("../src/api/cases");
  return {
    ...actual,
    getCases: vi.fn(),
  };
});

import { getCases } from "../src/api/cases";

const mockedGetCases = vi.mocked(getCases);

describe("CasesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders cases table rows", async () => {
    mockedGetCases.mockResolvedValue([
      {
        id: "case-1",
        reference_code: "CDEE-20260329-0001",
        title: "Unclear fee wording complaint",
        status: "needs_review",
        review_status: "unassigned",
        priority: "high",
        case_type: "complaint_review",
        correlation_id: "corr-1",
        latest_eval_run_id: null,
        eval_case_id: null,
        degraded_mode_active: false,
        created_at: "2026-03-29T10:00:00Z",
        updated_at: "2026-03-29T11:00:00Z",
        summary_snapshot: {},
      },
      {
        id: "case-2",
        reference_code: "CDEE-20260329-0002",
        title: "Provider failure fallback",
        status: "needs_review",
        review_status: "assigned",
        priority: "critical",
        case_type: "support_review",
        correlation_id: "corr-2",
        latest_eval_run_id: "eval-run-2",
        eval_case_id: "eval-case-2",
        degraded_mode_active: true,
        created_at: "2026-03-29T12:00:00Z",
        updated_at: "2026-03-29T13:00:00Z",
        summary_snapshot: {},
      },
    ]);

    renderWithProviders(<CasesPage />, {
      route: "/",
      path: "/",
    });

    expect(await screen.findByRole("heading", { name: "Cases" })).toBeInTheDocument();
    expect(screen.getByText("2 total")).toBeInTheDocument();

    expect(screen.getByText("CDEE-20260329-0001")).toBeInTheDocument();
    expect(screen.getByText("Unclear fee wording complaint")).toBeInTheDocument();
    expect(screen.getByText("complaint_review")).toBeInTheDocument();

    expect(screen.getByText("CDEE-20260329-0002")).toBeInTheDocument();
    expect(screen.getByText("Provider failure fallback")).toBeInTheDocument();
    expect(screen.getByText("support_review")).toBeInTheDocument();
  });

  it("renders empty state when no cases are returned", async () => {
    mockedGetCases.mockResolvedValue([]);

    renderWithProviders(<CasesPage />, {
      route: "/",
      path: "/",
    });

    expect(await screen.findByText("No cases returned.")).toBeInTheDocument();
  });
});