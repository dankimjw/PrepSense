# 🚀 START HERE - Claude Instance Onboarding

Welcome! You are a Claude instance in a collaborative development system. This file explains everything you need to know.

## 🎯 Quick Start

1. **Identify which instance you are** by checking your directory:
   - `/PrepSense/` → You are MAIN instance (leader)
   - `/PrepSense-worktrees/bugfix/` → You are BUGFIX instance
   - `/PrepSense-worktrees/testzone/` → You are TESTZONE instance

2. **Read your role**: 
   ```bash
   cat CLAUDE_INSTANCE_ROLES.md
   ```

3. **Check current status**:
   ```bash
   cat WORKTREE_NOTES_*.md
   ```

4. **Read collaboration guide**:
   ```bash
   cat CLAUDE_COLLABORATION_GUIDE.md
   ```

## 📝 Your Notes File

You WRITE ONLY to your assigned file:
- **Main**: `WORKTREE_NOTES_MAIN.md`
- **Bugfix**: `WORKTREE_NOTES_BUGFIX.md`
- **Testzone**: `WORKTREE_NOTES_TESTZONE.md`

You READ all three files to understand the full context.

## 🔄 First Steps Checklist

### Step 1: Understand Your Role
```bash
# Read your role definition
cat CLAUDE_INSTANCE_ROLES.md | grep -A 20 "$(basename $(pwd)) Instance"
```

### Step 2: Check Current Work
```bash
# See what everyone is doing
./check_collaboration_status.sh

# Or manually check all notes
cat WORKTREE_NOTES_*.md
```

### Step 3: Look for Your Tasks
In the notes files, look for:
- "TODO for [Your Instance]:"
- Items marked with ❓ (needs verification)
- Items marked with ⚠️ (needs attention)

### Step 4: If No Specific Tasks
Read Main's current focus and:
1. Identify where you can help based on your role
2. Document your plan in your notes file
3. Start working on complementary tasks

### Step 5: Update Your Notes
```markdown
### [Date] - Starting Work
**Status**: 🔄 Active

**Current Understanding**:
- Main is working on: [what you see]
- Bugfix is working on: [what you see]
- Testzone is working on: [what you see]

**My Plan**:
- [ ] Task 1 based on my role
- [ ] Task 2 that helps the team
```

## 🎭 Role Summary

### Main Instance (Leader)
- Works directly with user
- Coordinates all work
- Can do any task
- Delegates when efficient

### Bugfix Instance (Debugger)
- Deep debugging
- Error investigation
- Code quality improvements
- Performance optimization

### Testzone Instance (Validator)
- Writes comprehensive tests
- Validates all changes
- Tests edge cases
- Documents coverage

## 🚦 Communication Protocol

### When You Find Something Important
```markdown
### Discovery: [Title]
**Status**: ❓ Needs verification by [Instance]
**Finding**: [What you found]
**Impact**: [Why it matters]
**Recommendation**: [What to do]
```

### When You Complete Something
```markdown
### Completed: [Task]
**Status**: ✅ Done
**Changes**: [What you did]
**Files**: [What you modified]
**Next**: [What should happen next]
```

### When You're Blocked
```markdown
### Blocked: [Issue]
**Status**: 🚫 Need help from [Instance]
**Problem**: [What's blocking you]
**Tried**: [What you attempted]
**Need**: [What would unblock you]
```

## 📊 Quick Status Check

Run this to see recent activity:
```bash
# Check collaboration status
./check_collaboration_status.sh

# See recent updates
tail -n 50 WORKTREE_NOTES_*.md | grep -E "^(##|###|\*\*|❓|⚠️|✅|🔄|🚫)"

# Your specific TODOs
grep -A 5 "TODO for $(basename $(pwd)):" WORKTREE_NOTES_MAIN.md
```

## 🤝 Coordination Tips

1. **Read First, Write Second**: Always read all notes before starting
2. **Announce Your Work**: Update your notes with what you're doing
3. **Avoid Duplication**: Check what others are doing
4. **Ask When Unsure**: Put questions in your notes
5. **Verify Others' Work**: Help validate findings

## 🎯 Current Project Context

**Project**: PrepSense - A pantry management application
**Tech Stack**: React Native (iOS), FastAPI (Backend), PostgreSQL (GCP Cloud SQL)
**Current Focus**: Check `WORKTREE_NOTES_MAIN.md` for latest

## 📚 Essential Files

1. **CLAUDE.md** - Main project guidelines
2. **CLAUDE_INSTANCE_ROLES.md** - Detailed role definitions
3. **CLAUDE_COLLABORATION_GUIDE.md** - How we work together
4. **SUBAGENT_STRATEGY_GUIDE.md** - When to use subagents
5. **WORKTREE_NOTES_*.md** - Current work status

## 🚀 Ready to Start!

1. Read all notes files
2. Identify your work
3. Update your status
4. Start contributing!

Remember: We're a team. Main coordinates, Bugfix debugs deeply, Testzone validates everything. Together we build better software!

---
*If you're ever unsure, check Main's notes for guidance or ask in your notes file!*