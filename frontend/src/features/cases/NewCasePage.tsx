import { useState } from "react";

export function NewCasePage() {
  const [title, setTitle] = useState("");
  const [caseType, setCaseType] = useState("complaint_review");
  const [priority, setPriority] = useState("medium");

  return (
    <section>
      <div className="page-header">
        <div>
          <h2>New Case</h2>
          <p>Create a new review case and upload related artefacts.</p>
        </div>
      </div>

      <div className="panel">
        <form className="stack">
          <label htmlFor="title">Title</label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Complaint review for unclear monthly fee wording"
          />

          <label htmlFor="case-type">Case type</label>
          <select
            id="case-type"
            value={caseType}
            onChange={(event) => setCaseType(event.target.value)}
          >
            <option value="complaint_review">complaint_review</option>
            <option value="support_review">support_review</option>
            <option value="disclosure_review">disclosure_review</option>
          </select>

          <label htmlFor="priority">Priority</label>
          <select
            id="priority"
            value={priority}
            onChange={(event) => setPriority(event.target.value)}
          >
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
            <option value="critical">critical</option>
          </select>

          <label htmlFor="complaint-file">Complaint file</label>
          <input id="complaint-file" type="file" />

          <label htmlFor="related-files">Related artefacts</label>
          <input id="related-files" type="file" multiple />

          <button type="submit" disabled>
            Create case
          </button>

          <p>Intake form UI placeholder. Connect submission later if needed.</p>
        </form>
      </div>
    </section>
  );
}