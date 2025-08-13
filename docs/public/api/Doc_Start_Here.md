# PrepSense Live Documentation Hub

## 📚 Documentation Guidelines

**BEFORE making any changes to the codebase:**
1. **READ** the relevant Doc_*.md files for the area you're working on
2. **ANALYZE** the current implementation state thoroughly
3. **UPDATE** documentation immediately after making changes
4. **ADD** any missing documentation you discover
5. **FIX** incorrect documentation

**This is LIVE DOCUMENTATION** - it represents the current state of the codebase and MUST be kept synchronized with all changes.

---

## Documentation Index

### Core Documentation Files

#### 1. **[Doc_FastApi_Routers.md](./Doc_FastApi_Routers.md)** 
   - All backend API endpoints with examples
   - Request/response formats
   - Authentication requirements
   - Database queries

#### 2. **[Doc_FrontEnd_iOS.md](./Doc_FrontEnd_iOS.md)**
   - iOS app screens and components
   - API service implementations
   - State management
   - Navigation flows

#### 3. **[Doc_GCP.md](./Doc_GCP.md)**
   - Google Cloud Platform setup
   - Cloud SQL configuration
   - Environment variables
   - Deployment procedures

#### 4. **[Doc_Backup_Recipe_System.md](./Doc_Backup_Recipe_System.md)** 
   - Comprehensive backup recipe system (13k+ recipes)
   - Local database with intelligent fallback logic
   - Image serving infrastructure and optimization
   - CSV import pipeline and data processing
   - Enhanced search with ingredient matching
   - Performance optimization and monitoring

#### 5. **[Doc_Research.md](./Doc_Research.md)** 🆕
   - Research documentation index and standards
   - API & external service analysis
   - Performance & optimization studies
   - Technology stack research
   - **5.1** [Spoonacular API Analysis](./5.1_Spoonacular_API_ANALYSIS.md) - Comprehensive API usage analysis with caching strategies and cost optimization
   - **5.2** [Local Storage and Caching Strategy](./5.2_Local_Storage_and_Caching_Strategy.md) - Complete analysis of all storage mechanisms and caching layers

#### 6. **[Doc_Code_Quality_Tools.md](./Doc_Code_Quality_Tools.md)** 🆕
   - Code cleanup and analysis tools for React Native/Expo and FastAPI
   - Automated dependency scanning and unused code detection
   - ESLint integration for React Native style checking
   - CI/CD integration patterns for maintaining code quality
   - Lightbulb-recommender agent specific cleanup workflows

### Additional Documentation

#### 4.1 **[USDA Unit Mapping Plan](./4.1_USDA_UNIT_MAPPING_PLAN.md)**
   - USDA data integration for unit validation
   - Import scripts and API endpoints
   - Category-to-unit mapping strategy
   - Implementation phases and testing

### How to Use This Documentation

1. **Starting a new task?** 
   - Check Doc_Start_Here.md first
   - Read the relevant Doc_*.md for your area
   - Look for existing patterns before implementing

2. **Made changes?**
   - Update the relevant Doc_*.md immediately
   - Add code examples
   - Document any new patterns or decisions

3. **Found missing/incorrect documentation?**
   - Ask the user before making major documentation changes
   - Add missing sections with clear examples
   - Mark deprecated patterns clearly

### Adding New Documentation

When creating a new Doc_*.md file:
1. Add it to this index with a clear description
2. If it's a subcategory, link it in both the parent Doc and here
3. Include clear instructions at the top
4. Follow the existing format and structure

### Documentation Standards

#### File Naming Protocol
- **Main documentation**: `Doc_{Category}.md` (e.g., `Doc_FastApi_Routers.md`)
- **Subsection documents**: `{Section}.{Subsection}_{Topic_Name}.md` (e.g., `5.1_Spoonacular_API_ANALYSIS.md`)
- **All non-Doc_ prefixed files** must include section numbers in both filename and document title

#### Content Standards
- Use clear headings and subheadings
- Include code examples for all endpoints/components
- Document current state, not ideal state
- Mark TODOs and deprecated items clearly
- Include timestamps for major updates
- **Section numbers must match** between filename and document title

---

## Recent Documentation Updates

- **2025-08-02**: Added research documentation structure (Doc_Research.md) with section numbering system
- **2025-08-02**: Added comprehensive Spoonacular API analysis (5.1_Spoonacular_API_ANALYSIS.md)
- **2025-08-02**: Implemented file naming protocol - all subsection files now use `{Section}.{Subsection}_{Topic}.md` format
- **2025-01-30**: Added comprehensive backup recipe system documentation (Doc_Backup_Recipe_System.md)
- **2025-07-27**: Initial documentation system created
- **2025-07-27**: Added USDA unit mapping implementation (4.1_USDA_UNIT_MAPPING_PLAN.md)

## Quick Reference Links

- [Backend Setup Guide](./BACKEND_SETUP_GUIDE.md)
- [iOS Setup Guide](./IOS_SETUP_GUIDE.md)
- [Testing Requirements](./TESTING_REQUIREMENTS.md)
- [Changelog](./CHANGELOG.md)

---

**Remember**: This documentation is the single source of truth for the current implementation. Keep it updated!

<!-- AUTO‑DOC‑MAINTAINER: Doc_Start_Here -->
<!-- END -->