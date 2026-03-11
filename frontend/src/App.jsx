import { useMemo, useState } from "react";
import "./App.css";

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

function App() {
  const [sourceBytes, setSourceBytes] = useState("55 65 51 33 4D 95 59 C7 93 8C BD E3 D6 AB 2F 79");
  const [aMapping, setAMapping] = useState("3 13 14 11 4 10 15 9 1 0 12 2 5 8 6 7");
  const [bMapping, setBMapping] = useState("15 7 9 0 6 12 2 14 10 4 8 1 11 3 13 5");
  const [keyBytes, setKeyBytes] = useState("88 99 AA BB CC DD EE FF 00 11 22 33 44 55 66 77");
  const [actions, setActions] = useState([]);
  const [summaryHtml, setSummaryHtml] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const stats = useMemo(() => {
    const top = actions.length;
    const nested = actions.reduce((acc, action) => acc + (action.steps?.length || 0), 0);
    return { top, nested };
  }, [actions]);

  async function runTrace(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setActions([]);
    setSummaryHtml("");

    try {
      const response = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sourceBytes, aMapping, bMapping, keyBytes }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Ошибка API");
      }
      setActions(data.actions || []);
      setSummaryHtml(data.summaryTableHtml || "");
    } catch (err) {
      setError(err.message || "Не удалось выполнить вычисления.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="hero panel">
        <p className="eyebrow">KUZNYECHIK WEB</p>
      </section>

      <section className="panel">
        <form onSubmit={runTrace} className="input-grid">
          <label>
            Исходные байты b0..b15 (16 hex):
            <textarea value={sourceBytes} onChange={(e) => setSourceBytes(e.target.value)} rows={2} required />
          </label>
          <label>
            Индексы для a (16 чисел 0..15):
            <input value={aMapping} onChange={(e) => setAMapping(e.target.value)} required />
          </label>
          <label>
            Индексы для b (16 чисел 0..15):
            <input value={bMapping} onChange={(e) => setBMapping(e.target.value)} required />
          </label>
          <label>
            Ключ k (16 hex):
            <textarea value={keyBytes} onChange={(e) => setKeyBytes(e.target.value)} rows={2} required />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? "Считаю..." : "Запустить"}
          </button>
        </form>
      </section>

      {error && <section className="panel error">{error}</section>}

      {summaryHtml && (
        <section className="panel">
          <h2>Финальная сводка</h2>
          <div className="table-wrap" dangerouslySetInnerHTML={{ __html: summaryHtml }} />
        </section>
      )}

      {actions.length > 0 && (
        <section className="panel">
          <div className="meta">
            <h2>Действия</h2>
            <div className="chips">
              <span className="chip">Верхний уровень: {stats.top}</span>
              <span className="chip">Вложенные шаги: {stats.nested}</span>
            </div>
          </div>
          <div className="trace-list">
            {actions.map((action, idx) => (
              <TraceNode key={`${idx + 1}-${action.title}`} item={action} path={`${idx + 1}`} />
            ))}
          </div>
        </section>
      )}
    </main>
  );
}

export default App;
