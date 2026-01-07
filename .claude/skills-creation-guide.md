# Claude Skills Creation Guide

Reference document for creating effective Claude Skills for Django-allauth.

## Core Quality Checklist

### Description Requirements
- [ ] Specific and includes key terms
- [ ] Explains both WHAT the Skill does AND WHEN to use it
- [ ] SKILL.md body under 500 lines
- [ ] Additional details in separate reference files (if needed)
- [ ] No time-sensitive information (or in "old patterns" section)
- [ ] Consistent terminology throughout
- [ ] Examples are concrete, not abstract

### File Structure Rules
- [ ] References are ONE level deep from SKILL.md
- [ ] Progressive disclosure used appropriately
- [ ] Workflows have clear steps
- [ ] Files longer than 100 lines have table of contents

### Scripts and Code
- [ ] Scripts solve problems (don't punt to Claude)
- [ ] Error handling is explicit and helpful
- [ ] No "voodoo constants" (all values justified)
- [ ] Required packages listed and verified as available
- [ ] Scripts have clear documentation
- [ ] All forward slashes (no Windows-style paths)
- [ ] Validation/verification steps for critical operations
- [ ] Feedback loops for quality-critical tasks

## Recommended Structure

```
skill-name/
├── SKILL.md           # Overview, under 500 lines, points to reference files
└── reference/
    ├── topic-a.md     # Specific topic details
    ├── topic-b.md     # Another topic
    └── examples/      # Code examples if needed
```

## Key Patterns

### Plan-Validate-Execute Pattern
For complex tasks: analyze → create plan file → validate plan → execute → verify

### Progressive Disclosure
- SKILL.md contains overview and common operations
- Reference files contain detailed information
- Keep references one level deep

### Table of Contents
For files > 100 lines, include TOC at top so Claude sees full scope even with partial reads.

## Anti-Patterns to Avoid

1. **Deeply nested references** - Claude may only preview nested files
2. **Time-sensitive information** without marking as potentially outdated
3. **Abstract examples** - always use concrete, runnable examples
4. **Windows paths** - always use forward slashes
5. **Magic numbers** - justify all constants and values
6. **Exceeding 500 lines** in SKILL.md - split into reference files
