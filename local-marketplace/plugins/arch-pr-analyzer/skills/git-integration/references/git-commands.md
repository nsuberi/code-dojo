# Git Commands Reference

Complete reference for git commands used in directory analysis mode.

## Repository Detection

### Check if inside a git repository

```bash
git rev-parse --is-inside-work-tree
```

**Output:**
- `true` - Inside a git repository
- Error (exit code 128) - Not a git repository

**Example:**
```bash
$ cd /Users/user/code-dojo
$ git rev-parse --is-inside-work-tree
true

$ cd /tmp
$ git rev-parse --is-inside-work-tree
fatal: not a git repository (or any of the parent directories): .git
```

**Usage in script:**
```bash
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Valid git repository"
else
    echo "Not a git repository"
    exit 1
fi
```

## Repository Metadata

### Get repository root path

```bash
git rev-parse --show-toplevel
```

**Output:** Absolute path to repository root

**Example:**
```bash
$ cd /Users/user/code-dojo/src/components
$ git rev-parse --show-toplevel
/Users/user/code-dojo
```

### Get current directory relative to repo root

```bash
git rev-parse --show-prefix
```

**Output:** Relative path from root (empty if at root)

**Example:**
```bash
$ cd /Users/user/code-dojo/src/components
$ git rev-parse --show-prefix
src/components/

$ cd /Users/user/code-dojo
$ git rev-parse --show-prefix

```

### Get current branch name

```bash
git rev-parse --abbrev-ref HEAD
```

**Output:** Branch name

**Example:**
```bash
$ git rev-parse --abbrev-ref HEAD
feature/auth

$ git checkout main
$ git rev-parse --abbrev-ref HEAD
main
```

**Special cases:**
- Detached HEAD: Returns `HEAD`
- Empty repository: Error

### Get repository name

**Method 1: From remote URL**
```bash
git remote get-url origin
```

**Output:** Full remote URL

**Example:**
```bash
$ git remote get-url origin
https://github.com/username/code-dojo.git

$ git remote get-url origin
git@github.com:username/code-dojo.git
```

**Method 2: Extract name from URL**
```bash
basename -s .git $(git remote get-url origin)
```

**Output:** Repository name

**Example:**
```bash
$ basename -s .git $(git remote get-url origin)
code-dojo
```

**Method 3: Fallback to directory name**
```bash
basename $(git rev-parse --show-toplevel)
```

**Robust solution:**
```bash
# Try remote first, fallback to directory name
REPO_NAME=$(basename -s .git $(git remote get-url origin 2>/dev/null) || basename $(git rev-parse --show-toplevel))
```

### List all remotes

```bash
git remote
```

**Output:** List of remote names (one per line)

**Example:**
```bash
$ git remote
origin
upstream
```

### Get remote URL for specific remote

```bash
git remote get-url <remote-name>
```

**Example:**
```bash
$ git remote get-url upstream
https://github.com/original-org/code-dojo.git
```

## File Operations

### List all tracked files

```bash
git ls-files
```

**Output:** All tracked files (one per line)

**Example:**
```bash
$ git ls-files
.gitignore
README.md
app.py
config.py
routes/auth.py
routes/submissions.py
static/css/styles.css
static/js/app.js
templates/index.html
```

**With filters:**
```bash
# Only Python files
git ls-files | grep "\.py$"

# Files in specific directory
git ls-files | grep "^routes/"

# Multiple extensions
git ls-files | grep -E "\.(py|js|html)$"
```

**Performance:** Very fast, uses git index

### List untracked files

```bash
git ls-files --others --exclude-standard
```

**Output:** Untracked files (not ignored)

**Example:**
```bash
$ git ls-files --others --exclude-standard
new_feature.py
temp_notes.txt
```

**Flags:**
- `--others` - Show untracked files
- `--exclude-standard` - Respect .gitignore

### List ignored files

```bash
git ls-files --others --ignored --exclude-standard
```

**Example:**
```bash
$ git ls-files --others --ignored --exclude-standard
__pycache__/
.env
*.pyc
node_modules/
```

### Check if specific file is tracked

```bash
git ls-files --error-unmatch <file-path>
```

