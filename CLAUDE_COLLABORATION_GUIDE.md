# Claude Multi-Instance Collaboration Guide

## 🎯 Purpose
This system enables three Claude instances across different git worktrees to collaborate effectively, share knowledge, and verify each other's work to produce higher quality, bug-free code.

## 📁 File Structure

Each Claude instance has:
- **Write Permission**: Only to their assigned notes file
- **Read Permission**: All three notes files

| Worktree | Branch | Notes File | Role |
|----------|--------|------------|------|
| Main | cleanup/remove-outdated-crewai-docs | WORKTREE_NOTES_MAIN.md | Primary development |
| Bugfix | feat/recipe-quality-improvements | WORKTREE_NOTES_BUGFIX.md | Bug fixes & improvements |
| Testzone | fix-shopping-list-fractions | WORKTREE_NOTES_TESTZONE.md | Testing & validation |

## 🔄 Workflow Process

### 1. Starting Work (READ Phase)
```bash
# First, read all notes files
cat WORKTREE_NOTES_*.md

# Check for:
- Unfinished tasks from other instances
- Items marked "Needs Verification"
- Recent discoveries that affect your work
- Test results to validate
```

### 2. During Work (WRITE Phase)
Update your assigned notes file with:
- Current task and approach
- Code changes with file paths
- Test results
- Discoveries and insights
- Items that need verification

### 3. Cross-Verification Process
When you see "⚠️ Needs Verification" in another instance's notes:
1. Read their hypothesis/finding
2. Test it independently
3. Update the verification section in THEIR notes file
4. Document results in YOUR notes file

### 4. Knowledge Sharing Format

#### For Code Changes:
```markdown
### Feature: [Name]
**Files Modified**:
- `/path/to/file.ts:123` - Added validation
- `/path/to/other.ts:45-67` - Refactored function

**Code**:
```typescript
// Brief description
function example() {
  // implementation
}
```

**Test Command**: `npm test specific.test.ts`
**Result**: ✅ Passing (3/3 tests)
```

#### For Discoveries:
```markdown
### Discovery: [Topic]
**Context**: Where/how discovered
**Finding**: What was learned
**Verification**: ❓ Needs verification by [instance]
**Impact**: How this affects the codebase
```

## 🛡️ Error Prevention Strategies

### 1. Fact Checking Protocol
- Mark uncertain findings with ❓
- Request verification from specific instances
- Document both positive and negative results
- Include reproduction steps

### 2. Test-First Verification
Before implementing based on another instance's notes:
1. Run their test commands
2. Verify file paths exist
3. Check for conflicting changes
4. Validate assumptions

### 3. Conflict Resolution
If instances disagree:
1. Both document their findings
2. Third instance acts as tiebreaker
3. Run empirical tests
4. Document final decision

## 📋 Templates

### Daily Status Update
```markdown
### [Date] - [Time] Status
**Completed**:
- ✅ Task 1
- ✅ Task 2

**In Progress**:
- 🔄 Current task

**Blocked**:
- ❌ Blocker description

**For Verification**:
- ❓ Finding that needs checking
```

### Test Result
```markdown
### Test: [Test Name]
**Command**: `exact command used`
**Environment**: Node v20, npm 10.9.2
**Result**: ✅ Pass / ❌ Fail
**Output**:
```
paste relevant output
```
**Analysis**: What this means
```

## 🚀 Best Practices

1. **Be Specific**
   - Include line numbers
   - Show exact commands
   - Paste actual error messages

2. **Timestamp Everything**
   - Use format: 2025-01-19 14:30 PST
   - Note duration for long tasks

3. **Flag Uncertainty**
   - Use ❓ for uncertain findings
   - Use ⚠️ for critical issues
   - Use 🔍 for needs investigation

4. **Cross-Reference**
   - Link to relevant docs/issues
   - Reference other instances' findings
   - Point to specific sections

5. **Update Status**
   - Mark completed verifications
   - Update progress regularly
   - Clean up outdated info

## 🔧 Setup Instructions

### For Each Worktree:
```bash
# 1. Navigate to worktree
cd /path/to/worktree

# 2. Create symlinks to read other notes
ln -s ../PrepSense/WORKTREE_NOTES_*.md .

# 3. Add to .gitignore (if not already)
echo "WORKTREE_NOTES_*.md" >> .gitignore

# 4. Set up watch alias (optional)
alias watch-notes='watch -n 5 "tail -n 50 WORKTREE_NOTES_*.md"'
```

## 📊 Success Metrics

Track in your notes:
- Bugs caught by verification: X
- Time saved by reusing knowledge: Y hours
- Tests written/verified: Z
- Knowledge items shared: N

## 🎯 Goals

1. **Zero Redundancy**: Never re-learn what another instance discovered
2. **High Confidence**: Verify critical findings across instances
3. **Fast Iteration**: Share blockers and solutions immediately
4. **Quality Code**: Test everything, verify assumptions
5. **Clear Documentation**: Future instances can onboard quickly

## 💡 Example Collaboration

**Main Instance** discovers:
```markdown
### Discovery: Jest react-test-renderer deprecated
React 19+ doesn't support react-test-renderer
Use @testing-library/react-native instead
❓ Needs verification in actual React 19 project
```

**Testzone Instance** verifies:
```markdown
### Verification: react-test-renderer deprecation
✅ Confirmed - Tested in React 19.0.0 project
Error: "react-test-renderer doesn't support React 19"
Solution verified: @testing-library/react-native works
```

**Bugfix Instance** applies:
```markdown
### Applied: Jest configuration fix
Based on Main and Testzone findings
Updated all test files to use new library
Result: All tests now passing
```

---

Remember: The goal is to work as a cohesive team where each instance's strengths complement the others!