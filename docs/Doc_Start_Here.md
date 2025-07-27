# PrepSense Live Documentation Hub

## 🚨 CRITICAL INSTRUCTIONS FOR ALL CLAUDE INSTANCES 🚨

**BEFORE making any changes to the codebase:**
1. **READ** the relevant Doc_*.md files for the area you're working on
2. **ANALYZE** the current implementation state thoroughly
3. **UPDATE** documentation immediately after making changes
4. **ADD** any missing documentation you discover
5. **FIX** incorrect documentation (ask user first before updating)

**This is LIVE DOCUMENTATION** - it represents the current state of the codebase and MUST be kept synchronized with all changes.

---

## Documentation Index

### Core Documentation Files

1. **[Doc_FastApi_Routers.md](./Doc_FastApi_Routers.md)** 
   - All backend API endpoints with examples
   - Request/response formats
   - Authentication requirements
   - Database queries

2. **[Doc_FrontEnd_iOS.md](./Doc_FrontEnd_iOS.md)**
   - iOS app screens and components
   - API service implementations
   - State management
   - Navigation flows

3. **[Doc_GCP.md](./Doc_GCP.md)**
   - Google Cloud Platform setup
   - Cloud SQL configuration
   - Environment variables
   - Deployment procedures

4. **[USDA_UNIT_MAPPING_PLAN.md](./USDA_UNIT_MAPPING_PLAN.md)**
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
3. Include the Claude instance instructions at the top
4. Follow the existing format and structure

### Documentation Standards

- Use clear headings and subheadings
- Include code examples for all endpoints/components
- Document current state, not ideal state
- Mark TODOs and deprecated items clearly
- Include timestamps for major updates

---

## Recent Documentation Updates

- **2025-07-27**: Initial documentation system created
- **2025-07-27**: Added USDA unit mapping implementation (USDA_UNIT_MAPPING_PLAN.md)
- Add new updates here with date and summary

## Quick Reference Links

- [Backend Setup Guide](./BACKEND_SETUP_GUIDE.md)
- [iOS Setup Guide](./IOS_SETUP_GUIDE.md)
- [Testing Requirements](./TESTING_REQUIREMENTS.md)
- [Changelog](./CHANGELOG.md)

---

**Remember**: This documentation is the single source of truth for the current implementation. Keep it updated!