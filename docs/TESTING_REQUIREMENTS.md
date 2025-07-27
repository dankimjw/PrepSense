# ⚠️ TESTING REQUIREMENTS - Semantic Search

## Date: 2025-01-24
## Status: CRITICAL TESTING NEEDED

## Overview
The semantic search implementation for PrepSense is functionally complete but **REQUIRES COMPREHENSIVE TESTING** before production deployment.

## Test Scripts Available

### 1. `test_semantic_search_api.py`
**Full API Testing with Authentication**
- Tests all semantic search endpoints
- Requires backend server running
- Tests authentication flow
- Comprehensive error handling validation
- Performance benchmarking
- Saves detailed results to JSON

**Run Command:**
```bash
# Terminal 1: Start backend
source venv/bin/activate && python run_app.py

# Terminal 2: Run tests
source venv/bin/activate && python test_semantic_search_api.py
```

### 2. `test_semantic_search_standalone.py`
**Database-Level Testing (No Auth)**
- Direct database function testing
- Faster execution
- Good for development iteration
- Performance measurement

**Run Command:**
```bash
source venv/bin/activate && python test_semantic_search_standalone.py
```

## Critical Test Areas

### 🔴 HIGH PRIORITY
1. **Authentication Integration**
   - Verify all endpoints work with user login
   - Test with valid/invalid tokens
   - Confirm user-specific data access

2. **API Endpoint Functionality**
   - `/api/v1/semantic-search/recipes` - Recipe semantic search
   - `/api/v1/semantic-search/recipes/hybrid` - Hybrid search
   - `/api/v1/semantic-search/products` - Product search
   - `/api/v1/semantic-search/pantry/similar/{item_name}` - Similar items
   - `/api/v1/semantic-search/update-embedding/{type}/{id}` - Update embeddings

3. **Error Handling**
   - Invalid queries
   - Missing embeddings
   - Database connection issues
   - OpenAI API failures

### 🟡 MEDIUM PRIORITY
4. **Performance Validation**
   - Confirm <100ms query response times
   - Test with full dataset (861+ pantry items)
   - Load testing with multiple concurrent users

5. **Data Quality**
   - Verify similarity scores are reasonable (0.3-0.6 range)
   - Check semantic relevance of results
   - Validate embedding quality

### 🟢 LOW PRIORITY
6. **Integration Testing**
   - Frontend compatibility
   - iOS app integration
   - Existing feature compatibility

## Known Issues to Test

1. **Hybrid Search Function**
   - Ingredient matching has SQL grouping error
   - Needs fix in stored procedure
   - Test after fix

2. **Column Name Mismatches**
   - Some functions may use old column names
   - Verify all database queries work

3. **Large Dataset Performance**
   - Only 28 items have embeddings currently
   - Need to test with full 861+ pantry items

## Expected Results

### Recipe Search
- "healthy breakfast" → breakfast recipes with high protein
- "Italian dinner" → pasta, pizza, Italian cuisine
- "Mexican food" → tacos, burritos, Latin dishes

### Product Search
- "dairy products" → milk, cheese, yogurt
- "fresh fruit" → apples, berries, citrus
- "organic produce" → items marked as organic

### Performance
- Query time: <100ms
- Similarity scores: 0.3-0.6 for good matches
- Results ranked by relevance

## Test Completion Checklist

- [ ] Run `test_semantic_search_api.py` successfully
- [ ] Run `test_semantic_search_standalone.py` successfully
- [ ] All API endpoints return valid responses
- [ ] Authentication works correctly
- [ ] Error handling covers edge cases
- [ ] Performance meets <100ms target
- [ ] Results are semantically relevant
- [ ] No SQL errors or crashes
- [ ] Frontend integration works
- [ ] Production deployment safe

## Post-Testing Actions

Once testing is complete and successful:
1. Update documentation with test results
2. Fix any discovered issues
3. Populate remaining embeddings (pantry items)
4. Integrate with iOS app
5. Deploy to production

## Contact

If testing reveals issues, check:
1. Database connection and credentials
2. OpenAI API key configuration
3. Server startup and dependencies
4. Column names in database schema

**Status: AWAITING COMPREHENSIVE TESTING**