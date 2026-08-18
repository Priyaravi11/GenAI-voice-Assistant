╔════════════════════════════════════════════════════════════════════════════╗
║                  CUSTOMER ID FLOW - VISUAL DIAGRAMS                         ║
║                    Implementation Complete Reference                        ║
╚════════════════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════════════════
COMPLETE FLOW DIAGRAM
═══════════════════════════════════════════════════════════════════════════════

                             TURN 1: User Query
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  User: "What is my current bill?"                                       │
│                                                                          │
│              ↓                                                           │
│  ┌────────────────────────────────────────┐                            │
│  │  Orchestrator.process_text()           │                            │
│  │  - Validate input                      │                            │
│  │  - Get/Create session                  │                            │
│  │  - Check: waiting_for_customer_id? NO  │                            │
│  │  - Store customer message              │                            │
│  └────────────────────────────────────────┘                            │
│              ↓                                                           │
│  ┌────────────────────────────────────────┐                            │
│  │  SupervisorAgent.handle()              │                            │
│  │  Result: {agent: "billing", ...}       │                            │
│  └────────────────────────────────────────┘                            │
│              ↓                                                           │
│  ┌────────────────────────────────────────┐                            │
│  │  BillingAgent.handle()                 │                            │
│  │  - Detect tool: get_current_bill       │                            │
│  │  - Check customer_id: NOT FOUND        │                            │
│  │  - Return:                             │                            │
│  │    {requires_customer_id: true,        │                            │
│  │     response: "Please provide..."}     │                            │
│  └────────────────────────────────────────┘                            │
│              ↓                                                           │
│  ┌────────────────────────────────────────┐                            │
│  │  Orchestrator: Detect Signal           │                            │
│  │  - requires_customer_id = TRUE         │                            │
│  │  - Store pending state:                │                            │
│  │    * waiting_for_customer_id=True      │                            │
│  │    * pending_agent="billing"           │                            │
│  │    * pending_query="What is..."        │                            │
│  │  - Store assistant message             │                            │
│  └────────────────────────────────────────┘                            │
│              ↓                                                           │
│  ┌────────────────────────────────────────┐                            │
│  │  WebSocket: Send Response              │                            │
│  │  {response: "Please provide...",       │                            │
│  │   requires_customer_id: true}          │                            │
│  └────────────────────────────────────────┘                            │
│              ↓                                                           │
│  Client: Recognizes waiting state                                       │
│  Display prompt: "Please provide customer ID"                           │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

                        TURN 2: Customer Provides ID
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  User: "C251"  (SAME SESSION_ID)                                        │
│                                                                          │
│              ↓                                                           │
│  ┌────────────────────────────────────────┐                            │
│  │  Orchestrator.process_text()           │                            │
│  │  - Validate input                      │                            │
│  │  - Get/Create session (SAME)           │                            │
│  │  - Check: waiting_for_customer_id?     │                            │
│  │    YES ✓✓✓                             │                            │
│  │  - Call _handle_customer_id_input()    │                            │
│  └────────────────────────────────────────┘                            │
│              ↓                                                           │
│  ┌────────────────────────────────────────┐                            │
│  │  _handle_customer_id_input()           │                            │
│  │  - Validate: "C251" → Valid ✓         │                            │
│  │  - Store: customer_id = "C251"         │                            │
│  │  - Get pending request                 │                            │
│  │  - Retrieve pending agent: "billing"   │                            │
│  │  - Retrieve pending query              │                            │
│  │  - Build context with customer_id      │                            │
│  └────────────────────────────────────────┘                            │
│              ↓                                                           │
│  ┌────────────────────────────────────────┐                            │
│  │  BillingAgent.handle() [RESUMED]      │                            │
│  │  - Detect tool: get_current_bill       │                            │
│  │  - Check customer_id: FOUND ✓          │                            │
│  │  - Execute: get_current_bill("C251")   │                            │
│  │  - Tool returns: {success: true,       │                            │
│  │     bill_amount: 85.50, ...}           │                            │
│  │  - Generate response via Gemini        │                            │
│  │  - Return: {requires_customer_id: false│                            │
│  │             response: "Your bill..."}  │                            │
│  └────────────────────────────────────────┘                            │
│              ↓                                                           │
│  ┌────────────────────────────────────────┐                            │
│  │  Orchestrator: Continue Processing     │                            │
│  │  - Detect requires_customer_id=false   │                            │
│  │  - Check escalation                    │                            │
│  │  - Clear pending state                 │                            │
│  │  - Build final response                │                            │
│  └────────────────────────────────────────┘                            │
│              ↓                                                           │
│  ┌────────────────────────────────────────┐                            │
│  │  WebSocket: Send Response              │                            │
│  │  {response: "Your bill is $85.50...",  │                            │
│  │   requires_customer_id: false}         │                            │
│  └────────────────────────────────────────┘                            │
│              ↓                                                           │
│  Client: Displays answer                                               │
│  "Your current bill is $85.50, due September 15, 2026"                │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
ORCHESTRATOR ROUTING LOGIC
═══════════════════════════════════════════════════════════════════════════════

                    Customer Query Received
                            ↓
         ┌──────────────────────────────────────┐
         │  Process_text() Entry Point         │
         │  1. Validate input ✓                │
         │  2. Get/Create session ✓            │
         └──────────────────────────────────────┘
                            ↓
         ┌──────────────────────────────────────────────┐
         │  CRITICAL CHECK:                            │
         │  waiting_for_customer_id?                   │
         └──────────────────────────────────────────────┘
              ↙                               ↘
           YES                               NO
            ↓                                 ↓
    ┌──────────────────┐         ┌──────────────────────┐
    │ _handle_customer │         │  Supervisor Route    │
    │_id_input()       │         │  Classification      │
    │                  │         │                      │
    │ ✓ Validate ID    │         │ → agent selected     │
    │ ✓ Store ID       │         │   (billing, plans,   │
    │ ✓ Resume pending │         │    payment, etc.)    │
    │ ✓ Execute tool   │         └────────┬─────────────┘
    │ ✓ Return answer  │                  ↓
    └────────┬─────────┘         ┌──────────────────────┐
             │                   │ Specialized Agent    │
             │                   │ Execution            │
             │                   │                      │
             │                   │ Check tool needed?   │
             │                   │   ↓                  │
             │                   │ Check customer_id?   │
             │                   │                      │
             │                   │ ✗ Missing → returns: │
             │                   │   requires_customer_ │
             │                   │   id=True            │
             │                   │                      │
             │                   │ ✓ Available → exec   │
             │                   │   tool, return answer│
             │                   └────────┬─────────────┘
             │                           ↓
             │                   ┌──────────────────────┐
             │                   │ Check requires_      │
             │                   │ customer_id Signal   │
             │                   │                      │
             │                   │ YES → Store pending  │
             │                   │       Ask for ID     │
             │                   │                      │
             │                   │ NO → Generate resp.  │
             │                   │      Return answer   │
             │                   └────────┬─────────────┘
             └───────────────┬────────────┘
                             ↓
                    ┌──────────────────────┐
                    │ Return to Client     │
                    │ (WebSocket)          │
                    └──────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
