// Anteater Racing addition: tag parts with the boards they're on, and view each board's parts.
import { CircuitBoard, Download, Plus, RefreshCw, X } from "lucide-react";
import { useState } from "react";
import { api, Library, Part } from "./api";

export type Board = {
  key: string;
  name: string;
  season: string;
  project: string;
  archived: boolean;
};
export type Usage = Record<string, Record<string, { refs: string; qty: number; source: string }>>;
export type BoardsState = { boards: Board[]; usage: Usage };

const label = (b?: Board) => (b ? `${b.name} · ${b.season}` : "");

export function BoardView({
  board,
  boards,
  library,
  notify,
  onBoards,
  onOpenPart,
}: {
  board: Board;
  boards: BoardsState;
  library: Library;
  notify: (s: string, e?: boolean) => void;
  onBoards: (b: BoardsState) => void;
  onOpenPart: (p: Part) => void;
}) {
  const [busy, setBusy] = useState(false);
  const lines = library.parts
    .filter((p) => boards.usage[p.ID]?.[board.key])
    .map((p) => ({ part: p, ...boards.usage[p.ID][board.key] }))
    .sort((a, b) => a.refs.localeCompare(b.refs, undefined, { numeric: true }));
  const total = lines.reduce((n, l) => n + l.qty, 0);
  const exportCSV = () => {
    const q = (s: string) => `"${String(s ?? "").replaceAll('"', '""')}"`;
    const rows = [
      ["Refs", "Qty", "Manufacturer", "MPN", "Description", "Category", "Datasheet"],
      ...lines.map((l) => [
        l.refs, String(l.qty), l.part.Manufacturer, l.part.MPN, l.part.Description,
        l.part.Category.replace(/^components\//, ""), l.part.Datasheet,
      ]),
    ];
    const blob = new Blob([rows.map((r) => r.map(q).join(",")).join("\r\n")], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${board.name} ${board.season} parts.csv`;
    a.click();
  };
  return (
    <div className="content">
      <div className="page-heading">
        <div>
          <div className="eyebrow">BOARD · {board.season}{board.archived ? " · ARCHIVED" : ""}</div>
          <h1>
            {board.name} <span>{lines.length}</span>
          </h1>
          <p className="muted">
            {total} part{total === 1 ? "" : "s"} placed from the library
            {board.project ? <> · <code>{board.project}</code></> : " · no KiCad project in the repo yet"}
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {board.project && (
            <button
              className="secondary"
              disabled={busy}
              title="Replace this board's tags with what its KiCad schematic contains"
              onClick={async () => {
                if (!window.confirm(
                  `Update ${label(board)} from its KiCad schematic?\n\n` +
                  "This replaces this board's tags with the library parts actually placed in the schematic.",
                )) return;
                setBusy(true);
                try {
                  const r = await api("boards/import", { board: board.key });
                  onBoards(r);
                  notify(
                    `${r.imported} library part placement(s) found` +
                    (r.notInLibrary ? `; ${r.notInLibrary} other symbol(s) aren't library parts yet.` : ".") +
                    " Publish to share.",
                  );
                } catch (e) {
                  notify(String(e), true);
                } finally {
                  setBusy(false);
                }
              }}
            >
              <RefreshCw size={16} /> Update from schematic
            </button>
          )}
          <button className="primary" disabled={!lines.length} onClick={exportCSV}>
            <Download size={16} /> Export CSV
          </button>
        </div>
      </div>
      {lines.length ? (
        <table className="board-table">
          <thead>
            <tr><th>Refs</th><th>Qty</th><th>Part</th><th>Category</th></tr>
          </thead>
          <tbody>
            {lines.map((l) => (
              <tr key={l.part.ID} onClick={() => onOpenPart(l.part)}>
                <td className="mono">{l.refs || "—"}</td>
                <td>{l.qty}</td>
                <td>
                  <strong>{l.part.MPN}</strong>
                  <small>{l.part.Manufacturer} · {l.part.Description}</small>
                </td>
                <td>{l.part.Category.replace(/^components\//, "")}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr><td>Total</td><td>{total}</td><td colSpan={2} /></tr>
          </tfoot>
        </table>
      ) : (
        <div className="info-box">
          <strong>No parts tagged on this board yet</strong>
          <p>
            Open a component and add {board.name} under <em>Used on boards</em>
            {board.project ? ", or click Update from schematic." : "."}
          </p>
        </div>
      )}
    </div>
  );
}

export function BoardTags({
  part,
  boards,
  notify,
  onBoards,
}: {
  part: Part;
  boards: BoardsState;
  notify: (s: string, e?: boolean) => void;
  onBoards: (b: BoardsState) => void;
}) {
  const initial = Object.entries(boards.usage[part.ID] || {}).map(([board, u]) => ({
    board, refs: u.refs, qty: u.qty ? String(u.qty) : "",
  }));
  const [rows, setRows] = useState(initial);
  const [busy, setBusy] = useState(false);
  const dirty = JSON.stringify(rows) !== JSON.stringify(initial);
  const set = (i: number, k: string, v: string) =>
    setRows(rows.map((r, j) => (j === i ? { ...r, [k]: v } : r)));
  return (
    <section className="board-tags">
      <h3><CircuitBoard size={16} /> Used on boards</h3>
      {rows.map((r, i) => (
        <div className="board-tag-row" key={i}>
          <select value={r.board} onChange={(e) => set(i, "board", e.target.value)}>
            <option value="">Choose a board…</option>
            {boards.boards.map((b) => (
              <option key={b.key} value={b.key}>{label(b)}</option>
            ))}
          </select>
          <input
            placeholder="Refs, e.g. R1-R4, R7"
            value={r.refs}
            onChange={(e) => set(i, "refs", e.target.value)}
          />
          <input
            className="qty"
            type="number"
            min={1}
            placeholder="Qty"
            title="Leave blank to count the refs"
            value={r.qty}
            onChange={(e) => set(i, "qty", e.target.value)}
          />
          <button className="text-button" title="Remove" onClick={() => setRows(rows.filter((_, j) => j !== i))}>
            <X size={15} />
          </button>
        </div>
      ))}
      <div style={{ display: "flex", gap: 8 }}>
        <button
          className="secondary"
          onClick={() => setRows([...rows, { board: boards.boards.find((b) => !b.archived)?.key || "", refs: "", qty: "" }])}
        >
          <Plus size={15} /> Add board
        </button>
        {dirty && (
          <button
            className="primary"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                onBoards(await api("boards/usage", { partID: part.ID, entries: rows }));
                notify("Board tags saved. Publish to share.");
              } catch (e) {
                notify(String(e), true);
              } finally {
                setBusy(false);
              }
            }}
          >
            Save board tags
          </button>
        )}
      </div>
    </section>
  );
}

