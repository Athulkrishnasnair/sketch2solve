# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: ux-enhancements.spec.js >> Sketch2Solve UX Enhancements & Branding Suite >> 4. Truss Editor visual verification in Light and Dark themes
- Location: tests/e2e/ux-enhancements.spec.js:151:3

# Error details

```
Test timeout of 90000ms exceeded.
```

```
Test timeout of 90000ms exceeded.
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - complementary [ref=e4]:
    - link "Sketch2Solve STRUCTURE REVIEW" [ref=e5] [cursor=pointer]:
      - /url: /
      - generic [ref=e8]:
        - strong [ref=e9]: Sketch2Solve
        - generic [ref=e10]: STRUCTURE REVIEW
    - generic [ref=e11]: Local workspace
    - navigation "Main navigation" [ref=e13]:
      - button "Dashboard" [ref=e14] [cursor=pointer]
      - button "Natural Language Design" [ref=e21] [cursor=pointer]
      - button "New analysis" [ref=e27] [cursor=pointer]
      - button "Analysis history 0" [ref=e31] [cursor=pointer]:
        - generic [ref=e37]: Analysis history
        - generic [ref=e38]: "0"
      - button "Getting Started" [ref=e39] [cursor=pointer]
    - generic [ref=e44]:
      - generic [ref=e45]: 📐
      - generic [ref=e46]:
        - strong [ref=e47]: Interactive Tour
        - paragraph [ref=e48]: Explore the 9-step structural engineering workflow.
        - button "Open Guide →" [ref=e49] [cursor=pointer]
    - generic [ref=e50]: System Ready · v1.0
  - main [ref=e52]:
    - generic [ref=e53]:
      - generic [ref=e54]:
        - generic [ref=e55]: Workspace
        - generic [ref=e56]: /
        - strong [ref=e57]: Natural Language Design
      - generic [ref=e58]:
        - button "Switch to Dark Theme" [ref=e59] [cursor=pointer]
        - button "Open Getting Started Guide" [ref=e62] [cursor=pointer]:
          - generic [ref=e65]: Guide
        - button "E Engineer" [ref=e67] [cursor=pointer]:
          - generic [ref=e68]: E
          - generic [ref=e69]: Engineer
    - generic [ref=e72]:
      - generic [ref=e73]:
        - generic [ref=e74]:
          - generic [ref=e75]: CONVERSATIONAL TRUSS WORKBENCH
          - heading "Natural Language Design Studio" [level=1] [ref=e76]
          - paragraph [ref=e77]: Synthesize new structural geometries, modify canvas snapshots, and inspect determinacy using deterministic engineering rules.
        - generic [ref=e79]:
          - generic [ref=e80]: "Target Structure:"
          - combobox "Target Structure:" [ref=e81] [cursor=pointer]:
            - option "＋ New Truss Design (Blank Canvas)" [selected]
      - generic [ref=e82]:
        - generic [ref=e83]:
          - generic [ref=e84]:
            - generic [ref=e85]:
              - generic [ref=e86]:
                - generic "Model revision 1" [ref=e88]: Rev 1
                - radiogroup "Design Intent" [ref=e93]:
                  - button "Auto" [ref=e94] [cursor=pointer]
                  - button "Create" [ref=e95] [cursor=pointer]
                  - button "Modify" [ref=e96] [cursor=pointer]
                  - button "Explain" [ref=e97] [cursor=pointer]
              - generic [ref=e98]:
                - button "Add a diagonal between J1 and J3" [ref=e99] [cursor=pointer]
                - button "Move J2 up by 0.5 m" [ref=e100] [cursor=pointer]
                - button "Add 10 kN downward load at top" [ref=e101] [cursor=pointer]
                - button "Why is this structure unstable?" [ref=e102] [cursor=pointer]
            - generic [ref=e103]:
              - textbox "Describe structural change or question (e.g. \"Add a diagonal between J1 and J3\", \"Move J2 up 0.5m\", \"Why unstable?\")..." [active] [ref=e104]: Create a triangular truss with 6 m span and 3 m height
              - generic [ref=e105]:
                - generic [ref=e106]: Enter ↵ to submit · Shift+Enter for newline
                - button "Generate" [ref=e107] [cursor=pointer]
          - generic [ref=e112]:
            - strong [ref=e117]: CAD Design Conventions
            - list [ref=e118]:
              - listitem [ref=e119]:
                - strong [ref=e120]: "CREATE:"
                - text: Specify span, height, panel count, and support conditions (e.g.
                - emphasis [ref=e121]: "\"Warren truss, 6 m span, 4 panels\""
                - text: ).
              - listitem [ref=e122]:
                - strong [ref=e123]: "MODIFY:"
                - text: Reference existing joint/member IDs (e.g.
                - emphasis [ref=e124]: "\"Add diagonal between J1 and J3\""
                - text: ","
                - emphasis [ref=e125]: "\"Move J2 up 0.5 m\""
                - text: ).
              - listitem [ref=e126]:
                - strong [ref=e127]: "EXPLAIN:"
                - text: Ask about determinacy, stability, or support reactions (e.g.
                - emphasis [ref=e128]: "\"Why is this unstable?\""
                - text: ).
              - listitem [ref=e129]:
                - strong [ref=e130]: "SAFETY GATE:"
                - text: AI proposals are strictly non-destructive previews until explicitly approved.
        - generic [ref=e131]:
          - strong [ref=e135]: Structural Geometry Preview
          - generic [ref=e136]:
            - generic [ref=e137]:
              - strong [ref=e142]: Ready to Design
              - paragraph [ref=e143]: Type a prompt on the left to synthesize a new truss structure, or select an existing analysis above.
            - generic [ref=e144]:
              - generic [ref=e145]: Existing Member
              - generic [ref=e147]: Proposed Addition
              - generic [ref=e149]: Proposed Deletion
              - generic [ref=e151]: Support Constraint
    - generic [ref=e153]:
      - generic [ref=e154]: Sketch2Solve · Structural Truss Engineering
      - generic [ref=e155]: Deterministic analysis and verification.
  - dialog [ref=e157]:
    - generic [ref=e158]:
      - img "Sketch2Solve Logo" [ref=e160]
      - heading "Welcome to Sketch2Solve" [level=2] [ref=e161]
      - paragraph [ref=e162]: Lightweight structural engineering, sketch interpretation, and natural language design.
    - generic [ref=e163]:
      - generic [ref=e164]:
        - generic [ref=e165]: What should we call you?
        - textbox "What should we call you?" [ref=e166]:
          - /placeholder: e.g. Alex, Morgan, StructEng...
      - generic [ref=e167]:
        - button "Skip" [ref=e168] [cursor=pointer]
        - button "Get Started" [ref=e169] [cursor=pointer]
```