SESSION STATE TRANSITIONS
═══════════════════════════════════════════════════════════════════════════════

Session States:

        [INITIAL]
          ↓
    waiting_for_customer_id=False
    customer_id=None
    pending_agent=None
          ↓
    [NORMAL STATE]
    (Can handle queries that don't need customer_id)
    (Can handle queries that have customer_id in context)
          ↓
    Query needs customer_id, but missing
          ↓
    [AWAITING CUSTOMER ID]
    waiting_for_customer_id=True
    pending_agent="billing"
    pending_query="What is my bill?"
    customer_id=None
          ↓
    Customer provides: "C251"
          ↓
    [VALIDATING]
    validate_customer_id("C251") → Valid ✓
          ↓
    [RESUMING REQUEST]
    customer_id="C251"
    pending_agent→handle() with customer_id
          ↓
    [CLEARING STATE]
    waiting_for_customer_id=False
    pending_agent=None
    pending_query=None
          ↓
    [NORMAL STATE + CUSTOMER_ID]
    waiting_for_customer_id=False
    customer_id="C251" (stored!)
    (Next queries use stored customer_id)

═══════════════════════════════════════════════════════════════════════════════
AGENT RESULT CONTRACT
═══════════════════════════════════════════════════════════════════════════════

All Agents Return Same Structure:

    ┌─────────────────────────────────────────┐
    │  Agent Result Contract                  │
    ├─────────────────────────────────────────┤
    │ {                                       │
    │   "agent": "string",           ← Type   │
    │   "response": "string",        ← Answer │
    │   "success": bool,             ← Status │
    │   "confidence": float,         ← Trust  │
    │   "tool_used": str|None,       ← Tool   │
    │   "tool_result": dict|None,    ← Data   │
    │   "rag_context": dict|None,    ← Ref    │
    │   "requires_customer_id": bool ← SIGNAL │
    │ }                                       │
    └─────────────────────────────────────────┘

Example 1: Missing Customer ID
┌─────────────────────────────────────────────────────────────────┐
│ {                                                               │
│   "agent": "billing",                                           │
│   "response": "Please provide your customer ID.",              │
│   "success": true,                                              │
│   "confidence": 1.0,                                            │
│   "tool_used": "get_current_bill",                             │
│   "tool_result": null,                                          │
│   "rag_context": null,                                          │
│   "requires_customer_id": true  ← CRITICAL SIGNAL              │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘

Example 2: With Customer ID (Success)
┌─────────────────────────────────────────────────────────────────┐
│ {                                                               │
│   "agent": "billing",                                           │
│   "response": "Your bill is $85.50, due Sept 15.",            │
│   "success": true,                                              │
│   "confidence": 0.95,                                           │
│   "tool_used": "get_current_bill",                             │
│   "tool_result": {                                              │
│     "success": true,                                            │
│     "bill_amount": 85.50,                                       │
│     "due_date": "2026-09-15"                                   │
│   },                                                            │
│   "rag_context": null,                                          │
│   "requires_customer_id": false  ← NO LONGER NEEDED            │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘

Example 3: General Knowledge (No Tool)
┌─────────────────────────────────────────────────────────────────┐
│ {                                                               │
│   "agent": "billing",                                           │
│   "response": "A late fee is...",                              │
│   "success": true,                                              │
│   "confidence": 0.90,                                           │
│   "tool_used": null,  ← NO TOOL NEEDED                         │
│   "tool_result": null,                                          │
│   "rag_context": {...},  ← RAG USED INSTEAD                    │
│   "requires_customer_id": false                                 │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
CUSTOMER ID VALIDATION FLOW
═══════════════════════════════════════════════════════════════════════════════

Input: "C251"
  ↓
validate_customer_id("C251", allow_none=False)
  ↓
┌─────────────────────────────────────────┐
│ 1. Check None → NO, continue            │
│ 2. Check Type → str ✓                   │
│ 3. Strip whitespace → "C251"            │
│ 4. Check empty → NO, continue           │
│ 5. Check format:                        │
│    - "C" → alphanumeric ✓               │
│    - "2" → alphanumeric ✓               │
│    - "5" → alphanumeric ✓               │
│    - "1" → alphanumeric ✓               │
│ 6. All valid → return (True, "", "C251")│
└─────────────────────────────────────────┘
  ↓
(is_valid=True, error_msg="", normalized_id="C251")
  ↓
✓ ACCEPT - Can proceed to store & use

───────────────────────────────────────────

Input: "" (empty string)
  ↓
validate_customer_id("", allow_none=False)
  ↓
┌─────────────────────────────────────────┐
│ 1. Check None → NO                      │
│ 2. Check Type → str ✓                   │
│ 3. Strip → ""                           │
│ 4. Check empty → YES!                   │
│ 5. allow_none=False → return error      │
└─────────────────────────────────────────┘
  ↓
(is_valid=False, error_msg="Customer ID cannot be empty.", normalized_id=None)
  ↓
✗ REJECT - Prompt user again

───────────────────────────────────────────

Input: "C@251" (invalid character)
  ↓
validate_customer_id("C@251", allow_none=False)
  ↓
┌─────────────────────────────────────────┐
│ 1-4. Passed                             │
│ 5. Check format:                        │
│    - "C" → alphanumeric ✓               │
│    - "@" → NOT alphanumeric ✗           │
│ 6. Invalid format → return error        │
└─────────────────────────────────────────┘
  ↓
(is_valid=False, error_msg="Customer ID contains invalid characters...", None)
  ↓
✗ REJECT - Prompt user again

═══════════════════════════════════════════════════════════════════════════════
WEBSOCKET MESSAGE FLOW
═══════════════════════════════════════════════════════════════════════════════

CLIENT (Frontend) → WebSocket → SERVER (Backend)

TURN 1 - REQUEST:
┌───────────────────────────────────────────┐
│ {                                         │
│   "type": "user_message",                │
│   "session_id": "session-123",           │
│   "content": "What's my bill?",          │
│   "language": "en"                       │
│ }                                         │
└───────────────────────────────────────────┘
            ↓
    (Backend Processing)
    Orchestrator.process_text()
    → BillingAgent
    → requires_customer_id=True signal
            ↓
TURN 1 - RESPONSE:
┌───────────────────────────────────────────┐
│ {                                         │
│   "type": "assistant_response",          │
│   "content": "Please provide...",        │
│   "requires_customer_id": true, ← NEW    │
│   "intent": "billing",                   │
│   "confidence": 1.0                      │
│ }                                         │
└───────────────────────────────────────────┘
            ↓
    Client receives, recognizes waiting state
    Displays prompt to user

TURN 2 - REQUEST (SAME SESSION):
┌───────────────────────────────────────────┐
│ {                                         │
│   "type": "user_message",                │
│   "session_id": "session-123",  ← SAME! │
│   "content": "C251",          ← ID INPUT │
│   "language": "en"                       │
│ }                                         │
└───────────────────────────────────────────┘
            ↓
    (Backend Processing)
    Orchestrator.process_text()
    → Detects waiting_for_customer_id=True
    → _handle_customer_id_input()
    → Validates "C251"
    → Resumes BillingAgent
    → Executes tool
    → Generates response
            ↓
TURN 2 - RESPONSE:
┌───────────────────────────────────────────┐
│ {                                         │
│   "type": "assistant_response",          │
│   "content": "Your bill is $85.50...",   │
│   "requires_customer_id": false, ← DONE │
│   "intent": "billing",                   │
│   "confidence": 0.95                     │
│ }                                         │
└───────────────────────────────────────────┘
            ↓
    Client receives answer, displays it

═══════════════════════════════════════════════════════════════════════════════
IMPLEMENTATION COMPLETE ✓
═══════════════════════════════════════════════════════════════════════════════
