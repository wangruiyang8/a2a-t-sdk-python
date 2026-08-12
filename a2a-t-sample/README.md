# 时序图：流式告警订阅端到端流程

```plantuml
@startuml
autonumber
skinparam maxMessageSize 150

participant "client_example" as Client
participant "server_example" as Server
participant "agentcard_example\n(mock 注册中心)" as Registry
participant "a2a-t-sdk" as SDK
participant "DeepSeek LLM" as LLM

== 终端1: 启动注册中心 ==
Registry -> Registry : uvicorn 监听 127.0.0.1:5001

== 终端2: 启动服务端 ==
Server -> Registry : POST /rest/v1/registry-center/agent-cards\n{name, skills, streaming:true, extensions:[Notification-T]}
Registry --> Server : 201 Created
Server -> SDK : A2ATServer(env_path)
SDK --> Server : prompt_server 就绪
Server -> Server : uvicorn 监听 127.0.0.1:8000

== 终端3: 启动客户端 ==
Client -> Registry : GET /rest/v1/registry-center/agent-cards/\nSampleOrg/A2A-T Subscribe Incident Sample
Registry --> Client : 200 {agentCards:[{url:8000}]}
Client -> SDK : A2ATClient(env_path)
SDK --> Client : prompt_client 就绪
Client -> SDK : ClientFactory.create(agent_card)
SDK --> Client : a2a_client (streaming=True)

== Prompt 生成 (客户端) ==
Client -> SDK : prompt_client.generate_task_prompt(scenario_data)
SDK -> SDK : 根据 scenario 选模板\n渲染 slot 值
SDK -> LLM : 场景识别 + prompt 生成
LLM --> SDK : prompt_text (## 订阅描述...)
SDK --> Client : PromptGenerationResult(prompt_text)

== 发送请求 + Prompt 校验 (服务端) ==
Client -> Server : POST /message:stream\nHeaders: A2A-Extensions: Notification-T\nBody: SendMessageRequest(prompt_text)

Server -> SDK : prompt_server.check_task_prompt(prompt_text)
SDK -> LLM : 1. 场景识别
LLM --> SDK : {matched:true, scenario_code:"subscribe_incident"}
SDK -> LLM : 2. Slot 提取
LLM --> SDK : {slots:{订阅条件:"故障优先级为:critical..."}}
SDK -> LLM : 3. 语义校验
LLM --> SDK : {passed:true, errors:[]}
SDK --> Server : PromptComplianceResult(success=true)

== 流式推送 artifact ==
Server --> Client : StreamResponse(task: SUBMITTED)
Server --> Client : StreamResponse(status_update: WORKING)
loop 每 5 秒推送一个 Incident artifact
    Server --> Client : StreamResponse(artifact_update)\n{name:"LASER_MOD_ERR",...}
end
Server --> Client : StreamResponse(status_update: COMPLETED)
Client -> SDK : normalize_event(stream_response)
SDK --> Client : {kind:"artifact", ...}
Client -> Client : stream-completed\nevents=N artifacts=N
@enduml
```

## 流程说明

| 阶段 | 谁调 SDK | SDK 做什么 | LLM 调用次数 |
|------|---------|-----------|-------------|
| 启动 | client + server | A2ATClient / A2ATServer 初始化 | 0 |
| Prompt 生成 | 客户端 | 选模板 + 渲染 slot + 调 LLM 生成 | 1 |
| Prompt 校验 | 服务端 | 场景识别 → slot 提取 → 语义校验 | 3 |
| 流式推送 | 客户端 | normalize_event 归一化 stream 事件 | 0 |

## 关键点

- **SDK 是中间层**：client/server 不直接调 LLM，通过 SDK 的 A2ATClient/A2ATServer 间接调用
- **LLM 只在 prompt 阶段用**：推送 artifact 时不调 LLM
- **无协商**：客户端一次性提交完整输入，服务端校验通过直接推送
- **max_artifacts 控制停止**：CI 用固定值（5），端到端用 None（无限，Ctrl+C 停）
- **三层解耦**：client（发现 + 消费）→ server（注册 + 推送）→ registry（注册中心）
