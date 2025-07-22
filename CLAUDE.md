# Development Assistant Guidelines

## 🚨 IMPORTANT: Multi-Instance Collaboration - START HERE! 🚨

**EVERY Claude instance MUST do this at startup and after any git operation:**
```bash
# Read all instance notes to sync knowledge
cat WORKTREE_NOTES_*.md
```

**Your role is determined by your worktree:**
- `/PrepSense` → MAIN instance → Write to `WORKTREE_NOTES_MAIN.md`
- `/PrepSense-worktrees/bugfix` → BUGFIX instance → Write to `WORKTREE_NOTES_BUGFIX.md`
- `/PrepSense-worktrees/testzone` → TESTZONE instance → Write to `WORKTREE_NOTES_TESTZONE.md`

**Collaboration triggers - Read notes when:**
1. Starting any new task
2. After any `git pull`, `git checkout`, or `git commit`
3. Before making any significant changes
4. If you see `.claude_collaboration_reminder` file

**Quick reference:**
- Read all notes: `cat WORKTREE_NOTES_*.md`
- Check status: `./check_collaboration_status.sh`
- See guide: `cat CLAUDE_COLLABORATION_GUIDE.md`

## 🔧 CRITICAL: Worktree & Symlink Setup

**CLAUDE.md is shared via symlinks** - Changes in any worktree update all instances immediately!

### Key Facts:
- **Main directory** (`/PrepSense`): Contains actual CLAUDE.md file (tracked by git)
- **Worktrees** (`/PrepSense-worktrees/*`): Have symlinks pointing to main CLAUDE.md
- **WORKTREE_NOTES_*.md**: Actual files in main dir, symlinked from worktrees (NOT tracked by git)
- Each worktree needs its own Python venv and node_modules
- All worktrees share: Git history, GCP database, CLAUDE.md, and WORKTREE_NOTES files

### Quick Setup:
```bash
# List worktrees
git worktree list

# Create worktree (if needed)
git worktree add ../PrepSense-worktrees/newbranch -b branch-name

# Initialize worktree
cd ../PrepSense-worktrees/newbranch
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cd ios-app && npm install && cd ..
cp ../../PrepSense/.env .  # Copy env file
```

---

# Project guidelines for Claude Code
Section 1 must be followed no matter what. 
## Section 1: Core principles Must be Followed.

- **Targeted modifications only.**  When asked to add a feature or fix a bug, modify only the specified files, classes or functions.  Do not refactor unrelated code, change formatting or remove comments unless explicitly asked:contentReference[oaicite:0]{index=0}.
- **Preserve existing functionality.**  When adding a feature, clearly identify what must be preserved.  For example: “Add price filters to the product page **without removing any other features**”:contentReference[oaicite:1]{index=1}.  When removing a feature, specify the core functionality that must remain intact:contentReference[oaicite:2]{index=2}.
- **Test‑driven workflow.**  Before making any changes, write or update tests covering the desired behaviour and run them.  Confirm they fail, then implement only the code needed to make them pass:contentReference[oaicite:3]{index=3}.  Do **not** modify tests while implementing the fix.
- **Explain cross‑file edits.**  Do not touch other methods or files unless absolutely necessary:contentReference[oaicite:4]{index=4}.  If a change outside the targeted area is required (e.g., to import a new package), explain why you’re doing it.

## Workflow

1. **Research and plan** – When given a task, read the relevant files and plan your approach.  Do not write code until you have proposed a plan and received approval.
2. **Write tests first** – Create or update tests that describe the expected behaviour.  Run them and ensure they fail:contentReference[oaicite:5]{index=5}.
- Be sure to typecheck when you’re done making a series of code changes
- Prefer running single tests, and not the whole test suite, for performance
3. **Implement in small increments** – Make the minimal change required to satisfy the failing test.  After each change, run the linter, type checker and test suite.  Once the tests pass, commit the change with a descriptive message.
4. **Reset context regularly** – Use `/clear` to reset Claude’s context between tasks so old instructions do not carry over:contentReference[oaicite:6]{index=6}.

