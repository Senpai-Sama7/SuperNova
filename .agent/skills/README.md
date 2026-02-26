# AI Skills Library 🎯

**What is this?** Think of these as specialized "expert modes" for your AI assistant. Just like how you'd hire a security expert for a security audit or an architect for system design, these skills turn the AI into a specialist for specific tasks.

> 💡 **For Non-Technical Users:** You don't need to understand how these work—just know what they're good for. When you have a specific need, mention the skill name (like "use the docx skill") and the AI will automatically use the right expertise.

---

## 📚 Quick Navigation

| I Need To... | Use This Skill |
|--------------|----------------|
| Create or edit Word documents | [docx](#-document-skills) |
| Create or edit Excel spreadsheets | [xlsx](#-document-skills) |
| Create or edit PowerPoint presentations | [pptx](#-document-skills) |
| Work with PDFs (extract text, fill forms, merge) | [pdf](#-document-skills) |
| Build a website or web app | [frontend-design](#-design--frontend) or [web-artifacts-builder](#-design--frontend) |
| Debug why something is broken | [debugging-root-cause-analysis](#-debugging--problem-solving) |
| Review code for quality issues | [code-review-refactoring](#-code-quality--review) |
| Write tests for my code | [test-driven-development](#-code-quality--review) |
| Fix failing CI/CD checks on GitHub | [gh-fix-ci](#-github--git-workflows) |
| Address PR review comments | [gh-address-comments](#-github--git-workflows) |
| Design a database | [database-design-optimization](#-system-design--architecture) |
| Choose between technologies (microservices vs monolith, etc.) | [architecture-design](#-system-design--architecture) |
| Make my app faster | [performance-engineering](#-performance--optimization) |
| Add security to my application | [security-engineering](#-security--compliance) |
| Verify code has no fakes/stubs before shipping | [hostile-auditor](#-security--compliance) |
| Connect to an external API | [api-integration](#-development--integration) |
| Build an Android app | [android-app](#-mobile-development) |
| Create a plan for a complex task | [create-plan](#-project-management--planning) |
| Capture meeting notes to Notion | [notion-meeting-intelligence](#-notion--knowledge-management) |
| Research and document in Notion | [notion-research-documentation](#-notion--knowledge-management) |
| Create/manage Linear tickets | [linear](#-project-management--planning) |
| Build an MCP server (AI tool integration) | [mcp-builder](#-development--integration) |
| Fix Cloudflare blocking my requests | [cloudflare-403-triage](#-debugging--problem-solving) |
| Optimize prompts for better AI responses | [optimize-prompt](#-ai-ml-specialized) |
| Build multi-agent AI systems | [multi-agent-orchestration](#-ai-ml-specialized) |
| Design agent cognitive systems | [agent-cognitive-architecture](#-ai-ml-specialized) |

---

## 📄 Document Skills

### docx — Word Documents
**When to use:** Creating, editing, or analyzing Microsoft Word documents
- Write professional documents with proper formatting
- Track changes and redlining (collaborative editing)
- Extract text from existing documents
- Add comments and annotations
- Work with headers, footers, tables, and images

**Example:** *"Use the docx skill to create a professional proposal document with tracked changes"*

---

### xlsx — Excel Spreadsheets
**When to use:** Working with spreadsheets, data analysis, or calculations
- Create spreadsheets with formulas and formatting
- Analyze existing data with pivot tables and charts
- Modify spreadsheets while preserving formulas
- Generate reports with conditional formatting
- Import/export CSV, TSV, and Excel formats

**Example:** *"Use the xlsx skill to create a budget spreadsheet with formulas"*

---

### pptx — PowerPoint Presentations
**When to use:** Creating or editing slide decks
- Build professional presentations from scratch
- Modify existing slide layouts and content
- Add speaker notes and comments
- Apply consistent branding across slides
- Convert content to presentation format

**Example:** *"Use the pptx skill to turn this report into a 10-slide presentation"*

---

### pdf — PDF Manipulation
**When to use:** Working with PDF files (not just viewing)
- Extract text and tables from PDFs
- Fill out PDF forms programmatically
- Merge multiple PDFs into one
- Split a PDF into separate pages
- Create new PDFs from scratch
- Add watermarks or signatures

**Example:** *"Use the pdf skill to extract all tables from this research PDF"*

---

## 🎨 Design & Frontend

### frontend-design
**When to use:** Creating websites, web apps, or UI components
- Build modern, responsive web interfaces
- Create React/Vue/Angular components
- Design landing pages and dashboards
- Apply consistent styling and themes
- Build HTML/CSS/JavaScript from scratch

**Example:** *"Use the frontend-design skill to build me a landing page for my bakery"*

---

### web-artifacts-builder
**When to use:** Building complex interactive web apps
- Multi-component web applications
- Apps requiring state management
- Interactive dashboards with charts
- Complex React + Tailwind CSS projects
- Apps needing shadcn/ui components

**Example:** *"Use the web-artifacts-builder skill to create an interactive dashboard for tracking expenses"*

---

### webapp-testing
**When to use:** Testing web applications
- Verify frontend functionality works
- Debug UI behavior issues
- Capture screenshots of bugs
- View browser console logs
- Test user interactions

**Example:** *"Use the webapp-testing skill to test the login flow on localhost:3000"*

---

## 🐛 Debugging & Problem Solving

### debugging-root-cause-analysis
**When to use:** Something is broken and you don't know why
- Systematic investigation of errors
- Log analysis and pattern matching
- Hypothesis testing for bugs
- Finding root causes (not just symptoms)
- Analyzing stack traces and error messages

**Example:** *"Use the debugging-root-cause-analysis skill to figure out why the server keeps crashing"*

---

### cloudflare-403-triage
**When to use:** Getting blocked by Cloudflare or seeing "Just a moment..." pages
- Fix Cloudflare/WAF blocking your requests
- Handle challenge pages and CAPTCHAs
- Fix code incorrectly calling private endpoints
- Add error handling for blocked requests

**Example:** *"Use the cloudflare-403-triage skill — my API calls are being blocked"*

---

## 💻 Code Quality & Review

### code-review-refactoring
**When to use:** Improving existing code quality
- Find code smells and anti-patterns
- Refactor messy code to clean code
- Calculate code quality metrics
- Identify technical debt
- Apply design patterns

**Example:** *"Use the code-review-refactoring skill to review this legacy codebase"*

---

### test-driven-development
**When to use:** Writing tests or practicing TDD
- Write unit, integration, and e2e tests
- Follow test-driven development cycle
- Improve test coverage
- Design testable architectures
- Mock external dependencies

**Example:** *"Use the test-driven-development skill to add tests for this payment module"*

---

### spec-forge
**When to use:** Turning vague requirements into detailed specifications
- Transform vague ideas into precise requirements
- Break down complex features into steps
- Validate specification quality
- Generate implementation prompts
- Create testable acceptance criteria

**Example:** *"Use the spec-forge skill to turn 'build a chat app' into a detailed spec"*

---

## 🔧 GitHub & Git Workflows

### gh-address-comments
**When to use:** Addressing review feedback on GitHub PRs
- Find open PRs for your current branch
- Pull review comments that need addressing
- Understand what changes are requested
- Track which comments are resolved

**Example:** *"Use the gh-address-comments skill to see what I need to fix on my PR"*

---

### gh-fix-ci
**When to use:** GitHub Actions checks are failing
- Inspect failing CI checks
- Pull GitHub Actions logs
- Summarize failure context
- Create a fix plan
- Implement the fixes

**Example:** *"Use the gh-fix-ci skill — the tests are failing on my PR"*

---

## 🏗️ System Design & Architecture

### architecture-design
**When to use:** Making big technology decisions
- Choose between monolith vs microservices vs serverless
- Design scalable systems
- Evaluate architectural trade-offs
- Define service boundaries
- Select databases and infrastructure

**Example:** *"Use the architecture-design skill to help me choose between microservices and monolith for my startup"*

---

### database-design-optimization
**When to use:** Working with databases
- Design database schemas
- Optimize slow queries
- Choose between SQL vs NoSQL
- Implement migrations safely
- Tune database performance
- Design indexes for speed

**Example:** *"Use the database-design-optimization skill to design the database for my e-commerce app"*

---

## ⚡ Performance & Optimization

### performance-engineering
**When to use:** Making things faster
- Profile slow code to find bottlenecks
- Optimize algorithms and data structures
- Implement caching strategies
- Design for concurrency
- Load testing and capacity planning

**Example:** *"Use the performance-engineering skill — my API is too slow"*

---

### context-management
**When to use:** Working with very large codebases or files
- Manage AI context window efficiently
- Summarize large files for relevance
- Score content by importance
- Handle multi-file changes
- Prioritize what matters most

**Example:** *"Use the context-management skill — this codebase is huge and I need to find the relevant parts"*

---

## 🔒 Security & Compliance

### security-engineering
**When to use:** Security reviews or building secure systems
- Secure coding practices
- OWASP vulnerability checking
- Threat modeling
- Authentication & authorization design
- Handling sensitive data safely

**Example:** *"Use the security-engineering skill to audit my authentication system"*

---

### hostile-auditor
**When to use:** Verifying code is production-ready (no fakes, stubs, or TODOs)
- Find placeholders and stubs in production code
- Detect TODOs/FIXMEs that shouldn't be there
- Verify external integrations actually work
- Test security properties with real attempts
- Get a SHIP/DO NOT SHIP verdict

**Example:** *"Use the hostile-auditor skill to verify this codebase has no hidden stubs before we release"*

---

## 🔌 Development & Integration

### api-integration
**When to use:** Connecting to external services or building APIs
- Design REST APIs
- Implement GraphQL services
- Build gRPC services
- Handle authentication flows (OAuth, JWT, etc.)
- Add rate limiting and resilience
- Third-party API integration

**Example:** *"Use the api-integration skill to connect to the Stripe API"*

---

### mcp-builder
**When to use:** Building AI tool integrations (MCP servers)
- Create Model Context Protocol servers
- Integrate external APIs with AI
- Design well-structured AI tools
- Build in Python (FastMCP) or Node.js/TypeScript

**Example:** *"Use the mcp-builder skill to create an MCP server that lets AI query my database"*

---

### ci-cd-devops
**When to use:** Setting up automated builds and deployments
- Design CI/CD pipelines
- Set up automated testing on commit
- Implement deployment strategies
- Infrastructure as Code (IaC)
- GitOps workflows

**Example:** *"Use the ci-cd-devops skill to set up GitHub Actions for my project"*

---

## 📱 Mobile Development

### android-app
**When to use:** Building Android applications
- Create Android apps with Android Studio
- Build Jetpack Compose UIs
- Implement MVVM architecture
- Add Room database persistence
- Set up navigation and testing

**Example:** *"Use the android-app skill to build a todo app for Android"*

---

### android-app-dev
**When to use:** Android development (comprehensive)
- Full Android app development lifecycle
- UI with XML layouts or Jetpack Compose
- App architecture (MVVM, ViewModel, LiveData)
- Data persistence with Room
- Navigation, testing, and optimization

**Example:** *"Use the android-app-dev skill to help me refactor my Android app"*

---

### android-instructor-led-curriculum
**When to use:** Working with Android curriculum materials
- Index Android training lessons
- Extract slide text and speaker notes
- Generate instructor artifacts
- Create lesson plans and labs
- Build quizzes and homework

**Example:** *"Use the android-instructor-led-curriculum skill to create a 2-day workshop from these slides"*

---

## 📋 Project Management & Planning

### create-plan
**When to use:** Breaking down complex tasks
- Create step-by-step implementation plans
- Estimate effort and dependencies
- Identify risks and mitigation strategies
- Set milestones and checkpoints

**Example:** *"Use the create-plan skill to plan how to migrate our database"*

---

### linear
**When to use:** Managing work in Linear (issue tracking)
- Read existing Linear tickets
- Create new issues
- Update ticket status
- Track project progress

**Example:** *"Use the linear skill to create tickets for this feature"*

---

## 📝 Notion & Knowledge Management

### notion-knowledge-capture
**When to use:** Turning conversations into Notion documentation
- Save decisions to Notion
- Create wiki entries from chats
- Build how-to guides
- Document FAQs
- Link related pages

**Example:** *"Use the notion-knowledge-capture skill to save this decision to our wiki"*

---

### notion-meeting-intelligence
**When to use:** Preparing for meetings with Notion context
- Gather context from Notion before meetings
- Draft agendas with relevant background
- Tailor materials to attendees
- Prepare pre-reads

**Example:** *"Use the notion-meeting-intelligence skill to prepare for tomorrow's planning meeting"*

---

### notion-research-documentation
**When to use:** Researching across Notion and creating reports
- Gather information from multiple Notion pages
- Synthesize into structured documentation
- Create briefs and comparisons
- Generate reports with citations

**Example:** *"Use the notion-research-documentation skill to compile a report on our Q3 initiatives"*

---

### notion-spec-to-implementation
**When to use:** Turning Notion specs into implementation plans
- Convert PRDs to implementation tasks
- Create development plans from specs
- Track progress in Notion
- Link specs to code

**Example:** *"Use the notion-spec-to-implementation skill to turn this product spec into development tasks"*

---

## 🤖 AI/ML Specialized

### optimize-prompt
**When to use:** Improving AI prompts for better results
- Optimize prompts with measurable improvements
- A/B test prompt variations
- Benchmark prompt performance
- Test for bias and robustness
- Harden against prompt injection

**Example:** *"Use the optimize-prompt skill to improve this classification prompt"*

---

### multi-agent-orchestration
**When to use:** Building systems with multiple AI agents
- Design agent workflows
- Coordinate multiple agents
- Define agent roles and communication
- Resolve agent conflicts
- Build autonomous agent teams

**Example:** *"Use the multi-agent-orchestration skill to design a system where agents research, write, and review content"*

---

### agent-cognitive-architecture
**When to use:** Designing sophisticated autonomous agents
- Design agents with world models
- Implement theory of mind
- Add metacognition (thinking about thinking)
- Create goal arbitration systems
- Build persistent memory for agents
- Plan for safety and adversarial behavior

**Example:** *"Use the agent-cognitive-architecture skill to design an autonomous research agent"*

---

## 📊 UPS Decision Intelligence (Specialized)

A suite of skills for building prediction and decision systems:

| Skill | Purpose |
|-------|---------|
| **ups-probabilistic-answering** | Generate decision-grade probabilistic predictions with uncertainty quantification |
| **ups-evaluation-calibration** | Evaluate and calibrate probabilistic predictions (scoring rules, ECE, backtesting) |
| **ups-causal-interventions** | Causal and interventional prediction (P(y\|do(x))) |
| **ups-decision-intelligence-ui** | Design dashboards for probabilistic predictions and uncertainty signals |
| **ups-predict-dashboard** | Build UPS-style prediction dashboards with conformal bands and deferral tiers |
| **ups-system-blueprint-mlops** | End-to-end MLOps architecture for prediction systems |
| **ups-kb-authoring** | Write knowledge base content with retrieval-friendly structure |

**When to use:** Building prediction systems, forecasting applications, or decision-support AI that needs to quantify uncertainty and provide calibrated probabilistic outputs.

---

## 🔍 Observability & Monitoring

### observability-monitoring
**When to use:** Adding visibility to production systems
- Instrument code with logging and metrics
- Set up distributed tracing
- Design monitoring dashboards
- Configure alerting
- Define SLIs/SLOs/SLAs

**Example:** *"Use the observability-monitoring skill to add monitoring to my production service"*

---

## 🚀 Quick Start Guide

### For First-Time Users

1. **Don't memorize everything** — bookmark this page and reference it when needed
2. **Use natural language** — you can say "help me create a Word document" and the AI will automatically use the docx skill
3. **Be specific when needed** — if you want a particular skill, mention it by name: *"Use the hostile-auditor skill to check this code"*

### How to Use a Skill

There are three ways:

1. **Automatic** — Just describe what you need, and the AI will pick the right skill
   > *"Create a budget spreadsheet for my business"* → Automatically uses xlsx skill

2. **Explicit by name** — Mention the skill name to ensure it's used
   > *"Use the security-engineering skill to review this authentication code"*

3. **Slash command style** — Some interfaces support `/skill:name` syntax
   > `/skill:pdf extract text from invoice.pdf`

### Common Workflows

**Building a Web App:**
1. `create-plan` → Break down the project
2. `architecture-design` → Choose your tech stack
3. `frontend-design` or `web-artifacts-builder` → Build the UI
4. `database-design-optimization` → Design the data layer
5. `test-driven-development` → Add tests
6. `security-engineering` → Security review
7. `hostile-auditor` → Final verification before launch

**Creating Documentation:**
1. `notion-research-documentation` → Gather existing info
2. `docx` or `pptx` → Create the document
3. `pdf` → Export to PDF if needed

**Fixing Production Issues:**
1. `debugging-root-cause-analysis` → Find the cause
2. `observability-monitoring` → Add better monitoring
3. `performance-engineering` → Optimize if needed

---

## 📦 Skill File Locations

Skills are loaded from (in priority order):

1. **Built-in** — Core skills bundled with Kimi
2. **User directory** — `~/.config/agents/skills/` ← **You are here**
3. **Project directory** — `.agents/skills/` in your project

### Installation

Skills in this directory are automatically available. No installation needed!

To add more skills, place `.skill` files (zip archives) or skill directories here.

---

## 🛠️ For Skill Developers

### Skill Structure

```
skill-name/
├── SKILL.md              # Main skill definition (required)
│   ├── YAML frontmatter with name and description
│   └── Markdown instructions
├── references/           # Optional: Extended documentation
│   └── advanced-topic.md
├── scripts/             # Optional: Executable utilities
│   └── helper.py
└── assets/              # Optional: Templates, images, etc.
    └── template.docx
```

### Packaging Skills

To create a distributable `.skill` file:

```bash
cd ~/.config/agents/skills/
zip -r my-skill.skill my-skill/
```

### Best Practices

- **Keep SKILL.md concise** — Under 500 lines, use references for detailed content
- **Clear description** — The description triggers skill selection, make it comprehensive
- **Progressive disclosure** — Put advanced details in references/, load only when needed
- **Test scripts** — Any scripts included should be tested and working

---

## 📖 Full Skill Inventory

| Skill | Category | Description |
|-------|----------|-------------|
| agent-cognitive-architecture | AI/ML | Design autonomous agents with world models and metacognition |
| android-app | Mobile | Build Android apps with Android Studio and Jetpack |
| android-app-dev | Mobile | Comprehensive Android development guide |
| android-instructor-led-curriculum | Education | Work with Android training curriculum materials |
| api-integration | Integration | REST, GraphQL, gRPC API design and integration |
| architecture-design | Design | System architecture and technology decisions |
| ci-cd-devops | DevOps | CI/CD pipelines and automated delivery |
| cloudflare-403-triage | Debugging | Fix Cloudflare/WAF blocking issues |
| code-review-refactoring | Code Quality | Code review and refactoring patterns |
| context-management | Optimization | Context window management for large codebases |
| create-plan | Planning | Create implementation plans for complex tasks |
| database-design-optimization | Database | Database schema design and query optimization |
| debugging-root-cause-analysis | Debugging | Systematic debugging and root cause analysis |
| docx | Documents | Word document creation, editing, and analysis |
| frontend-design | Frontend | Create distinctive, production-grade web interfaces |
| gh-address-comments | GitHub | Address review comments on GitHub PRs |
| gh-fix-ci | GitHub | Fix failing GitHub Actions CI checks |
| hostile-auditor | Security | Adversarial verification of codebase readiness |
| linear | Project Mgmt | Manage Linear issues and projects |
| mcp-builder | Integration | Build MCP servers for AI tool integration |
| multi-agent-orchestration | AI/ML | Coordinate multiple AI agents |
| notion-knowledge-capture | Notion | Capture conversations into Notion documentation |
| notion-meeting-intelligence | Notion | Prepare meetings with Notion context |
| notion-research-documentation | Notion | Research and synthesize Notion content |
| notion-spec-to-implementation | Notion | Turn Notion specs into implementation plans |
| observability-monitoring | Operations | Production monitoring and observability |
| optimize-prompt | AI/ML | Optimize and harden prompts |
| pdf | Documents | PDF creation, editing, extraction, forms |
| performance-engineering | Performance | Performance profiling and optimization |
| pptx | Documents | PowerPoint presentation creation and editing |
| security-engineering | Security | Secure coding and vulnerability assessment |
| spec-forge | Planning | Transform requirements into specifications |
| test-driven-development | Code Quality | Test-driven development and testing strategies |
| ups-causal-interventions | UPS/Prediction | Causal and interventional prediction |
| ups-decision-intelligence-ui | UPS/Prediction | Dashboard design for probabilistic predictions |
| ups-evaluation-calibration | UPS/Prediction | Evaluate and calibrate predictions |
| ups-kb-authoring | UPS/Prediction | Knowledge base authoring for prediction systems |
| ups-predict-dashboard | UPS/Prediction | Build prediction dashboards |
| ups-probabilistic-answering | UPS/Prediction | Generate probabilistic predictions with uncertainty |
| ups-system-blueprint-mlops | UPS/Prediction | MLOps architecture for prediction systems |
| web-artifacts-builder | Frontend | Build complex multi-component web artifacts |
| webapp-testing | Testing | Test local web applications |
| xlsx | Documents | Spreadsheet creation, editing, and analysis |

**Total: 43 specialized skills**

---

*Last updated: 2026-02-18*
