# Git Integration Skill

## Purpose

This skill provides capabilities for local git repository operations to support directory-based architectural analysis. It enables the arch-pr-analyzer plugin to analyze the current working directory state, including uncommitted and untracked changes.

## When to Use This Skill

Use this skill when:
- Analyzing current directory architecture (default mode)
- Enumerating all files in a git repository
- Detecting uncommitted or untracked changes
- Reading file contents from the working directory
- Getting repository metadata (branch, name, remote)

## Core Capabilities

### 1. Repository Detection

Verify that the current directory is inside a git repository:

```bash
git rev-parse --is-inside-work-tree
```

**Returns:** `true` if inside a git repository, error otherwise

**Error handling:**
- Exit code 128: Not a git repository
- Exit code 0: Valid git repository

### 2. File Enumeration

Get a complete list of all tracked files in the repository:

```bash
git ls-files
```

**Returns:** List of all tracked file paths (one per line)

**Use for:** Building the complete file list to analyze

**Performance:** Fast even for large repositories (uses git's index)

### 3. File Content Reading

Read file contents from the working directory (includes uncommitted changes):

**Method 1 - Using Read tool (RECOMMENDED):**
```
Read tool with file path
```
- Automatically includes uncommitted changes
- Works with any file type
- Handles binary files appropriately

**Method 2 - Using bash cat:**
```bash
cat path/to/file.py
```
- Simple for text files
- May have issues with binary files

**Important:** Always read from the working directory, not from git objects, to capture uncommitted changes.

### 4. Current Branch Detection

Get the name of the currently checked out branch:

```bash
git rev-parse --abbrev-ref HEAD
```

**Returns:** Branch name (e.g., `main`, `feature/auth`)

**Special cases:**
- Returns `HEAD` if in detached HEAD state
- Use for report naming and context

### 5. Repository Name Extraction

Get the repository name from the remote URL:

```bash
git remote get-url origin | sed -n 's/.*\/\([^/]*\)\.git$/\1/p'
```

**Alternative (more robust):**
```bash
basename -s .git $(git remote get-url origin)
```

**Returns:** Repository name (e.g., `code-dojo`)

**Error handling:**
- If no remote named 'origin', try: `git remote` to list all remotes
- If no remotes, use directory name: `basename $(git rev-parse --show-toplevel)`

### 6. Uncommitted Changes Detection

Check for modified and untracked files:

```bash
# Get status in porcelain format
git status --porcelain
```

**Output format:**
- ` M file.py` - Modified file (not staged)
- `M  file.py` - Modified file (staged)
- `MM file.py` - Modified file (staged and unstaged changes)
- `?? file.py` - Untracked file
- `!! file.py` - Ignored file (use `--ignored` to show)

**Parsing:**
- Lines starting with `??` are untracked
- Lines with `M` anywhere are modified
- Empty output = clean working directory

**List only untracked files:**
```bash
git ls-files --others --exclude-standard
```

### 7. Repository Root Path

Get the absolute path to the repository root:

```bash
git rev-parse --show-toplevel
```

**Returns:** Absolute path (e.g., `/Users/user/code-dojo`)

**Use for:** Building absolute file paths, navigation

### 8. Working Directory Relative Path

Get the current directory relative to repository root:

```bash
git rev-parse --show-prefix
```

**Returns:** Relative path (e.g., `src/components/`)

**Use for:** Understanding current position in repository

## Complete Workflow Example

```bash
# Step 1: Verify git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: Not a git repository"
    exit 1
fi

# Step 2: Get repository metadata
REPO_ROOT=$(git rev-parse --show-toplevel)
REPO_NAME=$(basename -s .git $(git remote get-url origin 2>/dev/null) || basename "$REPO_ROOT")
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Step 3: Enumerate all tracked files
FILES=$(git ls-files)

# Step 4: Detect uncommitted changes
MODIFIED_COUNT=$(git status --porcelain | grep -c "^ M\|^M \|^MM" || echo "0")
UNTRACKED_COUNT=$(git ls-files --others --exclude-standard | wc -l | tr -d ' ')

# Step 5: Read file contents (use Read tool for each file)
# For each file in $FILES:
#   - Use Read tool to get contents
#   - Contents will include uncommitted changes automatically

# Step 6: Build analysis context
echo "Repository: $REPO_NAME"
echo "Branch: $CURRENT_BRANCH"
echo "Files: $(echo "$FILES" | wc -l)"
echo "Modified: $MODIFIED_COUNT"
echo "Untracked: $UNTRACKED_COUNT"
```

## Error Handling

### Not a Git Repository

**Error:** `fatal: not a git repository (or any of the parent directories): .git`

**Detection:**
```bash
git rev-parse --is-inside-work-tree 2>&1
```

**Response:**
```
Error: Not a git repository

Current directory is not a git repository: {current_path}

To analyze a directory, navigate to a git repository:
  cd /path/to/your/repo

Or to analyze a GitHub PR instead:
  /arch-analyze --pr <number|url>
```

### No Remote Configured

**Error:** `fatal: No remote configured to list refs from.`

**Fallback:**
```bash
# Use directory name as repository name
REPO_NAME=$(basename $(git rev-parse --show-toplevel))
```

### Permission Denied

**Error:** `fatal: could not read file`

**Detection:** Check exit code and error message

**Response:**
```
Error: Permission denied

Cannot read file: {file_path}

Ensure you have read permissions for the repository files.
```

### Large Repository Performance

For repositories with thousands of files:

1. **Use git ls-files:** Already optimized for performance
2. **Parallel file reading:** Process files in batches
3. **Filter by extension:** If needed, filter for relevant file types
4. **Progress indication:** Show progress for large operations

```bash
# Example: Filter for Python files only
git ls-files | grep "\.py$"

# Example: Count files first
TOTAL_FILES=$(git ls-files | wc -l)
echo "Analyzing $TOTAL_FILES files..."
```

## Integration with Architectural Analysis

### Data Structure to Build

After using git integration commands, build this context object:

```javascript
{
  mode: "directory",
  repoPath: "/Users/user/code-dojo",
  repoName: "code-dojo",
  currentBranch: "feature/auth",
  files: [
    {
      path: "app.py",
      content: "...",  // From Read tool
      modified: false,
      untracked: false
    },
    {
      path: "routes/auth.py",
      content: "...",
      modified: true,   // From git status
      untracked: false
    },
    {
      path: "new_file.py",
      content: "...",
      modified: false,
      untracked: true   // From git ls-files --others
    }
  ],
  uncommittedCount: 5,
  untrackedCount: 2,
  totalFiles: 47
}
```

### Pass to Architecture Analyzer

This context object is then passed to the architectural-analysis skill for:
- Component identification
- Dependency mapping
- Architecture diagram generation
- Report creation

## Best Practices

1. **Always verify git repository first** - Fail fast if not in a repo
2. **Use Read tool for file contents** - Handles all file types correctly
3. **Handle errors gracefully** - Provide clear error messages
4. **Consider performance** - Use efficient git commands
5. **Include uncommitted changes** - This is a key feature for real-time feedback
6. **Report metadata** - Include branch, modified count in output
7. **Use absolute paths** - Resolve all paths relative to repo root
8. **Parallel processing** - Read multiple files concurrently when possible

## Related Skills

- **architectural-analysis:** Uses the data gathered by this skill to perform analysis
- **pr-integration:** Alternative mode for analyzing GitHub pull requests

## References

See `references/git-commands.md` for complete command reference and examples.

## Examples

See `examples/directory-analysis-workflow.md` for a complete end-to-end workflow example.
