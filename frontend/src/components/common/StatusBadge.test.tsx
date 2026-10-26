import { render, screen } from "@testing-library/react";
import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it.each([
    ["on_track", "On track"],
    ["watch", "Watch"],
    ["off_track", "Off track"],
  ] as const)("renders %s as text + icon, never colour alone", (status, label) => {
    const { container } = render(<StatusBadge status={status} basis="94% of plan pace" />);
    expect(screen.getByText(label)).toBeInTheDocument();
    expect(container.querySelector("svg")).not.toBeNull();
    expect(screen.getByTestId("status-badge")).toHaveAttribute("data-status", status);
  });

  it("renders nothing without a status", () => {
    const { container } = render(<StatusBadge status={null} />);
    expect(container.firstChild).toBeNull();
  });
});
