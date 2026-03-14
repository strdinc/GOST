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

function parseFilename(contentDisposition, fallbackName = "gost-full-report.pdf") {
  if (!contentDisposition) {
    return fallbackName;
  }
  const match = contentDisposition.match(/filename\*?=(?:UTF-8''|\")?([^\";]+)/i);
  if (!match) {
    return fallbackName;
  }
  return decodeURIComponent(match[1].replace(/\"/g, ""));
}

function App() {
  const [sourceBytes, setSourceBytes] = useState("55 65 51 33 4D 95 59 C7 93 8C BD E3 D6 AB 2F 79");
  const [aMapping, setAMapping] = useState("3 13 14 11 4 10 15 9 1 0 12 2 5 8 6 7");
  const [bMapping, setBMapping] = useState("15 7 9 0 6 12 2 14 10 4 8 1 11 3 13 5");
  const [keyBytes, setKeyBytes] = useState("88 99 AA BB CC DD EE FF 00 11 22 33 44 55 66 77");
  const [actions, setActions] = useState([]);
  const [summaryHtml, setSummaryHtml] = useState("");
  const [checksHtml, setChecksHtml] = useState("");
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [simplePdfLoading, setSimplePdfLoading] = useState(false);
  const [error, setError] = useState("");

  const payload = {
    sourceBytes,
    aMapping,
    bMapping,
    keyBytes,
  };

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
    setChecksHtml("");

    try {
      const response = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Ошибка API");
      }
      setActions(data.actions || []);
      setSummaryHtml(data.summaryTableHtml || "");
      setChecksHtml(data.checksTableHtml || "");
    } catch (err) {
      setError(err.message || "Не удалось выполнить вычисления.");
    } finally {
      setLoading(false);
    }
  }

  async function downloadReport(endpoint, fallbackName, setBusy) {
    setBusy(true);
    setError("");

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || "Не удалось сформировать PDF.");
      }

      const blob = await response.blob();
      const filename = parseFilename(response.headers.get("content-disposition"), fallbackName);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message || "Не удалось скачать PDF.");
    } finally {
      setBusy(false);
    }
  }

  function downloadPdf() {
    return downloadReport("/api/report/pdf", "gost-full-report.pdf", setPdfLoading);
  }

  function downloadSimplePdf() {
    return downloadReport("/api/report/simple-pdf", "gost-simple-report.pdf", setSimplePdfLoading);
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
          <button type="submit" disabled={loading || pdfLoading || simplePdfLoading}>
            {loading ? "Считаю..." : "Запустить"}
          </button>
        </form>
      </section>

      {error && <section className="panel error">{error}</section>}

      {summaryHtml && (
        <section className="panel">
          <h2>Финальная сводка</h2>
          <div className="table-wrap" dangerouslySetInnerHTML={{ __html: summaryHtml }} />
          {checksHtml && (
            <>
              <h3>Финальная проверка</h3>
              <div className="table-wrap" dangerouslySetInnerHTML={{ __html: checksHtml }} />
            </>
          )}
          <div className="summary-actions">
            <button type="button" className="secondary" onClick={downloadPdf} disabled={pdfLoading || loading || simplePdfLoading}>
              {pdfLoading ? "Готовлю PDF..." : "Скачать в PDF"}
            </button>
            <button type="button" className="secondary ghost" onClick={downloadSimplePdf} disabled={simplePdfLoading || loading || pdfLoading}>
              {simplePdfLoading ? "Готовлю простой PDF..." : "Скачать простой PDF"}
            </button>
          </div>
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
