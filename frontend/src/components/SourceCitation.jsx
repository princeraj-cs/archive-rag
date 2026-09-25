import { FileText, ChevronDown } from "lucide-react";

export default function SourceCitation({ sources = [] }) {
  if (!sources.length) return null;

  return (
    <details className="sources">
      <summary>
        <span>
          <FileText size={15} /> {sources.length} source
          {sources.length === 1 ? "" : "s"}
        </span>
        <ChevronDown size={15} />
      </summary>
      <div className="source-list">
        {sources.map((source, index) => (
          <div className="source-item" key={`${source.source}-${index}`}>
            <div className="source-heading">
              {source.url ? (
                <a href={source.url} target="_blank" rel="noreferrer">
                  {source.source}
                </a>
              ) : (
                <strong>{source.source.split(/[\\/]/).pop()}</strong>
              )}
              {source.page ? <span>Page {source.page}</span> : null}
            </div>
            <p className="source-excerpt">{source.content}</p>
          </div>
        ))}
      </div>
    </details>
  );
}