**Exit codes:**
- 0 - File is tracked
- 1 - File is not tracked

**Example:**
```bash
$ git ls-files --error-unmatch app.py
app.py

$ git ls-files --error-unmatch nonexistent.py
error: pathspec 'nonexistent.py' did not match any file(s) known to git
```

## Status and Changes

### Get working directory status

```bash
git status --porcelain
```

**Output format:**
```
XY PATH
```

Where:
- `X` = index status (staged)
- `Y` = working tree status (unstaged)

**Status codes:**
- `??` - Untracked
- ` M` - Modified (not staged)
- `M ` - Modified (staged)
- `MM` - Modified (staged and more changes)
- `A ` - Added (new file, staged)
- `AM` - Added (staged) with modifications
- ` D` - Deleted (not staged)
- `D ` - Deleted (staged)
- `R ` - Renamed (staged)
- `C ` - Copied (staged)
- `!!` - Ignored (with `--ignored` flag)

**Example:**
```bash
$ git status --porcelain
 M app.py
M  routes/auth.py
MM config.py
?? new_file.py
```

**Parsing:**
```bash
# Count modified files
git status --porcelain | grep -c "^ M\|^M \|^MM"

# Count untracked files
git status --porcelain | grep -c "^??"

# List only modified files
git status --porcelain | grep "^ M\|^M \|^MM" | cut -c4-

# Check if working directory is clean
[ -z "$(git status --porcelain)" ] && echo "Clean" || echo "Dirty"
```

### Short status (human-readable)

```bash
git status --short
```

**Output:** Same as `--porcelain` but may include color

### Get list of modified files only

```bash
git diff --name-only
```

**Output:** Files with unstaged changes

**Example:**
```bash
$ git diff --name-only
app.py
config.py
```

### Get list of staged files

```bash
git diff --name-only --cached
```

**Output:** Files with staged changes

**Example:**
```bash
$ git diff --name-only --cached
routes/auth.py
```

### Get all changed files (staged + unstaged)

```bash
git diff --name-only HEAD
```

**Output:** All modified files

## File Content Access

### Read file from working directory

**Method 1: Standard cat (for text files)**
```bash
cat path/to/file.py
```

**Method 2: Handle binary files**
```bash
file path/to/file.png  # Check if binary first
```

**Method 3: Git show (for specific commit)**
```bash
git show HEAD:path/to/file.py
```

**For directory analysis, always read from working directory** to include uncommitted changes.

### Check file type

```bash
file -b path/to/file
```

**Output:** File type description

**Example:**
```bash
$ file -b app.py
Python script, ASCII text

$ file -b image.png
PNG image data, 800 x 600, 8-bit/color RGBA, non-interlaced
```

## Commit History

### Get latest commit hash

```bash
git rev-parse HEAD
```

**Output:** Full commit SHA

**Example:**
```bash
$ git rev-parse HEAD
84d230d5f3c4e2b1a9876543210abcdef1234567
```

### Get short commit hash

```bash
git rev-parse --short HEAD
```

**Output:** Short commit SHA (7 chars)

**Example:**
```bash
$ git rev-parse --short HEAD
84d230d
```

### Get commit message

```bash
git log -1 --pretty=%B
```

**Output:** Full commit message

**Example:**
```bash
$ git log -1 --pretty=%B
Add authentication feature

This commit implements user authentication with JWT tokens.
```

### Get commit info (one line)

```bash
git log -1 --oneline
```

**Example:**
```bash
$ git log -1 --oneline
84d230d Add authentication feature
```

## Statistics

### Count tracked files

```bash
git ls-files | wc -l
```

**Example:**
```bash
$ git ls-files | wc -l
      47
```

### Count files by extension

```bash
git ls-files | grep "\.py$" | wc -l
```

**Example:**
```bash
$ git ls-files | grep "\.py$" | wc -l
      23

$ git ls-files | grep "\.js$" | wc -l
       8
```

### Repository size

```bash
du -sh .git
```

**Example:**
```bash
$ du -sh .git
  12M	.git
```

## Error Patterns

### Not a git repository

**Command:** Any git command

**Error:**
```
fatal: not a git repository (or any of the parent directories): .git
```