## Command and tool guidelines

- Use `gh` commands (e.g. `gh issue view`, `gh pr create`) for GitHub interactions:contentReference[oaicite:7]{index=7}.
- Use bash tools to run tests (`npm test`, `pytest`), type‑check (`tsc --noEmit`, `mypy`), and lint (`eslint`, `pylint`).  Stop and ask for help if any command fails.
- When working with external libraries (e.g., crewAI), ensure you actually import and call the library’s API; do not reimplement its classes or functions under a different name.

## Safety instructions

- Do not introduce placeholder logic (e.g. `return null`) or leave TODOs in production code.
- Do not auto‑refactor or reformat files unless explicitly requested.
- Do not remove trailing newlines or comments unless removing the entire code block:contentReference[oaicite:8]{index=8}.

## Section 2

### Git Commit Policy
**NEVER include "Claude" or any reference to Claude AI in:**
- Commit messages
- Co-author lines  
- Any part of the git history

**NEVER add co-authorship attributions:**
- Do NOT include "Co-authored-by:" lines in commits or PRs
- Do NOT add any assistant, AI, or any other contributor attribution besides dankimjw
- Only the user (Daniel Kim) should appear as the commit author
- Specifically avoid: "Co-authored-by: Assistant <noreply@dev.com>"
- Specifically avoid: "Co-authored-by: Claude <noreply@anthropic.com>"

## Code Guidelines
- Always ask before making large changes such as adding authentication or deleting features
- Follow existing code patterns and conventions
- Preserve existing functionality when making changes
- If you are not sure an API exists or a behaviour is correct, answer Iʼm not sure.
- Test changes thoroughly before committing
- Always show an implementation plan and get approval before implementing.
- After producing code, list each acceptance criterion again and mark ✅ / ❌ based on your own output.
- **ALWAYS run health checks after making changes to verify the app still works**

## Dependency Management
**ALWAYS register new libraries and dependencies properly:**
- For JavaScript/TypeScript: Run `npm install <package>` in the appropriate directory (ios-app/ for frontend)
- For Python: Run `pip install <package>` and update requirements.txt using `pip freeze > requirements.txt`
- **NEVER import a library without first installing it as a dependency**
- After adding any dependency, verify it's listed in package.json or requirements.txt
- Document any new dependencies in the relevant documentation (see Documentation Structure below)

## Testing Requirements
**ALWAYS create comprehensive tests for any external API usage:**
- Test all API client methods with real or integration test responses
- Test all API endpoints/routes that call external services
- Include tests for error handling, timeouts, and retry logic
- Test authentication/API key configuration
- Add integration tests for complex flows

## Health Check Scripts
**Before committing any changes, verify the app works using these scripts:**

### Quick Check (30 seconds)
```bash
./quick_check.sh
```
- Fast port connectivity tests
- Process status validation
- Immediate pass/fail feedback

### Comprehensive Check (2 minutes) 
```bash
python check_app_health.py
```
- Full backend health validation
- API endpoint testing 
- iOS app bundle verification
- Environment configuration check
- Detailed diagnostic output with colored results

**Usage in development workflow:**
1. Make code changes
2. Run `./quick_check.sh` for immediate feedback
3. Run `python check_app_health.py` for full validation before commits
4. Both scripts return proper exit codes for CI/CD integration

## Project-Specific Notes
- This is a PrepSense project - a pantry management application
- Uses React Native for mobile, FastAPI for backend
- **PostgreSQL database is hosted on Google Cloud SQL, NOT locally**
  - Do NOT attempt to connect to local PostgreSQL
  - Database connection is configured through environment variables
  - Use the backend API endpoints to verify database connectivity
  - Database changes must be run against the GCP Cloud SQL instance
- **Environment configuration is in `/Users/danielkim/_Capstone/PrepSense/.env`**
  - This is the MAIN .env file for the entire project
  - Backend should read from this file, NOT from backend_gateway/.env
  - Contains GCP database credentials, API keys, and service configurations
