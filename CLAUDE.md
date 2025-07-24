# Development Assistant Guidelines

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
- Test all API client methods with mocked responses
- Test all API endpoints/routes that call external services
- Include tests for error handling, timeouts, and retry logic
- Create mock fixtures for API responses
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

## Parallel Development with Git Worktrees

### Setup Multiple Worktrees
For parallel development across multiple Claude instances:

```bash
# Run the setup script to create 3 worktrees
./setup_worktrees.sh

# This creates:
# ../PrepSense-worktrees/feature     - For new features
# ../PrepSense-worktrees/bugfix      - For bug fixes  
# ../PrepSense-worktrees/experiment  - For experiments
```

### Initialize Each Worktree
For each worktree, run:
```bash
cd ../PrepSense-worktrees/[feature|bugfix|experiment]
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

### Important Notes
- Each worktree needs its own Python venv and node_modules
- All worktrees connect to the same GCP database
- The .env file must be copied to each worktree
- Run health checks before switching between worktrees

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
- Setup file: `jest.setup.js` - Contains mocks for React Native modules
- Test directory: `__tests__/` with subdirectories for components, screens, utils, and api

**Key Testing Dependencies:**
- `jest-expo`: Jest preset configured for Expo
- `@testing-library/react-native`: Testing utilities for React Native
- `react-test-renderer`: Required for component rendering in tests

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

#### API Mocking
Use the mock helpers in `__tests__/helpers/apiMocks.ts`:
```javascript
import { mockFetch, createMockRecipe } from '@/__tests__/helpers/apiMocks';

global.fetch = mockFetch({ recipes: [createMockRecipe()] });
```

### Running Tests
```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test

# Run specific test file
npm test RecipeCompletionModal.test.tsx

# Generate coverage report
npm test -- --coverage
```

### Test Best Practices
1. **Always test actual behavior, not implementation details**
2. **Use `testID` props for reliable element selection**
3. **Mock external dependencies (APIs, async storage, etc.)**
4. **Write tests that verify all items in lists are rendered**
5. **Test both success and error scenarios**
6. **Use meaningful test descriptions**

### Common Test Patterns
- **Modal tests**: Check visibility prop changes
- **List tests**: Verify item count and order
- **API tests**: Mock responses and test error handling
- **Navigation tests**: Mock navigation functions

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

Last updated: 2025-07-19