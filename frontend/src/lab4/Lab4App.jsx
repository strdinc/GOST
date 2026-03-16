import { useMemo, useState } from "react";
import { TraceNode, parseFilename } from "../shared/trace-ui.jsx";

function Lab4App() {
  const [sourceBytes, setSourceBytes] = useState("55 65 51 33 4D 95 59 C7 93 8C BD E3 D6 AB 2F 79");
  const [aMapping, setAMapping] = useState("3 13 14 11 4 10 15 9 1 0 12 2 5 8 6 7");
  const [bMapping, setBMapping] = useState("15 7 9 0 6 12 2 14 10 4 8 1 11 3 13 5");
  const [actions, setActions] = useState([]);
  const [summaryHtml, setSummaryHtml] = useState("");
  const [checksHtml, setChecksHtml] = useState("");
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [error, setError] = useState("");

  const payload = { sourceBytes, aMapping, bMapping };

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
      const response = await fetch("/api/lab4/run", {
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
      setError(err.message || "Не удалось выполнить развертку ключа.");
    } finally {
      setLoading(false);
    }
  }

  async function downloadPdf() {
    setPdfLoading(true);
    setError("");

    try {
      const response = await fetch("/api/lab4/report/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || "Не удалось сформировать PDF.");
      }

      const blob = await response.blob();
      const filename = parseFilename(response.headers.get("content-disposition"), "gost-lab4-report.pdf");
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
      setPdfLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="hero panel">
        <p className="eyebrow">LAB 4</p>
        <h1>Развертка мастер-ключа «Кузнечик»</h1>
        <p className="subtitle">Сайт для поддомена `lab4.gost.strdinc.space`.</p>
      </section>

      <section className="panel">
        <p className="subtitle">
          В этой лабораторной мастер-ключ строится как `K = a || b`, где `a` и `b`
          собираются из `sourceBytes` по двум отображениям.
        </p>
      </section>

      <section className="panel">
        <form onSubmit={runTrace} className="input-grid">
          <label>
            Исходные байты b0..b15 (16 hex):
            <textarea value={sourceBytes} onChange={(e) => setSourceBytes(e.target.value)} rows={2} required />
          </label>
          <label>
            Индексы для a / K1 (16 чисел 0..15):
            <input value={aMapping} onChange={(e) => setAMapping(e.target.value)} required />
          </label>
          <label>
            Индексы для b / K2 (16 чисел 0..15):
            <input value={bMapping} onChange={(e) => setBMapping(e.target.value)} required />
          </label>
          <button type="submit" disabled={loading || pdfLoading}>
            {loading ? "Считаю..." : "Построить развертку"}
          </button>
        </form>
      </section>

      {error && <section className="panel error">{error}</section>}

      {summaryHtml && (
        <section className="panel">
          <h2>Раундовые ключи K1..K10</h2>
          <div className="table-wrap" dangerouslySetInnerHTML={{ __html: summaryHtml }} />
          {checksHtml && (
            <>
              <h3>Проверки</h3>
              <div className="table-wrap" dangerouslySetInnerHTML={{ __html: checksHtml }} />
            </>
          )}
          <div className="summary-actions">
            <button type="button" className="secondary" onClick={downloadPdf} disabled={pdfLoading || loading}>
              {pdfLoading ? "Готовлю PDF..." : "Скачать в PDF"}
            </button>
          </div>
        </section>
      )}

      {actions.length > 0 && (
        <section className="panel">
          <div className="meta">
            <h2>Шаги развертки</h2>
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

export default Lab4App;
