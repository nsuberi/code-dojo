// Data models for AI Eval Trace Viewer

// LangSmith Run/Trace types
export interface LangSmithRun {
  id: string;
  name: string;
  run_type: 'chain' | 'llm' | 'tool' | 'retriever';
  start_time: string;
  end_time: string | null;
  status: 'success' | 'error' | 'pending';
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown> | null;
  error: string | null;
  parent_run_id: string | null;
  trace_id: string;
  dotted_order: string;
  session_id: string;
  extra?: {
    metadata?: {
      harness_type?: string;
      [key: string]: unknown;
    };
    runtime?: Record<string, unknown>;
  };
  child_run_ids: string[] | null;
  tags: string[];
  feedback_stats: Record<string, unknown> | null;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
}

// AI Feature types
export type FeatureId = 'digi-trainer' | 'coding-planner' | 'code-review';

export interface Feature {
  id: FeatureId;
  name: string;
  description: string;
  traceNamePatterns: string[]; // patterns to match run names
  threadCount?: number;
  lastActivity?: Date;
}

// Thread represents a collection of related traces (conversation session)
export interface Thread {
  id: string;
  featureId: FeatureId;
  name: string;
  status: 'success' | 'error' | 'running';
  startTime: Date;
  endTime?: Date;
  durationMs?: number;
  inputPreview?: string;
  outputPreview?: string;
  tags: Tag[];
  annotations: Annotation[];
  runs: LangSmithRun[];
}

// Span represents a single operation within a thread
export interface Span {
  id: string;
  threadId: string;
  parentSpanId?: string;
  name: string;
  type: 'chain' | 'llm' | 'tool' | 'retriever';
  status: 'success' | 'error' | 'running';
  startTime: Date;
  endTime?: Date;
  durationMs?: number;
  input?: unknown;
  output?: unknown;
  metadata?: Record<string, unknown>;
  children: Span[];
  sourceMapping?: SourceMapping;
}

// Annotation for notes on traces/threads
export interface Annotation {
  id: string;
  targetId: string;
  targetType: 'thread' | 'span';
  text: string;
  createdAt: Date;
  createdBy?: string;
}

// Tag for categorization
export interface Tag {
  id: string;
  name: string;
  color: string;
}

// Dataset for evaluation testing
export interface Dataset {
  id: string;
  name: string;
  description: string;
  createdAt: Date;
  itemCount: number;
}

// DatasetItem junction record
export interface DatasetItem {
  id: string;
  datasetId: string;
  targetId: string;
  targetType: 'thread' | 'span';
  addedAt: Date;
}

// Source code mapping
export interface SourceMapping {
  filePath: string;
  functionName: string;
  startLine: number;
  endLine: number;
}

// Navigation state
export interface NavigationState {
  selectedFeatureId: FeatureId | null;
  selectedThreadId: string | null;
  selectedSpanId: string | null;
  panelOpen: 'annotation' | 'code' | null;
}

// Hotkey configuration
export interface HotkeyConfig {
  key: string;
  scope: string;
  action: () => void;
  description: string;
}
