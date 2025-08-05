# 🤝 Contributing to PrepSense

Welcome! We appreciate your interest in contributing to PrepSense. This directory contains guidelines and resources for contributors.

## 📋 Contributing Guidelines

### 🚀 Getting Started
1. **Setup**: Follow the [getting started guide](../getting-started/) to set up your development environment
2. **Read**: Review the [Developer Guide](./DEVELOPER_GUIDE.md) for code quality standards and workflow
3. **Understand**: Explore the [API documentation](../api/) and [architecture docs](../architecture/) to understand the system

### 🔄 Development Workflow

1. **Fork & Clone**: Fork the repository and clone it locally
2. **Branch**: Create a feature branch (`feature/your-feature-name`)
3. **Develop**: Make your changes following our coding standards
4. **Test**: Write tests and ensure all existing tests pass
5. **Document**: Update documentation for any API or feature changes
6. **Submit**: Create a pull request with a clear description

### 📝 Code Standards

- **Python (Backend)**: Follow PEP 8, use type hints, 127 character line limit
- **TypeScript (Frontend)**: Follow ESLint configuration, use proper typing
- **Testing**: Maintain >80% test coverage for new code
- **Documentation**: Update relevant docs in `docs/public/` for user-facing changes

### 🧪 Testing Requirements

Before submitting a PR:
```bash
# Backend tests
pytest --cov=./ --cov-report=term-missing

# Frontend tests  
npm test

# Health checks
./quick_check.sh
python check_app_health.py
```

### 📚 Documentation Standards

- **User-facing changes**: Update files in `docs/public/`
- **API changes**: Update `docs/public/api/Doc_FastApi_Routers.md`
- **New features**: Add to `docs/public/FEATURE_DOCUMENTATION.md`
- **Architecture changes**: Update relevant files in `docs/public/architecture/`

## 🎯 Areas for Contribution

### 🐛 Bug Fixes
- Check the issues tab for bugs labeled `bug`
- Include test cases that reproduce the bug
- Verify the fix doesn't break existing functionality

### ✨ New Features
- Discuss large features in an issue first
- Follow the existing architecture patterns
- Include comprehensive tests and documentation
- Update the feature documentation

### 📖 Documentation
- Improve existing documentation clarity
- Add missing documentation for features
- Fix broken links or outdated information
- Translate documentation (future scope)

### 🧪 Testing
- Improve test coverage for existing code
- Add integration tests for critical flows
- Performance testing and optimization
- Cross-platform testing (iOS/Android)

## 🔍 Code Review Process

All contributions go through code review:

1. **Automated Checks**: CI/CD runs tests, linting, and security checks
2. **Manual Review**: Team members review code quality, architecture, and documentation
3. **Feedback**: Address any feedback or requested changes
4. **Approval**: Once approved, changes are merged

### Review Criteria
- **Functionality**: Does it work as intended?
- **Quality**: Follows coding standards and best practices?
- **Testing**: Adequate test coverage and passes all tests?
- **Documentation**: Updated documentation for user-facing changes?
- **Performance**: No negative impact on app performance?

## 🚨 Important Guidelines

### Security
- Never commit sensitive information (API keys, passwords, etc.)
- Follow secure coding practices
- Report security vulnerabilities privately

### Database Changes
- Always create migration scripts for schema changes
- Test migrations on development data
- Consider backward compatibility

### API Changes
- Maintain backward compatibility when possible
- Update API documentation immediately
- Include proper error handling and validation

## 📞 Getting Help

- **Questions**: Open an issue with the `question` label
- **Discussion**: Use GitHub Discussions for broader topics
- **Real-time**: Join our development chat (if available)

## 🎉 Recognition

Contributors are recognized in:
- Commit history and GitHub contributors list
- Special thanks in release notes for significant contributions
- Contributor spotlight in project updates

## 📋 Pull Request Template

When creating a PR, please include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature  
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Other (please describe)

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Documentation
- [ ] Documentation updated
- [ ] API docs updated (if applicable)
- [ ] Feature docs updated (if applicable)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] No breaking changes (or clearly documented)
```

---

Thank you for contributing to PrepSense! 🎉