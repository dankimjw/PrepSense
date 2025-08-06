# 🔧 PrepSense Internal Development Documentation

This directory contains internal development documentation for PrepSense that is not meant for public GitHub viewing. These files contain detailed development processes, debugging information, Claude-specific instructions, and internal technical details.

## 🚨 IMPORTANT: Internal Use Only

**These files should NOT be included in public documentation or shared publicly.**

The files in this directory contain:
- Claude AI specific instructions and validation rules
- Detailed debugging sessions and technical analysis
- Internal development workflows and processes
- Sensitive technical implementation details
- Development session logs and progress tracking

## 📁 Directory Structure

### 🤖 [claude/](./claude/)
Claude-specific configuration, validation rules, and instructions:
- `CLAUDE.md` - Main Claude development guidelines
- `CLAUDE_VALIDATION_RULES.md` - Truth enforcement and validation protocols
- `CLAUDE_TRUTHFUL_PROMPT.md` - Prompting guidelines
- `START_HERE_CLAUDE.md` - Claude instance onboarding guide
- `CLAUDE_INSTANCE_ROLES.md` - Multi-instance collaboration roles
- `backend_CLAUDE.md` - Backend-specific Claude instructions

### 📝 [sessions/](./sessions/)
Development session summaries and progress logs:
- Session summaries (format: `2025-XX-XX-*.md`)
- `UPDATES_LOG.md` - High-level project updates
- `Capstone Presentation Storyline.md` - Presentation planning
- Feature implementation summaries and progress tracking

### 🧪 [testing/](./testing/)
Internal testing documentation, results, and analysis:
- Test implementation guides and lessons learned
- Performance optimization analysis and plans
- Feature-specific testing results and edge case documentation
- Test coverage summaries and validation reports
- Animation and UI testing documentation

### 🗄️ [database/](./database/)
Database-related internal documentation:
- PostgreSQL access and configuration details  
- Database migration documentation
- Schema analysis and validation reports
- USDA database integration and validation
- Performance optimization for database queries

### ⚙️ [workflows/](./workflows/)
Development workflow and process documentation:
- Worktree management and collaboration notes
- MCP server setup and configuration
- Subagent strategy guides and implementation
- CrewAI integration and orchestration
- Development collaboration protocols
- Internal backlog and task management

## 🔄 Development Workflow Integration

These internal docs are tightly integrated with the development workflow:

1. **Claude instances** read these files for configuration and validation rules
2. **Session summaries** track what was implemented, tested, and needs verification  
3. **Testing documentation** provides detailed results and edge case analysis
4. **Workflow docs** enable multi-instance collaboration and task coordination

## 🎯 Key Internal Files

### For Claude Instances
- [claude/START_HERE_CLAUDE.md](./claude/START_HERE_CLAUDE.md) - Onboarding guide
- [claude/CLAUDE_VALIDATION_RULES.md](./claude/CLAUDE_VALIDATION_RULES.md) - Truth enforcement
- [workflows/SUBAGENT_STRATEGY_GUIDE.md](./workflows/SUBAGENT_STRATEGY_GUIDE.md) - When to use agents

### For Development Progress
- [sessions/](./sessions/) - All session summaries and progress logs
- [testing/](./testing/) - Test results and validation reports
- [workflows/backlog.md](./workflows/backlog.md) - Internal task tracking

### For Technical Deep Dives
- [database/](./database/) - Database schema and migration details
- [testing/PERFORMANCE_OPTIMIZATION_PLAN.md](./testing/PERFORMANCE_OPTIMIZATION_PLAN.md) - Performance analysis
- [workflows/MCP_POSTGRES_SETUP.md](./workflows/MCP_POSTGRES_SETUP.md) - MCP configuration

## 📊 Usage Guidelines

### For Daniel (Project Owner)  
- Review session summaries to track progress
- Use testing docs to understand current implementation state
- Reference workflow docs for development process optimization
- Check database docs for schema and migration planning

### For Claude Instances
- **ALWAYS** read relevant validation rules before making claims
- Update session summaries after significant work
- Document test results and edge cases discovered
- Follow workflow protocols for multi-instance collaboration

### For Development Team (if expanded)
- These docs provide context on development decisions
- Session summaries show the evolution of implementation
- Testing docs reveal known issues and edge cases
- Workflow docs explain the development process

## 🔒 Security & Privacy

These internal docs may contain:
- API keys and configuration details
- Database connection information  
- Internal development processes
- Debugging information with sensitive data

**Never commit sensitive information to public repositories.**

## 🗂️ File Organization Standards

- **Session files**: Use date format `2025-MM-DD-description.md`
- **Testing files**: Prefix with test type (e.g., `RECIPE_COMPLETION_TEST_RESULTS.md`)
- **Workflow files**: Use descriptive names (e.g., `WORKTREE_NOTES_MAIN.md`)
- **Database files**: Include validation/migration in filename when applicable

---

**Remember**: This is internal documentation. For public-facing docs, see [../public/](../public/)