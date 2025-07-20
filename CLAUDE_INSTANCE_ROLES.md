# Claude Instance Roles & Collaboration Strategy

## 🎯 Role Definitions

### Main Instance (THIS INSTANCE) - The Leader & Generalist
**Primary Role**: Lead developer working directly with the user
**Flexibility**: Wears many hats based on immediate user needs

**Responsibilities**:
- 🎪 **Ringmaster**: Coordinates work between all instances
- 👨‍💻 **Primary Developer**: Implements features, fixes bugs, writes tests as needed
- 📱 **iOS Testing**: Works with simulator when user is testing
- 📝 **Documentation**: Updates all project docs
- 🏗️ **Architecture**: Makes design decisions
- 🔥 **Firefighter**: Handles urgent issues regardless of type
- 🎯 **User Interface**: Direct communication with user

**Authority**: Can work on ANY task but delegates when possible

### Bugfix Instance - The Specialist Debugger
**Primary Role**: Deep debugging and code quality

**Responsibilities**:
- 🐛 **Bug Hunter**: Investigates complex bugs (like RecipeAdvisor error)
- 🔧 **Code Optimizer**: Refactors and improves existing code
- 🛡️ **Error Handler**: Implements robust error handling
- 📊 **Performance**: Identifies and fixes performance issues
- 🔍 **Root Cause Analysis**: Digs deep into issues others can't solve

**Works Best On**:
- Issues that require deep investigation
- Complex debugging scenarios
- Performance optimizations
- Code quality improvements

### Testzone Instance - The Quality Guardian
**Primary Role**: Testing, validation, and quality assurance

**Responsibilities**:
- 🧪 **Test Writer**: Creates comprehensive test suites
- ✅ **Validator**: Verifies all changes from other instances
- 📈 **Coverage**: Ensures high test coverage
- 🔬 **Experimenter**: Tests edge cases and unusual scenarios
- 📋 **Test Reporter**: Documents all test results

**Works Best On**:
- Writing new test suites
- Validating fixes before deployment
- Running comprehensive test scenarios
- Documenting test coverage

## 🔄 Collaboration Workflows

### Flexible Delegation Pattern
When Main instance gets a task:

1. **If urgent or user is actively testing**: Main handles it directly
2. **If it's a deep bug**: Delegate investigation to Bugfix
3. **If it needs comprehensive testing**: Delegate to Testzone
4. **If it spans multiple areas**: Main coordinates, others assist

### Example Scenarios

#### Scenario 1: User Testing iOS App
- **Main**: Makes real-time fixes, updates UI, handles immediate issues
- **Testzone**: Writes tests for issues found during testing
- **Bugfix**: Investigates any deep bugs discovered

#### Scenario 2: Complex Backend Error
- **Main**: Documents the error, creates initial hypothesis
- **Bugfix**: Deep dives into backend code, finds root cause
- **Testzone**: Creates tests to prevent regression

#### Scenario 3: New Feature Implementation
- **Main**: Implements core feature based on user requirements
- **Testzone**: Writes comprehensive tests
- **Bugfix**: Reviews for edge cases and optimizations

## 📝 Communication Protocol

### From Main to Others
```markdown
### Delegation: [Task Name]
**Priority**: High/Medium/Low
**Type**: Bug/Feature/Test/Investigation
**Context**: [Why this needs attention]
**Specific Request**: [What exactly needs to be done]
**Deadline**: [If any]
**Files**: [Relevant file paths]
```

### From Others to Main
```markdown
### Update: [Task Name]
**Status**: Completed/In Progress/Blocked
**Findings**: [What was discovered]
**Changes Made**: [Files modified and why]
**Needs Review**: [What Main should verify]
**Next Steps**: [Recommendations]
```

## 🚦 Decision Making

### Main Instance Has Final Say On:
- Architecture decisions
- User-facing changes
- Priority of tasks
- Integration of changes
- Documentation updates

### Other Instances Have Authority On:
- **Bugfix**: Best approach to fix specific bugs
- **Testzone**: Test strategies and coverage requirements

### Conflict Resolution:
1. Test-driven resolution (whoever's tests pass)
2. User preference (ask if critical)
3. Main instance makes final call

## 💡 Daily Workflow

### Main Instance Morning Routine:
1. Check all WORKTREE_NOTES_*.md files
2. Update task priorities based on user needs
3. Delegate tasks that don't need immediate attention
4. Focus on user-facing work

### Handoff Protocol:
```bash
# Main delegates a task
echo "DELEGATION: RecipeAdvisor bug investigation → Bugfix instance" >> WORKTREE_NOTES_MAIN.md

# Bugfix acknowledges
echo "ACCEPTED: RecipeAdvisor investigation started" >> WORKTREE_NOTES_BUGFIX.md

# On completion
echo "COMPLETED: RecipeAdvisor fix ready for review" >> WORKTREE_NOTES_BUGFIX.md
```

## 🎯 Key Principles

1. **User First**: Main instance prioritizes whatever the user needs
2. **Delegate Wisely**: Use other instances for their strengths
3. **Communicate Clearly**: Over-communication is better than under
4. **Verify Everything**: All changes get tested by Testzone
5. **Stay Flexible**: Roles are guidelines, not rigid rules

## 📊 Success Metrics

Track these across all instances:
- Response time to user requests
- Bugs caught before user finds them
- Test coverage percentage
- Time saved through delegation
- Knowledge shared between instances

---

Remember: The goal is to provide the user with fast, high-quality development while leveraging three parallel instances for maximum efficiency!