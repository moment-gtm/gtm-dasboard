/** Metric change control (§10.2): log → assess (GTM Lead + Sales Ops) → decide (GTM Lead) → release. */
import { useState } from "react";
import { adminApi, type ChangeRequest } from "@/api/admin";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useAdminMutation, useChangeRequests } from "@/hooks/useAdminData";
import { useRole } from "@/state/role";
import { Field, FormError, inputStyle, Notice } from "./fields";

const LABEL: Record<ChangeRequest["status"], string> = {
  logged: "Logged",
  assessed: "Assessed",
  approved: "Approved",
  rejected: "Rejected",
  released: "Released",
};

function Actions({ cr }: { cr: ChangeRequest }) {
  const role = useRole();
  const [note, setNote] = useState("");
  const assess = useAdminMutation((n: string) => adminApi.assess(cr.id, n));
  const decide = useAdminMutation((a: { d: "approve" | "reject"; n: string }) =>
    adminApi.decide(cr.id, a.d, a.n),
  );
  const release = useAdminMutation(() => adminApi.release(cr.id));
  const mine = cr.assessments.some((a) => a.role === role);
  const needNote = cr.status === "logged" || cr.status === "assessed";
  const error = assess.error ?? decide.error ?? release.error;
  return (
    <div className="flex flex-col gap-2">
      {needNote ? (
        <Field label="Note">
          {(id) => (
            <input
              id={id}
              style={{ ...inputStyle, minWidth: 240 }}
              value={note}
              maxLength={500}
              onChange={(e) => setNote(e.target.value)}
            />
          )}
        </Field>
      ) : null}
      <div className="flex flex-wrap gap-2">
        {needNote ? (
          <button
            type="button"
            className="btn"
            disabled={note.trim().length < 3 || assess.isPending}
            onClick={() => assess.mutate(note)}
            data-testid={`cr-assess-${cr.id}`}
          >
            {mine ? "Update my assessment" : "Add my assessment"}
          </button>
        ) : null}
        {cr.status === "assessed" && role === "gtm_lead" ? (
          <>
            <button
              type="button"
              className="btn"
              disabled={note.trim().length < 3}
              onClick={() => decide.mutate({ d: "approve", n: note })}
              data-testid={`cr-approve-${cr.id}`}
            >
              Approve
            </button>
            <button
              type="button"
              className="btn"
              disabled={note.trim().length < 3}
              onClick={() => decide.mutate({ d: "reject", n: note })}
            >
              Reject
            </button>
          </>
        ) : null}
        {cr.status === "approved" ? (
          <button
            type="button"
            className="btn"
            onClick={() => release.mutate(undefined)}
            data-testid={`cr-release-${cr.id}`}
          >
            Mark as released
          </button>
        ) : null}
      </div>
      <FormError error={error} />
    </div>
  );
}

function LogForm() {
  const log = useAdminMutation(adminApi.logChange);
  const [metric, setMetric] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  return (
    <form
      aria-label="Log a metric change request"
      className="flex flex-wrap items-end gap-3"
      onSubmit={(e) => {
        e.preventDefault();
        log.mutate(
          { metric_id: metric.trim() || null, title, description },
          {
            onSuccess: () => {
              setMetric("");
              setTitle("");
              setDescription("");
            },
          },
        );
      }}
    >
      <Field label="Metric ID (optional)">
        {(id) => (
          <input
            id={id}
            style={{ ...inputStyle, width: 120 }}
            value={metric}
            placeholder="PIP-01"
            onChange={(e) => setMetric(e.target.value.toUpperCase())}
          />
        )}
      </Field>
      <Field label="Title">
        {(id) => (
          <input
            id={id}
            required
            minLength={3}
            maxLength={120}
            style={{ ...inputStyle, minWidth: 220 }}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            data-testid="cr-title"
          />
        )}
      </Field>
      <Field label="What should change and why">
        {(id) => (
          <input
            id={id}
            required
            minLength={3}
            maxLength={1000}
            style={{ ...inputStyle, minWidth: 300 }}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        )}
      </Field>
      <button type="submit" className="btn" disabled={log.isPending} data-testid="cr-submit">
        Log request
      </button>
      <FormError error={log.error} />
    </form>
  );
}

export function ChangeControl() {
  const q = useChangeRequests();
  return (
    <WidgetCard
      title="Metric change control"
      description="Definition changes need both the GTM Lead and Sales Ops to assess, then GTM Lead approval. Approved changes release in the next monthly window."
      testId="widget-change-control"
      isLoading={q.isLoading}
      error={q.error}
      onRetry={() => q.refetch()}
    >
      <div className="flex flex-col gap-4">
        <LogForm />
        {q.data?.length === 0 ? <Notice>No change requests yet.</Notice> : null}
        <ul className="m-0 flex list-none flex-col gap-3 p-0" data-testid="cr-list">
          {q.data?.map((cr) => (
            <li
              key={cr.id}
              className="flex flex-col gap-2 rounded p-3"
              style={{ border: "1px solid var(--grid)" }}
              data-testid={`cr-${cr.id}`}
            >
              <p className="m-0 text-sm font-semibold">
                #{cr.id} {cr.title}
                {cr.metric_id ? ` · ${cr.metric_id}` : ""} ·{" "}
                <span data-testid={`cr-status-${cr.id}`}>{LABEL[cr.status]}</span>
              </p>
              <p className="m-0 text-sm">{cr.description}</p>
              {cr.assessments.map((a) => (
                <p key={a.role} className="m-0 text-xs" style={{ color: "var(--ink-2)" }}>
                  Assessed by {a.role.replace("_", " ")}: {a.note}
                </p>
              ))}
              {cr.release_window ? (
                <p className="m-0 text-xs" style={{ color: "var(--ink-2)" }}>
                  Planned release window: {cr.release_window}
                </p>
              ) : null}
              {cr.status !== "rejected" && cr.status !== "released" ? <Actions cr={cr} /> : null}
            </li>
          ))}
        </ul>
      </div>
    </WidgetCard>
  );
}
