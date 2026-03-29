import { fireEvent, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { ReviewTaskDetailPage } from "../src/features/reviews/ReviewTaskDetailPage";
import { renderWithProviders } from "./test-utils";

vi.mock("../src/api/reviewTasks", () => ({
  fetchReviewTask: vi.fn(),
  assignReviewTask: vi.fn(),
  approveReviewTask: vi.fn(),
  escalateReviewTask: vi.fn(),
  overrideReviewTask: vi.fn(),
}));

import {
  approveReviewTask,
  assignReviewTask,
  escalateReviewTask,
  fetchReviewTask,
  overrideReviewTask,
} from "../src/api/reviewTasks";

const mockedFetchReviewTask = vi.mocked(fetchReviewTask);
const mockedAssignReviewTask = vi.mocked(assignReviewTask);
const mockedApproveReviewTask = vi.mocked(approveReviewTask);
const mockedEscalateReviewTask = vi.mocked(escalateReviewTask);
const mockedOverrideReviewTask = vi.mocked(overrideReviewTask);

function buildTask() {
  return {
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
      degraded_mode_active: true,
      created_at: "2026-03-29T09:00:00Z",
      updated_at: "2026-03-29T10:00:00Z",
    },
    actions: [
      {
        id: "action-1",
        review_task: "task-1",
        reviewer: {
          id: 9,
          username: "analyst_2",
          email: "analyst_2@example.com",
          first_name: "Analyst",
          last_name: "Two",
        },
        action_type: "assign",
        old_value: null,
        new_value: null,
        comment: "Picked up for review.",
        override_reason_code: null,
        created_at: "2026-03-29T10:20:00Z",
      },
    ],
  };
}

describe("ReviewTaskDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedFetchReviewTask.mockResolvedValue(buildTask());
    mockedAssignReviewTask.mockResolvedValue(buildTask());
    mockedApproveReviewTask.mockResolvedValue(buildTask());
    mockedEscalateReviewTask.mockResolvedValue(buildTask());
    mockedOverrideReviewTask.mockResolvedValue(buildTask());
  });

  it("renders task detail, linked case summary, and reviewer actions", async () => {
    renderWithProviders(<ReviewTaskDetailPage />, {
      route: "/review-tasks/task-1",
      path: "/review-tasks/:id",
    });

    expect(
      await screen.findByRole("heading", { name: "Review Task CDEE-20260329-0001" }),
    ).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: "Task summary" })).toBeInTheDocument();
    expect(screen.getByText("contradictions")).toBeInTheDocument();
    expect(screen.getByText("contradiction")).toBeInTheDocument();

    expect(
      screen.getByRole("heading", { name: "Linked case summary" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Contradictory support script")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();

    expect(
      screen.getByRole("heading", { name: "Reviewer actions" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Picked up for review.")).toBeInTheDocument();
    expect(screen.getByText("Analyst Two")).toBeInTheDocument();
  });

  it("validates approval comment before calling approve api", async () => {
    renderWithProviders(<ReviewTaskDetailPage />, {
      route: "/review-tasks/task-1",
      path: "/review-tasks/:id",
    });

    expect(
      await screen.findByRole("heading", { name: "Review Task CDEE-20260329-0001" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Approve task" }));

    expect(await screen.findByText("Approve action failed.")).toBeInTheDocument();
    expect(screen.getByText("Approval comment is required.")).toBeInTheDocument();
    expect(mockedApproveReviewTask).not.toHaveBeenCalled();
  });

  it("validates override fields before calling override api", async () => {
    renderWithProviders(<ReviewTaskDetailPage />, {
      route: "/review-tasks/task-1",
      path: "/review-tasks/:id",
    });

    expect(
      await screen.findByRole("heading", { name: "Review Task CDEE-20260329-0001" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Override task" }));

    expect(await screen.findByText("Override action failed.")).toBeInTheDocument();
    expect(screen.getByText("Override reason code is required.")).toBeInTheDocument();
    expect(mockedOverrideReviewTask).not.toHaveBeenCalled();
  });

  it("submits override when required fields are present", async () => {
    renderWithProviders(<ReviewTaskDetailPage />, {
      route: "/review-tasks/task-1",
      path: "/review-tasks/:id",
    });

    expect(
      await screen.findByRole("heading", { name: "Review Task CDEE-20260329-0001" }),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Override reason code"), {
      target: { value: "analyst_override" },
    });

    fireEvent.change(screen.getByLabelText("Override comment"), {
      target: { value: "Human review found stronger support than the model." },
    });

    fireEvent.change(screen.getByLabelText("Override recommended action"), {
      target: { value: "approve" },
    });

    fireEvent.change(screen.getByLabelText("Override recommended priority"), {
      target: { value: "medium" },
    });

    fireEvent.change(screen.getByLabelText("Override executive summary"), {
      target: { value: "Override to approve after manual validation." },
    });

    fireEvent.click(screen.getByRole("button", { name: "Override task" }));

    await waitFor(() => {
      expect(mockedOverrideReviewTask).toHaveBeenCalledWith("task-1", {
        recommended_action: "approve",
        override_reason_code: "analyst_override",
        comment: "Human review found stronger support than the model.",
        recommended_priority: "medium",
        executive_summary: "Override to approve after manual validation.",
      });
    });

    expect(
      await screen.findByText("Review task overridden successfully."),
    ).toBeInTheDocument();
  });
});