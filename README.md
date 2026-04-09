# 《长征史》交互式 AI 导览与闯关学习系统

这是一个基于 `Streamlit + Python + Chroma` 的多页面交互式学习产品，主题聚焦《长征史》。项目已经按 **Streamlit Community Cloud 可部署** 的方式重构，主入口为 `app.py`。推送到 GitHub 后可以直接部署为一个固定网址，并通过后续 `git push` 自动更新线上版本。

项目保留了 FastAPI 代码用于本地开发和后续扩展，但 **云端主运行路径不依赖单独启动 uvicorn**。页面打开后就是完整产品，核心逻辑全部可由 Streamlit 直接调用。

## 项目简介

系统包含以下能力：

- 长征路线图文导览
- 基于仓库内置知识库的 RAG 问答
- 长征讲解稿生成
- 长征短视频脚本生成
- 长征轻量闯关互动
- 语音播报与轻量数字人展示
- 管理员模型开放控制与临时上传补充导入

## 页面结构

当前 Streamlit 多页面结构如下：

```text
app.py
pages/
  1_首页.py
  2_智能导览.py
  3_讲解生成.py
  4_长征闯关.py
  5_配置页.py
  6_管理员后台.py
  7_测试体验.py
```

说明：

- `app.py`：部署入口文件，Community Cloud 中请选择它作为 Main file
- `pages/1_首页.py`：产品首页
- `pages/2_智能导览.py`：问答与节点导览
- `pages/3_讲解生成.py`：讲解稿 / 脚本生成
- `pages/4_长征闯关.py`：图文答题闯关
- `pages/5_配置页.py`：普通用户配置 + 管理员开放策略
- `pages/6_管理员后台.py`：后台维护页
- `pages/7_测试体验.py`：给组员快速试用

## 管理员 / 用户权限说明

### 管理员可以

- 登录管理员后台
- 上传文件进行临时补充导入
- 查看文件列表
- 删除上传文件
- 重建或增量导入 RAG
- 查看 chunk 与 metadata
- 查看检索调试结果
- 配置 provider
- 控制哪些模型开放给普通用户
- 控制是否允许普通用户输入自己的 API Key

### 普通用户可以

- 使用管理员开放的模型
- 提问问答
- 生成讲解稿
- 生成短视频脚本
- 体验长征闯关
- 在被允许时输入自己的 API Key

### 普通用户不可以

- 访问管理员后台
- 修改 provider 配置
- 修改全局配置
- 查看管理员密钥

## 多模型 Provider 说明

项目使用统一 provider adapter 结构，位于：

- `llm/providers.py`
- `llm/client.py`
- `config/enabled_models.yaml`

支持的 provider：

- `moonshot / kimi`
- `qwen / dashscope`
- `minimax`
- `deepseek`
- `mock`

统一配置结构示例：

```yaml
providers:
  moonshot:
    provider_name: moonshot
    display_name: Kimi / Moonshot
    provider: moonshot
    base_url: https://api.moonshot.cn/v1
    api_key: ""
    api_key_secret_name: MOONSHOT_API_KEY
    model: kimi-k2.5
    enabled: true
    visible_to_users: true
    allow_user_key: false
```

读取优先级：

1. 普通用户当前 session 临时输入的 key
2. `st.secrets`
3. 环境变量
4. 本地 `config/enabled_models.yaml`
5. `mock` 回退

如果某个 provider 没有可用 key，系统仍可运行，并会自动回退到本地演示模型。

## 仓库内置内容来源

为了适配免费部署和固定网址演示，系统默认内容全部来自仓库：

- `data/events.json`
- `data/figures.json`
- `data/places.json`
- `data/routes.csv`
- `data/route_nodes.json`
- `data/faq.csv`
- `data/spirit.json`
- `data/sample_scripts.json`
- `assets/images/`
- `assets/avatar/`

这意味着：

- 即使没有人上传文件，系统也能直接展示
- 首页示例、路线节点、图片、答题内容、语音与数字人展示都有仓库内置资源支撑
- RAG 启动时会优先初始化仓库内置数据

## 为什么管理员上传功能只作为临时演示 / 补充导入

Streamlit Community Cloud 更适合：

