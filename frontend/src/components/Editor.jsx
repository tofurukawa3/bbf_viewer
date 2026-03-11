import React, { useState, useEffect } from 'react';

const Editor = ({ selectedNode, selectedPath, onGenerateEdit, onGenerateGet, viewMode }) => {
  const [bulkValues, setBulkValues] = useState({});
  const [listInstances, setListInstances] = useState({});
  const [validationError, setValidationError] = useState("");

  // Reset inputs when selection changes
  useEffect(() => {
    setBulkValues({});
    setListInstances({});
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

  const instanceCount = (selectedPath.match(/{i}/g) || []).length;
  const isListInstance = instanceCount > 0;
  
  // Edit mode constraints
  const isWritableObject = selectedNode.node_type === 'object' && isListInstance;
  const isWritableParam = selectedNode.node_type === 'parameter' && selectedNode.access === 'readWrite';
  const showEditPanel = (isWritableObject || isWritableParam) && viewMode === 'edit';
  
  // View mode always allows generating GetParameterValues payload
  const showViewPanel = viewMode === 'view';

  const validateInput = (val, targetNode) => {
    // 1. Basic Type Validation
    const baseType = targetNode.data_type;
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
    const detailed = targetNode.detailed_type;
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
         if (isNaN(numVal)) return "Must be a number for range validation.";
         const min = Number(rangeMatch[1]);
         const max = Number(rangeMatch[2]);
         if (numVal < min || numVal > max) {
            return `Value must be between ${rangeMatch[1]} and ${rangeMatch[2]}.`;
         }
      }
      
      // Enum validation is inherently handled by the dropdowns for precise matches now.
      const enumMatch = detailed.match(/enum:\s*([^)]+)/);
      if (enumMatch) {
        let enumStr = enumMatch[1].trim();
        if (enumStr.endsWith('...')) {
          enumStr = enumStr.slice(0, -3).trim();
        } else {
          const allowedVals = enumStr.split(',').map(s => s.trim());
          if (!allowedVals.includes(val.trim())) {
            return `Invalid value. Allowed values are: ${allowedVals.join(', ')}`;
          }
        }
      }
    }
    return null;
  };

  const resolveListInstances = (basePath) => {
      let resolvedPath = basePath;
      for (let idx = 0; idx < instanceCount; idx++) {
          resolvedPath = resolvedPath.replace('{i}', listInstances[idx].trim());
      }
      return resolvedPath;
  }

  const validateInstanceIndexes = () => {
    if (isListInstance) {
       for (let idx = 0; idx < instanceCount; idx++) {
           if (!listInstances[idx] || listInstances[idx].trim() === "") {
               setValidationError(`Please specify all instance indexes (missing Index ${idx + 1})`);
               return false;
           }
       }
    }
    return true;
  }

  const handleGenerateGet = () => {
    if (!validateInstanceIndexes()) return;
    setValidationError("");

    let resolvedPaths = [];
    
    if (selectedNode.node_type === 'parameter') {
        resolvedPaths.push(resolveListInstances(selectedPath));
    } else {
        // If it's an object, GetParameterValues typically targets the parent object path 
        // string (e.g "Device.DeviceInfo." instead of iterating children) to get all sub-nodes.
        resolvedPaths.push(resolveListInstances(selectedPath));
    }

    onGenerateGet(resolvedPaths);
  };

  const handleGenerateEdit = () => {
    if (!validateInstanceIndexes()) return;

    const payloadBatches = [];

    // Evaluate single parameter
    if (isWritableParam) {
      const val = bulkValues[selectedNode.name] || "";
      if (val.trim() === "") {
         setValidationError("A parameter value is required.");
         return; 
      }
      
      const err = validateInput(val, selectedNode);
      if (err) {
        setValidationError(`${selectedNode.name}: ${err}`);
        return;
      }
      payloadBatches.push({
        path: resolveListInstances(selectedPath),
        value: val,
        datatype: selectedNode.data_type || "string"
      });
    }

    // Evaluate Object Bulk Editing
    if (isWritableObject) {
      const rwParams = selectedNode.children?.filter(c => c.node_type === 'parameter' && c.access === 'readWrite') || [];
      
      for (let param of rwParams) {
        let val = bulkValues[param.name];
        if (val === undefined || val.trim() === "") continue; // Skip unconfigured bulk properties
        
        const err = validateInput(val, param);
        if (err) {
          setValidationError(`[${param.name}]: ${err}`);
          return;
        }

        // Construct full path for payload (e.g. Device.IP.Interface.{i}.Enable)
        // Since selectedPath points to Device.IP.Interface.{i}. we append the param name
        const paramPath = selectedPath.endsWith('.') ? `${selectedPath}${param.name}` : `${selectedPath}.${param.name}`;
        payloadBatches.push({
          path: resolveListInstances(paramPath),
          value: val,
          datatype: param.data_type || "string"
        });
      }
      
      if (payloadBatches.length === 0) {
         setValidationError("Please fill out at least one parameter to generate XML payload.");
         return;
      }
    }

    setValidationError("");
    onGenerateEdit(payloadBatches, null);
  };

  const handleBulkChange = (paramName, val) => {
    setBulkValues(prev => ({...prev, [paramName]: val}));
    setValidationError("");
  };

  const renderSingleInput = (paramNode) => {
    const hasEnums = Array.isArray(paramNode.enum_values) && paramNode.enum_values.length > 0;
    const isBoolean = paramNode.data_type && paramNode.data_type.toLowerCase() === 'boolean';
    const currentValue = bulkValues[paramNode.name] || "";

    if (hasEnums || isBoolean) {
      return (
        <select 
          value={currentValue}
          onChange={(e) => handleBulkChange(paramNode.name, e.target.value)}
          style={{ flexGrow: 1, padding: '0.4rem', borderRadius: '4px', border: '1px solid #45475a', backgroundColor: '#1e1e2e', color: '#cdd6f4' }}
        >
          <option value="">-- Select a value --</option>
          {isBoolean && !hasEnums && (
            <>
              <option value="true">true</option>
              <option value="false">false</option>
            </>
          )}
          {hasEnums && paramNode.enum_values.map(v => (
            <option key={v} value={v}>{v}</option>
          ))}
        </select>
      );
    } else {
      return (
        <input 
          type="text" 
          placeholder={`Value`}
          value={currentValue}
          onChange={(e) => handleBulkChange(paramNode.name, e.target.value)}
          style={{ flexGrow: 1 }}
        />
      );
    }
  };

  const renderInstanceInputs = () => {
    const inputs = [];
    for (let idx = 0; idx < instanceCount; idx++) {
       inputs.push(
         <div key={idx} style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center' }}>
           <label style={{ width: '80px', color: '#a6adc8', fontSize: '0.9rem' }}>Index {idx + 1}</label>
           <input 
             type="text" 
             placeholder="e.g. 1" 
             value={listInstances[idx] || ""} 
             onChange={e => { 
                 const val = e.target.value; 
                 setListInstances(prev => ({...prev, [idx]: val})); 
                 setValidationError(""); 
             }} 
             style={{ width: '100px', padding: '0.4rem', borderRadius: '4px', border: '1px solid #45475a', backgroundColor: '#1e1e2e', color: '#cdd6f4' }} 
           />
         </div>
       );
    }
    return inputs;
  };

  const renderInputControls = () => {
    if (isWritableParam) {
        if (isListInstance) {
          return (
            <div style={{ width: '100%', marginBottom: '1rem' }}>
              <div style={{ marginBottom: '1rem', padding: '10px', backgroundColor: '#181825', borderRadius: '6px', border: '1px solid #313244' }}>
                 <p style={{ color: '#bac2de', fontSize: '0.9rem', marginBottom: '0.8rem', fontWeight: 'bold' }}>List Instances Definition</p>
                 {renderInstanceInputs()}
              </div>
              <div style={{ marginBottom: '0.5rem', color: '#bac2de', fontWeight: 'bold', fontSize: '0.9rem' }}>Parameter Value</div>
              <div style={{ display: 'flex' }}>
                 {renderSingleInput(selectedNode)}
              </div>
              <p style={{ fontSize: '0.8rem', color: '#a6adc8', marginTop: '0.8rem' }}>Generating XML will automatically inject indices into the hierarchy.</p>
            </div>
          );
        } else {
          return (
            <div className="input-group">
              {renderSingleInput(selectedNode)}
            </div>
          );
        }
    }

    if (isWritableObject) {
       const rwParams = selectedNode.children?.filter(c => c.node_type === 'parameter' && c.access === 'readWrite') || [];
       if (rwParams.length === 0) {
           return <p style={{ color: '#a6adc8' }}>No writable parameters exist under this list object.</p>;
       }

       return (
         <div style={{ width: '100%', marginBottom: '1rem' }}>
           <div style={{ marginBottom: '1.5rem', padding: '10px', backgroundColor: '#181825', borderRadius: '6px', border: '1px solid #313244' }}>
              <p style={{ color: '#bac2de', fontSize: '0.9rem', marginBottom: '0.8rem', fontWeight: 'bold' }}>List Instances Definition</p>
              {renderInstanceInputs()}
           </div>

           <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: '#181825', borderRadius: '6px', overflow: 'hidden' }}>
             <thead>
               <tr>
                 <th style={{ padding: '8px', borderBottom: '1px solid #313244', textAlign: 'left', width: '40%', color: '#a6adc8', fontSize: '0.9rem' }}>Parameter</th>
                 <th style={{ padding: '8px', borderBottom: '1px solid #313244', textAlign: 'left', color: '#a6adc8', fontSize: '0.9rem' }}>Value Input</th>
               </tr>
             </thead>
             <tbody>
               {rwParams.map(param => (
                  <tr key={param.name}>
                    <td style={{ padding: '8px', borderBottom: '1px solid #313244', color: '#cdd6f4', fontSize: '0.9rem' }}>
                       {param.name}
                       {param.data_type && <span style={{ marginLeft: '6px', color: '#6c7086', fontSize: '0.8rem' }}>({param.data_type})</span>}
                    </td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #313244' }}>
                      <div style={{ display: 'flex' }}>
                         {renderSingleInput(param)}
                      </div>
                    </td>
                  </tr>
               ))}
             </tbody>
           </table>
           <p style={{ fontSize: '0.8rem', color: '#a6adc8', marginTop: '0.5rem' }}>Unconfigured rows will be ignored. Generating XML will queue SetParameterValues for all populated inputs with the provided instance route.</p>
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
          <tr>
            <th>Type Description</th>
            <td>
              {selectedNode.detailed_type ? (
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
              ) : ""}
            </td>
          </tr>
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

      {showEditPanel && (
        <div className="editor-panel">
          <h3 style={{ color: '#89b4fa', marginBottom: '1rem' }}>Edit Configuration (CWMP SetParameterValues)</h3>
          {isListInstance && isWritableObject && (
            <p style={{ color: '#a6adc8', marginBottom: '1rem', fontSize: '0.9rem' }}>
              Bulk editing mode active. Populate the inputs below to set multiple parameters for list instance `{selectedNode.name}` simultaneously.
            </p>
          )}
          {!isListInstance && isWritableParam && (
            <p style={{ color: '#a6adc8', marginBottom: '1rem', fontSize: '0.9rem' }}>
              Set a new value for this parameter to generate a CWMP SetParameterValues SOAP envelope.
            </p>
          )}
          
          {validationError && (
             <div style={{ padding: '0.5rem', marginBottom: '1rem', backgroundColor: 'rgba(243, 139, 168, 0.2)', color: '#f38ba8', borderLeft: '4px solid #f38ba8', fontSize: '0.85rem' }}>
               ❌ <strong>Validation Error:</strong> {validationError}
             </div>
          )}

          {renderInputControls()}

          <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
            <button className="btn" onClick={handleGenerateEdit}>
              Generate XML
            </button>
          </div>
        </div>
      )}

      {showViewPanel && (
        <div className="editor-panel" style={{ marginTop: '2rem', borderTop: '2px dashed #45475a', paddingTop: '1.5rem' }}>
          <h3 style={{ color: '#a6e3a1', marginBottom: '1rem' }}>Generate Status Request (CWMP GetParameterValues)</h3>
          <p style={{ color: '#a6adc8', marginBottom: '1rem', fontSize: '0.9rem' }}>
             Request the CPE to return the current value(s) for the selected {selectedNode.node_type} path.
          </p>

          {validationError && (
             <div style={{ padding: '0.5rem', marginBottom: '1rem', backgroundColor: 'rgba(243, 139, 168, 0.2)', color: '#f38ba8', borderLeft: '4px solid #f38ba8', fontSize: '0.85rem' }}>
               ❌ <strong>Validation Error:</strong> {validationError}
             </div>
          )}

          {isListInstance ? (
            <div style={{ width: '100%', marginBottom: '1rem' }}>
              <div style={{ padding: '10px', backgroundColor: '#181825', borderRadius: '6px', border: '1px solid #313244' }}>
                <p style={{ color: '#bac2de', fontSize: '0.9rem', marginBottom: '0.8rem', fontWeight: 'bold' }}>Resolve List Instances ({selectedNode.name})</p>
                {renderInstanceInputs()}
              </div>
              <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
                <button className="btn" style={{ backgroundColor: '#a6e3a1', color: '#11111b' }} onClick={handleGenerateGet}>
                  Generate GetParameterValues
                </button>
              </div>
            </div>
          ) : (
             <div style={{ padding: '1rem', marginTop: '1rem', backgroundColor: 'rgba(166, 227, 161, 0.1)', color: '#a6e3a1', borderRadius: '4px', border: '1px solid rgba(166, 227, 161, 0.3)', fontSize: '0.9rem', textAlign: 'center' }}>
               ✨ XML Payloads are automatically generated upon selection for parameters without list instances `{'{i}'}` ✨
             </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Editor;
