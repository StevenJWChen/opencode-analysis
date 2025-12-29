# OpenCode - Detailed Implementation Analysis

## Table of Contents
1. [Core Architecture](#core-architecture)
2. [Data Flow](#data-flow)
3. [Session Management](#session-management)
4. [Message System](#message-system)
5. [Agent System](#agent-system)
6. [Tool System](#tool-system)
7. [Provider Integration](#provider-integration)
8. [Permission System](#permission-system)
9. [LLM Streaming](#llm-streaming)
10. [File System Operations](#file-system-operations)
11. [Implementation Patterns](#implementation-patterns)

---

## 1. Core Architecture

### 1.1 Overall Structure

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│  (yargs, commands, TUI with SolidJS)                        │
└───────────────────┬─────────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────────┐
│                      Server Layer                            │
│  (Hono HTTP/WebSocket server, mDNS, API endpoints)         │
└───────────────────┬─────────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────────┐
│                    Session Layer                             │
│  (Session, Message, Processor, LLM streaming)               │
└───────────────────┬─────────────────────────────────────────┘
                    │
┌───────────────────┴─────────────────────────────────────────┐
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Agent     │  │     Tool     │  │   Provider   │      │
│  │   System     │  │   Registry   │  │   Manager    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
└───────────────────┬─────────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────────┐
│                    Storage Layer                             │
│  (File-based storage, Snapshots, Patches)                   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Key Components

**Instance** - Project-scoped singleton state management
- Manages project directory and configuration
- Provides scoped state for agents, tools, and sessions

**Bus** - Event-driven communication
- Publishes events for session creation, updates, errors
- Enables loose coupling between components

**Storage** - Persistent data layer
- File-based JSON storage
- Hierarchical key-value structure: `["session", projectID, sessionID]`

**Identifier** - ID generation system
- Ascending IDs: Sortable, incremental (for parts, messages within session)
- Descending IDs: Reverse chronological (for sessions)
- ULID-based for global uniqueness

---

## 2. Data Flow

### 2.1 User Message Flow

```
User Input (CLI/TUI)
    │
    ├─> Session.createMessage(user message)
    │
    ├─> SessionProcessor.create(assistantMessage)
    │
    ├─> SessionProcessor.process()
    │     │
    │     ├─> LLM.stream() ──┐
    │     │                   │
    │     │                   ├─> Provider.getLanguage()
    │     │                   ├─> SystemPrompt.build()
    │     │                   ├─> ToolRegistry.resolve()
    │     │                   └─> streamText() [Vercel AI SDK]
    │     │
    │     ├─> Process stream events:
    │     │     ├─> text-delta → TextPart
    │     │     ├─> reasoning-delta → ReasoningPart
    │     │     ├─> tool-call → ToolPart
    │     │     └─> tool-result → Update ToolPart
    │     │
    │     ├─> Execute tools via ToolRegistry
    │     │     │
    │     │     ├─> Permission check
    │     │     ├─> Tool.execute()
    │     │     └─> Return result/error
    │     │
    │     ├─> Check for continuation:
    │     │     ├─> Has tool calls? → Continue loop
    │     │     ├─> Finish reason = "stop"? → Break
    │     │     └─> Max steps reached? → Break
    │     │
    │     └─> Update assistant message with parts
    │
    └─> Session.touch() (update timestamp)
```

### 2.2 Tool Execution Flow

```
Tool Call from LLM
    │
    ├─> ToolRegistry.get(toolName)
    │
    ├─> Tool.init(context) → { description, parameters, execute }
    │
    ├─> Validate parameters (Zod schema)
    │
    ├─> Permission.check(agent, tool, params)
    │     │
    │     ├─> "allow" → Continue
    │     ├─> "deny" → Throw PermissionDeniedError
    │     └─> "ask" → Permission.ask() → User approval dialog
    │
    ├─> Tool.execute(params, context)
    │     │
    │     └─> Tool-specific logic:
    │           ├─> BashTool → Shell execution
    │           ├─> EditTool → File modification
    │           ├─> GrepTool → Code search
    │           └─> etc.
    │
    └─> Return { title, metadata, output, attachments? }
```

---

## 3. Session Management

### 3.1 Session Data Structure

```typescript
Session.Info = {
  id: string                    // Descending ULID
  projectID: string             // Project identifier
  directory: string             // Working directory
  parentID?: string             // For child sessions (forks)
  title: string                 // User-visible name
  version: string               // OpenCode version
  time: {
    created: number
    updated: number
    compacting?: number         // During context compression
    archived?: number           // Soft delete
  }
  summary?: {                   // Code change stats
    additions: number
    deletions: number
    files: number
    diffs?: FileDiff[]
  }
  share?: {                     // Public sharing
    url: string
  }
  revert?: {                    // Undo state
    messageID: string
    partID?: string
    snapshot?: string
    diff?: string
  }
}
```

### 3.2 Session Operations

**Create Session**
```typescript
Session.create({ parentID?, title? })
  → Identifier.descending("session")
  → Storage.write(["session", projectID, sessionID], data)
  → Bus.publish(Session.Event.Created)
  → Auto-share if configured
```

**Fork Session** - Create child from existing session
```typescript
Session.fork({ sessionID, messageID? })
  → Create new session
  → Clone messages up to messageID
  → Clone parts for each message
  → Return new session
```

**Touch Session** - Update activity timestamp
```typescript
Session.touch(sessionID)
  → Update time.updated = Date.now()
  → Used to track "last used" for session list
```

### 3.3 Session Storage

File structure:
```
~/.opencode/
  storage/
    projects/
      <projectID>/
        sessions/
          <sessionID>/
            info.json          # Session metadata
            messages/
              <messageID>/
                info.json      # Message metadata
                parts/
                  <partID>.json  # Individual parts
```

---

## 4. Message System

### 4.1 Message Types

**User Message**
```typescript
MessageV2.User = {
  id: string
  sessionID: string
  role: "user"
  parts: Part[]              // TextPart, FilePart, AgentPart, etc.
  system?: string            // Custom system prompt override
  time: { created: number, updated: number }
}
```

**Assistant Message**
```typescript
MessageV2.Assistant = {
  id: string
  sessionID: string
  role: "assistant"
  parts: Part[]              // TextPart, ToolPart, ReasoningPart, etc.
  agent: string              // Agent name that generated this
  model: {
    id: string
    providerID: string
  }
  usage?: {                  // Token tracking
    promptTokens: number
    completionTokens: number
    totalTokens: number
  }
  error?: {                  // If generation failed
    name: string
    message: string
    data?: Record<string, any>
  }
  time: { created: number, updated: number }
}
```

### 4.2 Part Types

OpenCode uses a **discriminated union** of part types:

```typescript
// User-generated parts
TextPart = {
  type: "text"
  text: string
  synthetic?: boolean        // Auto-generated (not from user)
  ignored?: boolean          // Excluded from context
  metadata?: Record<string, any>
}

FilePart = {
  type: "file"
  mime: string
  filename?: string
  url: string                // data: URL or file path
  source?: FilePartSource    // Where file came from
}

AgentPart = {
  type: "agent"
  name: string               // Agent to invoke
  source?: { value, start, end }
}

// Assistant-generated parts
ToolPart = {
  type: "tool"
  tool: string               // Tool name
  callID: string             // Unique call identifier
  state: {
    status: "pending" | "running" | "success" | "error" | "rejected"
    input: Record<string, any>
    output?: string
    error?: string
    metadata?: Record<string, any>
    time?: { start: number, end?: number }
  }
}

ReasoningPart = {
  type: "reasoning"          // Extended thinking (Claude)
  text: string
  time: { start: number, end: number }
}

SnapshotPart = {
  type: "snapshot"
  snapshot: string           // Git-like snapshot hash
}

PatchPart = {
  type: "patch"
  hash: string               // Diff hash
  files: string[]            // Affected files
}
```

### 4.3 Message Context Building

For LLM context, messages are converted to ModelMessage format:

```typescript
function toModelMessage(message: MessageV2.User | MessageV2.Assistant) {
  if (message.role === "user") {
    return {
      role: "user",
      content: message.parts
        .filter(p => !p.ignored)
        .map(part => {
          if (part.type === "text") return { type: "text", text: part.text }
          if (part.type === "file") return { type: "image", image: part.url }
          // ...
        })
    }
  }

  if (message.role === "assistant") {
    return {
      role: "assistant",
      content: [
        ...message.parts
          .filter(p => p.type === "text")
          .map(p => ({ type: "text", text: p.text })),
        ...message.parts
          .filter(p => p.type === "tool")
          .map(p => ({
            type: "tool-call",
            toolCallId: p.callID,
            toolName: p.tool,
            args: p.state.input
          }))
      ]
    }
  }
}
```

---

## 5. Agent System

### 5.1 Agent Configuration

Agents are defined with:

```typescript
Agent.Info = {
  name: string                   // Unique identifier
  description?: string           // For subagent invocation
  mode: "subagent" | "primary" | "all"
  native: boolean               // Built-in agent
  hidden?: boolean              // Hide from UI
  default?: boolean             // Default agent

  // LLM parameters
  temperature?: number
  topP?: number
  model?: {
    modelID: string
    providerID: string
  }

  // Behavior
  prompt?: string               // Custom system prompt
  tools: Record<string, boolean> // Tool availability
  options: Record<string, any>  // Provider-specific options
  maxSteps?: number             // Max iterations

  // Permissions
  permission: {
    edit: "allow" | "deny" | "ask"
    bash: Record<glob, Permission>
    skill: Record<skillName, Permission>
    webfetch?: Permission
    doom_loop?: Permission      // Repeated tool calls
    external_directory?: Permission
  }
}
```

### 5.2 Built-in Agents

**build** - Default development agent
```typescript
{
  name: "build",
  mode: "primary",
  permission: {
    edit: "allow",
    bash: { "*": "allow" },
    skill: { "*": "allow" },
    webfetch: "allow",
    doom_loop: "ask",
    external_directory: "ask"
  },
  tools: { ...allTools }
}
```

**plan** - Read-only exploration agent
```typescript
{
  name: "plan",
  mode: "primary",
  permission: {
    edit: "deny",
    bash: {
      "cut*": "allow",
      "grep*": "allow",
      "ls*": "allow",
      "git diff*": "allow",
      // ... safe read-only commands
      "*": "ask"  // Ask for anything else
    },
    webfetch: "allow"
  },
  tools: { ...allTools }
}
```

**general** - Multi-step subagent
```typescript
{
  name: "general",
  description: "General-purpose agent for complex questions and multi-step tasks",
  mode: "subagent",
  hidden: true,
  tools: {
    todoread: false,    // No todo access
    todowrite: false,
    ...otherTools
  }
}
```

**explore** - Fast codebase exploration
```typescript
{
  name: "explore",
  description: "Fast agent for finding files and searching code",
  mode: "subagent",
  prompt: PROMPT_EXPLORE,  // Specialized instructions
  tools: {
    todoread: false,
    todowrite: false,
    edit: false,
    write: false,
    ...readOnlyTools
  }
}
```

**Hidden agents** (internal use):
- `compaction` - Context compression
- `title` - Generate session titles
- `summary` - Summarize changes

### 5.3 Permission Merging

Permissions cascade: user config → agent defaults

```typescript
function mergeAgentPermissions(base, override) {
  return {
    edit: override.edit ?? base.edit,
    bash: {
      ...base.bash,
      ...override.bash
    },
    skill: {
      ...base.skill,
      ...override.skill
    },
    // ... other permissions
  }
}
```

Bash permissions use glob matching:
```typescript
"git diff*": "allow"      // Allow git diff, git difftool, etc.
"find * -delete*": "ask"  // Ask before find with -delete
"*": "deny"               // Deny everything else
```

---

## 6. Tool System

### 6.1 Tool Definition Pattern

```typescript
Tool.define<Parameters, Metadata>(
  toolID: string,
  init: async (ctx?: InitContext) => {
    description: string           // Natural language description for LLM
    parameters: z.ZodType         // Zod schema for validation
    execute: async (
      args: z.infer<Parameters>,
      ctx: Tool.Context
    ) => {
      title: string               // Short description of action taken
      metadata: Metadata          // Structured data
      output: string              // Text result for LLM
      attachments?: FilePart[]    // Optional files
    }
    formatValidationError?: (error: z.ZodError) => string
  }
)
```

### 6.2 Tool Context

Tools receive execution context:

```typescript
Tool.Context = {
  sessionID: string
  messageID: string
  agent: string                  // Current agent name
  callID?: string                // Tool call ID
  abort: AbortSignal             // Cancellation
  extra?: Record<string, any>    // Tool-specific data
  metadata: (input: {
    title?: string
    metadata?: M
  }) => void                     // Update metadata during execution
}
```

### 6.3 Tool Registry

Tools are registered and resolved dynamically:

```typescript
class ToolRegistry {
  private tools: Map<string, Tool.Info> = new Map()

  async init(agent: Agent.Info) {
    for (const [toolID, enabled] of Object.entries(agent.tools)) {
      if (!enabled) continue

      const tool = await this.load(toolID)
      const initialized = await tool.init({ agent })
      this.tools.set(toolID, initialized)
    }
  }

  async execute(toolName: string, args: any, ctx: Tool.Context) {
    const tool = this.tools.get(toolName)
    if (!tool) throw new Error(`Tool not found: ${toolName}`)

    // Validate args
    tool.parameters.parse(args)

    // Execute
    return await tool.execute(args, ctx)
  }
}
```

### 6.4 Core Tools Implementation

**BashTool** - Shell command execution

```typescript
BashTool = Tool.define("bash", async () => ({
  description: "Execute bash commands...",
  parameters: z.object({
    command: z.string(),
    timeout: z.number().optional(),
    workdir: z.string().optional(),
    description: z.string()
  }),
  async execute(params, ctx) {
    // 1. Parse command with tree-sitter (bash grammar)
    const tree = await parser.parse(params.command)

    // 2. Check permissions
    const agent = await Agent.get(ctx.agent)
    await checkBashPermission(agent, params.command, ctx)

    // 3. Check external directory access
    const cwd = params.workdir || Instance.directory
    if (!Filesystem.contains(Instance.directory, cwd)) {
      await Permission.ask({ type: "external_directory", ... })
    }

    // 4. Execute with Shell.acceptable() (bash/sh/zsh)
    const proc = spawn(shell, ["-c", params.command], {
      cwd,
      timeout: params.timeout ?? 120000,
      signal: ctx.abort
    })

    // 5. Capture output (limit to MAX_OUTPUT_LENGTH)
    let stdout = ""
    let stderr = ""
    proc.stdout.on("data", d => stdout += d)
    proc.stderr.on("data", d => stderr += d)

    // 6. Wait for completion
    const exitCode = await proc

    return {
      title: params.description,
      metadata: { exitCode, cwd },
      output: `${stdout}\n${stderr}`.slice(0, MAX_OUTPUT_LENGTH)
    }
  }
}))
```

**EditTool** - File editing

```typescript
EditTool = Tool.define("edit", {
  description: "Perform exact string replacements in files...",
  parameters: z.object({
    filePath: z.string(),
    oldString: z.string(),
    newString: z.string(),
    replaceAll: z.boolean().optional()
  }),
  async execute(params, ctx) {
    // 1. Resolve absolute path
    const filePath = path.isAbsolute(params.filePath)
      ? params.filePath
      : path.join(Instance.directory, params.filePath)

    // 2. Check external directory
    if (!Filesystem.contains(Instance.directory, filePath)) {
      await Permission.ask({ type: "external_directory", ... })
    }

    // 3. Lock file (prevent concurrent edits)
    await FileTime.withLock(filePath, async () => {
      // 4. Read current content
      const contentOld = await Bun.file(filePath).text()

      // 5. Perform replacement
      let contentNew
      if (params.replaceAll) {
        contentNew = contentOld.replaceAll(params.oldString, params.newString)
      } else {
        const index = contentOld.indexOf(params.oldString)
        if (index === -1) throw new Error("oldString not found")

        // Check uniqueness
        if (contentOld.indexOf(params.oldString, index + 1) !== -1) {
          throw new Error("oldString appears multiple times, use replaceAll")
        }

        contentNew = contentOld.substring(0, index) +
                     params.newString +
                     contentOld.substring(index + params.oldString.length)
      }

      // 6. Generate diff
      const diff = createTwoFilesPatch(filePath, filePath, contentOld, contentNew)

      // 7. Ask permission if needed
      if (agent.permission.edit === "ask") {
        await Permission.ask({
          type: "edit",
          title: "Edit this file: " + filePath,
          metadata: { filePath, diff }
        })
      }

      // 8. Write file
      await Bun.write(filePath, contentNew)

      // 9. Notify change
      await Bus.publish(File.Event.Edited, { file: filePath })

      // 10. Get LSP diagnostics
      const diagnostics = await LSP.diagnostics(filePath)
    })

    return {
      title: `Edited ${path.basename(filePath)}`,
      metadata: { filePath, linesChanged: ... },
      output: diff + "\n" + diagnosticsText
    }
  }
})
```

**GrepTool** - Code search

```typescript
GrepTool = Tool.define("grep", {
  description: "Search code using ripgrep...",
  parameters: z.object({
    pattern: z.string(),
    glob: z.string().optional(),
    type: z.string().optional(),
    output_mode: z.enum(["content", "files_with_matches", "count"]),
    "-i": z.boolean().optional(),  // case insensitive
    "-A": z.number().optional(),   // after context
    "-B": z.number().optional(),   // before context
    head_limit: z.number().optional(),
    offset: z.number().optional()
  }),
  async execute(params, ctx) {
    // Build ripgrep args
    const args = ["rg"]
    if (params["-i"]) args.push("-i")
    if (params.glob) args.push("--glob", params.glob)
    if (params.type) args.push("--type", params.type)
    if (params.output_mode === "files_with_matches") args.push("-l")
    if (params.output_mode === "count") args.push("-c")
    if (params["-A"]) args.push("-A", params["-A"])
    args.push(params.pattern)

    // Execute
    const result = await $`${args}`.text()

    // Apply head_limit and offset
    let lines = result.split("\n")
    if (params.offset) lines = lines.slice(params.offset)
    if (params.head_limit) lines = lines.slice(0, params.head_limit)

    return {
      title: `Searched for "${params.pattern}"`,
      metadata: { matchCount: lines.length },
      output: lines.join("\n")
    }
  }
})
```

**ReadTool** - File reading

```typescript
ReadTool = Tool.define("read", {
  description: "Read file contents...",
  parameters: z.object({
    file_path: z.string(),
    limit: z.number().optional(),
    offset: z.number().optional()
  }),
  async execute(params, ctx) {
    const content = await Bun.file(params.file_path).text()
    const lines = content.split("\n")

    let start = params.offset ?? 0
    let end = params.limit ? start + params.limit : lines.length

    const selected = lines.slice(start, end)
    const numbered = selected.map((line, i) => `${start + i + 1}\t${line}`)

    return {
      title: `Read ${path.basename(params.file_path)}`,
      metadata: { totalLines: lines.length },
      output: numbered.join("\n")
    }
  }
})
```

**TaskTool** - Spawn subagent

```typescript
TaskTool = Tool.define("task", {
  description: "Launch specialized agent...",
  parameters: z.object({
    subagent_type: z.string(),
    prompt: z.string(),
    description: z.string(),
    model: z.enum(["sonnet", "opus", "haiku"]).optional(),
    resume: z.string().optional()  // Agent ID to resume
  }),
  async execute(params, ctx) {
    // 1. Get subagent definition
    const agent = await Agent.get(params.subagent_type)
    if (agent.mode !== "subagent") {
      throw new Error("Not a subagent")
    }

    // 2. Create child session
    const childSession = await Session.create({
      parentID: ctx.sessionID,
      title: params.description
    })

    // 3. Add user message with prompt
    await Session.updateMessage({
      sessionID: childSession.id,
      role: "user",
      parts: [{
        type: "text",
        text: params.prompt
      }]
    })

    // 4. Process until completion (max 50 steps)
    let steps = 0
    while (steps < 50) {
      const result = await SessionProcessor.process(...)
      if (result.finish_reason === "stop") break
      steps++
    }

    // 5. Collect all assistant messages
    const messages = await Session.messages({ sessionID: childSession.id })
    const output = messages
      .filter(m => m.role === "assistant")
      .flatMap(m => m.parts.filter(p => p.type === "text"))
      .map(p => p.text)
      .join("\n\n")

    return {
      title: params.description,
      metadata: { sessionID: childSession.id, steps },
      output: output
    }
  }
})
```

---

## 7. Provider Integration

### 7.1 Provider Abstraction

OpenCode uses **Vercel AI SDK** for provider abstraction:

```typescript
// Provider registry
const providers = {
  anthropic: createAnthropic({ apiKey: ... }),
  openai: createOpenAI({ apiKey: ... }),
  google: createGoogleGenerativeAI({ apiKey: ... }),
  // ... 15+ providers
}

// Get language model
async function getLanguage(model: Provider.Model) {
  const provider = await getProvider(model.providerID)
  return provider(model.id, model.options)
}
```

### 7.2 Provider Transformations

Different providers have different capabilities:

```typescript
ProviderTransform = {
  // Temperature mapping (0-1 for most, 0-2 for some)
  temperature(model: Model): number {
    if (model.api.npm === "@ai-sdk/anthropic") return 1.0
    if (model.api.npm === "@ai-sdk/openai") return 1.0
    return 0.7
  },

  // Max output tokens
  maxOutputTokens(npm: string, options: any, limit: number, max: number) {
    // Some providers don't support maxTokens
    if (npm === "@ai-sdk/google") return undefined

    // Use model limit or global max
    return Math.min(limit, max, options.maxTokens ?? Infinity)
  },

  // Provider-specific options
  options(model: Model, sessionID: string, providerOpts: any) {
    const opts: any = {}

    // Anthropic prompt caching
    if (model.api.npm === "@ai-sdk/anthropic") {
      opts.cacheControl = true
    }

    // OpenAI reasoning models
    if (model.id.includes("o1") || model.id.includes("o3")) {
      opts.reasoningEffort = "medium"
    }

    return opts
  },

  // Small model optimizations (for auxiliary tasks)
  smallOptions(model: Model) {
    if (model.api.npm === "@ai-sdk/anthropic") {
      return { cacheControl: false }  // Disable caching for quick calls
    }
    return {}
  }
}
```

### 7.3 Authentication

Credentials stored in `~/.opencode/credentials`:

```typescript
// Auth.get(providerID)
{
  anthropic: {
    apiKey: "sk-ant-..."
  },
  openai: {
    apiKey: "sk-...",
    organization: "org-..."
  },
  google: {
    apiKey: "AIza..."
  }
}
```

Providers can also use environment variables:
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`
- etc.

---

## 8. Permission System

### 8.1 Permission Flow

```typescript
// Permission check
async function checkPermission(
  agent: Agent.Info,
  type: "edit" | "bash" | "skill" | ...,
  details: any,
  ctx: Tool.Context
) {
  const permission = getPermission(agent, type, details)

  if (permission === "allow") return

  if (permission === "deny") {
    throw new Permission.RejectedError(
      ctx.sessionID,
      type,
      ctx.callID,
      details,
      "Permission denied"
    )
  }

  if (permission === "ask") {
    await Permission.ask({
      type,
      sessionID: ctx.sessionID,
      messageID: ctx.messageID,
      callID: ctx.callID,
      title: "Approve this action?",
      metadata: details
    })
  }
}
```

### 8.2 Permission Dialog

When permission = "ask", a dialog is shown:

```typescript
Permission.ask({
  type: "bash",
  pattern: ["rm -rf *"],
  title: "Run this bash command?",
  metadata: {
    command: "rm -rf dist",
    cwd: "/project"
  }
})
```

The TUI shows:
```
┌─────────────────────────────────────┐
│ Approve this bash command?          │
│                                      │
│ Command: rm -rf dist                 │
│ Directory: /project                  │
│                                      │
│ [Allow Once]  [Allow All]  [Deny]   │
└─────────────────────────────────────┘
```

User choices:
- **Allow Once** - Approve this single call
- **Allow All** - Update agent config to auto-approve this pattern
- **Deny** - Reject and stop execution

### 8.3 Doom Loop Detection

Prevents infinite tool call loops:

```typescript
const DOOM_LOOP_THRESHOLD = 3

// In SessionProcessor
const lastThree = parts.slice(-3)

if (
  lastThree.length === 3 &&
  lastThree.every(p =>
    p.type === "tool" &&
    p.tool === currentTool &&
    JSON.stringify(p.state.input) === JSON.stringify(currentInput)
  )
) {
  // Same tool called 3 times with same args
  await Permission.ask({
    type: "doom_loop",
    title: "Agent is repeating itself, continue?",
    metadata: { tool: currentTool, attempts: 3 }
  })
}
```

---

## 9. LLM Streaming

### 9.1 Stream Processing Loop

```typescript
async function process(streamInput: LLM.StreamInput) {
  while (true) {
    const stream = await LLM.stream(streamInput)

    for await (const event of stream.fullStream) {
      switch (event.type) {
        case "start":
          // Streaming started
          SessionStatus.set(sessionID, { type: "busy" })
          break

        case "text-delta":
          // Incremental text
          currentTextPart.text += event.text
          await Session.updatePart(currentTextPart, { delta: event.text })
          break

        case "reasoning-start":
        case "reasoning-delta":
        case "reasoning-end":
          // Extended thinking (Claude)
          handleReasoningEvent(event)
          break

        case "tool-call":
          // LLM wants to call a tool
          const toolPart = await Session.updatePart({
            type: "tool",
            tool: event.toolName,
            callID: event.toolCallId,
            state: {
              status: "running",
              input: event.input,
              time: { start: Date.now() }
            }
          })

          // Execute tool
          try {
            const result = await ToolRegistry.execute(
              event.toolName,
              event.input,
              ctx
            )

            await Session.updatePart({
              ...toolPart,
              state: {
                status: "success",
                output: result.output,
                metadata: result.metadata,
                time: { start: toolPart.state.time.start, end: Date.now() }
              }
            })
          } catch (error) {
            await Session.updatePart({
              ...toolPart,
              state: {
                status: "error",
                error: error.message,
                time: { start: toolPart.state.time.start, end: Date.now() }
              }
            })
          }
          break

        case "finish":
          if (event.finishReason === "stop") {
            // Normal completion, no more tool calls
            return { finishReason: "stop" }
          }

          if (event.finishReason === "tool-calls") {
            // Tools executed, continue loop for next LLM turn
            break
          }

          if (event.finishReason === "length") {
            // Context limit reached
            throw new Error("Context limit exceeded")
          }
          break
      }
    }

    // Check if we should continue
    if (stream.finishReason === "stop") break
    if (attempt >= agent.maxSteps) break

    // Add tool results to context and continue
    streamInput.messages = await buildContextMessages(sessionID)
    attempt++
  }
}
```

### 9.2 Context Management

```typescript
async function buildContextMessages(sessionID: string) {
  const messages = await Session.messages({ sessionID })
  const modelMessages: ModelMessage[] = []

  for (const msg of messages) {
    if (msg.role === "user") {
      modelMessages.push({
        role: "user",
        content: msg.parts
          .filter(p => !p.ignored && p.type === "text")
          .map(p => ({ type: "text", text: p.text }))
      })
    }

    if (msg.role === "assistant") {
      const textParts = msg.parts.filter(p => p.type === "text")
      const toolParts = msg.parts.filter(p => p.type === "tool")

      // Assistant message with text and tool calls
      modelMessages.push({
        role: "assistant",
        content: [
          ...textParts.map(p => ({ type: "text", text: p.text })),
          ...toolParts
            .filter(p => p.state.status !== "pending")
            .map(p => ({
              type: "tool-call",
              toolCallId: p.callID,
              toolName: p.tool,
              args: p.state.input
            }))
        ]
      })

      // Tool results as separate messages
      const toolResults = toolParts
        .filter(p => p.state.status !== "pending")
        .map(p => ({
          role: "tool",
          content: [
            {
              type: "tool-result",
              toolCallId: p.callID,
              toolName: p.tool,
              result: p.state.status === "success"
                ? p.state.output
                : `Error: ${p.state.error}`,
              isError: p.state.status === "error"
            }
          ]
        }))

      modelMessages.push(...toolResults)
    }
  }

  return modelMessages
}
```

### 9.3 System Prompt Building

```typescript
SystemPrompt.build(model: Provider.Model, agent: Agent.Info, user: MessageV2.User) {
  const parts: string[] = []

  // 1. Header (provider-specific)
  parts.push(SystemPrompt.header(model.providerID))

  // 2. Agent prompt OR provider prompt
  if (agent.prompt) {
    parts.push(agent.prompt)
  } else {
    parts.push(SystemPrompt.provider(model))
  }

  // 3. User-provided system prompt (if any)
  if (user.system) {
    parts.push(user.system)
  }

  // 4. Plugin transformations
  await Plugin.trigger("experimental.chat.system.transform", {}, { system: parts })

  // 5. Optimize for caching (maintain 2-part structure if header unchanged)
  if (parts.length > 2 && parts[0] === header) {
    const rest = parts.slice(1)
    return [header, rest.join("\n")]
  }

  return parts
}
```

---

## 10. File System Operations

### 10.1 Snapshot System

Git-like snapshots of workspace state:

```typescript
Snapshot.create(sessionID: string) {
  // 1. Get all tracked files
  const files = await git.getTrackedFiles()

  // 2. Compute hash of each file
  const hashes = await Promise.all(
    files.map(async f => ({
      path: f,
      hash: await hashFile(f)
    }))
  )

  // 3. Create snapshot hash
  const snapshotHash = hash(JSON.stringify(hashes))

  // 4. Store snapshot
  await Storage.write(
    ["snapshot", sessionID, snapshotHash],
    { files: hashes, time: Date.now() }
  )

  return snapshotHash
}

Snapshot.diff(snapshot1: string, snapshot2: string) {
  const s1 = await Storage.read(["snapshot", sessionID, snapshot1])
  const s2 = await Storage.read(["snapshot", sessionID, snapshot2])

  const diffs: FileDiff[] = []

  for (const file of [...s1.files, ...s2.files]) {
    const hash1 = s1.files.find(f => f.path === file.path)?.hash
    const hash2 = s2.files.find(f => f.path === file.path)?.hash

    if (hash1 !== hash2) {
      const content1 = hash1 ? await readFile(file.path, snapshot1) : ""
      const content2 = hash2 ? await readFile(file.path, snapshot2) : ""

      const diff = createTwoFilesPatch(file.path, file.path, content1, content2)

      diffs.push({
        path: file.path,
        additions: countAdditions(diff),
        deletions: countDeletions(diff),
        diff
      })
    }
  }

  return diffs
}
```

### 10.2 File Locking

Prevents concurrent modifications:

```typescript
FileTime.withLock<T>(filePath: string, callback: () => Promise<T>) {
  // 1. Acquire lock
  const lockFile = filePath + ".lock"
  while (await exists(lockFile)) {
    await sleep(10)
  }
  await Bun.write(lockFile, process.pid.toString())

  try {
    // 2. Execute callback
    const result = await callback()

    // 3. Release lock
    await unlink(lockFile)

    return result
  } catch (error) {
    await unlink(lockFile)
    throw error
  }
}
```

### 10.3 File Watching

```typescript
import { watch } from "@parcel/watcher"

const watcher = await watch(Instance.directory, (err, events) => {
  for (const event of events) {
    if (event.type === "update" || event.type === "create") {
      Bus.publish(File.Event.Changed, {
        file: event.path
      })

      // Invalidate LSP cache
      LSP.invalidate(event.path)
    }

    if (event.type === "delete") {
      Bus.publish(File.Event.Deleted, {
        file: event.path
      })
    }
  }
})
```

---

## 11. Implementation Patterns

### 11.1 Zod-First Validation

All data structures use Zod schemas:

```typescript
// Define schema
const Schema = z.object({
  name: z.string(),
  age: z.number().int().positive()
}).meta({ ref: "Person" })

// Type inference
type Person = z.infer<typeof Schema>

// Runtime validation
const parsed = Schema.parse(unknownData)

// Safe parsing
const result = Schema.safeParse(unknownData)
if (result.success) {
  result.data // typed
} else {
  result.error // ZodError
}
```

### 11.2 Functional Wrappers

`fn()` utility for parameter validation:

```typescript
import { fn } from "@/util/fn"

const myFunction = fn(
  z.object({
    name: z.string(),
    count: z.number()
  }),
  async (input) => {
    // input is typed and validated
    return input.name.repeat(input.count)
  }
)

// Usage
await myFunction({ name: "hello", count: 3 })  // ✅
await myFunction({ name: "hello" })            // ❌ Validation error
```

### 11.3 Event Bus Pattern

```typescript
// Define event
const MyEvent = BusEvent.define(
  "my.event",
  z.object({
    data: z.string()
  })
)

// Subscribe
Bus.subscribe(MyEvent, async (event) => {
  console.log(event.data)
})

// Publish
await Bus.publish(MyEvent, {
  data: "hello"
})
```

### 11.4 Instance State

Scoped singletons per project:

```typescript
const state = Instance.state(async () => {
  // Initialize once per project
  const config = await loadConfig()
  return { config }
})

// Access
const { config } = await state()
```

### 11.5 Lazy Initialization

```typescript
import { lazy } from "@/util/lazy"

const parser = lazy(async () => {
  const Parser = await import("web-tree-sitter")
  await Parser.init()
  return new Parser()
})

// First call initializes
const p1 = await parser()

// Subsequent calls reuse
const p2 = await parser()  // Same instance
```

### 11.6 Error Handling

Custom named errors:

```typescript
const MyError = NamedError.create(
  "MyError",
  z.object({
    code: z.number(),
    details: z.string()
  })
)

// Throw
throw new MyError({ code: 404, details: "Not found" })

// Catch
try {
  // ...
} catch (error) {
  if (error instanceof MyError) {
    console.log(error.data.code)
    console.log(error.data.details)
  }
}

// Serialize
error.toObject()  // { name: "MyError", data: { ... } }
```

---

## Summary

OpenCode's implementation follows these key principles:

1. **Type Safety** - Zod schemas for all data structures
2. **Modularity** - Clear separation: session → agent → tool → provider
3. **Streaming** - Real-time LLM output with incremental updates
4. **Permissions** - Fine-grained control with user approval dialogs
5. **Extensibility** - Plugin system, custom agents/tools
6. **Event-Driven** - Bus pattern for loose coupling
7. **Storage** - File-based JSON for persistence
8. **Provider-Agnostic** - Unified interface via Vercel AI SDK
9. **Context Management** - Efficient message history building
10. **Safety** - File locking, doom loop detection, external directory checks

The codebase is well-structured with 171 TypeScript files totaling ~50,000 lines of code, demonstrating production-grade architecture suitable for building AI coding assistants.
