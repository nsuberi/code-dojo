// LangSmith API client service
import type { LangSmithRun, Feature, FeatureId, Thread, Span } from '../types';

const LANGSMITH_API_URL = 'https://api.smith.langchain.com/api/v1';

// ============ CACHING & THROTTLING ============
const cache = new Map<string, { data: unknown; timestamp: number }>();
const CACHE_TTL = 30000; // 30 seconds

// Request queue for throttling
let lastRequestTime = 0;
const REQUEST_DELAY = 200; // 200ms between requests

// Exponential backoff settings
const MAX_RETRIES = 3;
const INITIAL_BACKOFF = 1000; // 1 second

async function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Get API key from environment
const getApiKey = (): string => {
  const key = import.meta.env.VITE_LANGSMITH_API_KEY;
  if (!key) {
    throw new Error('VITE_LANGSMITH_API_KEY is not set');
  }
  return key;
};

// Get project/session ID from environment
const getProjectId = (): string => {
  const id = import.meta.env.VITE_LANGSMITH_PROJECT_ID;
  if (!id) {
    throw new Error('VITE_LANGSMITH_PROJECT_ID is not set');
  }
  return id;
};

// Feature definitions with trace name patterns
export const FEATURES: Feature[] = [
  {
    id: 'digi-trainer',
    name: 'Digi-Trainer',
    description: 'Articulation practice for code explanation',
    traceNamePatterns: ['articulation_harness_orchestration'],  // Root-level session traces
  },
  {
    id: 'coding-planner',
    name: 'Coding Planner',
    description: 'Implementation planning assistance',
    traceNamePatterns: ['planning_harness_orchestration'],
  },
  {
    id: 'code-review',
    name: 'Code Review',
    description: 'Agentic PR code review orchestration',
    traceNamePatterns: ['LangGraph'],
  },
];

// API helper function with caching, throttling, and retry logic
async function langsmithFetch<T>(
  endpoint: string,
  options: RequestInit = {},
  useCache: boolean = true
): Promise<T> {
  const apiKey = getApiKey();
  const cacheKey = `${endpoint}:${JSON.stringify(options.body || '')}`;

  // Check cache first
  if (useCache) {
    const cached = cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      return cached.data as T;
    }
  }

  // Throttle requests
  const now = Date.now();
  const timeSinceLastRequest = now - lastRequestTime;
  if (timeSinceLastRequest < REQUEST_DELAY) {
    await delay(REQUEST_DELAY - timeSinceLastRequest);
  }
  lastRequestTime = Date.now();

  // Make request with retry logic for 429 errors
  let lastError: Error | null = null;
  for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
    try {
      const response = await fetch(`${LANGSMITH_API_URL}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
          ...options.headers,
        },
      });

      if (response.status === 429) {
        // Rate limited - exponential backoff
        const backoffTime = INITIAL_BACKOFF * Math.pow(2, attempt);
        console.warn(`Rate limited (429), retrying in ${backoffTime}ms (attempt ${attempt + 1}/${MAX_RETRIES})`);
        await delay(backoffTime);
        continue;
      }

      if (!response.ok) {
        throw new Error(`LangSmith API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      // Cache the successful response
      if (useCache) {
        cache.set(cacheKey, { data, timestamp: Date.now() });
      }

      return data;
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      if (attempt < MAX_RETRIES - 1) {
        const backoffTime = INITIAL_BACKOFF * Math.pow(2, attempt);
        console.warn(`Request failed, retrying in ${backoffTime}ms (attempt ${attempt + 1}/${MAX_RETRIES})`);
        await delay(backoffTime);
      }
    }
  }

  throw lastError || new Error('Request failed after max retries');
}