- Always maintain backwards compatibility with existing data

## Common Issues & Solutions
- **Router warnings**: Ensure all React components have `export default ComponentName;`
- **404 health endpoint**: Health endpoint is at `/api/v1/health` not `/health`
- **Port conflicts**: Use health check scripts to identify port issues
- **Backend not starting**: Check if virtual environment is activated

## Quick Start Commands
```bash

# run_app.py will start the back end fastapi and match the ip when launching the front end ios simulator when pressing 'i'
source venv/bin/activate && python run_app.py

# Health check
./quick_check.sh

# Full diagnostics
python check_app_health.py
```

## Parallel Development with Git Worktrees (Full Details)

### Setup Multiple Worktrees
For parallel development across multiple Claude instances:

```bash
# Run the setup script to create 3 worktrees
./setup_worktrees.sh

# This creates:
# ../PrepSense-worktrees/feature     - For new features
# ../PrepSense-worktrees/bugfix      - For bug fixes  
# ../PrepSense-worktrees/testzone    - For testing and experiments
```

### Initialize Each Worktree
For each worktree, run:
```bash
cd ../PrepSense-worktrees/[feature|bugfix|testzone]
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cd ios-app && npm install && cd ..
python setup.py
```

### Workflow
1. Open each worktree in a separate terminal tab
2. Start Claude in each directory with different tasks
3. All worktrees share the same Git history and database
4. Changes committed in one are immediately available to others

### Worktree Management
```bash
# List all worktrees
git worktree list

# Remove a worktree
git worktree remove ../PrepSense-worktrees/[name]

# Add a new worktree
git worktree add ../PrepSense-worktrees/newfeature -b new-branch
```

## MCP (Model Context Protocol) Servers

### Setup MCP Servers
```bash
# Install and run MCP servers (memory, sequential-thinking, filesystem)
./scripts/setup_mcp_servers.sh

# Check MCP status across all worktrees
./scripts/setup_mcp_servers.sh check
```

### MCP Configuration
- MCP servers provide enhanced capabilities for Claude:
  - **filesystem**: File operations with proper permissions
  - **memory**: Persistent memory across conversations (port 8003)
  - **sequential-thinking**: Step-by-step reasoning (port 8004)
  - **context7**: Up-to-date library documentation access
  - **ios-simulator**: iOS Simulator control and automation (option 1)
  - **mobile**: Mobile device control and automation (option 2)
- Each worktree needs its own `.mcp.json` configuration file
- Memory and sequential-thinking servers are shared across all worktrees
- To add MCP to a worktree: `cd /path/to/worktree && cp /Users/danielkim/_Capstone/PrepSense/.mcp.json .`

### Important MCP Notes
- The setup script and `.mcp.json` files are intentionally excluded from git
- MCP servers only need to be started once from any directory
- Use `claude mcp list` in any directory to verify available servers

## Context7 Documentation Tool

Context7 is an MCP server that provides up-to-date documentation for libraries. To use it:

### Setup
1. Ensure context7 is configured in your `.mcp.json` file
2. The server provides two main functions:
   - `resolve-library-id`: Resolves a library name to a Context7-compatible ID
   - `get-library-docs`: Fetches documentation for a specific library

### Usage
1. **Finding a library**: First resolve the library name to get its ID
   ```
   Example: When looking for "react" documentation, use resolve-library-id
   to get the correct library ID like "/facebook/react"
   ```

2. **Getting documentation**: Use the resolved library ID to fetch docs
   ```
   Example: get-library-docs with context7CompatibleLibraryID="/facebook/react"
   Optional parameters: topic="hooks", tokens=10000
   ```

### Common Libraries
- React: `/facebook/react`
- Next.js: `/vercel/next.js`
- Supabase: `/supabase/supabase`
- MongoDB: `/mongodb/docs`