export function addBoardPrompt(
  boards: BoardsState,
  notify: (s: string, e?: boolean) => void,
  onBoards: (b: BoardsState) => void,
) {
  const season = boards.boards[0]?.season || "26-27";
  const name = window.prompt(
    "New board name (e.g. HVB). Boards with a KiCad project in the repo appear automatically.",
  );
  if (!name) return;
  const s = window.prompt("Season", season);
  if (!s) return;
  api("boards/add", { name, season: s })
    .then((r) => {
      onBoards(r);
      notify(`Added ${name} (${s}). Publish to share.`);
    })
    .catch((e) => notify(String(e), true));
}

const CATEGORY_HIDDEN = /^components\/(generic_models|logos|Connector Accessory)(\/|$)/;

export function FilterBar({
  library,
  boards,
  category,
  boardFilter,
  onCategory,
  onBoard,
}: {
  library: Library;
  boards: BoardsState | null;
  category: string;
  boardFilter: string;
  onCategory: (c: string) => void;
  onBoard: (b: string) => void;
}) {
  const [showEmpty, setShowEmpty] = useState(false);
  const parts = library.parts.filter((p) => p.Type !== "accessory");
  const count = (c: string) => parts.filter((p) => p.Category === c || p.Category.startsWith(c + "/")).length;
  const cats = library.categories
    .filter((c) => c !== "components" && !CATEGORY_HIDDEN.test(c) && c.split("/").length === 2)
    .map((c) => ({ c, n: count(c) }));
  const shown = cats.filter((x) => x.n > 0 || showEmpty || x.c === category);
  const empty = cats.filter((x) => x.n === 0).length;
  const season = boards?.boards[0]?.season;
  const current = boards?.boards.filter((b) => b.season === season) || [];
  const older = boards?.boards.filter((b) => b.season !== season) || [];
  const tagged = (key: string) => parts.filter((p) => boards?.usage[p.ID]?.[key]).length;
  return (
    <div className="filter-bar">
      <div className="filter-row">
        <span className="filter-label">Category</span>
        <button className={"chip " + (!category ? "on" : "")} onClick={() => onCategory("")}>
          All <b>{parts.length}</b>
        </button>
        {shown.map(({ c, n }) => (
          <button
            key={c}
            className={"chip " + (category === c ? "on" : "") + (n ? "" : " empty")}
            onClick={() => onCategory(category === c ? "" : c)}
          >
            {c.split("/").pop()} <b>{n}</b>
          </button>
        ))}
        {empty > 0 && (
          <button className="chip ghost" onClick={() => setShowEmpty(!showEmpty)}>
            {showEmpty ? "Hide empty" : `+${empty} empty`}
          </button>
        )}
      </div>
      {boards && (
        <div className="filter-row">
          <span className="filter-label">Board</span>
          <button className={"chip " + (!boardFilter ? "on" : "")} onClick={() => onBoard("")}>
            All boards
          </button>
          {current.map((b) => (
            <button
              key={b.key}
              className={"chip board " + (boardFilter === b.key ? "on" : "")}
              onClick={() => onBoard(boardFilter === b.key ? "" : b.key)}
            >
              <CircuitBoard size={13} /> {b.name} <b>{tagged(b.key)}</b>
            </button>
          ))}
          {older.length > 0 && (
            <select
              className="chip-select"
              value={older.some((b) => b.key === boardFilter) ? boardFilter : ""}
              onChange={(e) => onBoard(e.target.value)}
            >
              <option value="">Older seasons…</option>
              {older.map((b) => (
                <option key={b.key} value={b.key}>{label(b)}</option>
              ))}
            </select>
          )}
        </div>
      )}
    </div>
  );
}

