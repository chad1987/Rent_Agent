# Rent_Agent（高分版实现）

这是一个可直接本地启动并对接判题系统的租房 Agent，实现了比赛要求的统一接口：

- `POST /api/v1/chat`
- 默认启动端口：`8191`
- 支持多轮会话上下文
- 支持房源查询、对比、租房、退租、下架

---

## 一、题目要求分析（已落地到代码）

### 1) 协议兼容
- 按 `Interface.md`，对外只暴露 `/api/v1/chat`。
- 返回结构固定：`session_id/response/status/tool_results/timestamp/duration_ms`。
- **查询完成后** `response` 必须为合法 JSON 字符串，包含 `message` 和 `houses`。

### 2) 数据与 API 使用规则
- 房源相关接口必须带 `X-User-ID`。
- 每新会话自动调用 `/api/houses/init`，防止历史状态污染。
- 租房/退租/下架必须调用官方 API，不靠文本模拟。

### 3) 得分与性能策略
- 采用**规则理解 + 直连检索 API**，避免额外模型调用带来的 token/时间片开销。
- 单轮查询尽量压缩为 1 次核心检索（`/api/houses/by_platform`）+ 本地打分排序。
- 多轮通过 `session_id` 维护上下文，减少重复理解成本。

---

## 二、程序能力说明

### 1) 会话能力
每个 `session_id` 持久化：
- `filters`：当前筛选条件
- `last_house_ids`：上轮结果（用于“租第一套”“对比前两套”）
- `last_platform`：平台偏好（链家/安居客/58同城）

### 2) 条件解析能力
支持从中文自然语言提取：
- 区域：海淀/朝阳/通州/昌平/大兴/房山/西城/丰台/顺义/东城
- 户型：一居/两居/三居/四居
- 租赁类型：整租/合租
- 预算：上限/下限/区间
- 面积：最小值/区间
- 地铁：近地铁（800m）/地铁可达（1000m）/指定站点
- 通勤：到西二旗通勤上限
- 装修、朝向、电梯、水电类型

### 3) 检索与推荐策略
- 使用 `/api/houses/by_platform` 按条件筛选。
- 本地多因子评分（价格、地铁距离、西二旗通勤、硬条件匹配加分）。
- 返回最多 5 套高匹配房源 ID。

### 4) 业务操作能力
- `租房` => `/api/houses/{id}/rent`
- `退租` => `/api/houses/{id}/terminate`
- `下架` => `/api/houses/{id}/offline`
- `对比` => 拉取两套详情后输出结果

---

## 三、启动方式

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8191
```

> 建议设置真实工号（强烈推荐）：

```bash
export COMPETITION_USER_ID=你的比赛工号
```

如未设置，程序会退化使用 `session_id` 作为 `X-User-ID`。

---

## 四、调用示例

### 查询
```bash
curl -s -X POST http://127.0.0.1:8191/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id":"case_1001",
    "message":"帮我找海淀两居，预算9000以内，近地铁，有电梯，民水民电"
  }'
```

### 对比
```bash
curl -s -X POST http://127.0.0.1:8191/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id":"case_1001",
    "message":"对比 HF_2001 和 HF_3050"
  }'
```

### 租房
```bash
curl -s -X POST http://127.0.0.1:8191/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id":"case_1001",
    "message":"租 HF_2001，用安居客"
  }'
```

---

## 五、满分建议（实战）

1. 使用真实工号配置 `COMPETITION_USER_ID`，避免用户态冲突。  
2. 遇到“无结果”时引导放宽条件（预算/地铁/通勤）以提高任务完成率。  
3. 多轮对话中尽量保留历史条件，仅增量修改，符合复杂任务用例风格。  
4. 运行时确保 Agent 进程稳定，避免超时与连接失败。  