- 使用 GitHub 仓库中的 `data/` 和 `assets/` 作为长期内容源
- 通过修改仓库并 `push` 来更新线上版本

因此本项目将管理员上传功能定位为：

- 临时补充演示资料
- 会话级或容器级补充导入
- 后续正式内容沉淀前的测试入口

如果你希望某些内容长期在线保留，推荐做法是：

1. 把资料整理进仓库的 `data/` 或 `assets/`
2. 提交到 GitHub
3. 让 Community Cloud 自动重新部署

## RAG 说明

RAG 逻辑位于 `rag.py`，已经按部署场景调整为：

- 应用启动时自动检查知识库是否存在
- 若 Chroma 为空，则自动用仓库内置 `data/` 构建默认知识库
- 问答、讲解稿、短视频脚本都先检索、再生成
- 页面会展示“本次回答依据 / 本次讲解依据”

支持的 metadata 过滤包括：

- `type`
- `place`
- `route_stage`
- `topic`
- `source_file`

保留了轻量意图识别：

- `event`
- `place`
- `figure`
- `route`
- `faq`
- `spirit`
- `generate_script`
- `timeline`

## 本地运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 可选：配置本地 Secrets

把 `.streamlit/secrets.toml.example` 复制为 `.streamlit/secrets.toml`，并填写自己的值。

至少建议配置：

```toml
ADMIN_PASSWORD = "你的管理员密码"
MOONSHOT_API_KEY = "你的 Kimi / Moonshot Key"
```

### 3. 启动 Streamlit

```bash
streamlit run app.py
```

### 4. 可选：重建知识库

```bash
python ingest.py --rebuild
```

### 5. 可选：本地调试 FastAPI

```bash
uvicorn api:app --reload
```

注意：部署到 Community Cloud 时 **不需要** 单独启动 FastAPI。

## requirements.txt / packages.txt

- `requirements.txt`：Python 依赖
- `packages.txt`：系统依赖

当前项目没有额外系统依赖，因此 `packages.txt` 仅作为占位说明文件保留。

## 如何部署到 Streamlit Community Cloud

### 1. 推到 GitHub

把当前项目推送到 GitHub 仓库，确保这些文件已经提交：

- `app.py`
- `requirements.txt`
- `packages.txt`
- `pages/`
- `data/`
- `assets/`
- `config/`

### 2. 进入 Streamlit Community Cloud

