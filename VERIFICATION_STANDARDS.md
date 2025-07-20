# Verification Standards for Claude Instances

## 🚨 CRITICAL: Never Claim Something Works Without Proof

### ❌ INVALID Verifications (What NOT to do)
1. **"APIs are loaded correctly"** - Just because endpoints appear in OpenAPI spec doesn't mean they work
2. **"Database is connected"** - Don't trust status endpoints, test with actual data queries
3. **"Tests are passing"** - Show the actual test output, not just claim it
4. **"Import successful"** - Importing without errors doesn't mean the code works
5. **"Health check says it's healthy"** - Health endpoints can have bugs (as we found!)

### ✅ VALID Verifications (What TO do)

#### 1. API Endpoint Verification
```bash
# WRONG: "All APIs are working"
curl -s http://localhost:8001/openapi.json | grep paths  # This only shows registration!

# RIGHT: Test each endpoint with actual requests
curl -s http://localhost:8001/api/v1/demo/recipes | python -m json.tool
# Show the response data, not just "it works"
```

#### 2. Database Verification
```bash
# WRONG: "Database is connected because health endpoint says so"
curl -s http://localhost:8001/api/v1/health  # Can be buggy!

# RIGHT: Query actual data
curl -s http://localhost:8001/api/v1/demo/recipes  # Returns real data
curl -s http://localhost:8001/api/v1/demo/pantry-status  # Shows DB queries work
```

#### 3. Test Verification
```bash
# WRONG: "Tests are passing"

# RIGHT: Show exact output
npm run test:ci -- RecipeLogic.test.ts
# Output: Test Suites: 1 passed, 1 total
# Tests: 8 passed, 8 total
```

#### 4. Process Verification
```bash
# WRONG: "Backend is running"

# RIGHT: Show process AND test endpoint
ps aux | grep uvicorn  # Show PID
curl -s http://localhost:8001/  # Show response
```

## 📋 Verification Checklist Template

When verifying ANYTHING, use this template:

```markdown
### Verification: [Feature Name]
**Claimed by**: [Which instance]
**Verified by**: [Your instance]
**Date**: [Timestamp]

**Step 1: Show the claim**
- Original claim: "X is working"
- Evidence provided: [what they showed]

**Step 2: Independent test**
Command: `[exact command]`
Output:
```
[paste full output]
```

**Step 3: Edge case test**
Command: `[test edge case]`
Output:
```
[paste output]
```

**Step 4: Verdict**
- ✅ VERIFIED: Works as claimed
- ❌ FALSE: Doesn't work (explain why)
- ⚠️ PARTIAL: Works with caveats (list them)
```

## 🔍 Common False Positives to Watch For

### 1. Health Endpoints
- Health endpoint says "database_connected: true" but DB queries fail
- Health endpoint returns 200 OK but subsystems are broken
- **Always test with real data queries**

### 2. Import Success
- `from module import X` succeeds but X.method() fails at runtime
- Module loads but is misconfigured
- **Always test the actual functionality**

### 3. Process Running
- Process exists but is in error state
- Port is open but not responding correctly
- **Always make actual API calls**

### 4. Test Passing
- Old test results being shown
- Tests pass in isolation but fail in full suite
- Mocked tests that don't reflect reality
- **Always run tests fresh and show timestamps**

## 🚫 Red Flags in Verifications

If you see these, the verification is suspect:

1. **No command output shown** - "I checked and it works"
2. **Vague success claims** - "Everything looks good"
3. **No error checking** - Only showing happy path
4. **No timestamps** - Could be stale results
5. **No edge cases tested** - Only basic functionality checked

## 📝 Memory Notes to Add

When adding to knowledge base, include:

```markdown
### Known False Positives
- Health endpoint reports DB disconnected even when working (bug in app.py:185)
- Some endpoints return 404 even when registered (authentication required)
- Process running doesn't mean API is healthy

### Verification Requirements
- MUST show actual command and full output
- MUST test with real data, not just status endpoints
- MUST include timestamp of verification
- MUST test edge cases and error conditions
- MUST NOT trust health/status endpoints blindly
```

## 🤝 Cross-Instance Verification Protocol

1. **Instance A claims**: "Feature X works"
2. **Instance B must**:
   - Run the EXACT same test
   - Try additional edge cases
   - Test in different order
   - Report any discrepancies
3. **Instance C confirms**: 
   - Reviews both results
   - Runs tiebreaker test if needed
   - Documents final verdict

## 🎯 Golden Rule

**"Show, Don't Tell"** - Always provide:
- Exact commands run
- Full output (or relevant portions)
- Timestamp of execution
- Environment details if relevant
- Multiple test cases, not just one

Remember: Another Claude instance should be able to reproduce your exact steps and get the same results. If they can't, your verification is incomplete.