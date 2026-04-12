# Architecture Diagrams

Three Mermaid flowcharts describing the `second_brain` package:
its module layout, its CLI entry points, and a typical user flow.

## 1. Package Overview

How modules, functions, and external dependencies connect.

```mermaid
flowchart LR
    subgraph External["External Dependencies"]
        direction TB
        Typer["typer"]
        Loguru["loguru"]
        Stdlib["stdlib<br/>(os, re, pathlib,<br/>datetime, unicodedata)"]
    end

    subgraph Entry["Entry Layer"]
        direction TB
        Main["__main__.py<br/>main()"]
        Init["__init__.py"]
    end

    subgraph CLI["CLI Layer — app.py"]
        direction TB
        AppObj["app (Typer)"]
        RootCb["_root()<br/>callback"]
        CfgLog["configure_logging()"]
        CmdNew["new()"]
        CmdList["list_notes()"]
        CmdShow["show()"]
        MainFn["main()"]
    end

    subgraph Core["Core Layer — notes.py"]
        direction TB
        NoteEntry["NoteEntry<br/>(dataclass)"]
        Slugify["slugify()"]
        Resolve["resolve_storage_dir()"]
        BuildFn["build_filename()"]
        SaveFn["save_thought()"]
        IterFn["iter_notes()"]
        TitleFn["_title_from_stem()"]
        FirstLn["_first_non_empty_line()"]
    end

    Main --> MainFn
    MainFn --> AppObj
    AppObj --> RootCb
    RootCb --> CfgLog
    AppObj --> CmdNew
    AppObj --> CmdList
    AppObj --> CmdShow

    CmdNew --> Resolve
    CmdNew --> SaveFn
    CmdList --> Resolve
    CmdList --> IterFn
    CmdShow --> Resolve
    CmdShow --> IterFn

    SaveFn --> BuildFn
    BuildFn --> Slugify
    IterFn --> NoteEntry
    IterFn --> TitleFn
    IterFn --> FirstLn

    CLI --> Typer
    CLI --> Loguru
    Core --> Stdlib
```

---

## 2. CLI Entry Points

The arguments and options accepted by each subcommand, and the
code path invoked behind each.

```mermaid
flowchart LR
    CLI(["python -m second_brain<br/>or: second-brain"]) --> Root["_root callback<br/>configure_logging()"]

    Root --> New["new"]
    Root --> List["list"]
    Root --> Show["show"]

    subgraph NewCmd["new — save a thought"]
        direction LR
        NewArg["THOUGHT<br/>(positional, required)"] --> NewCall["save_thought(<br/>text, storage_dir)"]
        NewCall --> NewOut["writes<br/>YYYY-MM-DD-&lt;slug&gt;.md"]
    end

    subgraph ListCmd["list — list notes newest first"]
        direction LR
        ListOpt["--limit N<br/>(optional, min=1)"] --> ListCall["iter_notes(storage_dir)"]
        ListCall --> ListOut["prints<br/>index. title — line — date"]
    end

    subgraph ShowCmd["show — print a note"]
        direction LR
        ShowArg["INDEX<br/>(positional, min=1)"] --> ShowCall["iter_notes(storage_dir)<br/>[index - 1]"]
        ShowCall --> ShowOut["prints<br/>header + file contents"]
    end

    New --> NewCmd
    List --> ListCmd
    Show --> ShowCmd

    EnvBox["Environment<br/>---<br/>SB_DIR (storage path)<br/>LOG_LEVEL (default INFO)<br/>LOG_FILE (default app.log)"]
    EnvBox -.read by.-> Root
    EnvBox -.read by.-> NewCmd
    EnvBox -.read by.-> ListCmd
    EnvBox -.read by.-> ShowCmd
```

---

## 3. Example User Flow

A typical capture → browse → read session.

```mermaid
flowchart LR
    Start(["User opens terminal"]) --> Cap["second-brain new<br/>'idea for onboarding flow'"]

    Cap --> Resolve1["resolve_storage_dir()<br/>reads SB_DIR"]
    Resolve1 --> Save["save_thought()"]
    Save --> Slug["slugify + build_filename"]
    Slug --> Collide{"file<br/>exists?"}
    Collide -- no --> Write["write .md to disk"]
    Collide -- yes --> Bump["append -2, -3, ..."] --> Write
    Write --> Echo1(["echo: Saved: /path/...md"])

    Echo1 --> Browse["second-brain list --limit 5"]
    Browse --> Resolve2["resolve_storage_dir()"]
    Resolve2 --> Iter["iter_notes()"]
    Iter --> Sort["sort by mtime<br/>(newest first)"]
    Sort --> Render(["echo each:<br/>idx. title — line — date"])

    Render --> Pick["user picks index 1"]
    Pick --> ShowCmd["second-brain show 1"]
    ShowCmd --> Iter2["iter_notes()"]
    Iter2 --> Range{"index<br/>in range?"}
    Range -- no --> Err(["stderr + exit 1"])
    Range -- yes --> Print(["echo header + file contents"])

    Print --> End(["User reads the note"])
```
