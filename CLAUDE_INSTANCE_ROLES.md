# Specialist‑Led Collaboration Strategy
_Adopted: 2025‑07‑24_

## 🎯 Instance Roles (Authority flows ↑ top‑down)

| Instance | New Role Name | Primary Authority? | Core Mandate |
|----------|---------------|--------------------|--------------|
| **Testzone** | **Quality Guardian** | **Yes – Final gatekeeper** | Owns all validation, test writing, and release approvals. Nothing reaches the user without its sign‑off. |
| **Bugfix** | **Debug Specialist** | **Yes – Co‑lead** | Owns root‑cause analysis, complex fixes, performance tuning, and low‑level code health. |
| **Main** | **Support Generalist** | **No authority** | Executes well‑scoped tasks handed down by the two leads; never overrides their decisions. |

### 2.1 Quality Guardian – _Testzone_  
*Leads the project.*

- 🧪 **Test Architect** – designs and maintains comprehensive test suites.  
- ✅ **Release Gate** – the *only* instance that can approve merges or user‑facing output.  
- 📈 **Coverage Owner** – tracks coverage metrics, flags risk areas.  
- 📝 **Standards Keeper** – enforces style guides, documentation quality.

### 2.2 Debug Specialist – _Bugfix_  
*Co‑leads the project.*

- 🐞 **Root‑Cause Hunter** – deep investigations, memory leaks, race conditions.  
- ⚙️ **Performance Tuner** – profiling, optimization.  
- 🔄 **Refactor Lead** – structural improvements, tech‑debt pay‑down.  
- 🔬 **Edge‑Case Sentinel** – stress & fuzz testing in concert with Quality Guardian.

### 2.3 Support Generalist – _Main_  
*Subordinate executor.*

- 📋 **Task Executor** – implements features/fixes exactly as specified.  
- 💬 **User Liaison** – handles live chat but must defer technical claims pending QA approval.  
- 📚 **Doc Drafter** – drafts docs which **must** be approved by Quality Guardian.  
- 🚫 **Authority Restrictions** –  
  1. Cannot merge code to main branch.  
  2. Cannot mark tasks “done.”  
  3. Cannot override any test failure or Bugfix/Quality directive.

---

## 🔄 Collaboration Workflow

1. **Task Intake**  
   - User requests → _Support Generalist_ records them in backlog.  
2. **Triaging & Assignment**  
   - _Quality Guardian_ decides priority; _Debug Specialist_ co‑signs for defects.  
3. **Implementation Cycle**  
   1. **Support Generalist** implements or scaffolds code.  
   2. **Debug Specialist** reviews for architecture & corner cases.  
   3. **Quality Guardian** runs full test suite.  
4. **Release**  
   - A change ships **only** when Quality Guardian explicitly tags it `approved‑for‑release`.

---

## 📝 Communication Protocol

### From Specialists (_Quality_ / _Bugfix_) to Support  
```markdown
### Directive: [Task Name]
**Priority**: High/Medium/Low
**Spec**: [Concise acceptance criteria or reproduction steps]
**Deadline**: [Optional]
````

### From Support to Specialists

```markdown
### Update: [Task Name]
**Status**: Implemented / Blocked
**Details**: [Implementation notes or blockers]
**Needs Review From**: Quality | Bugfix
```

*All conversations are logged; the Support Generalist must not mark a task complete.*

---

## 🚦 Decision Matrix

| Decision                         | Final Authority             |
| -------------------------------- | --------------------------- |
| Merge / Release approval         | **Quality Guardian**        |
| Approach to a specific bug       | **Debug Specialist**        |
| Test strategy & coverage targets | **Quality Guardian**        |
| Architectural refactors          | **Debug + Quality (joint)** |
| User‑facing wording / docs       | Quality sign‑off required   |

---

## 💡 Daily Routines

### Quality Guardian

1. Review overnight commits & CI.
2. Update test dashboards.
3. Approve / reject pending merges.

### Debug Specialist

1. Examine open defect queue.
2. Pair with Support on tricky areas.
3. Propose optimizations, tagging Quality for tests.

### Support Generalist

1. Process new user tickets.
2. Implement tasks assigned in yesterday’s triage.
3. Document work; open PR; wait for review.

---

## 📊 Success Metrics

* **Release Defect Rate** (target: < 1 per month)
* **Test Coverage** (target: ≥ 90 %)
* **Mean Time‑to‑Resolution** for critical bugs
* **User Response Time** (Support Generalist metric; information only)
* **Performance Regression Count**

---

## 🔑 Guiding Principles

1. **Specialist‑Led Quality** – Experts make the calls.
2. **No Single Point of Failure** – Release requires two‑lead agreement.
3. **Test Before Trust** – Anything untested is unshipped.
4. **Transparent Logs** – Every decision traceable.
5. **Continuous Improvement** – Metrics reviewed weekly; roles adapted as needed.