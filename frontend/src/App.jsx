import { useState, useEffect, useMemo } from 'react'
import TreeView from './components/TreeView'
import Editor from './components/Editor'
import NetconfPreview from './components/NetconfPreview'

const API_BASE_URL = 'http://127.0.0.1:8000'

// Helper to deeply filter the tree for edit mode (only readWrite parameters and their parent objects)
function filterForEditMode(node) {
  if (!node) return null;

  // If it's a parameter, it must be readWrite to be kept
  if (node.node_type === 'parameter') {
    return node.access === 'readWrite' ? { ...node } : null;
  }

  // If it's an object, filter its children
  if (node.children) {
    const filteredChildren = node.children
      .map(child => filterForEditMode(child))
      .filter(child => child !== null);

    // Keep the object if it has any valid children (meaning they eventually contain readWrite)
    if (filteredChildren.length > 0) {
      return { ...node, children: filteredChildren };
    }
  }

  // If object has no valid children, or is something else entirely, discard
  return null;
}

function App() {
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState("")
  const [treeData, setTreeData] = useState(null)
  
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedPath, setSelectedPath] = useState("")
  
  const [netconfXml, setNetconfXml] = useState("")
  
  // Search and Mode state
  const [searchTerm, setSearchTerm] = useState("")
  const [viewMode, setViewMode] = useState("view") // "view" | "edit"

  // Fetch available models on load
  useEffect(() => {
    fetch(`${API_BASE_URL}/models`)
      .then(res => res.json())
      .then(data => {
        setModels(data.models || [])
        if (data.models && data.models.length > 0) {
          setSelectedModel(data.models[0])
        }
      })
      .catch(err => console.error("Failed to fetch models", err))
  }, [])

  // Fetch tree data when model changes
  useEffect(() => {
    if (!selectedModel) return

    setTreeData(null)
    setSelectedNode(null)
    setSelectedPath("")
    setNetconfXml("")
    setSearchTerm("")

    fetch(`${API_BASE_URL}/models/${selectedModel}`)
      .then(res => res.json())
      .then(data => setTreeData(data))
      .catch(err => console.error(`Failed to fetch model ${selectedModel}`, err))
  }, [selectedModel])

  const handleSelectNode = (node, path) => {
    setSelectedNode(node)
    // The TreeView builds path recursively. E.g "Root.Device.FAP.Control."
    // Let's strip the leading "Root." to make it cleaner for the Netconf target
    const cleanPath = path.startsWith("Root.") ? path.substring(5) : path
    
    // Append node name for the final path, preventing double dots
    const finalPath = cleanPath 
      ? (cleanPath.endsWith('.') ? `${cleanPath}${node.name}` : `${cleanPath}.${node.name}`)
      : node.name;
      
    setSelectedPath(finalPath)
  }

  const handleGenerateEdit = async (path, value, listInstances = null) => {
    try {
      const response = await fetch(`${API_BASE_URL}/netconf/edit-config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_name: selectedModel,
          target_path: path,
          value: value,
          existing_xml: netconfXml || null,
          list_instances: listInstances
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setNetconfXml(result.xml_payload);
    } catch (e) {
      console.error("Failed to generate edit config", e);
      setNetconfXml(`Error generating XML: ${e.message}`);
    }
  }

  const displayedTree = useMemo(() => {
    if (!treeData) return null;
    if (viewMode === "edit") {
      return filterForEditMode(treeData);
    }
    return treeData;
  }, [treeData, viewMode]);

  return (
    <div className="app-container">
      <div className="sidebar">
        <div className="header">
          <h1>BBF DataModel Viewer</h1>
        </div>
        
        <div className="tabs" style={{ display: 'flex', borderBottom: '1px solid #313244' }}>
          <button 
            className={`tab-btn ${viewMode === 'view' ? 'active' : ''}`}
            onClick={() => setViewMode('view')}
          >
            🔎 View Mode
          </button>
          <button 
            className={`tab-btn ${viewMode === 'edit' ? 'active' : ''}`}
            onClick={() => setViewMode('edit')}
          >
            ✏️ Edit Mode
          </button>
        </div>

        <div className="model-selector">
          <select 
            value={selectedModel} 
            onChange={(e) => {
               setSelectedModel(e.target.value)
               setSelectedNode(null)
               setNetconfXml("")
            }}
          >
            {models.map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
          <input 
            type="text"
            className="search-input"
            placeholder="Search parameters..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ marginTop: '0.5rem', width: '100%', padding: '0.5rem', backgroundColor: '#313244', color: '#cdd6f4', border: '1px solid #45475a', borderRadius: '4px', outline: 'none' }}
          />
        </div>
        <div className="tree-container">
          {displayedTree ? (
             displayedTree.name === "Root" && displayedTree.children ? (
               displayedTree.children.map((childNode, idx) => (
                 <TreeView 
                   key={idx}
                   node={childNode} 
                   path="Root" 
                   onSelectNode={handleSelectNode}
                   searchTerm={searchTerm}
                 />
               ))
             ) : (
               <TreeView 
                 node={displayedTree} 
                 path="Root" 
                 onSelectNode={handleSelectNode}
                 searchTerm={searchTerm}
               />
             )
          ) : treeData ? (
             <div style={{ color: '#6c7086', textAlign: 'center', marginTop: '2rem' }}>No writable parameters found.</div>
          ) : (
             <div style={{ color: '#6c7086', textAlign: 'center', marginTop: '2rem' }}>Loading Model...</div>
          )}
        </div>
      </div>

      <div className={`main-content ${viewMode === 'edit' ? 'edit-mode' : ''}`}>
        {selectedNode ? (
          <Editor  
            selectedNode={selectedNode} 
            selectedPath={selectedPath}
            onGenerateEdit={handleGenerateEdit}
            viewMode={viewMode}
          />
        ) : (
          <div className="details-panel">
            <h2>Details</h2>
            <p style={{ color: '#a6adc8' }}>Select a node from the tree to view its details.</p>
          </div>
        )}

        {viewMode === 'edit' && <NetconfPreview xmlPayload={netconfXml} />}
      </div>
    </div>
  )
}

export default App
