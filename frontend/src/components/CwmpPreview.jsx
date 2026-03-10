import React, { useState, useEffect } from 'react';
import Editor from 'react-simple-code-editor';
import Prism from 'prismjs';
import 'prismjs/themes/prism-tomorrow.css';

const CwmpPreview = ({ xmlPayload }) => {
  const [code, setCode] = useState(xmlPayload || "");
  const [lintStatus, setLintStatus] = useState(null);

  useEffect(() => {
    setCode(xmlPayload || "");
    setLintStatus(null);
  }, [xmlPayload]);

  const handleLint = () => {
    if (!code.trim()) {
      setLintStatus({ type: 'error', message: "XML is empty." });
      return;
    }
    try {
      const parser = new DOMParser();
      const resultDoc = parser.parseFromString(code, "application/xml");
      const errorNode = resultDoc.querySelector("parsererror");
      if (errorNode) {
        setLintStatus({ type: 'error', message: errorNode.textContent || "Invalid XML format." });
      } else {
        setLintStatus({ type: 'success', message: "✨ OK: XML syntax is valid!" });
      }
    } catch (e) {
      setLintStatus({ type: 'error', message: e.message });
    }
  };

  const handleCopy = () => {
    if (!code.trim()) return;
    navigator.clipboard.writeText(code).then(() => {
      setLintStatus({ type: 'success', message: "✨ Copied to clipboard!" });
      setTimeout(() => setLintStatus(null), 3000);
    }).catch(err => {
      setLintStatus({ type: 'error', message: "Failed to copy: " + err });
    });
  };

  const handleClear = () => {
    setCode("");
    setLintStatus(null);
  };

  if (!xmlPayload && !code) return null;

  return (
    <div className="details-panel cwmp-preview" style={{ display: 'flex', flexDirection: 'column', minWidth: '400px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ color: '#89b4fa', margin: 0 }}>Generated CWMP SetParameterValues</h3>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={handleLint} className="btn" style={{ padding: '0.4rem 0.8rem', fontSize: '0.9rem' }}>
            ✓ Lint XML
          </button>
          <button onClick={handleCopy} className="btn" style={{ padding: '0.4rem 0.8rem', fontSize: '0.9rem', backgroundColor: '#a6e3a1', color: '#11111b' }}>
            📋 Copy
          </button>
          <button onClick={handleClear} className="btn" style={{ padding: '0.4rem 0.8rem', fontSize: '0.9rem', backgroundColor: '#f38ba8', color: '#11111b' }}>
            🗑️ Clear
          </button>
        </div>
      </div>

      {lintStatus && (
        <div style={{
          marginBottom: '1rem',
          padding: '0.8rem',
          borderRadius: '4px',
          backgroundColor: lintStatus.type === 'success' ? 'rgba(166, 227, 161, 0.2)' : 'rgba(243, 139, 168, 0.2)',
          color: lintStatus.type === 'success' ? '#a6e3a1' : '#f38ba8',
          border: `1px solid ${lintStatus.type === 'success' ? '#a6e3a1' : '#f38ba8'}`,
          fontSize: '0.9rem',
          whiteSpace: 'pre-wrap'
        }}>
          {lintStatus.message}
        </div>
      )}

      <div className="notepad-view" style={{ flex: 1, padding: 0, overflow: 'auto', backgroundColor: '#1e1e2e', display: 'flex', flexDirection: 'column' }}>
        <Editor
          value={code}
          onValueChange={c => { setCode(c); setLintStatus(null); }}
          highlight={c => Prism.highlight(c, Prism.languages.xml, 'xml')}
          padding={15}
          style={{
            fontFamily: '"BIZ UDGothic", sans-serif',
            fontSize: '9pt',
            flex: 1,
            color: '#cdd6f4',
            outline: 'none'
          }}
        />
      </div>
    </div>
  );
};

export default CwmpPreview;
