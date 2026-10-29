// Anteater Racing addition: pictures in a part's Notes. Images are stored in the library
// (appdata/note-images/) and the Notes text refers to them as [image: <name>].
import { ImagePlus, StickyNote, X } from "lucide-react";
import { useRef, useState } from "react";
import { api, assetURL } from "./api";

const IMAGE = /\s*\[image:\s*([0-9a-f]{16}\.(?:png|jpg|gif|webp))\]/g;

export function noteImages(notes: string) {
  return [...(notes || "").matchAll(IMAGE)].map((m) => m[1]);
}

function noteText(notes: string) {
  return (notes || "").replace(IMAGE, "").replace(/[;\s]+$/, "").trim();
}

const imageURL = (name: string) => assetURL("note-image", { name });

function base64(file: Blob) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",", 2)[1]);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

// Notes field in the add/edit dialog: text, plus Add image (or paste a screenshot)
export function NotesField({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const picker = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const images = noteImages(value);

  async function add(files: Blob[]) {
    if (!files.length) return;
    setBusy(true);
    setError("");
    let notes = value || "";
    try {
      for (const file of files) {
        const { name } = await api<{ name: string }>("note-image", { data: await base64(file) });
        if (!noteImages(notes).includes(name))
          notes = (notes.trim() ? notes.trim().replace(/;?$/, "; ") : "") + `[image: ${name}]`;
      }
    } catch (e) {
      setError(String(e));
    }
    onChange(notes);
    setBusy(false);
  }

  function remove(name: string) {
    onChange(
      (value || "")
        .replace(new RegExp(`;?\\s*\\[image:\\s*${name.replace(".", "\\.")}\\]`), "")
        .trim(),
    );
  }

  return (
    <div className="field notes-field">
      <span>Notes</span>
      <input
        type="text"
        value={value || ""}
        placeholder="Optional. Paste a screenshot here, or use Add image"
        onChange={(e) => onChange(e.target.value)}
        onPaste={(e) => {
          const files = [...e.clipboardData.files].filter((f) => f.type.startsWith("image/"));
          if (files.length) {
            e.preventDefault();
            add(files);
          }
        }}
      />
      <div className="note-images">
        {images.map((name) => (
          <figure key={name}>
            <a href={imageURL(name)} target="_blank" rel="noreferrer">
              <img src={imageURL(name)} alt="Note image" />
            </a>
            <button type="button" className="icon" title="Remove image" onClick={() => remove(name)}>
              <X size={14} />
            </button>
          </figure>
        ))}
        <button type="button" className="secondary" disabled={busy} onClick={() => picker.current?.click()}>
          <ImagePlus size={16} /> {busy ? "Adding…" : "Add image"}
        </button>
        <input
          ref={picker}
          type="file"
          accept="image/png,image/jpeg,image/gif,image/webp"
          multiple
          hidden
          onChange={(e) => {
            add([...(e.target.files || [])]);
            e.target.value = "";
          }}
        />
      </div>
      {error && <small className="error-text">{error}</small>}
    </div>
  );
}

// Notes on the part's record (shown when you click a part)
export function NotesView({ notes }: { notes: string }) {
  const text = noteText(notes);
  const images = noteImages(notes);
  if (!text && !images.length) return null;
  return (
    <section className="notes-view">
      <h3><StickyNote size={16} /> Notes</h3>
      {text && <p>{text}</p>}
      {images.length > 0 && (
        <div className="note-images">
          {images.map((name) => (
            <a key={name} href={imageURL(name)} target="_blank" rel="noreferrer" title="Open full size">
              <img src={imageURL(name)} alt="Note image" />
            </a>
          ))}
        </div>
      )}
    </section>
  );
}
