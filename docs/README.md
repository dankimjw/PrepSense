# 📚 PrepSense Documentation Hub

Welcome to the PrepSense documentation! This directory has been reorganized to separate public documentation from internal development files.

## 📁 Documentation Structure

### 🌐 [public/](./public/) - Public Documentation
**Safe for GitHub public repositories**

Documentation intended for users, contributors, and the general public:

- **[Getting Started Guide](./public/getting-started/)** - Setup instructions for new users and developers
- **[API Documentation](./public/api/)** - Backend API endpoints, database schemas, and integration guides  
- **[Architecture Documentation](./public/architecture/)** - System architecture, data flows, and feature specifications
- **[Contributing Guidelines](./public/contributing/)** - Development workflow, code quality, and testing standards
- **[Feature Documentation](./public/FEATURE_DOCUMENTATION.md)** - Complete feature overview
- **[User Guide](./public/Guide_v1.0.md)** - Comprehensive user manual
- **[Changelog](./public/CHANGELOG.md)** - Technical changes and updates

### 🔒 [internal/](./internal/) - Internal Development Documentation  
**For Daniel and Claude development use only**

Internal documentation not meant for public GitHub:

- **[claude/](./internal/claude/)** - Claude-specific instructions, validation rules, and configuration
- **[sessions/](./internal/sessions/)** - Development session summaries and progress logs
- **[testing/](./internal/testing/)** - Test results, performance analysis, and edge case documentation
- **[database/](./internal/database/)** - Database schemas, migrations, and internal configuration details
- **[workflows/](./internal/workflows/)** - Development workflows, worktree management, and process documentation

### 📊 [flows/](./flows/) - Flow Documentation
**Shared flow documentation**

System and user flow documentation used by both public and internal docs.

## 🎯 Quick Start

### For New Users
Start with the [Public Documentation](./public/) → [Getting Started Guide](./public/getting-started/)

### For Contributors  
1. Read [Contributing Guidelines](./public/contributing/)
2. Review [API Documentation](./public/api/)
3. Explore [Architecture Documentation](./public/architecture/)

### For Claude Instances
1. **CRITICAL**: Read [internal/claude/CLAUDE_VALIDATION_RULES.md](./internal/claude/CLAUDE_VALIDATION_RULES.md) immediately
2. Follow [internal/claude/START_HERE_CLAUDE.md](./internal/claude/START_HERE_CLAUDE.md) for onboarding
3. Review [public/api/Doc_Start_Here.md](./public/api/Doc_Start_Here.md) for live documentation standards

## 🚨 Important Notes

### For Claude Instances
**BEFORE making any changes to the codebase:**
1. **READ** the relevant documentation in both public and internal sections
2. **ANALYZE** the current implementation state thoroughly  
3. **UPDATE** documentation immediately after making changes
4. **NEVER** claim unimplemented features work - see validation rules

### For GitHub/Public Sharing
- **Share**: Anything in `docs/public/` and `docs/flows/`
- **Keep Private**: Everything in `docs/internal/`
- Consider adding `docs/internal/` to `.gitignore` for public forks

### Documentation Maintenance
- **Public docs**: Keep professional, clean, and user-focused
- **Internal docs**: Detailed technical analysis, debugging info, and development processes
- **Both**: Must stay synchronized with actual codebase implementation

## 🔄 Recent Reorganization (2025-08-05)

This documentation was reorganized to separate:
- **Public-facing documentation** suitable for GitHub and external contributors
- **Internal development documentation** with sensitive technical details and Claude-specific instructions

All content has been preserved and reorganized by purpose and audience.

---

**Remember**: Documentation is only as good as it is current. Keep it updated! 

For the most up-to-date technical documentation, see [public/api/Doc_Start_Here.md](./public/api/Doc_Start_Here.md)