# Crypto Market State Machine
## 加密市场状态机（牛熊状态机）

将复杂的市场分析，压缩成一个**数据驱动的四象限状态机**：  
你每天只需要输入两类数据（趋势结构 + 资金姿态），系统就能输出当前 BTC 市场处于哪一个状态，并用校验层给出风险温度与 ETF 加速提示。

> ⚠️ 免责声明：本项目仅用于研究与教育，不构成任何投资建议。

---

## 愿景

用**数据驱动的方法**替代情绪化的市场判断，帮助投资者清晰了解：
- 当前处于牛/熊的哪个阶段？
- 资金是在进攻还是防守？
- 风险温度是否过高？
- ETF 是否在放大趋势？

---

## 核心概念：Input → 四象限 Output → 校验层（不改变状态）

- **Input A：趋势结构（MA50 / MA200）** → 输出 `Trend = 趋势多 / 趋势空`
- **Input B：资金姿态（Stablecoin vs TOTAL）** → 输出 `Funding = 资金进攻 / 资金防守`
- **Output：四象限状态（2×2）** → 直接定位到 4 个状态之一
- **校验层：ATH / ETF** → 不改变象限，只输出风险与可信度提示

---

## 四象限状态（核心输出）

> 用户打开四象限图的那一刻，应该能立刻看到现在 BTC 处于哪一格。

```mermaid
flowchart TB
  subgraph C1["资金进攻 (Offensive)"]
    direction TB
    A["牛市进攻<br/>RISK: HIGH"]
    C["熊市反弹<br/>RISK: MEDIUM"]
  end

  subgraph C2["资金防守 (Defensive)"]
    direction TB
    B["牛市修复<br/>RISK: MEDIUM"]
    D["熊市消化<br/>RISK: LOW"]
  end

  A --- B
  C --- D

  R1["趋势多 (Bullish)"]:::label
  R2["趋势空 (Bearish)"]:::label

  R1 -.-> A
  R2 -.-> C

  classDef label fill:transparent,stroke:transparent,color:#333;
  linkStyle 0 stroke:transparent;
  linkStyle 1 stroke:transparent;
  linkStyle 2 stroke:transparent;
  linkStyle 3 stroke:transparent;
