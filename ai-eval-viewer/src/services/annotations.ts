// Local storage service for annotations, tags, and datasets
import type { Annotation, Tag, Dataset, DatasetItem } from '../types';

const STORAGE_KEYS = {
  ANNOTATIONS: 'ai-eval-viewer:annotations',
  TAGS: 'ai-eval-viewer:tags',
  DATASETS: 'ai-eval-viewer:datasets',
  DATASET_ITEMS: 'ai-eval-viewer:dataset-items',
};

// Helper to generate UUIDs
function generateId(): string {
  return crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substr(2, 9);
}

// === Annotations ===

export function getAnnotations(targetId?: string): Annotation[] {
  const stored = localStorage.getItem(STORAGE_KEYS.ANNOTATIONS);
  const annotations: Annotation[] = stored ? JSON.parse(stored) : [];

  if (targetId) {
    return annotations.filter((a) => a.targetId === targetId);
  }
  return annotations;
}

export function saveAnnotation(
  targetId: string,
  targetType: 'thread' | 'span',
  text: string
): Annotation {
  const annotations = getAnnotations();
  const newAnnotation: Annotation = {
    id: generateId(),
    targetId,
    targetType,
    text,
    createdAt: new Date(),
  };

  annotations.push(newAnnotation);
  localStorage.setItem(STORAGE_KEYS.ANNOTATIONS, JSON.stringify(annotations));

  return newAnnotation;
}

export function deleteAnnotation(annotationId: string): void {
  const annotations = getAnnotations().filter((a) => a.id !== annotationId);
  localStorage.setItem(STORAGE_KEYS.ANNOTATIONS, JSON.stringify(annotations));
}

// === Tags ===

const DEFAULT_TAGS: Tag[] = [
  { id: 'error-handling', name: 'Error Handling', color: '#ef4444' },
  { id: 'good-response', name: 'Good Response', color: '#22c55e' },
  { id: 'needs-review', name: 'Needs Review', color: '#f59e0b' },
  { id: 'hallucination', name: 'Hallucination', color: '#8b5cf6' },
  { id: 'edge-case', name: 'Edge Case', color: '#3b82f6' },
];

export function getTags(): Tag[] {
  const stored = localStorage.getItem(STORAGE_KEYS.TAGS);
  if (!stored) {
    // Initialize with default tags
    localStorage.setItem(STORAGE_KEYS.TAGS, JSON.stringify(DEFAULT_TAGS));
    return DEFAULT_TAGS;
  }
  return JSON.parse(stored);
}

export function createTag(name: string, color: string): Tag {
  const tags = getTags();
  const newTag: Tag = {
    id: generateId(),
    name,
    color,
  };

  tags.push(newTag);
  localStorage.setItem(STORAGE_KEYS.TAGS, JSON.stringify(tags));

  return newTag;
}

export function deleteTag(tagId: string): void {
  const tags = getTags().filter((t) => t.id !== tagId);
  localStorage.setItem(STORAGE_KEYS.TAGS, JSON.stringify(tags));
}

// Tag assignments (stored as annotation metadata)
interface TagAssignment {
  tagId: string;
  targetId: string;
  targetType: 'thread' | 'span';
}

const TAG_ASSIGNMENTS_KEY = 'ai-eval-viewer:tag-assignments';

export function getTagAssignments(targetId: string): Tag[] {
  const stored = localStorage.getItem(TAG_ASSIGNMENTS_KEY);
  const assignments: TagAssignment[] = stored ? JSON.parse(stored) : [];
  const tags = getTags();

  return assignments
    .filter((a) => a.targetId === targetId)
    .map((a) => tags.find((t) => t.id === a.tagId))
    .filter((t): t is Tag => t !== undefined);
}

export function addTagToTarget(tagId: string, targetId: string, targetType: 'thread' | 'span'): void {
  const stored = localStorage.getItem(TAG_ASSIGNMENTS_KEY);
  const assignments: TagAssignment[] = stored ? JSON.parse(stored) : [];

  // Check if already assigned
  if (assignments.some((a) => a.tagId === tagId && a.targetId === targetId)) {
    return;
  }

  assignments.push({ tagId, targetId, targetType });
  localStorage.setItem(TAG_ASSIGNMENTS_KEY, JSON.stringify(assignments));
}

export function removeTagFromTarget(tagId: string, targetId: string): void {
  const stored = localStorage.getItem(TAG_ASSIGNMENTS_KEY);
  const assignments: TagAssignment[] = stored ? JSON.parse(stored) : [];

  const filtered = assignments.filter((a) => !(a.tagId === tagId && a.targetId === targetId));
  localStorage.setItem(TAG_ASSIGNMENTS_KEY, JSON.stringify(filtered));
}

