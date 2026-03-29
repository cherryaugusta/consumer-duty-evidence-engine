import { screen } from "@testing-library/react";
import { vi } from "vitest";

import { ReviewQueuePage } from "../src/features/reviews/ReviewQueuePage";
import { renderWithProviders } from "./test-utils";

vi.mock("../src/api/reviewTasks", () => ({
  fetchReviewTasks: vi.fn(),
}));

import { fetchReviewTasks } from "../src/api/reviewTasks";

const mockedFetchReviewTasks = vi.mocked(fetchReviewTasks);

describe("ReviewQueuePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders queue stats and review task rows", async () => {
    mockedFetchReviewTasks.mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: "task-1",
          queue_name: "contradictions",
          assigned_to: null,
          status: "unassigned",
          reason_code: "contradiction",
          sla_due_at: "2026-03-30T10:00:00Z",
          created_at: "2026-03-29T10:00:00Z",
          updated_at: "2026-03-29T10:15:00Z",
          case: {
            id: "case-1",
            reference_code: "CDEE-20260329-0001",
            title: "Contradictory support script",
            status: "needs_review",
            review_status: "unassigned",
            priority: "high",
            case_type: "support_review",
            degraded_mode_active: false,
            created_at: "2026-03-29T09:00:00Z",
            updated_at: "2026-03-29T10:00:00Z",
          },
          actions: [],
        },
        {
          id: "task-2",
          queue_name: "fallback",
          assigned_to: {
            id: 7,
            username: "analyst_1",
            email: "analyst_1@example.com",
            first_name: "Analyst",
            last_name: "One",
          },
          status: "assigned",
          reason_code: "model_unavailable",
          sla_due_at: "2026-03-30T12:00:00Z",
          created_at: "2026-03-29T11:00:00Z",
          updated_at: "2026-03-29T11:05:00Z",
          case: {
            id: "case-2",
            reference_code: "CDEE-20260329-0002",
            title: "Provider failure fallback",
            status: "needs_review",
            review_status: "assigned",
            priority: "critical",
            case_type: "complaint_review",
            degraded_mode_active: true,
            created_at: "2026-03-29T10:30:00Z",
            updated_at: "2026-03-29T11:00:00Z",
          },
          actions: [],
        },
      ],
    });

    renderWithProviders(<ReviewQueuePage />, {
      route: "/review-tasks",
      path: "/review-tasks",
    });

    expect(await screen.findByText("Total review tasks")).toBeInTheDocument();
    expect(screen.getByText("Visible on page")).toBeInTheDocument();

    expect(screen.getByText("CDEE-20260329-0001")).toBeInTheDocument();
    expect(screen.getByText("Contradictory support script")).toBeInTheDocument();
    expect(screen.getByText("contradictions")).toBeInTheDocument();
    expect(screen.getByText("contradiction")).toBeInTheDocument();
    expect(screen.getByText("Unassigned")).toBeInTheDocument();

    expect(screen.getByText("CDEE-20260329-0002")).toBeInTheDocument();
    expect(screen.getByText("Provider failure fallback")).toBeInTheDocument();
    expect(screen.getByText("fallback")).toBeInTheDocument();
    expect(screen.getByText("model_unavailable")).toBeInTheDocument();
    expect(screen.getByText("Analyst One")).toBeInTheDocument();
  });

  it("renders empty state when no review tasks exist", async () => {
    mockedFetchReviewTasks.mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: [],
    });

    renderWithProviders(<ReviewQueuePage />, {
      route: "/review-tasks",
      path: "/review-tasks",
    });

    expect(await screen.findByText("No review tasks found.")).toBeInTheDocument();
  });
});