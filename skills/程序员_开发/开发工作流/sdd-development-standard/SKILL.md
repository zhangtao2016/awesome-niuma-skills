---
name: sdd-development-standard
description: 标准化的软件设计文档（SDD）分层开发规范，定义固定职责的文档体系，实现AI辅助开发的需求全链路锚定、上下文稳定、变更可追溯。适用于 IDE中复杂项目的需求管理、架构设计、代码实现与测试全流程管控。
metadata:
  author: Cursor Community
  version: "1.0.0"
  created: 2026-03-08
allowed-tools: Read Write FileSystem
---

# SDD (Software Design Document) Development Standard
## Core Definition
This specification defines a modular, document-driven AI-assisted development framework with a fixed layered file structure and clear responsibility boundaries. All AI operations MUST be anchored to the corresponding document, ensuring full traceability, requirement alignment, and context stability in complex coding projects.

## Fixed File Structure & Responsibility Boundaries
All files MUST be stored in the root directory of the project, with exact filenames and fixed usage rules as defined below. Document modification must follow the top-down order, no reverse modification is allowed without explicit developer approval.

---

### 01_requirements.md - User Requirements & User Stories
#### Core Purpose
The single source of truth for all business requirements, user needs, and acceptance criteria. All subsequent design, implementation, and testing MUST be strictly aligned with the content of this file.
#### Mandatory Content Structure
1. **Feature Overview**: High-level description of the feature/module, business objectives, and scope boundaries
2. **User Stories**: Standardized format: `As a [user role], I want [feature], so that [business value]`
3. **Acceptance Criteria**: Clear, testable pass/fail conditions for each user story
4. **Non-Functional Requirements**: Performance, security, compatibility, and other non-business requirements
5. **Constraints & Limitations**: Technical constraints, dependency limits, and out-of-scope content
#### Operation Rules
- This file may only be modified with explicit developer approval
- All requirements must be traceable to a user story in this file
- Any deviation from the requirements in this file must be explicitly flagged to the developer

---

### 02_interface.md - Tech Stack & Data Structures
#### Core Purpose
Define the technical architecture, module boundaries, data models, and interface specifications, bridging business requirements and technical implementation.
#### Mandatory Content Structure
1. **Tech Stack Selection**: Exact programming language, framework, library versions, and dependency list
2. **Module Architecture**: High-level module division, dependency graph, and responsibility boundaries for each module
3. **Core Data Structures**: Exact definition of all data models, including field names, types, constraints, and relationships
4. **Interface Specifications**: Exact API definitions, including request/response formats, endpoint paths, HTTP methods, and error codes
5. **Dependency Management**: Third-party dependencies, internal module dependencies, and version constraints
#### Operation Rules
- This file may only be modified after the corresponding content in `01_requirements.md` is approved
- All data structures and interfaces must be aligned with the user stories in `01_requirements.md`
- No implementation details or executable code may be included in this file

---

### 03_implementation.md - Detailed Implementation Logic
#### Core Purpose
Define the exact, step-by-step implementation logic for all features, serving as the only valid input for code execution.
#### Mandatory Content Structure
1. **Implementation Overview**: High-level implementation flow and module execution order
2. **File-by-File Implementation Details**: Exact file paths, function names, parameter definitions, and core logic for each file to be modified/created
3. **Error Handling Strategy**: Exact error handling logic, exception types, and fallback mechanisms
4. **Performance Optimization Details**: Specific optimization measures aligned with non-functional requirements
5. **Final Implementation Checklist**: Atomic, sequential execution steps for code implementation
#### Operation Rules
- This file may only be modified after the corresponding content in `02_interface.md` is approved
- All implementation details must be strictly aligned with the data structures and interfaces in `02_interface.md`
- No executable code may be included in this file, only logical descriptions and implementation specifications
- The final checklist must be comprehensive enough that no creative decisions are required during code execution

---

### 04_test.md - Test Cases
#### Core Purpose
Define all test cases to validate the implementation meets the requirements, serving as the standard for final delivery review.
#### Mandatory Content Structure
1. **Test Scope**: Test coverage boundaries, including unit tests, integration tests, end-to-end tests, and edge case tests
2. **Test Environment**: Exact environment requirements, dependency versions, and test setup steps
3. **Test Cases**: For each user story, detailed test cases with: Test ID, Corresponding User Story ID, Preconditions, Test Steps, Expected Results, Acceptance Criteria
4. **Edge Case Tests**: Boundary conditions, error scenarios, and abnormal input test cases
5. **Performance Test Benchmarks**: Exact performance metrics and pass/fail thresholds
#### Operation Rules
- This file may only be modified after the corresponding content in `01_requirements.md` and `03_implementation.md` is approved
- All test cases must be strictly aligned with the acceptance criteria in `01_requirements.md`
- No implementation code may be included in this file, only test specifications

---

### AI_CHANGELOG.md - AI Operation Changelog
#### Core Purpose
Full traceability of all AI-generated modifications, ensuring every change has a clear origin, purpose, and corresponding document anchor.
#### Mandatory Entry Format
Each change entry MUST follow this exact format:

[Timestamp] - [Change Type: Feature Implementation / Bug Fix / Refactor / Documentation Update]
+ Corresponding SDD Document Anchor: [File Name + Section ID]
+ Corresponding Implementation Checklist Item: [Checklist Number]
+ Detailed Change Description: Exact files modified, line numbers changed, and core content of the modification
+ Developer Approval Status: [Approved / Pending]

#### Operation Rules
- This file MUST be updated immediately after completing any code modification or document update
- Every entry must have a clear anchor to the corresponding SDD document
- No changes may be made to the codebase without a corresponding entry in this file
- All entries must be approved by the developer before being merged into the main branch

## Global Operation Rules
1. All AI operations MUST be anchored to the corresponding SDD document. No unanchored operations are allowed
2. Document modification must follow the top-down order: `01_requirements.md` → `02_interface.md` → `03_implementation.md` → `04_test.md`
3. All code implementation must be strictly based on the content of `03_implementation.md`
4. All review operations must be based on the content of `04_test.md` and the approved implementation plan
5. Keep individual reference files focused, avoid deeply nested reference chains, use relative paths from the project root when referencing files

## Progressive Disclosure Guidelines
- Metadata (name and description) is loaded at startup for skill matching
- Full `SKILL.md` content is loaded when the skill is activated
- Detailed reference material should be moved to the `references/` directory, loaded only when required
- Keep the main `SKILL.md` under 500 lines for optimal context efficiency

## Validation
Validate this skill with the official skills-ref tool:
