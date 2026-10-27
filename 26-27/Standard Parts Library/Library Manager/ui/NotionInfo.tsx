// Anteater Racing addition: the part's PCB Wiki planning info (who added it, what it replaces).
// The Notion sync writes appdata/notion-info.json, so this needs no Notion access on the PC.
import { History } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "./api";

type Info = {
  row: string;
  url: string;
  addedBy: string[];
  verifier: string[];
  replaces: string;
  boards: string;
  status: string;
};

export function NotionInfo({ partID }: { partID: string }) {
  const [info, setInfo] = useState<Info | null | undefined>(undefined);
  useEffect(() => {
    api<{ info: Info | null }>("notion-info?part=" + encodeURIComponent(partID))
      .then((r) => setInfo(r.info))
      .catch(() => setInfo(null));
  }, [partID]);
  if (info === undefined) return null;
  const row = (label: string, value: string) => (
    <div>
      <dt>{label}</dt>
      <dd>{value || <span className="muted">Not filled in on Notion</span>}</dd>
    </div>
  );
  return (
    <section className="notion-info">
      <h3><History size={16} /> History (from Notion)</h3>
      {info ? (
        <>
          <dl>
            {row("Added by", info.addedBy.join(", "))}
            {row("Replaces", info.replaces)}
            {info.boards && row("Boards", info.boards)}
            {info.verifier.length > 0 && row("Verified by", info.verifier.join(", "))}
          </dl>
          {info.url && (
            <a className="secondary" href={info.url} target="_blank" rel="noreferrer">
              Open "{info.row}" in Notion ↗
            </a>
          )}
        </>
      ) : (
        <p className="muted">
          Not linked to a PCB Wiki row yet. Edit the part and start its Notes with{" "}
          <code>Notion: &lt;Component Name&gt;;</code>, then Save. It shows up here right away.
        </p>
      )}
    </section>
  );
}