// === Datasets ===

export function getDatasets(): Dataset[] {
  const stored = localStorage.getItem(STORAGE_KEYS.DATASETS);
  return stored ? JSON.parse(stored) : [];
}

export function createDataset(name: string, description: string): Dataset {
  const datasets = getDatasets();
  const newDataset: Dataset = {
    id: generateId(),
    name,
    description,
    createdAt: new Date(),
    itemCount: 0,
  };

  datasets.push(newDataset);
  localStorage.setItem(STORAGE_KEYS.DATASETS, JSON.stringify(datasets));

  return newDataset;
}

export function updateDataset(datasetId: string, updates: Partial<Dataset>): Dataset | null {
  const datasets = getDatasets();
  const index = datasets.findIndex((d) => d.id === datasetId);
  if (index === -1) return null;

  datasets[index] = { ...datasets[index], ...updates };
  localStorage.setItem(STORAGE_KEYS.DATASETS, JSON.stringify(datasets));

  return datasets[index];
}

export function deleteDataset(datasetId: string): void {
  const datasets = getDatasets().filter((d) => d.id !== datasetId);
  localStorage.setItem(STORAGE_KEYS.DATASETS, JSON.stringify(datasets));

  // Also remove all items from this dataset
  const allItems = getAllDatasetItems().filter((i) => i.datasetId !== datasetId);
  localStorage.setItem(STORAGE_KEYS.DATASET_ITEMS, JSON.stringify(allItems));
}

// === Dataset Items ===

function getAllDatasetItems(): DatasetItem[] {
  const stored = localStorage.getItem(STORAGE_KEYS.DATASET_ITEMS);
  return stored ? JSON.parse(stored) : [];
}

export function getDatasetItems(datasetId: string): DatasetItem[] {
  return getAllDatasetItems().filter((i) => i.datasetId === datasetId);
}

export function getItemDatasets(targetId: string): Dataset[] {
  const allItems = getAllDatasetItems();
  const datasets = getDatasets();

  const datasetIds = allItems
    .filter((i) => i.targetId === targetId)
    .map((i) => i.datasetId);

  return datasets.filter((d) => datasetIds.includes(d.id));
}

export function addToDataset(
  datasetId: string,
  targetId: string,
  targetType: 'thread' | 'span'
): DatasetItem {
  const items = getAllDatasetItems();

  // Check if already in dataset
  const existing = items.find((i) => i.datasetId === datasetId && i.targetId === targetId);
  if (existing) return existing;

  const newItem: DatasetItem = {
    id: generateId(),
    datasetId,
    targetId,
    targetType,
    addedAt: new Date(),
  };

  items.push(newItem);
  localStorage.setItem(STORAGE_KEYS.DATASET_ITEMS, JSON.stringify(items));

  // Update dataset item count
  const datasets = getDatasets();
  const datasetIndex = datasets.findIndex((d) => d.id === datasetId);
  if (datasetIndex !== -1) {
    datasets[datasetIndex].itemCount = getDatasetItems(datasetId).length;
    localStorage.setItem(STORAGE_KEYS.DATASETS, JSON.stringify(datasets));
  }

  return newItem;
}

export function removeFromDataset(datasetId: string, targetId: string): void {
  const items = getAllDatasetItems().filter(
    (i) => !(i.datasetId === datasetId && i.targetId === targetId)
  );
  localStorage.setItem(STORAGE_KEYS.DATASET_ITEMS, JSON.stringify(items));

  // Update dataset item count
  const datasets = getDatasets();
  const datasetIndex = datasets.findIndex((d) => d.id === datasetId);
  if (datasetIndex !== -1) {
    datasets[datasetIndex].itemCount = items.filter((i) => i.datasetId === datasetId).length;
    localStorage.setItem(STORAGE_KEYS.DATASETS, JSON.stringify(datasets));
  }
}

// === Export ===

export interface ExportedDataset {
  dataset: Dataset;
  items: Array<{
    targetId: string;
    targetType: 'thread' | 'span';
    tags: Tag[];
    annotations: Annotation[];
  }>;
}

export function exportDataset(datasetId: string): ExportedDataset | null {
  const datasets = getDatasets();
  const dataset = datasets.find((d) => d.id === datasetId);
  if (!dataset) return null;

  const items = getDatasetItems(datasetId).map((item) => ({
    targetId: item.targetId,
    targetType: item.targetType,
    tags: getTagAssignments(item.targetId),
    annotations: getAnnotations(item.targetId),
  }));

  return { dataset, items };
}
