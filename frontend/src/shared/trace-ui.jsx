function HtmlBlock({ block }) {
  return (
    <div
      className={`block block-${block.type}`}
      dangerouslySetInnerHTML={{ __html: block.html }}
    />
  );
}

function TraceNode({ item, path, level = 0 }) {
  const hasSteps = Array.isArray(item.steps) && item.steps.length > 0;
  return (
    <details className={`trace-node level-${level}`} open={level === 0}>
      <summary>
        <span className="badge">{path}</span>
        <span>{item.title}</span>
      </summary>
      <div className="trace-body">
        <div className="blocks">
          {(item.blocks || []).map((block, idx) => (
            <HtmlBlock key={`${path}-block-${idx}`} block={block} />
          ))}
        </div>
        {hasSteps && (
          <div className="children">
            {item.steps.map((child, idx) => (
              <TraceNode
                key={`${path}-${idx + 1}-${child.title}`}
                item={child}
                path={`${path}.${idx + 1}`}
                level={level + 1}
              />
            ))}
          </div>
        )}
      </div>
    </details>
  );
}

function parseFilename(contentDisposition, fallbackName) {
  if (!contentDisposition) {
    return fallbackName;
  }
  const match = contentDisposition.match(/filename\*?=(?:UTF-8''|\")?([^\";]+)/i);
  if (!match) {
    return fallbackName;
  }
  return decodeURIComponent(match[1].replace(/\"/g, ""));
}

export { TraceNode, parseFilename };
