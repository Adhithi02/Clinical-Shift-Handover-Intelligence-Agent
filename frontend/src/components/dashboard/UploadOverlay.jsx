export default function UploadOverlay({ show, onClose, onUpload }) {
  if (!show) return null

  return (
    <div className="upload-overlay" onClick={onClose}>
      <div 
        className="upload-box" 
        onClick={(e) => e.stopPropagation()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { 
          e.preventDefault()
          if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            onUpload(e.dataTransfer.files)
          }
        }}
      >
        <div style={{ fontWeight: 600, fontSize: '15px' }}>Drop patient PDFs here</div>
        <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '8px', marginBottom: '16px' }}>Supports multiple files</div>
        <input 
          type="file" 
          multiple 
          accept=".pdf"
          onChange={(e) => onUpload(e.target.files)}
          style={{ width: '100%', padding: '8px' }}
        />
        <button onClick={onClose} style={{ marginTop: '16px', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontFamily: 'var(--font-mono)' }}>Cancel</button>
      </div>
    </div>
  )
}
