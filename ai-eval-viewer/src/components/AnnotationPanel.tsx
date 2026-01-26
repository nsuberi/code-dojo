import { useState, useEffect, useRef } from 'react';
import type { Annotation, Tag, Dataset } from '../types';
import {
  getAnnotations,
  saveAnnotation,
  deleteAnnotation,
  getTags,
  createTag,
  getTagAssignments,
  addTagToTarget,
  removeTagFromTarget,
  getDatasets,
  createDataset,
  getItemDatasets,
  addToDataset,
  removeFromDataset,
} from '../services/annotations';

interface AnnotationPanelProps {
  isOpen: boolean;
  onClose: () => void;
  targetId: string;
  targetType: 'thread' | 'span';
  targetName: string;
}

export function AnnotationPanel({
  isOpen,
  onClose,
  targetId,
  targetType,
  targetName,
}: AnnotationPanelProps) {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [assignedTags, setAssignedTags] = useState<Tag[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [assignedDatasets, setAssignedDatasets] = useState<Dataset[]>([]);

  const [noteText, setNoteText] = useState('');
  const [tagSearch, setTagSearch] = useState('');
  const [showTagDropdown, setShowTagDropdown] = useState(false);
  const [showDatasetDropdown, setShowDatasetDropdown] = useState(false);
  const [newTagName, setNewTagName] = useState('');
  const [newDatasetName, setNewDatasetName] = useState('');
  const [newDatasetDesc, setNewDatasetDesc] = useState('');
  const [showNewTagForm, setShowNewTagForm] = useState(false);
  const [showNewDatasetForm, setShowNewDatasetForm] = useState(false);

  const noteInputRef = useRef<HTMLTextAreaElement>(null);

  // Load data when target changes
  useEffect(() => {
    if (targetId) {
      setAnnotations(getAnnotations(targetId));
      setTags(getTags());
      setAssignedTags(getTagAssignments(targetId));
      setDatasets(getDatasets());
      setAssignedDatasets(getItemDatasets(targetId));
    }
  }, [targetId]);

  // Focus note input when panel opens
  useEffect(() => {
    if (isOpen && noteInputRef.current) {
      noteInputRef.current.focus();
    }
  }, [isOpen]);

  const handleSaveNote = () => {
    if (!noteText.trim()) return;

    const newAnnotation = saveAnnotation(targetId, targetType, noteText.trim());
    setAnnotations([...annotations, newAnnotation]);
    setNoteText('');
  };

  const handleDeleteNote = (annotationId: string) => {
    deleteAnnotation(annotationId);
    setAnnotations(annotations.filter((a) => a.id !== annotationId));
  };

  const handleAddTag = (tag: Tag) => {
    addTagToTarget(tag.id, targetId, targetType);
    setAssignedTags([...assignedTags, tag]);
    setTagSearch('');
    setShowTagDropdown(false);
  };

  const handleRemoveTag = (tagId: string) => {
    removeTagFromTarget(tagId, targetId);
    setAssignedTags(assignedTags.filter((t) => t.id !== tagId));
  };

  const handleCreateTag = () => {
    if (!newTagName.trim()) return;

    const colors = ['#ef4444', '#22c55e', '#f59e0b', '#3b82f6', '#8b5cf6', '#ec4899', '#06b6d4'];
    const randomColor = colors[Math.floor(Math.random() * colors.length)];

    const newTag = createTag(newTagName.trim(), randomColor);
    setTags([...tags, newTag]);
    handleAddTag(newTag);
    setNewTagName('');
    setShowNewTagForm(false);
  };

  const handleAddToDataset = (dataset: Dataset) => {
    addToDataset(dataset.id, targetId, targetType);
    setAssignedDatasets([...assignedDatasets, dataset]);
    setShowDatasetDropdown(false);
  };

  const handleRemoveFromDataset = (datasetId: string) => {
    removeFromDataset(datasetId, targetId);
    setAssignedDatasets(assignedDatasets.filter((d) => d.id !== datasetId));
  };

  const handleCreateDataset = () => {
    if (!newDatasetName.trim()) return;

    const newDataset = createDataset(newDatasetName.trim(), newDatasetDesc.trim());
    setDatasets([...datasets, newDataset]);
    handleAddToDataset(newDataset);
    setNewDatasetName('');
    setNewDatasetDesc('');
    setShowNewDatasetForm(false);
  };

  const filteredTags = tags.filter(
    (t) =>
      t.name.toLowerCase().includes(tagSearch.toLowerCase()) &&
      !assignedTags.some((at) => at.id === t.id)
  );

  const availableDatasets = datasets.filter(
    (d) => !assignedDatasets.some((ad) => ad.id === d.id)
  );

  if (!isOpen) return null;

  return (
    <div className={`panel ${isOpen ? 'open' : ''}`}>
      <div className="panel-header">
        <div>
          <span className="text-secondary" style={{ fontSize: '12px' }}>
            Annotating {targetType}
          </span>
          <div style={{ fontWeight: 600 }}>{targetName}</div>
        </div>
        <button className="btn btn-ghost" onClick={onClose} aria-label="Close panel">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" />
          </svg>
        </button>
      </div>

      <div className="panel-body">
        {/* Notes Section */}
        <section style={{ marginBottom: 'var(--spacing-lg)' }}>
          <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: 'var(--spacing-sm)' }}>
            Notes
          </h4>

          <div className="form-group">
            <textarea
              ref={noteInputRef}
              className="form-input form-textarea"
              placeholder="Add a note..."
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                  e.preventDefault();
                  handleSaveNote();
                }
              }}
            />
            <div className="flex justify-between items-center mt-sm">
              <span className="text-muted" style={{ fontSize: '11px' }}>
                <kbd className="kbd">Ctrl</kbd>+<kbd className="kbd">Enter</kbd> to save
              </span>
              <button
                className="btn btn-primary"
                onClick={handleSaveNote}
                disabled={!noteText.trim()}
              >
                Save Note
              </button>
            </div>
          </div>

          {annotations.length > 0 && (
            <div style={{ marginTop: 'var(--spacing-md)' }}>
              {annotations.map((note) => (
                <div
                  key={note.id}
                  className="card"
                  style={{ marginBottom: 'var(--spacing-sm)', padding: 'var(--spacing-sm)' }}
                >
                  <div style={{ whiteSpace: 'pre-wrap', marginBottom: 'var(--spacing-xs)' }}>
                    {note.text}
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted" style={{ fontSize: '11px' }}>
                      {new Date(note.createdAt).toLocaleString()}
                    </span>
                    <button
                      className="btn btn-ghost"
                      onClick={() => handleDeleteNote(note.id)}
                      style={{ padding: '2px 6px', fontSize: '11px' }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Tags Section */}
        <section style={{ marginBottom: 'var(--spacing-lg)' }}>
          <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: 'var(--spacing-sm)' }}>
            Tags
          </h4>

          {/* Assigned tags */}
          <div className="flex gap-sm" style={{ flexWrap: 'wrap', marginBottom: 'var(--spacing-sm)' }}>
            {assignedTags.map((tag) => (
              <span
                key={tag.id}
                className="tag"
                style={{ backgroundColor: tag.color + '20', borderColor: tag.color, color: tag.color }}
              >
                {tag.name}
                <span className="tag-remove" onClick={() => handleRemoveTag(tag.id)}>
                  ×
                </span>
              </span>
            ))}
            {assignedTags.length === 0 && (
              <span className="text-muted" style={{ fontSize: '12px' }}>No tags assigned</span>
            )}
          </div>

          {/* Tag search/picker */}
          <div style={{ position: 'relative' }}>
            <input
              type="text"
              className="form-input"
              placeholder="Search or add tags..."
              value={tagSearch}
              onChange={(e) => {
                setTagSearch(e.target.value);
                setShowTagDropdown(true);
              }}
              onFocus={() => setShowTagDropdown(true)}
            />
            {showTagDropdown && (
              <div
                className="card"
                style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  zIndex: 10,
                  maxHeight: '200px',
                  overflow: 'auto',
                }}
              >
                {filteredTags.map((tag) => (
                  <div
                    key={tag.id}
                    className="list-item"
                    onClick={() => handleAddTag(tag)}
                    style={{ padding: 'var(--spacing-sm)' }}
                  >
                    <span
                      style={{
                        width: '12px',
                        height: '12px',
                        borderRadius: '50%',
                        backgroundColor: tag.color,
                        marginRight: 'var(--spacing-sm)',
                      }}
                    />
                    {tag.name}
                  </div>
                ))}
                {filteredTags.length === 0 && tagSearch && !showNewTagForm && (
                  <div
                    className="list-item"
                    onClick={() => {
                      setNewTagName(tagSearch);
                      setShowNewTagForm(true);
                    }}
                    style={{ padding: 'var(--spacing-sm)' }}
                  >
                    Create tag "{tagSearch}"
                  </div>
                )}
                {showNewTagForm && (
                  <div style={{ padding: 'var(--spacing-sm)' }}>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Tag name"
                      value={newTagName}
                      onChange={(e) => setNewTagName(e.target.value)}
                      autoFocus
                    />
                    <div className="flex gap-sm mt-sm">
                      <button className="btn btn-primary" onClick={handleCreateTag}>
                        Create
                      </button>
                      <button
                        className="btn btn-secondary"
                        onClick={() => {
                          setShowNewTagForm(false);
                          setNewTagName('');
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </section>

        {/* Datasets Section */}
        <section>
          <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: 'var(--spacing-sm)' }}>
            Datasets
          </h4>

          {/* Assigned datasets */}
          <div style={{ marginBottom: 'var(--spacing-sm)' }}>
            {assignedDatasets.map((dataset) => (
              <div
                key={dataset.id}
                className="card flex items-center justify-between"
                style={{ padding: 'var(--spacing-sm)', marginBottom: 'var(--spacing-xs)' }}
              >
                <div>
                  <div style={{ fontWeight: 500 }}>{dataset.name}</div>
                  {dataset.description && (
                    <div className="text-muted" style={{ fontSize: '11px' }}>
                      {dataset.description}
                    </div>
                  )}
                </div>
                <button
                  className="btn btn-ghost"
                  onClick={() => handleRemoveFromDataset(dataset.id)}
                  style={{ padding: '2px 6px', fontSize: '11px' }}
                >
                  Remove
                </button>
              </div>
            ))}
            {assignedDatasets.length === 0 && (
              <span className="text-muted" style={{ fontSize: '12px' }}>Not in any datasets</span>
            )}
          </div>

          {/* Add to dataset */}
          <div style={{ position: 'relative' }}>
            <button
              className="btn btn-secondary"
              onClick={() => setShowDatasetDropdown(!showDatasetDropdown)}
              style={{ width: '100%' }}
            >
              Add to Dataset
            </button>
            {showDatasetDropdown && (
              <div
                className="card"
                style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  zIndex: 10,
                  maxHeight: '200px',
                  overflow: 'auto',
                }}
              >
                {availableDatasets.map((dataset) => (
                  <div
                    key={dataset.id}
                    className="list-item"
                    onClick={() => handleAddToDataset(dataset)}
                    style={{ padding: 'var(--spacing-sm)' }}
                  >
                    <div>
                      <div style={{ fontWeight: 500 }}>{dataset.name}</div>
                      <div className="text-muted" style={{ fontSize: '11px' }}>
                        {dataset.itemCount} items
                      </div>
                    </div>
                  </div>
                ))}
                {availableDatasets.length === 0 && !showNewDatasetForm && (
                  <div
                    className="list-item"
                    onClick={() => setShowNewDatasetForm(true)}
                    style={{ padding: 'var(--spacing-sm)' }}
                  >
                    Create new dataset...
                  </div>
                )}
                {showNewDatasetForm && (
                  <div style={{ padding: 'var(--spacing-sm)' }}>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Dataset name"
                      value={newDatasetName}
                      onChange={(e) => setNewDatasetName(e.target.value)}
                      autoFocus
                    />
                    <textarea
                      className="form-input form-textarea mt-sm"
                      placeholder="Description (optional)"
                      value={newDatasetDesc}
                      onChange={(e) => setNewDatasetDesc(e.target.value)}
                      rows={2}
                    />
                    <div className="flex gap-sm mt-sm">
                      <button className="btn btn-primary" onClick={handleCreateDataset}>
                        Create
                      </button>
                      <button
                        className="btn btn-secondary"
                        onClick={() => {
                          setShowNewDatasetForm(false);
                          setNewDatasetName('');
                          setNewDatasetDesc('');
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
