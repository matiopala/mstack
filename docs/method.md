# Method workflow

Method moves a task from an idea to a recorded merge. You approve the preparation
documents, then authorize implementation. An implementer changes the code, and a
fresh independent verifier checks an exact candidate commit. You try and accept
the verified candidate before manual delivery.

```mermaid
flowchart TD
    Start["You invoke $method or /method"] --> Prep

    subgraph Prep["Preparation — you approve each artifact"]
        I["Interview: what do you want?"]
        E["Exploration: how does the project work?"]
        R["Requirements: what must change?"]
        V["Verification design: how will we prove it?"]
        P["Plan: how will we build it?"]
        I --> E --> R --> V --> P
    end

    Prep --> Auth{"You authorize execution"}
    Auth --> Build["Implementer agent makes changes"]
    Build --> Candidate["Controller saves an exact candidate commit"]
    Candidate --> Check["Fresh independent verifier tests and reviews it"]
    Check --> Result{"Required checks pass?"}
    Result -->|"No: scoped repairs within budget"| Build
    Result --> Yes["You try the verified candidate"]
    Yes --> Decision{"Your decision"}
    Decision -->|"Request corrections"| Auth
    Decision -->|"Accept"| Merge["Manual merge"]
    Merge --> Done["Record delivery → complete"]

    classDef human fill:#fff2cc,stroke:#9a7600,color:#332600;
    class Auth,Yes,Decision,Merge human;
```

Repairs use the remaining execution budget. Code changes require a new candidate
and fresh verification. Requirement changes return to preparation for approval.
The dashboard shows progress and evidence; decisions stay in the conversation.

For maintenance details, see [Method controller internals](method-controller.md).
