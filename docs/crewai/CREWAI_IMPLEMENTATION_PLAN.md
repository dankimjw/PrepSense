# CrewAI Implementation Plan

## Overview
Replace the fake "CrewAIService" with a real CrewAI implementation using multiple specialized agents working together to provide intelligent recipe recommendations.

## Architecture Design

### Agent Structure
1. **PantryAnalystAgent** - Analyzes pantry items, expiration dates, categorizes ingredients
2. **RecipeSearchAgent** - Searches multiple sources (Spoonacular, saved recipes)
3. **NutritionExpertAgent** - Evaluates nutritional content and dietary gaps
4. **PreferenceAgent** - Applies user preferences and dietary restrictions
5. **RankingAgent** - Ranks and selects the best recipes based on all factors

### Data Flow
```
User Message → PantryAnalyst → RecipeSearch → NutritionExpert → PreferenceAgent → RankingAgent → Response
```

## Implementation Phases

### Phase 1: Setup & Planning (2 hours)
**Goal**: Foundation ready for development

**Tasks**:
- [ ] Update requirements.txt to CrewAI 0.41+
- [ ] Create feature branch `feature/real-crewai`
- [ ] Set up project structure for agents and tools
- [ ] Test basic CrewAI imports and functionality

**Success Criteria**:
- CrewAI 0.41+ imports successfully
- Basic Agent/Task/Crew can be instantiated
- No import conflicts with existing code

**Deliverables**:
- Updated requirements.txt
- New directory structure: `backend_gateway/agents/crewai/`
- Basic import test script

### Phase 2: Tools Development (4 hours)
**Goal**: Create reusable tools for agents

**Tools to Create**:
1. **PantryTool**: Query and analyze pantry items
2. **SpoonacularTool**: Search recipes from API
3. **NutritionTool**: Analyze nutritional content
4. **PreferenceTool**: Apply user preferences
5. **DatabaseTool**: General database operations

**Success Criteria**:
- Each tool can be called independently
- Tools return expected data formats
- Tools handle errors gracefully

**Deliverables**:
- `backend_gateway/tools/pantry_tool.py`
- `backend_gateway/tools/spoonacular_tool.py`
- `backend_gateway/tools/nutrition_tool.py`
- `backend_gateway/tools/preference_tool.py`
- `backend_gateway/tools/database_tool.py`

### Phase 3: Agent Development (6 hours)
**Goal**: Create specialized agents with their tools

**Agents to Create**:

1. **PantryAnalystAgent**
   - Tools: PantryTool, DatabaseTool
   - Responsibilities: Analyze pantry, identify expiring items, categorize ingredients

2. **RecipeSearchAgent**
   - Tools: SpoonacularTool, DatabaseTool
   - Responsibilities: Search recipes, filter by ingredients, handle multiple sources

3. **NutritionExpertAgent**
   - Tools: NutritionTool
   - Responsibilities: Evaluate nutritional content, identify dietary gaps

4. **PreferenceAgent**
   - Tools: PreferenceTool, DatabaseTool
   - Responsibilities: Apply user preferences, dietary restrictions, allergen filtering

5. **RankingAgent**
   - Tools: Custom ranking algorithms
   - Responsibilities: Combine all factors, rank recipes, select top recommendations

**Success Criteria**:
- Each agent can execute its task using its tools
- Agents produce expected output formats
- Agents handle edge cases (empty pantry, no preferences, etc.)

**Deliverables**:
- `backend_gateway/agents/crewai/pantry_analyst_agent.py`
- `backend_gateway/agents/crewai/recipe_search_agent.py`
- `backend_gateway/agents/crewai/nutrition_expert_agent.py`
- `backend_gateway/agents/crewai/preference_agent.py`
- `backend_gateway/agents/crewai/ranking_agent.py`

### Phase 4: Crew Integration (4 hours)
**Goal**: Orchestrate agents to work together

**Tasks**:
- [ ] Create RecipeRecommendationCrew
- [ ] Define tasks and workflows
- [ ] Set up agent communication and data passing
- [ ] Test crew execution with sample data

**Success Criteria**:
- Full crew can execute end-to-end
- Agents communicate effectively
- Crew returns recipe recommendations in expected format

**Deliverables**:
- `backend_gateway/crews/recipe_recommendation_crew.py`
- Crew configuration and task definitions
- Integration test suite

### Phase 5: Service Integration (4 hours)
**Goal**: Replace fake service with real CrewAI

**Tasks**:
- [ ] Create new RealCrewAIService
- [ ] Update chat router with feature flag
- [ ] Implement A/B testing capability
- [ ] Maintain backward compatibility

**Success Criteria**:
- Chat API returns results from real CrewAI
- Feature flag allows switching between old/new
- Response format matches existing API
- Performance is acceptable (<10s response time)

**Deliverables**:
- `backend_gateway/services/real_crew_ai_service.py`
- Updated chat router with feature flag
- A/B testing configuration

### Phase 6: Testing & Optimization (3 hours)
**Goal**: Ensure production readiness

**Tasks**:
- [ ] Comprehensive testing (unit, integration, system)
- [ ] Performance optimization
- [ ] Documentation updates
- [ ] Error handling and monitoring

**Success Criteria**:
- All tests pass
- Performance meets requirements
- Error rates are acceptable
- Documentation is complete

**Deliverables**:
- Complete test suite
- Performance benchmarks
- Updated documentation
- Monitoring and alerting setup

## Risk Management

### Technical Risks
- **Version Compatibility**: CrewAI 0.1.32 → 0.41+ is a major jump
- **Performance**: Multi-agent system may be slower than direct API calls
- **Complexity**: More components = more potential failure points

### Mitigation Strategies
- **Feature Flag**: Keep old system as fallback
- **Gradual Rollout**: Test with limited users first
- **Performance Monitoring**: Track response times and error rates
- **Rollback Plan**: Can instantly revert if issues arise

## Success Metrics

### Functional Metrics
- Recipe recommendations quality (user feedback)
- Response accuracy (ingredient matching)
- Feature completeness (all current features work)

### Performance Metrics
- Response time: <10 seconds for recipe recommendations
- Error rate: <5% of requests
- Uptime: >99.9%

### User Experience Metrics
- User satisfaction scores
- Feature adoption rate
- Recommendation click-through rate

## Timeline

**Total Estimated Time**: 23 hours (3 days of focused work)

**Week 1**: Phases 1-2 (Setup and Tools)
**Week 2**: Phases 3-4 (Agents and Crew)
**Week 3**: Phases 5-6 (Integration and Testing)

## Next Steps

1. Get approval for this plan
2. Create feature branch
3. Begin Phase 1 implementation
4. Regular progress reviews and adjustments

## Dependencies

- OpenAI API access (for agent LLMs)
- Spoonacular API access
- Database access
- Existing service interfaces (for backward compatibility)

## Rollback Strategy

1. **Immediate**: Feature flag to switch back to old service
2. **Short-term**: Keep old service code intact for 1 month
3. **Long-term**: Monitor performance and user feedback for 3 months before full removal