export function BoardsOverview({
  boards,
  library,
  showOld,
  onToggleOld,
  onOpen,
  onAdd,
}: {
  boards: BoardsState;
  library: Library;
  showOld: boolean;
  onToggleOld: () => void;
  onOpen: (key: string) => void;
  onAdd: () => void;
}) {
  const season = boards.boards[0]?.season;
  const list = boards.boards.filter((b) => showOld || b.season === season);
  const stats = (key: string) => {
    const lines = library.parts.filter((p) => boards.usage[p.ID]?.[key]);
    return { parts: lines.length, qty: lines.reduce((n, p) => n + boards.usage[p.ID][key].qty, 0) };
  };
  return (
    <div className="content">
      <div className="page-heading">
        <div>
          <div className="eyebrow">SEASON {season}</div>
          <h1>Boards <span className="count">{list.length}</span></h1>
          <p>Every board in the repo. Open one to see its parts, refs and quantities.</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {boards.boards.some((b) => b.season !== season) && (
            <button className="secondary" onClick={onToggleOld}>
              {showOld ? "Hide older seasons" : "Show older seasons"}
            </button>
          )}
          <button className="primary" onClick={onAdd}>
            <Plus size={16} /> Add board
          </button>
        </div>
      </div>
      <div className="board-grid">
        {list.map((b) => {
          const s = stats(b.key);
          return (
            <button key={b.key} className={"board-card" + (b.archived ? " archived" : "")} onClick={() => onOpen(b.key)}>
              <div className="board-card-top">
                <CircuitBoard size={20} />
                <span className="season">{b.season}</span>
              </div>
              <strong>{b.name}</strong>
              <span className="board-card-stats">
                {s.parts} part{s.parts === 1 ? "" : "s"} · {s.qty} placed
              </span>
              <small>{b.project ? b.project.split("/").slice(1).join("/") : "No KiCad project yet"}</small>
            </button>
          );
        })}
      </div>
    </div>
  );
}
