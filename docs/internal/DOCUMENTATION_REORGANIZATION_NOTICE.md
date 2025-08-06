# 📁 DOCUMENTATION REORGANIZATION NOTICE

## 🚨 IMPORTANT FOR ALL CLAUDE INSTANCES 🚨

**Date:** August 5, 2025  
**Status:** ACTIVE - All future Claude instances must follow this structure

---

## What Changed

The PrepSense documentation has been reorganized into **PUBLIC** and **INTERNAL** sections for better organization and security:

### NEW STRUCTURE:

```
docs/
├── public/           # 🌐 PUBLIC - Safe for GitHub, tracked in git
│   ├── getting-started/
│   ├── api/
│   ├── architecture/
│   └── contributing/
└── internal/         # 🔒 INTERNAL - Claude development use, git-ignored
    ├── claude/       # Claude-specific instructions
    ├── sessions/     # Development session summaries
    ├── testing/      # Test results and analysis
    ├── database/     # Database schemas and access details
    └── workflows/    # Development workflows
```

---

## 🎯 Key Instructions for Claude Instances

### FOR PUBLIC DOCUMENTATION (`docs/public/`):
- User-facing setup guides
- API documentation and examples  
- Architecture overviews
- Contributing guidelines
- Feature documentation for users

### FOR INTERNAL DOCUMENTATION (`docs/internal/`):
- Session summaries and development logs
- Claude-specific instructions and validation rules
- Test results and performance analysis
- Database schemas and access credentials
- Development workflows and processes

---

## 📋 Updated Workflow

### BEFORE making changes:
1. Check **`/docs/public/api/Doc_Start_Here.md`** for main documentation index
2. Check **`/docs/internal/`** for Claude-specific context
3. Read relevant documentation for your implementation area

### AFTER making changes:
- **User-facing changes** → Update `/docs/public/`
- **Development notes** → Update `/docs/internal/`
- **Session summaries** → Always go in `/docs/internal/sessions/`

---

## 🔧 Technical Details

- **Git Status:** `docs/internal/` is added to `.gitignore`
- **README Updated:** Main README.md now points to `/docs/public/`
- **CLAUDE.md Updated:** Contains new documentation structure instructions

---

## ✅ Benefits

1. **Clean Public Documentation:** Professional documentation suitable for GitHub
2. **Organized Internal Context:** All development context preserved and organized
3. **Security:** No sensitive development information exposed publicly
4. **Maintainability:** Clear separation of concerns for different audiences

---

## 🚨 MANDATORY FOR ALL CLAUDE INSTANCES

**ALL future Claude instances MUST:**
1. Read this notice upon first interaction with the project
2. Follow the new PUBLIC/INTERNAL documentation structure
3. Update the appropriate section based on the type of changes made
4. Reference `/docs/internal/claude/` for Claude-specific instructions

---

**This reorganization ensures PrepSense has professional public documentation while maintaining comprehensive internal development context.**