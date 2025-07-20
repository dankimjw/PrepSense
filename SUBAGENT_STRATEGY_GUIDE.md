# Subagent (Task Tool) Strategy Guide

## 🎯 Overview
This guide helps decide when to use subagents vs delegating to worktree instances.

## 🤖 What Are Subagents?
- Autonomous agents launched via the Task tool
- Stateless - no memory between invocations
- Single-purpose - complete one task and return
- Parallel - can launch multiple simultaneously
- Fast - no coordination overhead

## 📊 Decision Matrix

### ✅ Use Subagents When:

| Scenario | Example | Why |
|----------|---------|-----|
| Wide searches | "Find all files using RecipeAdvisor" | Can search entire codebase quickly |
| Parallel analysis | "Check 10 components for pattern X" | Launch 10 agents at once |
| Quick investigations | "What does each service do?" | Get summaries fast |
| User is waiting | "Find that error message" | Immediate results needed |
| Simple, bounded tasks | "Count TODO comments" | Clear start/end, no iteration |
| Information gathering | "List all API endpoints" | Collect data for main work |

### 🤝 Use Worktree Instances When:

| Scenario | Example | Why |
|----------|---------|-----|
| Complex debugging | "Fix RecipeAdvisor error" | Needs investigation + solution |
| Feature development | "Add new recipe filter" | Requires iteration |
| Test writing | "Create test suite for X" | Needs refinement |
| Verification tasks | "Validate this approach" | Requires back-and-forth |
| Learning/exploration | "Understand this system" | Builds on discoveries |
| Multi-step processes | "Refactor this module" | Sequential dependent tasks |

## 🔄 Hybrid Approach

### Pattern 1: Scout → Delegate
```
1. Main uses subagent: "Find all recipe-related components"
2. Main delegates to Bugfix: "Fix issues in these 5 components"
3. Bugfix works iteratively on each
```

### Pattern 2: Parallel Discovery
```
1. Launch 3 subagents simultaneously:
   - Agent 1: "Find all untested files"
   - Agent 2: "Find all TODO comments"  
   - Agent 3: "Find all deprecated code"
2. Compile results and prioritize
```

### Pattern 3: Verify Before Deep Dive
```
1. Subagent: "Does RecipeAdvisor exist in codebase?"
2. If yes → Delegate to Bugfix instance
3. If no → Different investigation needed
```

## 📝 Practical Examples

### Example 1: User Reports Bug
```markdown
User: "The app crashes when saving recipes"

Main Instance:
1. Subagent: "Find all files with recipe saving logic"
2. Subagent: "Search for error messages about saving"
3. Review results
4. Delegate to Bugfix: "Investigate crash in RecipeService.save()"
```

### Example 2: Code Quality Check
```markdown
User: "Are we following React best practices?"

Main Instance:
1. Launch 5 subagents in parallel:
   - "Check for useEffect dependencies"
   - "Find components without memoization"
   - "Look for inline styles"
   - "Find missing PropTypes"
   - "Check for console.logs"
2. Compile report for user
```

### Example 3: Test Coverage
```markdown
User: "What needs testing?"

Testzone Instance:
1. Subagent: "List all components without .test files"
2. Subagent: "Find functions over 20 lines without tests"
3. Create testing plan
4. Start writing tests (iterative work)
```

## 🚀 Subagent Best Practices

### DO:
- ✅ Give extremely detailed instructions
- ✅ Specify exactly what to return
- ✅ Use for read-only operations
- ✅ Launch multiple for parallel work
- ✅ Set clear boundaries

### DON'T:
- ❌ Use for writing complex code
- ❌ Expect iteration or refinement
- ❌ Use for tasks needing context
- ❌ Use when verification is critical
- ❌ Rely on for user interaction

## 💡 Quick Decision Guide

Ask yourself:
1. **Can this be done in one pass?** → Subagent
2. **Do I need to iterate?** → Worktree instance
3. **Is the user waiting?** → Subagent for quick info
4. **Multiple similar tasks?** → Multiple subagents
5. **Need to build on results?** → Worktree instance

## 📊 Efficiency Metrics

Track success by:
- Time saved through parallel execution
- Reduced back-and-forth with user
- Faster initial investigations
- More thorough searches
- Better task distribution

## 🎯 Rule of Thumb

> **"Use subagents for breadth, worktree instances for depth"**

- Subagents: Wide but shallow
- Worktree instances: Narrow but deep
- Combine both: Complete coverage

---

Remember: Subagents are tools to make the worktree instances more effective, not replacements for thoughtful development!