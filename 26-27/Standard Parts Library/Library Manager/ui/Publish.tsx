// Anteater Racing addition: commit + push library changes from the manager.
import { CloudUpload, Mail, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { api, Library } from "./api";

type Status = {
  branch: string;
  upstream: string;
  user: string;
  dirty: boolean;
  ahead: number;
  behind: number;
  added: string[];
  edited: string[];
  removed: string[];
  parts: string[];
};

export function Publish({
  library,
  notify,
  onLibrary,
}: {
  library: Library;
  notify: (s: string, e?: boolean) => void;
  onLibrary: (l: Library) => void;
}) {
  const [status, setStatus] = useState<Status | null>(null),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false),
    [conflict, setConflict] = useState<any>(null);
  const load = () =>
    api<Status>("publish-status")
      .then((s) => {
        setStatus(s);
        setError("");
        if (!message) setMessage(suggest(s));
      })
      .catch((e) => setError(String(e)));
  useEffect(() => {
    load();
  }, [library]);
  const nothing = status && !status.dirty && status.ahead === 0 && !status.behind;
  const onlyDownload = status && !status.dirty && status.ahead === 0 && status.behind > 0;
  const publish = async (prefer?: "mine" | "theirs") => {
    setBusy(true);
    setConflict(null);
    try {
      const r = await api("publish", { message, prefer });
      if (r.library) onLibrary(r.library);
      if (r.conflict) {
        setConflict(r);
        notify(r.message, true);
      } else {
        notify(
          r.merged && r.pushed
            ? r.message + " Teammates' changes were merged in too."
            : r.message,
        );
        setMessage("");
      }
    } catch (e) {
      notify(String(e), true);
    } finally {
      setBusy(false);
      load();
    }
  };
  return (
    <div className="content narrow">
      <div className="eyebrow">SHARE WITH THE TEAM</div>
      <h1>Publish to GitHub</h1>
      <p className="muted">
        Sends your library changes to the team repository. Notion's PCB Wiki
        and board BOMs update automatically a few minutes later.
      </p>
      {error && <div className="info-box"><strong>Can't publish yet</strong><p>{error}</p></div>}
      {status && (
        <section className="settings-card">
          <h3>Your changes</h3>
          {nothing ? (
            <p>Everything is published and you have everyone's latest parts.</p>
          ) : (
            <ul>
              {status.added.map((p) => <li key={"a" + p}>Added {p}</li>)}
              {status.edited.map((p) => <li key={"e" + p}>Edited {p}</li>)}
              {status.removed.map((p) => <li key={"r" + p}>Removed {p}</li>)}
              {status.parts.map((p) => <li key={"f" + p}>Updated files of {p}</li>)}
              {status.behind > 0 && (
                <li>
                  {status.behind} update{status.behind === 1 ? "" : "s"} from teammates to download
                </li>
              )}
              {status.ahead > 0 && (
                <li>{status.ahead} saved commit(s) waiting to be pushed</li>
              )}
              {status.dirty &&
                !status.added.length && !status.edited.length &&
                !status.removed.length && !status.parts.length && (
                  <li>Library index files changed</li>
                )}
            </ul>
          )}
          <p className="muted">
            Publishing as <strong>{status.user || "(no git name set)"}</strong>{" "}
            on <code>{status.branch}</code>
          </p>
          <label>
            Describe the change
            <input
              type="text"
              value={message}
              placeholder="e.g. Add Molex Mini-Fit Jr 4-pos header"
              onChange={(e) => setMessage(e.target.value)}
            />
          </label>
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button
              className="primary"
              disabled={busy || !!nothing}
              onClick={() => publish()}
            >
              <CloudUpload size={17} />
              {busy ? (onlyDownload ? "Updating…" : "Publishing…") : onlyDownload ? "Get latest" : "Publish"}
            </button>
            <button className="secondary" disabled={busy} onClick={load}>
              <RefreshCw size={17} />
              Refresh
            </button>
          </div>
        </section>
      )}
      {conflict && (
        <section className="settings-card">
          <h3>Someone else changed the same part</h3>
          <p>{conflict.message}</p>
          <p>
            Conflicting: <strong>{conflict.parts.join(", ")}</strong>
          </p>
          {conflict.authors.map((a: any) => (
            <div className="info-box" key={a.email}>
              <strong>{a.name}</strong>
              <p className="mono">{a.commits.join(" · ")}</p>
              <a
                className="secondary"
                href={
                  "mailto:" + a.email +
                  "?subject=" + encodeURIComponent("Parts library conflict: " + conflict.parts.join(", ")) +
                  "&body=" + encodeURIComponent(
                    `Hi ${a.name},\n\nWe both changed ${conflict.parts.join(", ")} in the Anteater parts library ` +
                    `(your commit ${a.commits[0]}). Can we agree which version to keep?\n\nThanks,\n${status?.user || ""}`,
                  )
                }
              >
                <Mail size={16} /> Email {a.name.split(" ")[0]}
              </a>
            </div>
          ))}
          <p className="muted">
            Talk to them first. Once you've agreed which version is right:
          </p>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="primary" disabled={busy} onClick={() => publish("mine")}>
              Keep my version
            </button>
            <button className="secondary" disabled={busy} onClick={() => publish("theirs")}>
              Keep {conflict.authors.map((a: any) => a.name.split(" ")[0]).join(" / ") || "their"}'s version
            </button>
          </div>
        </section>
      )}
    </div>
  );
}

function suggest(s: Status) {
  const bits = [
    ...s.added.map((p) => "Add " + p),
    ...s.edited.map((p) => "Update " + p),
    ...s.removed.map((p) => "Remove " + p),
  ];
  return bits.length ? bits.join(", ").slice(0, 120) : "";
}