### Best Practices
- Always resolve library names first unless the user provides an exact library ID
- Use the `topic` parameter to focus on specific documentation areas
- Adjust `tokens` parameter based on how much context you need (default: 10000)

## Mobile Testing MCP Tools

We have two MCP servers for mobile testing. Use whichever works properly - if one doesn't work, try the other.

### Option 1: iOS Simulator MCP
The ios-simulator MCP server enables programmatic control of the iOS Simulator.

**Setup:**
```bash
claude mcp add ios-simulator npx ios-simulator-mcp
```

**Features:**
- Launch and manage simulator instances
- Install and uninstall apps
- Take screenshots
- Simulate user interactions
- Access simulator logs

### Option 2: Mobile MCP
The mobile MCP server provides broader mobile device control and automation.

**Setup:**
```bash
claude mcp add mobile -- npx -y @mobilenext/mobile-mcp@latest
```

**Features:**
- Cross-platform mobile device control
- Advanced automation capabilities
- Device management and interaction
- Testing automation support

### Usage with PrepSense
- Automated testing of the iOS app
- Screenshot capture for documentation
- Debug simulator-specific issues
- Automate repetitive testing tasks
- Test app behavior across different devices

### Best Practices
- Try ios-simulator first for iOS-specific testing
- Use mobile MCP if ios-simulator encounters issues
- Ensure Xcode is installed and iOS Simulator is available
- Close unused simulators to free resources
- Coordinate with `python run_app.py` for integrated testing
- Restart Claude Code after adding either server

## React Native Testing Guide

### Test Setup
The project uses Jest with React Native Testing Library for unit and integration tests.

**Configuration:**
- Jest preset: `jest-expo`
- Config file: `jest.config.js` - Jest configuration with proper settings
- Setup file: `jest.setup.js` - Contains mocks for React Native modules
- Test directory: `__tests__/` with subdirectories for components, screens, utils, and api

**Key Testing Dependencies:**
- `jest-expo`: Jest preset configured for Expo (handles React Native mocking)
- `@testing-library/react-native`: Testing utilities for React Native
- **Note**: Do NOT use `react-test-renderer` - it's deprecated for React 19+

### Writing Tests

#### Modal Visibility Testing
Test modal visibility using the `visible` prop:
```javascript
const { getByTestId } = render(<Modal testID="test-modal" visible={isVisible} />);
expect(getByTestId('test-modal')).toHaveProp('visible', true);
```

#### Testing Lists and Recipe Steps
Verify all items are rendered and in correct order:
```javascript
const steps = ['Chop onions', 'Saute vegetables', 'Simmer sauce'];
render(<RecipeSteps steps={steps} />);
expect(screen.getAllByRole('text')).toHaveLength(steps.length);
steps.forEach(step => expect(screen.getByText(step)).toBeTruthy());
```

#### API Testing
Use integration test helpers in `__tests__/helpers/testUtils.ts`:
```javascript
import { setupTestEnvironment } from '@/__tests__/helpers/testUtils';

// Setup test environment with real API endpoints
setupTestEnvironment();
```

### Running Tests
```bash
# Run all tests in watch mode (default)
npm test

# Run tests once (CI mode - recommended for development)
npm run test:ci

# Run specific test file
npm run test:ci -- __tests__/screens/RecipeTabs.test.tsx

# Run tests matching a pattern
npm run test:ci -- RecipeLogic

# Generate coverage report
npm run test:coverage
```

### Test Best Practices
1. **Always test actual behavior, not implementation details**
2. **Use `testID` props for reliable element selection**
3. **Use integration tests with real API endpoints when possible**
4. **Write tests that verify all items in lists are rendered**
5. **Test both success and error scenarios**
6. **Use meaningful test descriptions**

### Common Test Patterns
- **Modal tests**: Check visibility prop changes
- **List tests**: Verify item count and order
- **API tests**: Use integration tests with real endpoints
- **Navigation tests**: Test actual navigation flows

