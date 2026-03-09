import React, { useState, useEffect } from 'react';

const TreeView = ({ node, path = "", onSelectNode, searchTerm = "" }) => {
  const [expanded, setExpanded] = useState(false);
  const [visibleCount, setVisibleCount] = useState(50);

  // Auto-expand if searchTerm matches current or children
  useEffect(() => {
    if (searchTerm && hasMatch(node, searchTerm.toLowerCase())) {
      setExpanded(true);
      setVisibleCount(node.children ? node.children.length : 0); // Show all if searching
    } else if (!searchTerm) {
      setExpanded(false);
      setVisibleCount(50);
    }
  }, [searchTerm, node]);

  if (!node) return null;

  // Helper to check if subtree contains the search term
  const hasMatch = (n, term) => {
    if (n.name.toLowerCase().includes(term)) return true;
    if (n.children && n.children.length > 0) {
      return n.children.some(child => hasMatch(child, term));
    }
    return false;
  };

  const isMatch = searchTerm && hasMatch(node, searchTerm.toLowerCase());

  // If there's a search term and this node doesn't match and has no matching children, hide it
  if (searchTerm && !isMatch) {
    return null;
  }

  const handleToggle = (e) => {
    e.stopPropagation();
    if (node.children && node.children.length > 0) {
      setExpanded(!expanded);
    }
    onSelectNode(node, path);
  };

  const hasChildren = node.children && node.children.length > 0;
  
  // Guard against double dots if path already ends with a dot (common in CWMP)
  const currentPath = path 
    ? (path.endsWith('.') ? `${path}${node.name}` : `${path}.${node.name}`) 
    : node.name;

  return (
    <div className="tree-node">
      <div 
        className="tree-label"
        onClick={handleToggle}
      >
        <span className="tree-icon">
          {hasChildren ? (expanded ? '▼' : '▶') : '•'}
        </span>
        <span className="node-name-box">
          {node.name}
        </span>
        <span className={`type-badge ${node.node_type === 'parameter' ? node.access : node.node_type}`}>
          {node.node_type === 'parameter' ? node.access : 'object'}
        </span>
      </div>
      
      {expanded && hasChildren && (
        <div className="tree-children">
          {node.children.slice(0, visibleCount).map((child, index) => (
            <TreeView 
              key={`${currentPath}-${index}`} 
              node={child} 
              path={currentPath}
              onSelectNode={onSelectNode}
              searchTerm={searchTerm}
            />
          ))}
          {node.children.length > visibleCount && !searchTerm && (
            <button 
              className="show-more-btn"
              onClick={(e) => {
                e.stopPropagation();
                setVisibleCount(prev => prev + 50);
              }}
              style={{
                background: 'none', border: 'none', color: '#89b4fa', 
                cursor: 'pointer', fontSize: '0.85rem', padding: '4px 8px',
                marginTop: '4px', textAlign: 'left', outline: 'none'
              }}
            >
              Show More ({node.children.length - visibleCount} hidden)...
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default React.memo(TreeView);
