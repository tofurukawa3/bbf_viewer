import React, { useState, useEffect } from 'react';

const Editor = ({ selectedNode, selectedPath, onGenerateEdit, viewMode }) => {
  const [editValue, setEditValue] = useState("");
  const [listInstanceI, setListInstanceI] = useState("");
  const [validationError, setValidationError] = useState("");

  // Reset input when selection changes
  useEffect(() => {
    setEditValue("");
    setListInstanceI("");
    setValidationError("");
  }, [selectedPath]);

  if (!selectedNode) {
    return (
      <div className="details-panel">
        <h2>Details</h2>
        <p style={{ color: '#a6adc8' }}>Select a node from the tree to view its details.</p>
      </div>
    );
  }

  const isWritable = selectedNode.node_type === 'parameter' && selectedNode.access === 'readWrite';
  const showEditor = isWritable && viewMode === 'edit';

  const validateInput = (val) => {
    // 1. Basic Type Validation
    const baseType = selectedNode.data_type;
    if (baseType && baseType.toLowerCase().includes('int')) {
      if (isNaN(val) || val.trim() === '') {
        return "Must be a valid integer.";
      }
      if (baseType === 'unsignedInt' && parseInt(val, 10) < 0) {
        return "Must be an unsigned integer (>= 0).";
      }
    }
    if (baseType === 'boolean') {
      const b = val.trim().toLowerCase();
      if (b !== 'true' && b !== 'false' && b !== '1' && b !== '0') {
        return "Must be a boolean (true/false or 1/0).";
      }
    }

    // 2. Detailed Constraints Validation
    const detailed = selectedNode.detailed_type;
    if (detailed) {
      // Length / Max Length
      const maxLenMatch = detailed.match(/max_length:\s*(\d+)/);
      if (maxLenMatch) {
        if (val.length > parseInt(maxLenMatch[1], 10)) {
          return `Exceeds max length of ${maxLenMatch[1]} characters.`;
        }
      }
      const lenMatch = detailed.match(/length:\s*(\d+)-(\d+)/);
      if (lenMatch) {
         const minL = parseInt(lenMatch[1], 10);
         const maxL = parseInt(lenMatch[2], 10);
         if (val.length < minL || val.length > maxL) {
           return `Length must be between ${minL} and ${maxL} characters.`;
         }
      }
      
      // Range
      const rangeMatch = detailed.match(/range:\s*\[([^,]+),\s*([^\]]+)\]/);
      if (rangeMatch) {
         const numVal = Number(val);
         // CWMP ranges can be numeric strings. Provide safe fallback parsing.
         if (isNaN(numVal)) return "Must be a number for range validation.";
         const min = Number(rangeMatch[1]);
         const max = Number(rangeMatch[2]);
         if (numVal < min || numVal > max) {
            return `Value must be between ${rangeMatch[1]} and ${rangeMatch[2]}.`;
         }
      }
      
      // Enum
      const enumMatch = detailed.match(/enum:\s*([^)]+)/);
      if (enumMatch) {
        // Strip out trailing '...' if it was truncated by the backend
        let enumStr = enumMatch[1].trim();
        if (enumStr.endsWith('...')) {
          enumStr = enumStr.slice(0, -3).trim();
          // If it's a truncated enum, we only loosely enforce it as a suggestion, 
          // but if we want strict, we shouldn't fail them if they pass a valid one not in the top 5.
          // For now, if we see '...', we just warn but allow, or we don't block.
        } else {
          // Strict enum check
          const allowedVals = enumStr.split(',').map(s => s.trim());
          if (!allowedVals.includes(val.trim())) {
            return `Invalid value. Allowed values are: ${allowedVals.join(', ')}`;
          }
        }
      }
    }
    return null;
  };

  const isListInstance = selectedPath.includes('{i}');
  const isBoolean = selectedNode.data_type === 'boolean';
  const hasEnum = selectedNode.enum_values && selectedNode.enum_values.length > 0;
  const isDropdown = isBoolean || hasEnum;

  const handleGenerate = () => {
    if (editValue.trim() === "") return;
    if (isListInstance && listInstanceI.trim() === "") {
       setValidationError("Please specify an instance index 'i' (e.g. 1)");
       return;
    }

    const err = validateInput(editValue);
    if (err) {
      setValidationError(err);
      return;
    }
    setValidationError("");
    onGenerateEdit(selectedPath, editValue, listInstanceI.trim() || null);
  };

  const renderInputControls = () => {
    let inputEl;

    if (isDropdown) {
      inputEl = (
        <select 
          value={editValue}
          onChange={(e) => {
             setEditValue(e.target.value);
             setValidationError("");
          }}
          style={{ flexGrow: 1, padding: '0.4rem', borderRadius: '4px', border: '1px solid #45475a', backgroundColor: '#1e1e2e', color: '#cdd6f4' }}
        >
          <option value="">-- Select --</option>
          {isBoolean && (
            <>
              <option value="true">true</option>
              <option value="false">false</option>
            </>
          )}
          {hasEnum && selectedNode.enum_values.map(v => (
            <option key={v} value={v}>{v}</option>
          ))}
        </select>
      );
    } else {
      inputEl = (
        <input 
          type="text" 
          placeholder={`Value`}
          value={editValue}
          onChange={(e) => {
            setEditValue(e.target.value);
            setValidationError("");
          }}
          style={{ flexGrow: 1 }}
        />
      );
    }

    if (isListInstance) {
      return (
        <div style={{ width: '100%', marginBottom: '1rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: '#181825', borderRadius: '6px', overflow: 'hidden' }}>
            <thead>
              <tr>
                <th style={{ padding: '8px', borderBottom: '1px solid #313244', textAlign: 'left', width: '30%', color: '#a6adc8', fontSize: '0.9rem' }}>i (Instance)</th>
                <th style={{ padding: '8px', borderBottom: '1px solid #313244', textAlign: 'left', color: '#a6adc8', fontSize: '0.9rem' }}>Parameter Value</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ padding: '8px', borderBottom: '1px solid #313244' }}>
                  <input type="text" placeholder="e.g. 1" value={listInstanceI} onChange={e => { setListInstanceI(e.target.value); setValidationError(""); }} style={{ width: '100%', padding: '0.4rem', borderRadius: '4px', border: '1px solid #45475a', backgroundColor: '#1e1e2e', color: '#cdd6f4' }} />
                </td>
                <td style={{ padding: '8px', borderBottom: '1px solid #313244' }}>
                  <div style={{ display: 'flex' }}>
                    {inputEl}
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <p style={{ fontSize: '0.8rem', color: '#a6adc8', marginTop: '0.5rem' }}>Generating XML will automatically inject {"<index>"}{listInstanceI || 'i'}{"</index>"} as the instance key.</p>
        </div>
      );
    } else {
      return (
        <div className="input-group">
          {inputEl}
        </div>
      );
    }
  };

  return (
    <div className="details-panel">
      <h2>{selectedNode.name}</h2>
      
      <table className="details-table">
        <tbody>
          <tr>
            <th>Path</th>
            <td>{selectedPath}</td>
          </tr>
          <tr>
            <th>Type</th>
            <td style={{ textTransform: 'capitalize' }}>
              {selectedNode.node_type} {selectedNode.data_type ? `(${selectedNode.data_type})` : ''}
            </td>
          </tr>
          {selectedNode.detailed_type && (
            <tr>
              <th>Description Type</th>
              <td>
                <span style={{ 
                  fontSize: '0.85rem', 
                  padding: '2px 6px', 
                  backgroundColor: 'rgba(137, 180, 250, 0.1)', 
                  color: '#89b4fa',
                  border: '1px solid rgba(137, 180, 250, 0.3)',
                  borderRadius: '4px',
                  fontFamily: 'monospace',
                  display: 'inline-block'
                }}>
                  {selectedNode.detailed_type}
                </span>
              </td>
            </tr>
          )}
          <tr>
            <th>Access</th>
            <td>{selectedNode.access}</td>
          </tr>
          {selectedNode.default_value && (
            <tr>
              <th>Default Value</th>
              <td>{selectedNode.default_value}</td>
            </tr>
          )}
          {selectedNode.description && (
            <tr>
              <th>Description</th>
              <td>{selectedNode.description}</td>
            </tr>
          )}
        </tbody>
      </table>

      {showEditor && (
        <div className="editor-panel">
          <h3 style={{ color: '#89b4fa', marginBottom: '1rem' }}>Edit Configuration (NETCONF)</h3>
          {isListInstance ? null : (
            <p style={{ color: '#a6adc8', marginBottom: '1rem', fontSize: '0.9rem' }}>
              Set a new value for this parameter to generate a NETCONF &lt;edit-config&gt; message.
            </p>
          )}
          
          {validationError && (
             <div style={{ padding: '0.5rem', marginBottom: '1rem', backgroundColor: 'rgba(243, 139, 168, 0.2)', color: '#f38ba8', borderLeft: '4px solid #f38ba8', fontSize: '0.85rem' }}>
               ❌ <strong>Validation Error:</strong> {validationError}
             </div>
          )}

          {renderInputControls()}

          <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
            <button className="btn" onClick={handleGenerate}>
              Generate XML
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Editor;