### Current Test Status (as of 2025-01-19)
- **Total Tests**: 71 (50 passing, 21 failing)
- **Passing Suites**: simple, recipeLogic, recipeApiIntegration, RecipeSteps
- **Known Issues**:
  - ApiClient tests need integration test setup
  - Some RecipeTabs tests have async timing issues
  - RecipeCompletionModal has prop validation failures
- **Note**: Run `npm run test:ci` for one-time test runs to avoid watch mode timeouts

## Documentation Structure

### Primary Documentation Locations:
1. **`/docs/` folder** - Main project documentation hub
   - Session summaries (e.g., `2025-01-19-session-summary.md`) for tracking development progress
   - `CHANGELOG.md` - Detailed technical changes with problem/solution format
   - `UPDATES_LOG.md` - High-level project updates
   - Feature documentation files (e.g., `RECIPE_COMPLETION_EDGE_CASES.md`)
   - Implementation status and test results

2. **`/backend_gateway/docs/`** - Backend-specific documentation
   - API implementation details
   - Database schema documentation
   - Feature-specific backend documentation

3. **Implementation Tracking:**
   - **Session summaries** in `/docs/` track what was implemented, tested, and needs verification
   - **CHANGELOG.md** documents all technical changes with detailed problem/solution entries
   - **Feature documentation** includes implementation status, code examples, and test results
   - **Test results** are documented in feature-specific files

### Documentation Requirements:
- Create session summaries for significant development work
- Update CHANGELOG.md with technical changes
- Document implementation status (implemented/tested/needs verification) in feature docs
- Include code examples and usage instructions
- Track test results and known issues
- Any Claude Code instance can refer to `/docs/` to understand project state

## Claude Multi-Instance Collaboration System

### 🚀 New Instance? Start Here!
```bash
cat START_HERE_CLAUDE.md
```

### Overview
A system for three Claude instances across git worktrees to collaborate, share knowledge, and verify each other's work.

### How It Works
1. **Each instance writes to their own notes file**:
   - Main: `WORKTREE_NOTES_MAIN.md`
   - Bugfix: `WORKTREE_NOTES_BUGFIX.md`
   - Testzone: `WORKTREE_NOTES_TESTZONE.md`

2. **All instances read all notes files** via symlinks

3. **Collaboration workflow**:
   - Start by reading all notes: `cat WORKTREE_NOTES_*.md`
   - Document findings in your assigned file
   - Mark items needing verification with ❓
   - Verify other instances' work and update ✅

### Quick Commands
```bash
# Check collaboration status
./check_collaboration_status.sh

# Read collaboration guide
cat CLAUDE_COLLABORATION_GUIDE.md

# See recent updates from all instances
tail -f WORKTREE_NOTES_*.md
```

### Benefits
- No redundant work - reuse discoveries
- Cross-verification reduces errors
- Faster development through parallel work
- Better test coverage through validation

Last updated: 2025-01-19

---

# CLAUDE.md – Project-wide rules for Claude Code
This file is automatically loaded by Claude Code.  
Follow it **exactly** even if an ad-hoc prompt is vague or incorrect.

---

## 1 · Core principles

| Rule | Why |
|------|-----|
| **Write tests first.**  Draft or extend failing tests, run them, then code until they pass. | Anthropic recommends the "write tests, commit; code, iterate, commit" loop. |
| **Plan before coding.**  Summarise intended edits, files, functions and tests.  Wait for confirmation if needed. | Prevents runaway refactors and hallucinated APIs. |
| **Targeted minimal edits.**  Touch only the files/functions named in the plan.  Explain every cross-file change. | Keeps diffs small and reviewable. |
| **No silent placeholders.**  Do not leave TODOs or `pass`.  Either implement or ask. | Avoids half-implemented features. |

---

## 2 · Approved MCP servers