// Query runs from LangSmith
export async function queryRuns(options: {
  session?: string[];
  filter?: string;
  limit?: number;
  cursor?: string;
}): Promise<{ runs: LangSmithRun[]; cursors: { next?: string; prev?: string } }> {
  const projectId = getProjectId();

  const body = {
    session: options.session || [projectId],
    filter: options.filter,
    limit: options.limit || 20,
    ...(options.cursor && { cursor: options.cursor }),
  };

  return langsmithFetch('/runs/query', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// Get runs for a specific feature
export async function getFeatureRuns(
  featureId: FeatureId,
  limit: number = 20,
  cursor?: string
): Promise<{ runs: LangSmithRun[]; cursors: { next?: string; prev?: string } }> {
  const feature = FEATURES.find((f) => f.id === featureId);
  if (!feature) {
    throw new Error(`Unknown feature: ${featureId}`);
  }

  // Build filter for name patterns AND root runs only
  // is_root=true ensures we only get top-level traces (threads)
  const filterParts = feature.traceNamePatterns.map((p) => `eq(name, "${p}")`);
  const nameFilter = filterParts.length > 1 ? `or(${filterParts.join(', ')})` : filterParts[0];
  const filter = `and(${nameFilter}, eq(is_root, true))`;

  return queryRuns({ filter, limit, cursor });
}

// Get feature statistics (thread counts, last activity)
export async function getFeatureStats(): Promise<Map<FeatureId, { count: number; lastActivity?: Date }>> {
  const stats = new Map<FeatureId, { count: number; lastActivity?: Date }>();

  for (const feature of FEATURES) {
    const { runs } = await getFeatureRuns(feature.id, 1);
    stats.set(feature.id, {
      count: runs.length > 0 ? runs.length : 0, // Note: would need pagination for accurate count
      lastActivity: runs.length > 0 ? new Date(runs[0].start_time) : undefined,
    });
  }

  return stats;
}

// Convert LangSmith run to Thread (for top-level runs)
export function runToThread(run: LangSmithRun, featureId: FeatureId): Thread {
  const inputPreview = run.inputs
    ? JSON.stringify(run.inputs).substring(0, 100)
    : undefined;
  const outputPreview = run.outputs
    ? JSON.stringify(run.outputs).substring(0, 100)
    : undefined;

  const startTime = new Date(run.start_time);
  const endTime = run.end_time ? new Date(run.end_time) : undefined;

  return {
    id: run.id,
    featureId,
    name: run.name,
    status: run.status === 'success' ? 'success' : run.status === 'error' ? 'error' : 'running',
    startTime,
    endTime,
    durationMs: endTime ? endTime.getTime() - startTime.getTime() : undefined,
    inputPreview,
    outputPreview,
    tags: [],
    annotations: [],
    runs: [run],
  };
}

// Convert LangSmith run to Span
export function runToSpan(run: LangSmithRun, threadId: string): Span {
  const startTime = new Date(run.start_time);
  const endTime = run.end_time ? new Date(run.end_time) : undefined;

  return {
    id: run.id,
    threadId,
    parentSpanId: run.parent_run_id || undefined,
    name: run.name,
    type: run.run_type,
    status: run.status === 'success' ? 'success' : run.status === 'error' ? 'error' : 'running',
    startTime,
    endTime,
    durationMs: endTime ? endTime.getTime() - startTime.getTime() : undefined,
    input: run.inputs,
    output: run.outputs,
    metadata: run.extra?.metadata,
    children: [],
  };
}

// Get child runs for a trace by trace_id
export async function getChildRuns(traceId: string): Promise<LangSmithRun[]> {
  const { runs } = await queryRuns({
    filter: `eq(trace_id, "${traceId}")`,
    limit: 100,
  });
  return runs;
}

// Get runs linked to a topic thread by topic_thread_id metadata
export async function getTopicThreadRuns(topicThreadId: string): Promise<LangSmithRun[]> {
  const { runs } = await queryRuns({
    filter: `eq(metadata["topic_thread_id"], "${topicThreadId}")`,
    limit: 100,
  });
  return runs;
}

// Build span tree from flat list of runs
export function buildSpanTree(runs: LangSmithRun[], threadId: string): Span[] {
  const spanMap = new Map<string, Span>();
  const rootSpans: Span[] = [];

  // Deduplicate runs by ID before processing
  const seenIds = new Set<string>();
  const uniqueRuns = runs.filter(run => {
    if (seenIds.has(run.id)) {
      console.warn(`Duplicate run ID detected and filtered: ${run.id}`);
      return false;
    }
    seenIds.add(run.id);
    return true;
  });

  // First pass: create all spans
  for (const run of uniqueRuns) {
    spanMap.set(run.id, runToSpan(run, threadId));
  }

  // Second pass: build tree structure
  for (const run of uniqueRuns) {
    const span = spanMap.get(run.id)!;
    if (run.parent_run_id && spanMap.has(run.parent_run_id)) {
      const parent = spanMap.get(run.parent_run_id)!;
      parent.children.push(span);
    } else {
      rootSpans.push(span);
    }
  }

  // Sort children by start time
  const sortChildren = (spans: Span[]) => {
    spans.sort((a, b) => a.startTime.getTime() - b.startTime.getTime());
    for (const span of spans) {
      if (span.children.length > 0) {
        sortChildren(span.children);
      }
    }
  };
  sortChildren(rootSpans);

  return rootSpans;
}

// Get full thread details with span tree
export async function getThreadDetails(
  threadId: string,
  featureId: FeatureId
): Promise<{ thread: Thread; spans: Span[] }> {
  // Get the root run
  const { runs } = await queryRuns({
    filter: `eq(id, "${threadId}")`,
    limit: 1,
  });

  if (runs.length === 0) {
    throw new Error(`Thread not found: ${threadId}`);
  }

  const rootRun = runs[0];
  const thread = runToThread(rootRun, featureId);

  // Get all child runs for this trace
  let childRuns = await getChildRuns(rootRun.trace_id);

  // For topic conversation threads, also fetch runs linked by topic_thread_id metadata
  // These are message traces from separate HTTP requests that reference this topic
  if (rootRun.name === 'articulation_topic_conversation') {
    const topicThreadId = rootRun.extra?.metadata?.topic_thread_id as string | undefined;
    if (topicThreadId) {
      const topicRuns = await getTopicThreadRuns(topicThreadId);
      // Merge runs, avoiding duplicates
      const existingIds = new Set(childRuns.map(r => r.id));
      const newRuns = topicRuns.filter(r => !existingIds.has(r.id) && r.id !== rootRun.id);
      childRuns = [...childRuns, ...newRuns];
    }
  }

  // Build span tree
  const spans = buildSpanTree([rootRun, ...childRuns], threadId);

  return { thread, spans };
}