打开 [Streamlit Community Cloud](https://share.streamlit.io/) 并登录 GitHub 账号。

### 3. 连接仓库

选择你的 GitHub 仓库，并设置：

- Repository：你的仓库
- Branch：例如 `main`
- Main file path：`app.py`

如果你使用的是 **Paste GitHub URL** 模式，请填写具体的 Python 文件地址，例如：

```text
https://github.com/你的用户名/你的仓库/blob/main/app.py
```

### 3.1 Python 版本建议

Community Cloud 部署时，建议在高级设置中选择 **Python 3.12**。

原因：

- 本项目已经固定了一组适合 Community Cloud 的依赖版本
- 某些 `chromadb / protobuf / opentelemetry` 组合在更新的 Python 运行时下更容易出现兼容问题
- 选择 3.12 通常更稳，更适合比赛演示环境

### 4. 配置自定义子域名

部署时可以在 Streamlit Community Cloud 的域名设置中申请或修改固定的 `streamlit.app` 子域名。

### 5. 配置 Secrets

在 Community Cloud 的应用设置中打开 **Secrets**，填入：

```toml
ADMIN_PASSWORD = "你的管理员密码"
MOONSHOT_API_KEY = "你的 Kimi / Moonshot Key"
DASHSCOPE_API_KEY = ""
MINIMAX_API_KEY = ""
DEEPSEEK_API_KEY = ""
```

项目代码会按以下优先级读取：

1. `st.secrets`
2. 环境变量
3. 本地配置文件
4. `mock`

### 6. 完成部署

保存 Secrets 后重新部署，打开固定网址即可访问。

## 如何通过 GitHub push 更新线上版本

Streamlit Community Cloud 与 GitHub 仓库绑定后，后续更新流程很简单：

1. 在本地修改代码或数据
2. `git add .`
3. `git commit -m "your message"`
4. `git push`
5. Community Cloud 自动检测新提交并重新部署

如果你修改的是以下内容，最适合通过 GitHub push 更新：

- `data/` 中的默认内容
- `assets/` 中的图片、数字人、音频资源
- `config/` 中的默认 provider 开放策略
- 页面样式与功能逻辑

## 如何设置 app.py 为入口

在 Streamlit Community Cloud 中创建应用时，Main file path 填：

```text
app.py
```

本项目已经确保：

- 入口文件位于仓库根目录
- 页面结构符合 Streamlit 多页面规范
- 不依赖额外单独启动的后端服务

## Secrets 读取说明

代码中已经统一支持：

- `st.secrets`
- 环境变量
- 本地配置文件

主要逻辑位于 `utils.py`：

- `get_streamlit_secret(...)`
- `get_secret_or_env(...)`
- `resolve_provider_config(...)`
- `get_admin_password(...)`

管理员密码优先读取：

- `ADMIN_PASSWORD`

模型密钥优先读取：

- `MOONSHOT_API_KEY`
- `DASHSCOPE_API_KEY`
- `MINIMAX_API_KEY`
- `DEEPSEEK_API_KEY`

## 常见部署报错与排查

### 1. 页面启动后提示管理员密码未配置

原因：

- 没有在 Streamlit Secrets 或环境变量中配置 `ADMIN_PASSWORD`

处理：

- 在 Community Cloud 的 Secrets 中补上 `ADMIN_PASSWORD`

### 2. 模型调用自动回退到了 mock

原因：

- 对应 provider 没有可用 key
- Secrets 名称与 `config/enabled_models.yaml` 中配置不一致
- 外部模型服务暂时不可达

处理：

- 检查 Secrets 是否已填写
- 检查 `api_key_secret_name` 是否正确
- 查看页面中的运行时提示

### 3. 页面可以打开，但知识库内容为空

原因：

- 首次启动时 Chroma 尚未初始化成功

处理：

- 刷新页面，系统会再次检查默认知识库
- 本地可执行 `python ingest.py --rebuild`

### 3.1 启动时出现 chromadb / protobuf / opentelemetry 相关 TypeError

常见表现：

- 日志里出现 `google/protobuf/descriptor.py`
- 或 `opentelemetry.proto.common.v1.common_pb2`
- 或 `TypeError`、`_CheckCalledFromGeneratedFile`

原因：

- 云端安装到了彼此不兼容的 `chromadb`、`protobuf`、`opentelemetry` 版本组合
- 或部署时使用了过新的 Python 运行时

处理：

- 确认仓库里的 `requirements.txt` 已包含固定版本
- 在 Community Cloud 中重新部署
- 优先选择 **Python 3.12**
- 若应用已创建且 Python 版本不可改，删除应用后按 3.12 重新创建

### 4. 上传文件后重启应用就没了

原因：

- Community Cloud 的运行时文件系统不适合作为长期内容存储

处理：

- 把长期需要展示的内容整理后提交到仓库 `data/` 与 `assets/`

### 5. 新提交没有立刻更新线上页面

原因：

- Community Cloud 仍在重新部署

处理：

- 打开应用管理页查看构建日志
- 确认 push 的分支与部署分支一致

## 目录结构

```text
project/
  app.py
  api.py
  auth.py
  rag.py
  ingest.py
  generator.py
  game.py
  prompts.py
  models.py
  file_loader.py
  chunking.py
  retrieval_debug.py
  media.py
  tts.py
  sample_content.py
  node_detail.py
  streamlit_ui.py
  utils.py
  llm/
    __init__.py
    client.py
    providers.py
    mock_provider.py
  pages/
    1_首页.py
    2_智能导览.py
    3_讲解生成.py
    4_长征闯关.py
    5_配置页.py
    6_管理员后台.py
    7_测试体验.py
  config/
    enabled_models.yaml
    system_settings.yaml
    admin_users.yaml
  data/
    events.json
    figures.json
    places.json
    routes.csv
    route_nodes.json
    faq.csv
    spirit.json
    sample_scripts.json
  assets/
    images/
    avatar/
    audio/
  storage/
    chroma_db/
    uploads/
    processed/
  .streamlit/
    secrets.toml.example
  requirements.txt
  packages.txt
  README.md
```