| Server | Purpose |
|--------|---------|
| **ios-simulator** | Automate iOS Simulator: launch app, tap, scroll, read UI hierarchy, capture screenshots. |
| **mobile** | Similar automation for Android/iOS devices/emulators if needed. |
| **memory** | Persist project context (past test failures, decisions) across sessions. |
| **Apidog** | Send live HTTP requests to external APIs and to our FastAPI endpoints; fetch OpenAPI specs. |
| **PostgreSQL** | Natural-language queries against Cloud SQL to verify data persistence. |
| **Context7** | Pull up-to-date library docs (CrewAI, FastAPI, etc.) to avoid hallucinated APIs. |
| **Auto-Improve** | Monitor prompts & responses; suggest rewrites when hallucinations detected. |

Add or remove tools in `.claude.json` or via `/allowed-tools`.

---

## 3 · Test technology stack  

### Backend (Python)
* **pytest** – test runner  
* **pytest-asyncio** or `httpx.AsyncClient` – async endpoint tests  
* **pytest fixtures** – setup test data and environment for Spoonacular, OpenAI, CrewAI integration tests  
* **SQLAlchemy + pytest fixtures** – in-memory or containerised PostgreSQL  
* **Schemathesis / pytest-openapi** – contract-test FastAPI's OpenAPI schema  

### Front-end (React Native with Expo)
* **Jest** – JS test runner  
* **@testing-library/react-native** – unit & component assertions  
* **Detox** – e2e tests on local emulators (optional)  
* **ios-simulator / mobile MCP** – alternative e2e control via Claude  

---

## 4 · Workflow

1. **Plan**  
   - List endpoints / client functions affected.  
   - List tests to add (happy-path + edge cases).  
2. **Write / extend tests** in `tests/` (Python) or `__tests__/` (JS).  
3. **Run tests** – they should fail.  
4. **Code** – modify only what the failing tests require.  
5. **Re-run tests** until green.  
6. **Use MCP checks**  
   - `mcp__apidog__test_endpoint` → call live API routes.  
   - `mcp__postgresql__ask` → confirm DB rows.  
   - `mcp__ios-simulator__tap` / `query` → verify a modal truly appears.  
7. **Commit** – one logical change per commit.  
8. **Reviewer instance** – another Claude reads the diff & tests, runs them, writes feedback to `docs/api_review.md`.

---

## 5 · Backend testing specifics

* **Spoonacular / OpenAI wrappers** – integration tests with real API endpoints; test error handling and rate limiting.  
* **CrewAI integration** – test with actual CrewAI execution; verify proper arguments and handle exceptions.  
* **DB client (`db_client.py`)** – fixture spins up test DB; test CRUD & transaction rollback.  

---

## 6 · FastAPI endpoint tests

* Use `fastapi.testclient.TestClient(app)` (sync) or `httpx.AsyncClient` (async).  
* Override dependencies to inject mocks:  

```python
@app.dependency_overrides[get_spoonacular_client] = lambda: mock_spoon
```

* Assert that endpoints call mocked clients and return correct JSON.
* Contract test with Schemathesis against `/openapi.json`.

---

## 7 · Front-end tests

* Unit/component:

```jsx
render(<RecipeModal visible />);
expect(screen.getByText('Recipe')).toBeVisible();
```

* Detox/ios-simulator e2e:

```js
await element(by.id('openMenu')).tap();
await expect(element(by.id('recipeSteps'))).toBeVisible();
```

---

## 8 · File conventions

| Purpose            | Path                         |
| ------------------ | ---------------------------- |
| Service wrappers   | `src/clients/*.py`           |
| Pytest tests       | `tests/test_*.py`            |
| React-Native tests | `__tests__/*.test.js`        |
| E2E scripts        | `e2e/*.spec.js`              |
| Developer log      | `docs/api_implementation.md` |
| Reviewer feedback  | `docs/api_review.md`         |

---

## 9 · Allowed commands & tooling

* `pytest`, `pytest -k` for subsets
* `jest`, `npm test`
* `detox test` (or ios-simulator/mobile MCP)
* `mcp__*` tools listed above
* `/clear` between tasks to reset context

---

Adhere to these rules to ensure reliable, test-driven development and trustworthy automated UI checks for iOS/Android simulators.