**Exit code:** 128

**Detection:**
```bash
git rev-parse --is-inside-work-tree >/dev/null 2>&1
if [ $? -eq 128 ]; then
    echo "Not a git repository"
fi
```

### No remote configured

**Command:** `git remote get-url origin`

**Error:**
```
fatal: No remote configured to list refs from.
```

**Fallback:**
```bash
REPO_NAME=$(git remote get-url origin 2>/dev/null || basename $(git rev-parse --show-toplevel))
```

### Ambiguous argument

**Command:** `git rev-parse <name>`

**Error:**
```
fatal: ambiguous argument '<name>': unknown revision or path not in the working tree.
```

**Occurs when:** Branch or commit doesn't exist

### Permission denied

**Command:** `cat <file>` or `git` commands

**Error:**
```
fatal: unable to read file
Permission denied
```

**Detection:**
```bash
if [ ! -r "path/to/file" ]; then
    echo "Cannot read file: permission denied"
fi
```

## Complete Examples

### Example 1: Basic repository check

```bash
#!/bin/bash

# Verify git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: Not a git repository"
    exit 1
fi

echo "✓ Valid git repository"

# Get basic info
REPO_ROOT=$(git rev-parse --show-toplevel)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
FILE_COUNT=$(git ls-files | wc -l | tr -d ' ')

echo "Repository: $REPO_ROOT"
echo "Branch: $BRANCH"
echo "Files: $FILE_COUNT"
```

### Example 2: Detect uncommitted changes

```bash
#!/bin/bash

# Get status
STATUS=$(git status --porcelain)

if [ -z "$STATUS" ]; then
    echo "Working directory clean"
else
    # Count changes
    MODIFIED=$(echo "$STATUS" | grep -c "^ M\|^M \|^MM" || echo "0")
    UNTRACKED=$(echo "$STATUS" | grep -c "^??" || echo "0")
    STAGED=$(echo "$STATUS" | grep -c "^M \|^A " || echo "0")

    echo "Modified: $MODIFIED"
    echo "Untracked: $UNTRACKED"
    echo "Staged: $STAGED"
fi
```

### Example 3: List all Python files

```bash
#!/bin/bash

# Get all tracked Python files
PYTHON_FILES=$(git ls-files | grep "\.py$")

echo "Python files in repository:"
echo "$PYTHON_FILES"

# Count
COUNT=$(echo "$PYTHON_FILES" | wc -l | tr -d ' ')
echo "Total: $COUNT files"
```

### Example 4: Robust repository name

```bash
#!/bin/bash

# Try multiple methods to get repo name
get_repo_name() {
    # Method 1: From origin remote
    if REMOTE_URL=$(git remote get-url origin 2>/dev/null); then
        basename -s .git "$REMOTE_URL"
        return
    fi

    # Method 2: From any remote
    if FIRST_REMOTE=$(git remote | head -1); then
        if REMOTE_URL=$(git remote get-url "$FIRST_REMOTE" 2>/dev/null); then
            basename -s .git "$REMOTE_URL"
            return
        fi
    fi

    # Method 3: From directory name
    basename "$(git rev-parse --show-toplevel)"
}

REPO_NAME=$(get_repo_name)
echo "Repository name: $REPO_NAME"
```

## Performance Considerations

### Fast operations (< 100ms)
- `git rev-parse --is-inside-work-tree`
- `git rev-parse --abbrev-ref HEAD`
- `git ls-files`
- `git status --porcelain`

### Medium operations (100ms - 1s)
- `git diff --name-only HEAD`
- Reading file contents (depends on file size)

### Potentially slow operations (> 1s)
- Reading many large files
- Operations on very large repositories (> 100k files)

### Optimization strategies

1. **Use git index operations** - `git ls-files` is much faster than `find`
2. **Filter early** - Use grep to filter file lists before processing
3. **Parallel processing** - Read multiple files concurrently
4. **Batch operations** - Process files in batches of 10-100
5. **Cache results** - Cache git metadata if running multiple commands

## See Also

- Main skill documentation: `../SKILL.md`
- Complete workflow example: `../examples/directory-analysis-workflow.md`
- Git documentation: https://git-scm.com/docs
