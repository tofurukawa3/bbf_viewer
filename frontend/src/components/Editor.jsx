import React, { useState } from 'react';

const Editor = ({ selectedNode, selectedPath, onGenerateEdit, viewMode }) => {
  const [editValue, setEditValue] = useState("");

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

  const handleGenerate = () => {
    if (editValue.trim() === "") return;
    onGenerateEdit(selectedPath, editValue);
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
              {selectedNode.node_type} 
              {selectedNode.data_type ? ` (${selectedNode.data_type})` : ''}
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

      {showEditor && (
        <div className="editor-panel">
          <h3 style={{ color: '#89b4fa', marginBottom: '1rem' }}>Edit Configuration (NETCONF)</h3>
          <p style={{ color: '#a6adc8', marginBottom: '1rem', fontSize: '0.9rem' }}>
            Set a new value for this parameter to generate a NETCONF &lt;edit-config&gt; message.
          </p>
          <div className="input-group">
            <input 
              type="text" 
              placeholder={`Enter new value for ${selectedNode.name}`}
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
            />
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
