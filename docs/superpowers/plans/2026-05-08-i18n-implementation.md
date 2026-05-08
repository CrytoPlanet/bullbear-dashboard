# BullBear Dashboard 中英双语实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把目前仅中文的 dashboard 改造为中英双语，header 右上角 `[中|EN]` 切换，依据浏览器语言初始化、localStorage 持久化。

**Architecture:** 前端引入 vue-i18n@9（Composition API 模式），文案集中在 `frontend/src/locales/{zh,en}.ts` 字典；后端继续返回中文枚举字符串作为内部标识符（不翻译），前端通过 `STATE_KEYS` / `TREND_KEYS` / `FUNDING_KEYS` / `THERMOMETER_KEYS` / `ETF_ACCEL_KEYS` 五张映射表把后端值映射到字典 key；script 内的长文计算函数重写为响应式 `computed`，内部直接调 `t()`。

**Tech Stack:** Vue 3 + TypeScript + Vite + vue-i18n@9（Composition API）

**前置阅读：** [设计文档 `docs/superpowers/specs/2026-05-08-i18n-design.md`](../specs/2026-05-08-i18n-design.md)

**关于测试：** 项目目前没有自动化测试基础设施，设计文档已明确不在本次范围内引入测试。每个任务的"验证"步骤是 `pnpm type-check`（类型系统会捕获缺失/错拼的字典 key —— 这是我们的主要安全网）+ `pnpm dev` 浏览器人工 smoke check。

---

## 文件结构总览

```
frontend/src/
├── locales/                  # 新增
│   ├── index.ts              # createI18n + detectInitialLocale + setLocale
│   ├── zh.ts                 # 中文文案（源语言，事实标准）
│   └── en.ts                 # 英文文案（与 zh.ts 字段镜像对齐）
├── main.ts                   # +1 行：app.use(i18n)
├── types.ts                  # 删除 DATA_LABELS、QUADRANT_MAP（迁入字典）
└── App.vue                   # 模板/script 中所有中文 → t('…')；新增 lang-toggle UI 和样式
```

## 字典 key 命名规范

- 嵌套结构按"业务域 → 字段"组织
- camelCase（除已有 snake_case 的 data type id 如 `btc_price`）
- 短文案直接是字符串，长文案/复合文案放在子对象里：`{ status, summary }` 或 `{ name, desc }`
- 完整字典见 Task 3 / Task 4

## 后端枚举值映射（务必看完再开始）

后端 `state` / `trend` / `funding` / `validation.risk_thermometer` / `validation.etf_accelerator` 是中文标识符，**不翻译**，仅在显示时映射：

| 字段 | 后端可能值 | 映射 key |
|------|------------|----------|
| state | 牛市进攻 / 牛市修复 / 熊市反弹 / 熊市消化 | bullOffensive / bullRecovery / bearBounce / bearDigest |
| trend | 趋势多 / 趋势空 | bull / bear |
| funding | 资金进攻 / 资金防守 / 无法判断 | offensive / defensive / unknown |
| risk_thermometer | 正常体温 / 低/中烧 / 高烧威胁 / 生命体征极差 | normal / midFever / highFever / critical |
| etf_accelerator | 顺风 / 逆风 / 钝化 / 未知 | tailwind / headwind / blunted / unknown |

App.vue 内的条件判断（如 `v-if="state === '牛市进攻'"`、`switch (thermometer) { case '正常体温' }`）保持原样不动 —— 它们比对的是后端标识符，不是显示文案。

---

## Task 1: 安装 vue-i18n

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/pnpm-lock.yaml`

- [ ] **Step 1: 安装依赖**

```bash
cd frontend && pnpm add vue-i18n@^9.14.0
```

- [ ] **Step 2: 验证 package.json**

预期 `frontend/package.json` 的 `dependencies` 段新增：
```json
"vue-i18n": "^9.14.0"
```

- [ ] **Step 3: 提交**

```bash
git add frontend/package.json frontend/pnpm-lock.yaml
git commit -m "chore(i18n): add vue-i18n@9 dependency"
```

---

## Task 2: 新建 i18n 核心模块（locales/index.ts）

**Files:**
- Create: `frontend/src/locales/index.ts`

- [ ] **Step 1: 创建 locales 目录与 index.ts**

```bash
mkdir -p /home/ivanjin/bullbear-dashboard/frontend/src/locales
```

写入 `frontend/src/locales/index.ts`：

```ts
import { createI18n } from 'vue-i18n';
import zh from './zh';
import en from './en';

export type AppLocale = 'zh' | 'en';
export type MessageSchema = typeof zh;

const STORAGE_KEY = 'locale';

function detectInitialLocale(): AppLocale {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'zh' || saved === 'en') return saved;
  } catch {
    // localStorage 不可用（隐私模式），降级
  }
  const navLang = (typeof navigator !== 'undefined' && navigator.language) || '';
  return navLang.toLowerCase().startsWith('zh') ? 'zh' : 'en';
}

const initialLocale = detectInitialLocale();

const i18n = createI18n<[MessageSchema], AppLocale>({
  legacy: false,
  locale: initialLocale,
  fallbackLocale: 'en',
  messages: { zh, en },
});

if (typeof document !== 'undefined') {
  document.documentElement.lang = initialLocale === 'zh' ? 'zh-CN' : 'en-US';
}

export function setLocale(loc: AppLocale): void {
  i18n.global.locale.value = loc;
  try {
    localStorage.setItem(STORAGE_KEY, loc);
  } catch {
    // 忽略 localStorage 写入失败
  }
  if (typeof document !== 'undefined') {
    document.documentElement.lang = loc === 'zh' ? 'zh-CN' : 'en-US';
  }
}

export default i18n;
```

- [ ] **Step 2: 暂不验证（依赖 zh.ts/en.ts，下个任务才有）**

**注意**：本任务结束时类型检查会失败（`./zh`、`./en` 还不存在）；这是预期的，Task 3、4 完成后会通过。

---

## Task 3: 编写完整中文字典（locales/zh.ts）

**Files:**
- Create: `frontend/src/locales/zh.ts`

这是**源语言事实标准**。字段命名将被 en.ts 严格镜像。

- [ ] **Step 1: 写入完整 zh.ts**

```ts
export default {
  app: {
    title: 'BullBear Dashboard',
    subtitle: '加密市场状态机 - 四象限状态可视化',
  },
  langToggle: {
    zh: '中',
    en: 'EN',
    aria: '切换语言',
  },
  actions: {
    refresh: '刷新数据',
    loading: '加载中...',
    refreshIcon: '🔄',
  },
  loading: {
    title: '正在加载市场数据...',
    subtitle: '请稍候，正在获取最新状态',
    rawData: '正在加载原始数据...',
  },
  errors: {
    dataLoadFailed: '无法加载数据，请稍后重试',
    stateLoadFailed: '无法加载状态数据，请稍后重试',
    stateFetchPrefix: '状态获取失败',
    unknownError: '未知错误',
  },
  status: {
    currentLabel: '当前状态：',
    separator: '｜',
  },
  data: {
    btc_price: 'BTC 价格',
    total_market_cap: '总市值',
    stablecoin_market_cap: '稳定币市值',
    ma50: 'MA50 均线',
    ma200: 'MA200 均线',
    etf_net_flow: 'ETF 净流入',
    etf_aum: 'ETF 总规模',
    sourceLabel: '来源:',
    periodLabel: '周期:',
  },
  metric: {
    risk: {
      label: '风险等级',
      tooltipTitle: '风险等级说明：',
      high: 'HIGH：牛市进攻状态，市场可能过热，需注意回调风险',
      medium: 'MEDIUM：牛市修复或熊市反弹，中等风险',
      low: 'LOW：熊市消化状态，已充分回调，风险相对较低',
    },
    confidence: {
      label: '置信度',
      tooltipTitle: '置信度说明：',
      item1: '由"趋势结构 + 资金姿态"一致性计算',
      item2: '越接近 100% 表示信号更一致、结构更清晰',
      item3: '低置信度通常来自斜率走平或信号分歧',
    },
  },
  quadrant: {
    bullOffensive: { name: '牛市进攻', trendLabel: '趋势偏多', flowLabel: '资金进攻' },
    bullRecovery:  { name: '牛市修复', trendLabel: '趋势偏多', flowLabel: '资金防守' },
    bearBounce:    { name: '熊市反弹', trendLabel: '趋势偏空', flowLabel: '资金进攻' },
    bearDigest:    { name: '熊市消化', trendLabel: '趋势偏空', flowLabel: '资金防守' },
  },
  trend: { bull: '趋势多', bear: '趋势空' },
  funding: { offensive: '资金进攻', defensive: '资金防守', unknown: '无法判断' },
  axis: {
    trendUp: '趋势多',
    trendDown: '趋势空',
    fundingLeft: '资金防守',
    fundingRight: '资金进攻',
  },
  badge: {
    coreOutput: '核心输出',
    hardRule: '硬规则',
    validationLayer: '检验层',
    coreLogic: '核心切换逻辑',
  },
  section: {
    quadrant: {
      title: '📈 四象限状态矩阵',
      description: '市场状态由"趋势结构"和"资金姿态"共同决定',
    },
    trendStructure: {
      badge: '硬规则1',
      title: '📈 趋势结构 (Trend Structure)',
      description: '使用 MA50（中期节奏线）和 MA200（长期生命线）的排列关系',
      conclusionTitle: '趋势结构结论',
      systemJudgment: '系统判断：',
    },
    fundingPosture: {
      badge: '硬规则2',
      title: '💰 资金姿态 (Capital Posture)',
      description: '核心在于观察资金是在"撤回现金避险"还是"进入风险资产进攻"',
      changeTitle: '资金姿态变化程度',
      changeIntro: '使用线性回归在对数坐标上计算最近10天的斜率，表示每日百分比变化率。正值表示上升（变多），负值表示下降（变少）。数据来源：CoinGecko历史API。',
      dataWarning: '⚠️ 当前显示为0.000%可能是因为外部数据源（CoinGecko）返回的历史数据不足，或API调用失败。系统会尝试从缓存数据计算，如仍为0则说明数据不足。',
      patternsTitle: '资金组合模式',
      currentCombination: '当前组合模式：',
    },
    riskThermometer: {
      badge: '检验层A',
      title: '🌡️ 风险温度计 (Validation Layer 1)',
      description: '使用 ATH（历史最高价）回撤率来衡量风险',
      formula: '公式: (ATH - 当前价格) / ATH × 100%',
      athLabel: 'ATH:',
    },
    etfAccelerator: {
      badge: '检验层B',
      title: '🚀 ETF 加速器 (Validation Layer 2)',
      description: '观察现货 ETF 的净流入/流出 (Net Flow) 和管理规模 (AUM)',
      ruleNote: '判定口径：',
      ruleNoteBody: '顺风 = 净流入为主且 AUM 趋势向上；逆风 = 净流出为主且 AUM 趋势向下；钝化 = 两者不一致或数据不足',
    },
    transitions: {
      badge: '核心切换逻辑',
      title: '🔄 状态切换信号',
      currentStatePrefix: '当前状态：',
      currentStateSuffix: '。以下显示切换到其他状态需要的信号：',
      requirements: '需要条件：',
      validationLabel: '校验层（仅供参考）：',
      arrow: '→',
    },
    rawData: {
      title: '📊 原始数据',
    },
  },
  trendCard: {
    priceMARelation: '价格与均线关系',
    ma50Trend: 'MA50 趋势',
    ma200Trend: 'MA200 趋势',
    quality: '趋势质量判定',
    diff50Label: 'MA50 差值',
    diff200Label: 'MA200 差值',
    slopeLabel: '斜率',
    perDay: '/天',
    unavailable: '数据暂未可用',
    ma50Description: '中期节奏线的趋势方向，反映市场中期推动力',
    ma50FlatUp: 'MA50 走平或向上',
    ma50Down: 'MA50 趋势向下',
    ma200FlatUp: 'MA200 走平或向上',
    ma200Down: 'MA200 趋势向下',
    ma200BullCondition: '多头排列条件之二：MA200 走平或向上（斜率 >= 0）',
    ma200BearCondition: '空头排列条件之二：MA200 趋势向下（斜率 < 0）',
  },
  maPrice: {
    aboveBoth:  { status: '价格在 MA50 和 MA200 上方', summary: '多头排列条件之一：价格在 MA200 上方（且高于 MA50）' },
    belowBoth:  { status: '价格在 MA50 和 MA200 下方', summary: '空头排列条件之一：价格在 MA200 下方（且低于 MA50）' },
    aboveMa50:  { status: '价格在 MA50 上方、MA200 下方', summary: '价格处于 MA50 与 MA200 之间，趋势未成列' },
    belowMa50:  { status: '价格在 MA50 下方、MA200 上方', summary: '价格低于 MA50 但高于 MA200，信号分歧' },
    unknown:    { status: '价格与均线重合或数据不足', summary: '价格与均线重合或数据不足，趋势无法判定' },
  },
  trendStructure: {
    bullStack:    { name: '多头排列（趋势多）', desc: '价格在 MA200 上方，MA200 走平或向上，且 MA50 在 MA200 上方' },
    trendBull:    { name: '趋势多', desc: '价格在 MA200 上方，且 MA200 走平或向上' },
    bearStack:    { name: '空头排列（趋势空）', desc: '价格在 MA200 下方，MA200 趋势向下，且 MA50 在 MA200 下方' },
    trendBear:    { name: '趋势空', desc: '价格在 MA200 下方，且 MA200 趋势向下' },
    bullDegrade:  { name: '趋势多（降级）', desc: '价格在 MA200 上方，但 MA200 走弱（斜率 < 0）' },
    bearDegrade:  { name: '趋势空（降级）', desc: '价格在 MA200 下方，但 MA200 走平或向上（斜率 >= 0）' },
    unknown:      { name: '无法确定', desc: '价格与 MA200 重合或数据不足，趋势无法判定' },
  },
  trendQuality: {
    good: 'MA50 在 MA200 上方，说明中期趋势跟得上，市场有推动力',
    bad:  '价格 < MA50 < MA200，典型的空头排列，反弹仅视为压力位修复而非反转',
  },
  fundingChange: {
    stablecoinTrendLabel: '稳定币市值趋势',
    totalTrendLabel: '加密总市值趋势',
    stablecoinRatioLabel: '稳定币占比',
    upMore: '上升（变多）',
    downLess: '下降（变少）',
    stablecoinUpDesc: '稳定币市值上升，资金避险',
    stablecoinDownDesc: '稳定币市值下降，资金流入风险资产',
    totalUpDesc: '总市值上升，风险资产扩张',
    totalDownDesc: '总市值下降，风险资产收缩',
    thresholdGap: '距离阈值:',
    changeLabel: '变化:',
    explanationStrong: '说明：',
    explanationBody: '稳定币市值 / 加密总市值。占比增加表示资金避险，占比减少表示资金流入风险资产。',
  },
  fundingPattern: {
    incrementalOffensive: { name: '增量进攻', desc: '场内现金变多，且资产也在涨，说明场外资金进场。偏进攻/偏牛' },
    strongOffensive:      { name: '强力进攻', descPre: '稳定币池子缩小换成币，风险资产大幅扩张。', descStrong: '最强进攻状态' },
    deriskDefensive:      { name: '去风险防守', desc: '币缩水，现金变大，投资者卖币换钱躲避风险。典型去风险/防守' },
    deepDefensive:        { name: '深度防守/撤退', desc: '资产和现金同步缩水，说明资金彻底离开加密体系。更强的防守/彻底熊' },
    insufficient:         { name: '历史不足/走平' },
  },
  thermometer: {
    normal: '正常体温',
    midFever: '低/中烧',
    highFever: '高烧威胁',
    critical: '生命体征极差',
    rangeUnder20: '< 20%: 正常体温（36-37度，可大胆进攻）',
    range20To35: '20% ~ 35%: 低/中烧（37-39度，市场难受，需要修复）',
    rangeOver35: '> 35%: 高烧威胁（熊市主导概率大增）',
    rangeOver60: '> 60%: 生命体征极差（深出清阶段，处于快死透的区间）',
  },
  etfAccelerator: {
    tailwind: '顺风',
    headwind: '逆风',
    blunted: '钝化',
    unknown: '未知',
    netFlowLabel: '净资金流',
    aumLabel: '资产管理规模 (AUM)',
    flow14dLabel: '近14日净流入合计',
    flowSpeedLabel: '流入/流出速度',
    avgRecent: '近7日均值',
    avgPrev: '前7日均值',
    flowTrendLabel: '流入趋势',
    aumTrendLabel: 'AUM 趋势',
    posRatioLabel: '正流入占比',
    netFlowDesc: '现货 ETF 的净资金流入（正数）或流出（负数）',
    aumDesc: 'ETF 的总资产管理规模',
    flow14dDesc: '用于判断近期资金方向与 AUM 趋势',
    flowSpeedDesc: '近7日与前7日的均值对比，用于判断流入/流出速度是否减缓',
    posRatioDesc: '近周期净流入为正的天数占比',
    unavailable: '数据暂未可用',
    info: {
      tailwindStrong: '顺风（加速）：',
      tailwindBody: '持续净流入，加速上涨趋势。ETF 资金持续净流入，为市场提供增量资金支持，推动价格上涨。',
      headwindStrong: '逆风（抑制）：',
      headwindBody: '持续净流出，放大下跌压力。ETF 资金持续净流出，增加市场卖压，可能加速价格下跌。',
      bluntedStrong: '钝化：',
      bluntedBody: '流出速度减缓，通常意味着卖压衰竭，可能转入震荡消化。卖压逐渐减弱，市场可能进入横盘整理阶段。',
      unknownStrong: '未知：',
      unknownBody: '无法获取 ETF 数据，请检查网络连接或数据源。系统无法判断 ETF 资金流向对市场的影响。',
    },
  },
  trendBadge: {
    up: '向上',
    down: '向下',
    flat: '走平',
    unknown: '未知',
  },
  signals: {
    trendBull: {
      name: '趋势转多',
      description: '价格在 MA200 上方，且 MA200 走平或向上',
      activeFmt: '价格({price}) > MA200({ma200})，MA200斜率({slope}%) >= 0',
      pendingFmt: '需要价格站上 MA200 且 MA200 走平或向上',
    },
    trendBear: {
      name: '趋势转空',
      description: '价格在 MA200 下方，且 MA200 趋势向下',
      activeFmt: '价格({price}) < MA200({ma200})，MA200斜率({slope}%) < 0',
      pendingFmt: '需要价格跌破 MA200 且 MA200 趋势向下',
    },
    fundingOffensive: {
      name: '资金转进攻',
      description: '稳定币市值下降或总市值上升，资金流入风险资产',
      active: '资金组合模式符合进攻状态',
      pending: '需要稳定币市值下降或总市值上升',
    },
    fundingDefensive: {
      name: '资金转防守',
      description: '稳定币市值上升或总市值下降，资金避险',
      active: '资金组合模式符合防守状态',
      pending: '需要稳定币市值上升或总市值下降',
    },
    risk: {
      name: '风险温度计',
      bullDescription: '风险温度计：正常体温或低/中烧（回撤率 < 35%）',
      bearDescription: '风险温度计：高烧威胁或生命体征极差（回撤率 >= 35%）',
      activeBullFmt: '当前回撤率：{drawdown}%（{thermometer}），符合牛市条件',
      pendingBullFmt: '需要回撤率 < 35%（当前：{drawdown}%）',
      activeBearFmt: '当前回撤率：{drawdown}%（{thermometer}），符合熊市条件',
      pendingBearFmt: '需要回撤率 >= 35%（当前：{drawdown}%）',
      naValue: 'N/A',
    },
    etf: {
      name: 'ETF 加速器',
      bullDescription: 'ETF 加速器：顺风（持续净流入，AUM 回升）',
      bullActiveFmt: 'ETF 加速器：{accelerator}，AUM：{aum}',
      bullPendingFmt: '需要 ETF 转为持续净流入且 AUM 回升（当前：{accelerator}）',
      bearBounceDescription: 'ETF 加速器：钝化或顺风（卖压衰竭或开始流入）',
      bearBounceActiveFmt: 'ETF 加速器：{accelerator}，AUM：{aum}',
      bearBouncePendingFmt: '需要 ETF 钝化（卖压衰竭）或转为顺风（当前：{accelerator}）',
      bearDigestDescription: 'ETF 加速器：逆风或钝化（持续流出或卖压衰竭）',
      bearDigestActiveFmt: 'ETF 加速器：{accelerator}，AUM：{aum}',
      bearDigestPendingFmt: '需要 ETF 逆风（持续流出）或钝化（卖压衰竭）（当前：{accelerator}）',
      unknownAccelerator: '未知',
    },
  },
};
```

- [ ] **Step 2: 提交（中间状态，类型检查仍未通过）**

```bash
git add frontend/src/locales/zh.ts
git commit -m "feat(i18n): add Chinese locale dictionary"
```

---

## Task 4: 编写英文字典（locales/en.ts）

**Files:**
- Create: `frontend/src/locales/en.ts`

英文字典必须与 zh.ts **字段结构完全一致**（leaf 名同名同类型，仅 leaf 值替换）。下面是初译版，**用户将在最终阶段审稿，但本任务先以下面的内容写入。**

- [ ] **Step 1: 写入 en.ts**

```ts
export default {
  app: {
    title: 'BullBear Dashboard',
    subtitle: 'Crypto Market State Machine — Quadrant Visualization',
  },
  langToggle: {
    zh: '中',
    en: 'EN',
    aria: 'Switch language',
  },
  actions: {
    refresh: 'Refresh',
    loading: 'Loading...',
    refreshIcon: '🔄',
  },
  loading: {
    title: 'Loading market data...',
    subtitle: 'Please wait while we fetch the latest state',
    rawData: 'Loading raw data...',
  },
  errors: {
    dataLoadFailed: 'Failed to load data, please try again later',
    stateLoadFailed: 'Failed to load state data, please try again later',
    stateFetchPrefix: 'State fetch failed',
    unknownError: 'unknown error',
  },
  status: {
    currentLabel: 'Current state: ',
    separator: ' | ',
  },
  data: {
    btc_price: 'BTC Price',
    total_market_cap: 'Total Market Cap',
    stablecoin_market_cap: 'Stablecoin Market Cap',
    ma50: 'MA50',
    ma200: 'MA200',
    etf_net_flow: 'ETF Net Flow',
    etf_aum: 'ETF AUM',
    sourceLabel: 'Source:',
    periodLabel: 'Period:',
  },
  metric: {
    risk: {
      label: 'Risk Level',
      tooltipTitle: 'Risk levels:',
      high: 'HIGH: Bull-Offensive state — market may be overheated, watch for pullback',
      medium: 'MEDIUM: Bull-Recovery or Bear-Bounce — moderate risk',
      low: 'LOW: Bear-Digest state — already pulled back, relatively low risk',
    },
    confidence: {
      label: 'Confidence',
      tooltipTitle: 'Confidence:',
      item1: 'Computed from coherence between trend structure and capital posture',
      item2: 'Closer to 100% means signals are more aligned and structure is clearer',
      item3: 'Low confidence usually comes from flat slopes or signal divergence',
    },
  },
  quadrant: {
    bullOffensive: { name: 'Bull Offensive', trendLabel: 'Bullish trend',  flowLabel: 'Offensive flow' },
    bullRecovery:  { name: 'Bull Recovery',  trendLabel: 'Bullish trend',  flowLabel: 'Defensive flow' },
    bearBounce:    { name: 'Bear Bounce',    trendLabel: 'Bearish trend',  flowLabel: 'Offensive flow' },
    bearDigest:    { name: 'Bear Digest',    trendLabel: 'Bearish trend',  flowLabel: 'Defensive flow' },
  },
  trend: { bull: 'Bullish trend', bear: 'Bearish trend' },
  funding: { offensive: 'Offensive flow', defensive: 'Defensive flow', unknown: 'Indeterminate' },
  axis: {
    trendUp: 'Bullish',
    trendDown: 'Bearish',
    fundingLeft: 'Defensive',
    fundingRight: 'Offensive',
  },
  badge: {
    coreOutput: 'Core Output',
    hardRule: 'Hard Rule',
    validationLayer: 'Validation Layer',
    coreLogic: 'Core Logic',
  },
  section: {
    quadrant: {
      title: '📈 Four-Quadrant State Matrix',
      description: 'Market state is determined by trend structure and capital posture',
    },
    trendStructure: {
      badge: 'Hard Rule 1',
      title: '📈 Trend Structure',
      description: 'Uses MA50 (mid-term tempo line) and MA200 (long-term lifeline)',
      conclusionTitle: 'Trend-Structure Conclusion',
      systemJudgment: 'System verdict: ',
    },
    fundingPosture: {
      badge: 'Hard Rule 2',
      title: '💰 Capital Posture',
      description: 'Whether capital is "retreating to cash" or "advancing into risk assets"',
      changeTitle: 'Magnitude of Capital-Posture Change',
      changeIntro: 'Linear regression on log-scale slope over the last 10 days, expressed as % per day. Positive = rising, negative = falling. Source: CoinGecko historical API.',
      dataWarning: '⚠️ A reading of 0.000% may mean the upstream source (CoinGecko) returned insufficient history or the API call failed. The system will retry from cached data; if still 0, history is insufficient.',
      patternsTitle: 'Capital-Posture Combinations',
      currentCombination: 'Current combination:',
    },
    riskThermometer: {
      badge: 'Validation A',
      title: '🌡️ Risk Thermometer (Validation Layer 1)',
      description: 'Drawdown from ATH (all-time high) as a risk gauge',
      formula: 'Formula: (ATH − price) / ATH × 100%',
      athLabel: 'ATH:',
    },
    etfAccelerator: {
      badge: 'Validation B',
      title: '🚀 ETF Accelerator (Validation Layer 2)',
      description: 'Spot-ETF Net Flow and AUM',
      ruleNote: 'Rule:',
      ruleNoteBody: 'Tailwind = sustained inflows + AUM trending up; Headwind = sustained outflows + AUM trending down; Blunted = mixed signals or insufficient data',
    },
    transitions: {
      badge: 'Core Switch Logic',
      title: '🔄 State-Transition Signals',
      currentStatePrefix: 'Current state: ',
      currentStateSuffix: '. Below: signals required to transition to other states.',
      requirements: 'Required:',
      validationLabel: 'Validation layer (reference only):',
      arrow: '→',
    },
    rawData: {
      title: '📊 Raw Data',
    },
  },
  trendCard: {
    priceMARelation: 'Price vs Moving Averages',
    ma50Trend: 'MA50 Trend',
    ma200Trend: 'MA200 Trend',
    quality: 'Trend Quality',
    diff50Label: 'MA50 diff',
    diff200Label: 'MA200 diff',
    slopeLabel: 'Slope',
    perDay: '/day',
    unavailable: 'Data not available yet',
    ma50Description: 'Direction of the mid-term tempo line — reflects mid-term momentum',
    ma50FlatUp: 'MA50 flat or rising',
    ma50Down: 'MA50 trending down',
    ma200FlatUp: 'MA200 flat or rising',
    ma200Down: 'MA200 trending down',
    ma200BullCondition: 'Bull-stack condition #2: MA200 flat or rising (slope ≥ 0)',
    ma200BearCondition: 'Bear-stack condition #2: MA200 trending down (slope < 0)',
  },
  maPrice: {
    aboveBoth:  { status: 'Price above MA50 and MA200',  summary: 'Bull-stack condition #1: price above MA200 (and above MA50)' },
    belowBoth:  { status: 'Price below MA50 and MA200',  summary: 'Bear-stack condition #1: price below MA200 (and below MA50)' },
    aboveMa50:  { status: 'Price above MA50, below MA200', summary: 'Price between MA50 and MA200 — trend not yet stacked' },
    belowMa50:  { status: 'Price below MA50, above MA200', summary: 'Price below MA50 but above MA200 — divergent signal' },
    unknown:    { status: 'Price overlaps MAs or data insufficient', summary: 'Price overlaps MAs or data insufficient — trend cannot be determined' },
  },
  trendStructure: {
    bullStack:    { name: 'Bull stack (Bullish)',    desc: 'Price above MA200, MA200 flat or rising, and MA50 above MA200' },
    trendBull:    { name: 'Bullish trend',           desc: 'Price above MA200 and MA200 flat or rising' },
    bearStack:    { name: 'Bear stack (Bearish)',    desc: 'Price below MA200, MA200 trending down, and MA50 below MA200' },
    trendBear:    { name: 'Bearish trend',           desc: 'Price below MA200 and MA200 trending down' },
    bullDegrade:  { name: 'Bullish (degraded)',      desc: 'Price above MA200, but MA200 weakening (slope < 0)' },
    bearDegrade:  { name: 'Bearish (degraded)',      desc: 'Price below MA200, but MA200 flat or rising (slope ≥ 0)' },
    unknown:      { name: 'Indeterminate',           desc: 'Price overlaps MA200 or data insufficient — cannot determine trend' },
  },
  trendQuality: {
    good: 'MA50 above MA200 — mid-term trend is keeping up, market has momentum',
    bad:  'Price < MA50 < MA200 — classic bear stack; bounces are pressure-level repairs, not reversals',
  },
  fundingChange: {
    stablecoinTrendLabel: 'Stablecoin Market-Cap Trend',
    totalTrendLabel: 'Total Crypto Market-Cap Trend',
    stablecoinRatioLabel: 'Stablecoin Ratio',
    upMore: 'Rising (more)',
    downLess: 'Falling (less)',
    stablecoinUpDesc: 'Stablecoin cap rising — capital seeking safety',
    stablecoinDownDesc: 'Stablecoin cap falling — capital flowing into risk assets',
    totalUpDesc: 'Total cap rising — risk assets expanding',
    totalDownDesc: 'Total cap falling — risk assets contracting',
    thresholdGap: 'Gap to threshold:',
    changeLabel: 'Change:',
    explanationStrong: 'Note: ',
    explanationBody: 'Stablecoin cap / total crypto cap. Higher ratio = capital de-risking; lower ratio = capital advancing into risk assets.',
  },
  fundingPattern: {
    incrementalOffensive: { name: 'Incremental Offensive', desc: 'Cash on the field grows AND assets rise — outside capital is entering. Offensive / bullish.' },
    strongOffensive:      { name: 'Strong Offensive', descPre: 'Stablecoin pool shrinks as it converts to coins; risk assets expand sharply. ', descStrong: 'Strongest offensive state' },
    deriskDefensive:      { name: 'De-risk Defensive', desc: 'Coins shrink while cash grows — investors selling coins for cash to dodge risk. Classic de-risk / defense.' },
    deepDefensive:        { name: 'Deep Defensive / Retreat', desc: 'Both assets and cash shrink in tandem — capital is leaving the crypto system entirely. Stronger defense / full bear.' },
    insufficient:         { name: 'Insufficient history / flat' },
  },
  thermometer: {
    normal: 'Normal',
    midFever: 'Low/Mid fever',
    highFever: 'High fever',
    critical: 'Critical',
    rangeUnder20: '< 20%: Normal (36–37°C, free to push offense)',
    range20To35: '20–35%: Low/Mid fever (37–39°C, market hurts and needs repair)',
    rangeOver35: '> 35%: High-fever threat (bear regime probability rises sharply)',
    rangeOver60: '> 60%: Critical vitals (deep liquidation phase, near full washout)',
  },
  etfAccelerator: {
    tailwind: 'Tailwind',
    headwind: 'Headwind',
    blunted: 'Blunted',
    unknown: 'Unknown',
    netFlowLabel: 'Net Flow',
    aumLabel: 'AUM',
    flow14dLabel: '14-Day Net Flow Sum',
    flowSpeedLabel: 'Flow Velocity',
    avgRecent: 'Recent 7-day avg',
    avgPrev: 'Prior 7-day avg',
    flowTrendLabel: 'Flow trend',
    aumTrendLabel: 'AUM trend',
    posRatioLabel: 'Positive-flow ratio',
    netFlowDesc: 'Spot-ETF net inflow (positive) or outflow (negative)',
    aumDesc: 'Total assets under management for ETFs',
    flow14dDesc: 'Used to gauge recent capital direction and AUM trend',
    flowSpeedDesc: 'Recent vs prior 7-day average — gauges whether flow velocity is decelerating',
    posRatioDesc: 'Share of recent days with positive net flow',
    unavailable: 'Data not available yet',
    info: {
      tailwindStrong: 'Tailwind (accelerating): ',
      tailwindBody: 'Sustained inflows accelerating the uptrend. ETF capital provides incremental support, pushing prices higher.',
      headwindStrong: 'Headwind (suppressing): ',
      headwindBody: 'Sustained outflows amplifying downside pressure. ETF outflows add selling pressure that may accelerate declines.',
      bluntedStrong: 'Blunted: ',
      bluntedBody: 'Outflow speed slowing — typically signals seller exhaustion and a likely shift into sideways consolidation.',
      unknownStrong: 'Unknown: ',
      unknownBody: 'ETF data unavailable — check connectivity or source. The system cannot judge ETF capital impact on the market.',
    },
  },
  trendBadge: {
    up: 'Up',
    down: 'Down',
    flat: 'Flat',
    unknown: 'Unknown',
  },
  signals: {
    trendBull: {
      name: 'Trend → Bullish',
      description: 'Price above MA200 and MA200 flat or rising',
      activeFmt: 'Price ({price}) > MA200 ({ma200}); MA200 slope ({slope}%) ≥ 0',
      pendingFmt: 'Need price to reclaim MA200 with MA200 flat or rising',
    },
    trendBear: {
      name: 'Trend → Bearish',
      description: 'Price below MA200 and MA200 trending down',
      activeFmt: 'Price ({price}) < MA200 ({ma200}); MA200 slope ({slope}%) < 0',
      pendingFmt: 'Need price to break below MA200 with MA200 trending down',
    },
    fundingOffensive: {
      name: 'Capital → Offensive',
      description: 'Stablecoin cap falling or total cap rising — capital flowing into risk assets',
      active: 'Capital combination matches offensive posture',
      pending: 'Need stablecoin cap to fall or total cap to rise',
    },
    fundingDefensive: {
      name: 'Capital → Defensive',
      description: 'Stablecoin cap rising or total cap falling — capital seeking safety',
      active: 'Capital combination matches defensive posture',
      pending: 'Need stablecoin cap to rise or total cap to fall',
    },
    risk: {
      name: 'Risk Thermometer',
      bullDescription: 'Risk thermometer: Normal or Low/Mid fever (drawdown < 35%)',
      bearDescription: 'Risk thermometer: High fever or Critical (drawdown ≥ 35%)',
      activeBullFmt: 'Current drawdown: {drawdown}% ({thermometer}) — meets bull-regime condition',
      pendingBullFmt: 'Need drawdown < 35% (current: {drawdown}%)',
      activeBearFmt: 'Current drawdown: {drawdown}% ({thermometer}) — meets bear-regime condition',
      pendingBearFmt: 'Need drawdown ≥ 35% (current: {drawdown}%)',
      naValue: 'N/A',
    },
    etf: {
      name: 'ETF Accelerator',
      bullDescription: 'ETF accelerator: Tailwind (sustained inflows, AUM recovering)',
      bullActiveFmt: 'ETF accelerator: {accelerator}; AUM: {aum}',
      bullPendingFmt: 'Need ETF to turn into sustained inflows with AUM recovering (currently: {accelerator})',
      bearBounceDescription: 'ETF accelerator: Blunted or Tailwind (seller exhaustion or starting inflows)',
      bearBounceActiveFmt: 'ETF accelerator: {accelerator}; AUM: {aum}',
      bearBouncePendingFmt: 'Need ETF Blunted (seller exhaustion) or Tailwind (currently: {accelerator})',
      bearDigestDescription: 'ETF accelerator: Headwind or Blunted (sustained outflows or seller exhaustion)',
      bearDigestActiveFmt: 'ETF accelerator: {accelerator}; AUM: {aum}',
      bearDigestPendingFmt: 'Need ETF Headwind (sustained outflows) or Blunted (seller exhaustion) (currently: {accelerator})',
      unknownAccelerator: 'unknown',
    },
  },
};
```

- [ ] **Step 2: 类型检查**

```bash
cd frontend && pnpm type-check
```

预期：通过（zh.ts 与 en.ts 字段对齐；vue-i18n 还没接入 App.vue，但类型独立可通过）。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/locales/en.ts
git commit -m "feat(i18n): add English locale dictionary"
```

---

## Task 5: 在 main.ts 注册 i18n 插件

**Files:**
- Modify: `frontend/src/main.ts`

- [ ] **Step 1: 修改 main.ts**

把：
```ts
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(router)

app.mount('#app')
```

改为：
```ts
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import i18n from './locales'

const app = createApp(App)

app.use(router)
app.use(i18n)

app.mount('#app')
```

- [ ] **Step 2: 运行 dev server 验证启动**

```bash
cd frontend && pnpm dev
```

预期：dev server 正常启动，打开 `http://localhost:5173/`，页面显示无报错（此时 App.vue 还没用 t()，仍是中文，但 i18n 已挂载）。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/main.ts
git commit -m "feat(i18n): register vue-i18n plugin"
```

---

## Task 6: 添加 lang-toggle UI 与样式

**Files:**
- Modify: `frontend/src/App.vue` (template header + style)

- [ ] **Step 1: 在 App.vue 模板的 `<header>` 内添加切换器**

定位 `<header>` 块（约 681-692 行），在 `</header>` 闭合标签之前插入：

```vue
      <div class="lang-toggle" role="group" :aria-label="$t('langToggle.aria')">
        <button
          type="button"
          class="lang-btn"
          :class="{ active: $i18n.locale === 'zh' }"
          @click="onSetLocale('zh')"
        >{{ $t('langToggle.zh') }}</button>
        <button
          type="button"
          class="lang-btn"
          :class="{ active: $i18n.locale === 'en' }"
          @click="onSetLocale('en')"
        >{{ $t('langToggle.en') }}</button>
      </div>
```

- [ ] **Step 2: 在 `<script setup>` 顶部导入并添加 onSetLocale**

在 App.vue `<script setup>` 现有导入下方加：

```ts
import { useI18n } from 'vue-i18n';
import { setLocale, type AppLocale } from './locales';

const { t } = useI18n();

function onSetLocale(loc: AppLocale) {
  setLocale(loc);
}
```

（`t` 后续任务会使用；这里一次性引入。）

- [ ] **Step 3: 在 `<style scoped>` 末尾添加切换器样式**

把以下 CSS 追加到 App.vue 的 `<style scoped>` 段末尾（最后一个 `}` 后、`</style>` 前）：

```css
.lang-toggle {
  position: absolute;
  top: 1rem;
  right: 1rem;
  display: inline-flex;
  border: 1px solid #334155;
  border-radius: 6px;
  overflow: hidden;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
}

.lang-btn {
  appearance: none;
  background: transparent;
  border: 0;
  color: #94a3b8;
  padding: 0.25rem 0.6rem;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.lang-btn:hover {
  color: #e2e8f0;
}

.lang-btn.active {
  background: #1e293b;
  color: #f8fafc;
}

.lang-btn + .lang-btn {
  border-left: 1px solid #334155;
}
```

并确保 `header` 是 `position: relative`（如果不是，加进 header 的样式块）：

```css
header {
  position: relative;
  /* … 原有样式保留 … */
}
```

如果 `header` 已经有样式块（搜索 `^header\s*{`），在其内部加 `position: relative;`，不要重复创建。

- [ ] **Step 4: 类型检查 + 浏览器验证**

```bash
cd frontend && pnpm type-check
```
预期：通过。

```bash
cd frontend && pnpm dev
```
浏览器打开 `http://localhost:5173/`：
- header 右上角应能看到 `[中|EN]` 切换器
- 点击 EN：当前页面其他文案仍是中文（因 App.vue 还未迁移），但切换器自身的高亮状态切换正确
- 刷新页面，切换器维持上次选择（localStorage 持久化）
- 浏览器开发者工具切到 Application → Local Storage，应有 `locale: 'en'` 项

- [ ] **Step 5: 提交**

```bash
git add frontend/src/App.vue
git commit -m "feat(i18n): add language toggle UI in header"
```

---

## Task 7: App.vue 添加映射常量、迁移 currentQuadrant、迁移错误字符串

**Files:**
- Modify: `frontend/src/App.vue` (script section)

- [ ] **Step 1: 在 `<script setup>` 顶部导入下方添加映射常量**

把现有的 `import { type DataResult, DATA_LABELS, ... QUADRANT_MAP } from './types';` 改为：

```ts
import { type DataResult, type StateApiResponse, STATE_STYLES, RISK_COLORS } from './types';
```

（`DATA_LABELS` 和 `QUADRANT_MAP` 移除；它们 Task 21 会从 types.ts 删除。）

并在 `useI18n` 使用之后（即 `const { t } = useI18n();` 这一行之后）追加：

```ts
const STATE_KEYS: Record<string, string> = {
  '牛市进攻': 'bullOffensive',
  '牛市修复': 'bullRecovery',
  '熊市反弹': 'bearBounce',
  '熊市消化': 'bearDigest',
};

const TREND_KEYS: Record<string, string> = {
  '趋势多': 'bull',
  '趋势空': 'bear',
};

const FUNDING_KEYS: Record<string, string> = {
  '资金进攻': 'offensive',
  '资金防守': 'defensive',
  '无法判断': 'unknown',
};

const THERMOMETER_KEYS: Record<string, string> = {
  '正常体温': 'normal',
  '低/中烧': 'midFever',
  '高烧威胁': 'highFever',
  '生命体征极差': 'critical',
};

const ETF_ACCEL_KEYS: Record<string, string> = {
  '顺风': 'tailwind',
  '逆风': 'headwind',
  '钝化': 'blunted',
  '未知': 'unknown',
};
```

- [ ] **Step 2: 重写 currentQuadrant**

定位 currentQuadrant computed（约 669-672 行），把：

```ts
const currentQuadrant = computed(() =>
  stateData.value?.ok ? (QUADRANT_MAP[stateData.value.state] ?? null) : null
);
```

替换为：

```ts
const currentQuadrant = computed(() => {
  if (!stateData.value?.ok) return null;
  const key = STATE_KEYS[stateData.value.state];
  if (!key) return null;
  return {
    key,
    name: t(`quadrant.${key}.name`),
    trend: t(`quadrant.${key}.trendLabel`),
    flow: t(`quadrant.${key}.flowLabel`),
  };
});
```

模板侧（Task 13）会用 `currentQuadrant.name` / `.trend` / `.flow` 直接拿到当前 locale 的文本 —— 不再像旧 `QUADRANT_MAP` 那样并排显示中英两版。

- [ ] **Step 3: 迁移 fetchData / fetchState / fetchData 内的 error.value 中文**

定位以下行（约 75、130、137 行附近）：

把：
```ts
error.value = '无法加载数据，请稍后重试';
```
改为：
```ts
error.value = t('errors.dataLoadFailed');
```

把：
```ts
error.value = '无法加载状态数据，请稍后重试';
```
改为：
```ts
error.value = t('errors.stateLoadFailed');
```

把：
```ts
error.value = `状态获取失败: ${e.message || '未知错误'}`;
```
改为：
```ts
error.value = `${t('errors.stateFetchPrefix')}: ${e.message || t('errors.unknownError')}`;
```

- [ ] **Step 4: 迁移 getTrendBadge 函数**

定位（约 169-174 行）：

```ts
const getTrendBadge = (trend: string | null | undefined) => {
  if (trend === 'up') return { text: '向上', className: 'positive', icon: '📈' };
  if (trend === 'down') return { text: '向下', className: 'negative', icon: '📉' };
  if (trend === 'flat') return { text: '走平', className: 'neutral', icon: '➖' };
  return { text: '未知', className: 'neutral', icon: '—' };
};
```

替换为：

```ts
const getTrendBadge = (trend: string | null | undefined) => {
  if (trend === 'up')   return { text: t('trendBadge.up'),      className: 'positive', icon: '📈' };
  if (trend === 'down') return { text: t('trendBadge.down'),    className: 'negative', icon: '📉' };
  if (trend === 'flat') return { text: t('trendBadge.flat'),    className: 'neutral',  icon: '➖' };
  return { text: t('trendBadge.unknown'), className: 'neutral', icon: '—' };
};
```

注意：`getRiskThermometerColor` 和 `getETFAcceleratorColor` 这两个函数的 case 是后端中文标识符，**保持原样**。

- [ ] **Step 5: 类型检查**

```bash
cd frontend && pnpm type-check
```
预期：通过。

- [ ] **Step 6: 提交**

```bash
git add frontend/src/App.vue
git commit -m "feat(i18n): add backend-enum→key maps and migrate error/badge strings"
```

---

## Task 8: 重写 getPriceMARelation → priceMARelation computed

**Files:**
- Modify: `frontend/src/App.vue` (script, 约 238-280 行)

- [ ] **Step 1: 替换函数**

把 `getPriceMARelation` 整个函数（含 `// 获取价格与均线（MA50/MA200）的关系` 注释）替换为：

```ts
const priceMARelation = computed(() => {
  if (!stateData.value?.metadata) return null;
  const btcPrice = stateData.value.metadata.btc_price;
  const ma50 = stateData.value.metadata.ma50;
  const ma200 = stateData.value.metadata.ma200;
  if (btcPrice == null || ma50 == null || ma200 == null) return null;

  const above50 = btcPrice > ma50;
  const above200 = btcPrice > ma200;
  const diff50 = ((btcPrice - ma50) / ma50) * 100;
  const diff200 = ((btcPrice - ma200) / ma200) * 100;

  let key: 'aboveBoth' | 'belowBoth' | 'aboveMa50' | 'belowMa50' | 'unknown' = 'unknown';
  let statusClass = '';
  if (above50 && above200) {
    key = 'aboveBoth';
    statusClass = 'positive';
  } else if (!above50 && !above200) {
    key = 'belowBoth';
    statusClass = 'negative';
  } else if (above50 && !above200) {
    key = 'aboveMa50';
  } else if (!above50 && above200) {
    key = 'belowMa50';
  }

  return {
    above50,
    above200,
    diff50,
    diff200,
    statusText: t(`maPrice.${key}.status`),
    summary: t(`maPrice.${key}.summary`),
    statusClass,
  };
});
```

- [ ] **Step 2: 更新模板调用**

定位模板中所有 `getPriceMARelation()` 调用（应在约 925-945 行），把每个 `getPriceMARelation()` 改为 `priceMARelation`（去掉括号 —— 它现在是 computed 而不是函数）。

包括：
- `<div v-if="getPriceMARelation()"` → `<div v-if="priceMARelation"`
- `getPriceMARelation()?.statusClass` → `priceMARelation?.statusClass`
- `getPriceMARelation()?.statusText` → `priceMARelation?.statusText`
- `getPriceMARelation()?.summary` → `priceMARelation?.summary`
- `(() => { const rel = getPriceMARelation(); ... })()` → `(() => { const rel = priceMARelation; ... })()`

- [ ] **Step 3: 类型检查 + dev 验证**

```bash
cd frontend && pnpm type-check
```
预期：通过。

dev server 浏览器查看趋势结构区块的「价格与均线关系」卡，文案随语言切换。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/App.vue
git commit -m "refactor(i18n): convert getPriceMARelation to reactive computed with t()"
```

---

## Task 9: 重写 getTrendConclusion → trendConclusion computed

**Files:**
- Modify: `frontend/src/App.vue` (script, 约 282-346 行)

- [ ] **Step 1: 替换函数**

把整个 `getTrendConclusion` 函数（含注释）替换为：

```ts
const trendConclusion = computed(() => {
  if (!stateData.value?.metadata) return null;
  const btcPrice = stateData.value.metadata.btc_price;
  const ma50 = stateData.value.metadata.ma50;
  const ma200 = stateData.value.metadata.ma200;
  const ma200Slope = stateData.value.metadata.ma200_slope;

  if (btcPrice == null || ma50 == null || ma200 == null || ma200Slope === undefined) return null;

  if (btcPrice > ma200 && ma200Slope >= 0) {
    const isBullStack = ma50 > ma200;
    const k = isBullStack ? 'bullStack' : 'trendBull';
    return {
      type: 'bullish' as const,
      name: t(`trendStructure.${k}.name`),
      description: t(`trendStructure.${k}.desc`),
      color: '#10b981',
      icon: '📈',
    };
  }

  if (btcPrice < ma200 && ma200Slope < 0) {
    const isBearStack = btcPrice < ma50 && ma50 < ma200;
    const k = isBearStack ? 'bearStack' : 'trendBear';
    return {
      type: 'bearish' as const,
      name: t(`trendStructure.${k}.name`),
      description: t(`trendStructure.${k}.desc`),
      color: '#ef4444',
      icon: '📉',
    };
  }

  if (btcPrice > ma200) {
    return {
      type: 'bullish' as const,
      name: t('trendStructure.bullDegrade.name'),
      description: t('trendStructure.bullDegrade.desc'),
      color: '#f59e0b',
      icon: '⚠️',
    };
  }
  if (btcPrice < ma200) {
    return {
      type: 'bearish' as const,
      name: t('trendStructure.bearDegrade.name'),
      description: t('trendStructure.bearDegrade.desc'),
      color: '#f59e0b',
      icon: '⚠️',
    };
  }
  return {
    type: 'uncertain' as const,
    name: t('trendStructure.unknown.name'),
    description: t('trendStructure.unknown.desc'),
    color: '#6b7280',
    icon: '❓',
  };
});
```

- [ ] **Step 2: 更新模板调用**

定位 `getTrendConclusion()` 在模板中的调用（约 901-916 行），把所有 `getTrendConclusion()` 改为 `trendConclusion`。

- [ ] **Step 3: 类型检查 + 提交**

```bash
cd frontend && pnpm type-check
git add frontend/src/App.vue
git commit -m "refactor(i18n): convert getTrendConclusion to reactive computed with t()"
```

---

## Task 10: 重写 getTrendQuality → trendQuality computed

**Files:**
- Modify: `frontend/src/App.vue` (script, 约 348-365 行)

- [ ] **Step 1: 替换函数**

```ts
const trendQuality = computed(() => {
  if (!stateData.value?.metadata) return null;
  const btcPrice = stateData.value.metadata.btc_price;
  const ma50 = stateData.value.metadata.ma50;
  const ma200 = stateData.value.metadata.ma200;
  if (!btcPrice || !ma50 || !ma200) return null;

  if (ma50 > ma200) {
    return { type: 'good' as const, text: t('trendQuality.good') };
  }
  if (btcPrice < ma50 && ma50 < ma200) {
    return { type: 'bad' as const, text: t('trendQuality.bad') };
  }
  return null;
});
```

- [ ] **Step 2: 更新模板调用**

`getTrendQuality()` → `trendQuality`，所有出现处。

- [ ] **Step 3: 类型检查 + 提交**

```bash
cd frontend && pnpm type-check
git add frontend/src/App.vue
git commit -m "refactor(i18n): convert getTrendQuality to reactive computed with t()"
```

---

## Task 11: 重写 getFundingPatternInfo → fundingPatternInfo computed

**Files:**
- Modify: `frontend/src/App.vue` (script, 约 367-410 行)

注意：`getFundingPattern` 函数（约 412-422 行）目前总是 `return null`，是历史遗留死代码 —— 删掉它。

- [ ] **Step 1: 删除死函数 getFundingPattern**

删除整段 `// 获取资金姿态组合模式` 注释 + `getFundingPattern` 函数（约 412-422 行）。

- [ ] **Step 2: 替换 getFundingPatternInfo**

把整个 `getFundingPatternInfo` 函数（约 367-410 行）替换为：

```ts
const fundingPatternInfo = computed(() => {
  if (!stateData.value?.metadata) return null;
  const stablecoinSlope = stateData.value.metadata.stablecoin_slope;
  const totalSlope = stateData.value.metadata.total_slope;

  if (stablecoinSlope === undefined || totalSlope === undefined) return null;

  const stablecoinTrend = stablecoinSlope > 0 ? '↑' : stablecoinSlope < 0 ? '↓' : '→';
  const totalTrend = totalSlope > 0 ? '↑' : totalSlope < 0 ? '↓' : '→';

  if (stablecoinTrend === '↑' && totalTrend === '↑') {
    return {
      pattern: 'Stable ↑ + Total ↑',
      name: t('fundingPattern.incrementalOffensive.name'),
      funding: t('funding.offensive'),
    };
  } else if (stablecoinTrend === '↓' && totalTrend === '↑') {
    return {
      pattern: 'Stable ↓ + Total ↑',
      name: t('fundingPattern.strongOffensive.name'),
      funding: t('funding.offensive'),
    };
  } else if (stablecoinTrend === '↑' && totalTrend === '↓') {
    return {
      pattern: 'Stable ↑ + Total ↓',
      name: t('fundingPattern.deriskDefensive.name'),
      funding: t('funding.defensive'),
    };
  } else if (stablecoinTrend === '↓' && totalTrend === '↓') {
    return {
      pattern: 'Stable ↓ + Total ↓',
      name: t('fundingPattern.deepDefensive.name'),
      funding: t('funding.defensive'),
    };
  }

  return {
    pattern: '—',
    name: t('fundingPattern.insufficient.name'),
    funding: t('funding.unknown'),
  };
});
```

注：`pattern` 字段保留 `'Stable ↑ + Total ↑'` 等英文标识 —— 这些是模板里的 `:class="{ active: ... === 'Stable ↑ + Total ↑' }"` 比对值，是稳定标识符不翻译。

- [ ] **Step 3: 更新模板调用**

`getFundingPatternInfo()` → `fundingPatternInfo`，所有出现处。

- [ ] **Step 4: 类型检查 + 提交**

```bash
cd frontend && pnpm type-check
git add frontend/src/App.vue
git commit -m "refactor(i18n): convert getFundingPatternInfo to reactive computed with t(); drop dead getFundingPattern"
```

---

## Task 12: 重写 getStateTransitionSignals → stateTransitionSignals computed

**Files:**
- Modify: `frontend/src/App.vue` (script, 约 443-631 行)

这是最大的一段。整体重写：

- [ ] **Step 1: 替换函数**

把整个 `getStateTransitionSignals` 函数（含 `// 计算状态切换信号` 注释和它上方的 `interface TransitionSignal { ... }` / `interface Transition { ... }` 保留不动）替换为：

```ts
const stateTransitionSignals = computed<Transition[]>(() => {
  if (!stateData.value?.metadata || !stateData.value?.state) return [];

  const currentState = stateData.value.state;
  const btcPrice = stateData.value.metadata.btc_price;
  const ma50 = stateData.value.metadata.ma50;
  const ma200 = stateData.value.metadata.ma200;
  const ma200Slope = stateData.value.metadata.ma200_slope;
  const ma50Slope = stateData.value.metadata.ma50_slope;
  const stablecoinRatioChange = stateData.value.metadata.stablecoin_ratio_change;
  const stablecoinSlope = stateData.value.metadata.stablecoin_slope;
  const totalSlope = stateData.value.metadata.total_slope;
  const etfAccelerator = stateData.value?.validation?.etf_accelerator;
  const etfAum = stateData.value?.validation?.etf_aum;

  const transitions: Transition[] = [];

  const allStates = ['牛市进攻', '牛市修复', '熊市反弹', '熊市消化'];
  const targetStates = allStates.filter(s => s !== currentState);

  const fmtPrice = (v: number | null | undefined) => v != null ? `$${v.toLocaleString()}` : '—';
  const fmtSlope = (v: number | null | undefined) => v != null ? v.toFixed(2) : '—';
  const fmtPct = (v: number | null | undefined) => v != null ? v.toFixed(2) : t('signals.risk.naValue');

  targetStates.forEach(targetState => {
    const signals: TransitionSignal[] = [];

    let targetTrend = '';
    let targetFunding = '';
    if (targetState === '牛市进攻')      { targetTrend = '趋势多'; targetFunding = '资金进攻'; }
    else if (targetState === '牛市修复') { targetTrend = '趋势多'; targetFunding = '资金防守'; }
    else if (targetState === '熊市反弹') { targetTrend = '趋势空'; targetFunding = '资金进攻'; }
    else if (targetState === '熊市消化') { targetTrend = '趋势空'; targetFunding = '资金防守'; }

    // 1. 趋势切换信号
    if (targetTrend === '趋势多') {
      const trendSignal = btcPrice && ma200 && ma200Slope !== undefined
        ? (btcPrice > ma200 && ma200Slope >= 0)
        : false;
      signals.push({
        name: t('signals.trendBull.name'),
        description: t('signals.trendBull.description'),
        active: trendSignal,
        details: trendSignal
          ? t('signals.trendBull.activeFmt', { price: fmtPrice(btcPrice), ma200: fmtPrice(ma200), slope: fmtSlope(ma200Slope) })
          : t('signals.trendBull.pendingFmt'),
      });
    } else {
      const trendSignal = btcPrice && ma200 && ma200Slope !== undefined
        ? (btcPrice < ma200 && ma200Slope < 0)
        : false;
      signals.push({
        name: t('signals.trendBear.name'),
        description: t('signals.trendBear.description'),
        active: trendSignal,
        details: trendSignal
          ? t('signals.trendBear.activeFmt', { price: fmtPrice(btcPrice), ma200: fmtPrice(ma200), slope: fmtSlope(ma200Slope) })
          : t('signals.trendBear.pendingFmt'),
      });
    }

    // 2. 资金姿态切换信号
    if (targetFunding === '资金进攻') {
      const fundingSignal = stablecoinSlope !== undefined && totalSlope !== undefined
        ? (stablecoinSlope < 0 && totalSlope > 0) || (stablecoinSlope > 0 && totalSlope > 0)
        : stablecoinRatioChange !== undefined && stablecoinRatioChange !== null ? stablecoinRatioChange < 0 : false;
      signals.push({
        name: t('signals.fundingOffensive.name'),
        description: t('signals.fundingOffensive.description'),
        active: fundingSignal,
        details: fundingSignal ? t('signals.fundingOffensive.active') : t('signals.fundingOffensive.pending'),
      });
    } else {
      const fundingSignal = stablecoinSlope !== undefined && totalSlope !== undefined
        ? (stablecoinSlope > 0 && totalSlope < 0) || (stablecoinSlope < 0 && totalSlope < 0)
        : stablecoinRatioChange !== undefined && stablecoinRatioChange !== null ? stablecoinRatioChange > 0 : false;
      signals.push({
        name: t('signals.fundingDefensive.name'),
        description: t('signals.fundingDefensive.description'),
        active: fundingSignal,
        details: fundingSignal ? t('signals.fundingDefensive.active') : t('signals.fundingDefensive.pending'),
      });
    }

    // 校验层信号（不计入需要条件）
    const validationSignals: TransitionSignal[] = [];

    const athDrawdown = stateData.value?.validation?.ath_drawdown;
    const riskThermometer = stateData.value?.validation?.risk_thermometer;
    const thermometerKey = riskThermometer ? THERMOMETER_KEYS[riskThermometer] : '';
    const thermometerLabel = thermometerKey ? t(`thermometer.${thermometerKey}`) : (riskThermometer ?? '');

    let riskSignal = false;
    let riskDescription = '';
    let riskDetails = '';

    if (targetState === '牛市进攻' || targetState === '牛市修复') {
      riskSignal = athDrawdown !== undefined && athDrawdown < 35;
      riskDescription = t('signals.risk.bullDescription');
      riskDetails = riskSignal
        ? t('signals.risk.activeBullFmt', { drawdown: fmtPct(athDrawdown), thermometer: thermometerLabel })
        : t('signals.risk.pendingBullFmt', { drawdown: fmtPct(athDrawdown) });
    } else if (targetState === '熊市反弹' || targetState === '熊市消化') {
      riskSignal = athDrawdown !== undefined && athDrawdown >= 35;
      riskDescription = t('signals.risk.bearDescription');
      riskDetails = riskSignal
        ? t('signals.risk.activeBearFmt', { drawdown: fmtPct(athDrawdown), thermometer: thermometerLabel })
        : t('signals.risk.pendingBearFmt', { drawdown: fmtPct(athDrawdown) });
    }

    validationSignals.push({
      name: t('signals.risk.name'),
      description: riskDescription,
      active: riskSignal,
      details: riskDetails,
    });

    // ETF 加速器
    let etfSignal = false;
    let etfDescription = '';
    let etfDetails = '';

    const acceleratorKey = etfAccelerator ? ETF_ACCEL_KEYS[etfAccelerator] : '';
    const acceleratorLabel = acceleratorKey ? t(`etfAccelerator.${acceleratorKey}`) : (etfAccelerator ?? t('signals.etf.unknownAccelerator'));
    const aumLabel = etfAum != null ? formatETFValue(etfAum) : '';

    if (targetState === '牛市进攻' || targetState === '牛市修复') {
      etfSignal = etfAccelerator === '顺风' && etfAum !== null && etfAum !== undefined && etfAum > 0;
      etfDescription = t('signals.etf.bullDescription');
      etfDetails = etfSignal && etfAum
        ? t('signals.etf.bullActiveFmt', { accelerator: acceleratorLabel, aum: aumLabel })
        : t('signals.etf.bullPendingFmt', { accelerator: acceleratorLabel || t('signals.etf.unknownAccelerator') });
    } else if (targetState === '熊市反弹') {
      etfSignal = etfAccelerator === '钝化' || (etfAccelerator === '顺风' && etfAum !== null && etfAum !== undefined && etfAum > 0);
      etfDescription = t('signals.etf.bearBounceDescription');
      etfDetails = etfSignal && etfAum
        ? t('signals.etf.bearBounceActiveFmt', { accelerator: acceleratorLabel, aum: aumLabel })
        : t('signals.etf.bearBouncePendingFmt', { accelerator: acceleratorLabel || t('signals.etf.unknownAccelerator') });
    } else if (targetState === '熊市消化') {
      etfSignal = etfAccelerator === '逆风' || etfAccelerator === '钝化';
      etfDescription = t('signals.etf.bearDigestDescription');
      etfDetails = etfSignal && etfAum
        ? t('signals.etf.bearDigestActiveFmt', { accelerator: acceleratorLabel, aum: aumLabel })
        : t('signals.etf.bearDigestPendingFmt', { accelerator: acceleratorLabel || t('signals.etf.unknownAccelerator') });
    }

    validationSignals.push({
      name: t('signals.etf.name'),
      description: etfDescription,
      active: etfSignal,
      details: etfDetails,
    });

    const activeCount = signals.filter(s => s.active).length;
    const totalCount = signals.length;

    transitions.push({
      targetState,
      targetTrend,
      targetFunding,
      signals,
      validationSignals,
      activeCount,
      totalCount,
      progress: totalCount > 0 ? (activeCount / totalCount) * 100 : 0,
    });
  });

  return transitions;
});
```

- [ ] **Step 2: 更新模板调用**

`getStateTransitionSignals()` → `stateTransitionSignals`，所有出现处（约 1273 行）。

- [ ] **Step 3: 类型检查 + 提交**

```bash
cd frontend && pnpm type-check
git add frontend/src/App.vue
git commit -m "refactor(i18n): convert getStateTransitionSignals to reactive computed with t()"
```

---

## Task 13: 迁移 header / loading / state-header 模板

**Files:**
- Modify: `frontend/src/App.vue` (template, 约 681-751 行)

- [ ] **Step 1: 迁移 header 静态文本**

把：
```vue
<h1>📊 BullBear Dashboard</h1>
<p class="subtitle">加密市场状态机 - 四象限状态可视化</p>
<button @click="loadAllData" :disabled="loading" class="refresh-btn">
  {{ loading ? '加载中...' : '🔄 刷新数据' }}
</button>
<div v-if="currentQuadrant" class="status-summary">
  <p class="status-primary">当前状态：{{ currentQuadrant.en }}（{{ currentQuadrant.cn }}）</p>
  <p class="status-secondary">{{ currentQuadrant.trend }}｜{{ currentQuadrant.flow }}</p>
</div>
```

替换为：
```vue
<h1>📊 {{ $t('app.title') }}</h1>
<p class="subtitle">{{ $t('app.subtitle') }}</p>
<button @click="loadAllData" :disabled="loading" class="refresh-btn">
  {{ loading ? $t('actions.loading') : `${$t('actions.refreshIcon')} ${$t('actions.refresh')}` }}
</button>
<div v-if="currentQuadrant" class="status-summary">
  <p class="status-primary">{{ $t('status.currentLabel') }}{{ currentQuadrant.name }}</p>
  <p class="status-secondary">{{ currentQuadrant.trend }}{{ $t('status.separator') }}{{ currentQuadrant.flow }}</p>
</div>
```

- [ ] **Step 2: 迁移 loading 段（约 700-714 行）**

把：
```vue
<p class="loading-title">正在加载市场数据...</p>
<p class="loading-subtitle">请稍候，正在获取最新状态</p>
```
改为：
```vue
<p class="loading-title">{{ $t('loading.title') }}</p>
<p class="loading-subtitle">{{ $t('loading.subtitle') }}</p>
```

- [ ] **Step 3: 迁移 state-header（state-name + state-details）**

把：
```vue
<div class="state-name">{{ stateData.state }}</div>
<div class="state-details">
  {{ stateData.trend }} | {{ stateData.funding }}
</div>
```

改为：
```vue
<div class="state-name">{{ STATE_KEYS[stateData.state] ? $t(`quadrant.${STATE_KEYS[stateData.state]}.name`) : stateData.state }}</div>
<div class="state-details">
  {{ TREND_KEYS[stateData.trend] ? $t(`trend.${TREND_KEYS[stateData.trend]}`) : stateData.trend }}
  | {{ FUNDING_KEYS[stateData.funding] ? $t(`funding.${FUNDING_KEYS[stateData.funding]}`) : stateData.funding }}
</div>
```

为了让模板能访问 `STATE_KEYS` / `TREND_KEYS` / `FUNDING_KEYS`，确认它们在 `<script setup>` 顶层定义即可（Task 7 已加 —— `<script setup>` 内的 `const` 默认对模板可见）。

- [ ] **Step 4: 迁移风险等级 / 置信度 tooltip 段（约 723-748 行）**

把整个 `metric-item`（风险等级）块的标签和 tooltip 内文字替换：

```vue
<div class="metric-item">
  <span class="metric-label">{{ $t('metric.risk.label') }}</span>
  <span class="metric-value">{{ RISK_COLORS[stateData.risk_level] || '⚪' }} {{ stateData.risk_level }}</span>
  <div class="metric-tooltip">
    <span class="tooltip-icon">ℹ️</span>
    <div class="tooltip-content">
      <strong>{{ $t('metric.risk.tooltipTitle') }}</strong><br>
      • {{ $t('metric.risk.high') }}<br>
      • {{ $t('metric.risk.medium') }}<br>
      • {{ $t('metric.risk.low') }}
    </div>
  </div>
</div>
<div class="metric-item">
  <span class="metric-label">{{ $t('metric.confidence.label') }}</span>
  <span class="metric-value">{{ (stateData.confidence * 100).toFixed(1) }}%</span>
  <div class="metric-tooltip">
    <span class="tooltip-icon">ℹ️</span>
    <div class="tooltip-content">
      <strong>{{ $t('metric.confidence.tooltipTitle') }}</strong><br>
      • {{ $t('metric.confidence.item1') }}<br>
      • {{ $t('metric.confidence.item2') }}<br>
      • {{ $t('metric.confidence.item3') }}
    </div>
  </div>
</div>
```

- [ ] **Step 5: 类型检查 + dev 验证**

```bash
cd frontend && pnpm type-check
cd frontend && pnpm dev
```

浏览器打开：
- 中/EN 切换，header 标题、副标题、刷新按钮、状态摘要、风险/置信度 tooltip 文案随之切换
- 切换时无控制台报错

- [ ] **Step 6: 提交**

```bash
git add frontend/src/App.vue
git commit -m "feat(i18n): migrate header, loading, state-header sections"
```

---

## Task 14: 迁移四象限矩阵模板

**Files:**
- Modify: `frontend/src/App.vue` (template, 约 752-888 行)

四个象限块结构高度对称。统一替换：

- [ ] **Step 1: 迁移 section header + 描述 + 坐标轴**

把：
```vue
<span class="section-badge core-output">核心输出</span>
<h2>📈 四象限状态矩阵</h2>
…
<p class="section-description">市场状态由"趋势结构"和"资金姿态"共同决定</p>
<div class="quadrant-chart-container">
  <div class="quadrant-chart">
    <div class="axis-y-label top">趋势多</div>
    <div class="axis-y-label bottom">趋势空</div>
    <div class="axis-x-label left">资金防守</div>
    <div class="axis-x-label right">资金进攻</div>
```

改为：
```vue
<span class="section-badge core-output">{{ $t('badge.coreOutput') }}</span>
<h2>{{ $t('section.quadrant.title') }}</h2>
…
<p class="section-description">{{ $t('section.quadrant.description') }}</p>
<div class="quadrant-chart-container">
  <div class="quadrant-chart">
    <div class="axis-y-label top">{{ $t('axis.trendUp') }}</div>
    <div class="axis-y-label bottom">{{ $t('axis.trendDown') }}</div>
    <div class="axis-x-label left">{{ $t('axis.fundingLeft') }}</div>
    <div class="axis-x-label right">{{ $t('axis.fundingRight') }}</div>
```

- [ ] **Step 2: 迁移每个 quadrant 块的显示文字**

每个象限块都有 `<div class="quadrant-name">…</div>` 和两个 `condition-text`。重写如下（牛市修复块为例）：

```vue
<div class="quadrant-name">{{ $t('quadrant.bullRecovery.name') }}</div>
<div class="quadrant-risk">MEDIUM RISK</div>
<div class="condition-indicator">
  <div class="condition-item" :class="{ met: stateData.trend === '趋势多' }">
    <span class="condition-icon">{{ stateData.trend === '趋势多' ? '✅' : '⏳' }}</span>
    <span class="condition-text">{{ $t('trend.bull') }}</span>
  </div>
  <div class="condition-item" :class="{ met: stateData.funding === '资金防守' }">
    <span class="condition-icon">{{ stateData.funding === '资金防守' ? '✅' : '⏳' }}</span>
    <span class="condition-text">{{ $t('funding.defensive') }}</span>
  </div>
</div>
```

四个象限的目标 key 对应表：

| 象限 | quadrant key | trend key | funding key | RISK 文案 |
|------|--------------|-----------|-------------|-----------|
| 牛市修复（左上 quadrant-2） | bullRecovery | bull | defensive | MEDIUM RISK |
| 牛市进攻（右上 quadrant-1） | bullOffensive | bull | offensive | HIGH RISK |
| 熊市消化（左下 quadrant-4） | bearDigest | bear | defensive | LOW RISK |
| 熊市反弹（右下 quadrant-3） | bearBounce | bear | offensive | MEDIUM RISK |

`v-if="stateData.state === '牛市修复'"`、`:class="{ met: stateData.trend === '趋势多' }"` 这类**条件判断**保持原样，比对的是后端中文标识符。

`MEDIUM RISK` / `HIGH RISK` / `LOW RISK` 这三个英文短语是设计上的 UI tag，两种语言下都保留为英文。

- [ ] **Step 3: 类型检查 + dev 验证**

```bash
cd frontend && pnpm type-check
cd frontend && pnpm dev
```

四象限矩阵的标题、描述、坐标轴、四个象限的名字和达成条件文案都随语言切换。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/App.vue
git commit -m "feat(i18n): migrate quadrant matrix section"
```

---

## Task 15: 迁移趋势结构 section 模板

**Files:**
- Modify: `frontend/src/App.vue` (template, 约 893-1012 行)

- [ ] **Step 1: 替换该 section 的所有静态中文**

参照下列对应表，**逐处把模板中的中文字面量替换为 `$t(...)` 表达式**。条件判断和后端标识符比对保持原样。

| 原中文 / 表达式 | 替换为 |
|------|------|
| `<span class="section-badge hard-rule">硬规则1</span>` | `<span class="section-badge hard-rule">{{ $t('section.trendStructure.badge') }}</span>` |
| `<h2>📈 趋势结构 (Trend Structure)</h2>` | `<h2>{{ $t('section.trendStructure.title') }}</h2>` |
| `<p class="section-description">使用 MA50（中期节奏线）和 MA200（长期生命线）的排列关系</p>` | `<p class="section-description">{{ $t('section.trendStructure.description') }}</p>` |
| `<h3>趋势结构结论</h3>` | `<h3>{{ $t('section.trendStructure.conclusionTitle') }}</h3>` |
| `系统判断：<strong>{{ stateData.trend }}</strong>` | `{{ $t('section.trendStructure.systemJudgment') }}<strong>{{ TREND_KEYS[stateData.trend] ? $t(\`trend.${TREND_KEYS[stateData.trend]}\`) : stateData.trend }}</strong>` |
| `<h3>价格与均线关系</h3>` | `<h3>{{ $t('trendCard.priceMARelation') }}</h3>` |
| `MA50 差值: …%` | `{{ $t('trendCard.diff50Label') }}: …%` |
| `MA200 差值: …%` | `{{ $t('trendCard.diff200Label') }}: …%` |
| `<div class="trend-unavailable">数据暂未可用</div>` | `<div class="trend-unavailable">{{ $t('trendCard.unavailable') }}</div>` |
| `<h3>MA50 趋势</h3>` | `<h3>{{ $t('trendCard.ma50Trend') }}</h3>` |
| `{{ stateData.metadata.ma50_slope >= 0 ? 'MA50 走平或向上' : 'MA50 趋势向下' }}` | `{{ stateData.metadata.ma50_slope >= 0 ? $t('trendCard.ma50FlatUp') : $t('trendCard.ma50Down') }}` |
| `斜率: …%/天` | `{{ $t('trendCard.slopeLabel') }}: …{{ $t('trendCard.perDay') }}` |
| `中期节奏线的趋势方向，反映市场中期推动力` | `{{ $t('trendCard.ma50Description') }}` |
| `<h3>MA200 趋势</h3>` | `<h3>{{ $t('trendCard.ma200Trend') }}</h3>` |
| `{{ stateData.metadata.ma200_slope >= 0 ? 'MA200 走平或向上' : 'MA200 趋势向下' }}` | `{{ stateData.metadata.ma200_slope >= 0 ? $t('trendCard.ma200FlatUp') : $t('trendCard.ma200Down') }}` |
| `'多头排列条件之二：MA200 走平或向上（斜率 >= 0）'` / `'空头排列条件之二：MA200 趋势向下（斜率 < 0）'` 三元表达式 | `{{ stateData.metadata.ma200_slope >= 0 ? $t('trendCard.ma200BullCondition') : $t('trendCard.ma200BearCondition') }}` |
| `<h3>趋势质量判定</h3>` | `<h3>{{ $t('trendCard.quality') }}</h3>` |

注意 `斜率: …%/天` 这一行的具体形式：原模板是
```vue
斜率: {{ stateData.metadata.ma50_slope > 0 ? '+' : '' }}{{ stateData.metadata.ma50_slope.toFixed(2) }}%/天
```
改为：
```vue
{{ $t('trendCard.slopeLabel') }}: {{ stateData.metadata.ma50_slope > 0 ? '+' : '' }}{{ stateData.metadata.ma50_slope.toFixed(2) }}%{{ $t('trendCard.perDay') }}
```
（MA200 那处同理。）

- [ ] **Step 2: 类型检查 + dev 验证**

```bash
cd frontend && pnpm type-check
cd frontend && pnpm dev
```

趋势结构 section 的标题、描述、4 个 trend-card 的标题、内文、不可用占位都随语言切换。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/App.vue
git commit -m "feat(i18n): migrate trend structure section"
```

---

## Task 16: 迁移资金姿态 section 模板

**Files:**
- Modify: `frontend/src/App.vue` (template, 约 1015-1114 行)

- [ ] **Step 1: 替换静态文本（按对应表）**

| 原 | 替换为 |
|---|---|
| `<span class="section-badge hard-rule">硬规则2</span>` | `<span class="section-badge hard-rule">{{ $t('section.fundingPosture.badge') }}</span>` |
| `<h2>💰 资金姿态 (Capital Posture)</h2>` | `<h2>{{ $t('section.fundingPosture.title') }}</h2>` |
| `<p class="section-description">核心在于观察资金是在"撤回现金避险"还是"进入风险资产进攻"</p>` | `<p class="section-description">{{ $t('section.fundingPosture.description') }}</p>` |
| `<h3>资金姿态变化程度</h3>` | `<h3>{{ $t('section.fundingPosture.changeTitle') }}</h3>` |
| `<p>使用线性回归在对数坐标上计算最近10天的斜率，…数据来源：CoinGecko历史API。</p>` | `<p>{{ $t('section.fundingPosture.changeIntro') }}</p>` |
| `<p v-if="…" class="data-warning">⚠️ 当前显示为0.000%可能是…</p>` 整段 | `<p v-if="…" class="data-warning">{{ $t('section.fundingPosture.dataWarning') }}</p>` |
| `<div class="change-label">稳定币市值趋势</div>` | `<div class="change-label">{{ $t('fundingChange.stablecoinTrendLabel') }}</div>` |
| `<strong>{{ stateData.metadata.stablecoin_slope > 0 ? '上升（变多）' : '下降（变少）' }}：</strong>` | `<strong>{{ stateData.metadata.stablecoin_slope > 0 ? $t('fundingChange.upMore') : $t('fundingChange.downLess') }}：</strong>` |
| `{{ stateData.metadata.stablecoin_slope > 0 ? '稳定币市值上升，资金避险' : '稳定币市值下降，资金流入风险资产' }}` | `{{ stateData.metadata.stablecoin_slope > 0 ? $t('fundingChange.stablecoinUpDesc') : $t('fundingChange.stablecoinDownDesc') }}` |
| `<div class="change-label">加密总市值趋势</div>` | `<div class="change-label">{{ $t('fundingChange.totalTrendLabel') }}</div>` |
| `<strong>{{ stateData.metadata.total_slope > 0 ? '上升（变多）' : '下降（变少）' }}：</strong>` | `<strong>{{ stateData.metadata.total_slope > 0 ? $t('fundingChange.upMore') : $t('fundingChange.downLess') }}：</strong>` |
| `{{ stateData.metadata.total_slope > 0 ? '总市值上升，风险资产扩张' : '总市值下降，风险资产收缩' }}` | `{{ stateData.metadata.total_slope > 0 ? $t('fundingChange.totalUpDesc') : $t('fundingChange.totalDownDesc') }}` |
| `<div class="change-label">稳定币占比</div>` | `<div class="change-label">{{ $t('fundingChange.stablecoinRatioLabel') }}</div>` |
| `<span>距离阈值: …%</span>` | `<span>{{ $t('fundingChange.thresholdGap') }} …%</span>` |
| `变化: …%` | `{{ $t('fundingChange.changeLabel') }} …%` |
| `<strong>说明：</strong>稳定币市值 / 加密总市值。…` | `<strong>{{ $t('fundingChange.explanationStrong') }}</strong>{{ $t('fundingChange.explanationBody') }}` |
| `<div class="combination-label">当前组合模式：</div>` | `<div class="combination-label">{{ $t('section.fundingPosture.currentCombination') }}</div>` |
| `{{ getFundingPatternInfo()?.pattern }} - {{ getFundingPatternInfo()?.name }}` | `{{ fundingPatternInfo?.pattern }} - {{ fundingPatternInfo?.name }}` |
| `<h3>资金组合模式</h3>` | `<h3>{{ $t('section.fundingPosture.patternsTitle') }}</h3>` |
| 4 个 funding-pattern-item 块的 `pattern-name` 和 `pattern-desc` | 见 Step 2 |
| `:class="{ active: getFundingPatternInfo()?.pattern === 'Stable ↑ + Total ↑' }"` 等 4 处 | 改为 `fundingPatternInfo?.pattern === 'Stable ↑ + Total ↑'` 等 |

- [ ] **Step 2: 替换 4 个 funding-pattern-item 的 name/desc**

第一个（`Stable ↑ + Total ↑`）：
```vue
<div class="pattern-name">{{ $t('fundingPattern.incrementalOffensive.name') }}</div>
<div class="pattern-desc">{{ $t('fundingPattern.incrementalOffensive.desc') }}</div>
```

第二个（`Stable ↓ + Total ↑`）：
```vue
<div class="pattern-name">{{ $t('fundingPattern.strongOffensive.name') }}</div>
<div class="pattern-desc">{{ $t('fundingPattern.strongOffensive.descPre') }}<strong>{{ $t('fundingPattern.strongOffensive.descStrong') }}</strong></div>
```

第三个（`Stable ↑ + Total ↓`）：
```vue
<div class="pattern-name">{{ $t('fundingPattern.deriskDefensive.name') }}</div>
<div class="pattern-desc">{{ $t('fundingPattern.deriskDefensive.desc') }}</div>
```

第四个（`Stable ↓ + Total ↓`）：
```vue
<div class="pattern-name">{{ $t('fundingPattern.deepDefensive.name') }}</div>
<div class="pattern-desc">{{ $t('fundingPattern.deepDefensive.desc') }}</div>
```

- [ ] **Step 3: 类型检查 + dev 验证 + 提交**

```bash
cd frontend && pnpm type-check
cd frontend && pnpm dev   # 浏览器人工核对
```

```bash
git add frontend/src/App.vue
git commit -m "feat(i18n): migrate capital posture section"
```

---

## Task 17: 迁移风险温度计 + ETF 加速器 section

**Files:**
- Modify: `frontend/src/App.vue` (template, 约 1117-1259 行)

- [ ] **Step 1: 风险温度计 section（约 1117-1142 行）**

替换：

| 原 | 替换为 |
|---|---|
| `<span class="section-badge validation-layer">检验层A</span>` | `<span class="section-badge validation-layer">{{ $t('section.riskThermometer.badge') }}</span>` |
| `<h2>🌡️ 风险温度计 (Validation Layer 1)</h2>` | `<h2>{{ $t('section.riskThermometer.title') }}</h2>` |
| `<p class="section-description">使用 ATH（历史最高价）回撤率来衡量风险</p>` | `<p class="section-description">{{ $t('section.riskThermometer.description') }}</p>` |
| `<div class="thermometer-label">{{ stateData.validation.risk_thermometer }}</div>` | `<div class="thermometer-label">{{ THERMOMETER_KEYS[stateData.validation.risk_thermometer] ? $t(\`thermometer.${THERMOMETER_KEYS[stateData.validation.risk_thermometer]}\`) : stateData.validation.risk_thermometer }}</div>` |
| `ATH: \${{ … }}` | `{{ $t('section.riskThermometer.athLabel') }} \${{ … }}` |
| `<p>公式: (ATH - 当前价格) / ATH × 100%</p>` | `<p>{{ $t('section.riskThermometer.formula') }}</p>` |
| 4 个 `<li>` 内的中文区间说明 | 用 `$t('thermometer.rangeUnder20')` / `range20To35` / `rangeOver35` / `rangeOver60` |

具体 4 个 `<li>`：
```vue
<li>{{ $t('thermometer.rangeUnder20') }}</li>
<li>{{ $t('thermometer.range20To35') }}</li>
<li>{{ $t('thermometer.rangeOver35') }}</li>
<li>{{ $t('thermometer.rangeOver60') }}</li>
```

- [ ] **Step 2: ETF 加速器 section（约 1145-1259 行）**

替换 section header：
```vue
<span class="section-badge validation-layer">{{ $t('section.etfAccelerator.badge') }}</span>
<h2>{{ $t('section.etfAccelerator.title') }}</h2>
…
<p class="section-description">{{ $t('section.etfAccelerator.description') }}</p>
```

替换 etf-label：
```vue
<div class="etf-label">{{ ETF_ACCEL_KEYS[stateData.validation.etf_accelerator] ? $t(`etfAccelerator.${ETF_ACCEL_KEYS[stateData.validation.etf_accelerator]}`) : (stateData.validation.etf_accelerator || $t('etfAccelerator.unknown')) }}</div>
```

各 metric label / desc：

| 原 | 替换为 |
|---|---|
| `<div class="etf-metric-label">净资金流</div>` | `<div class="etf-metric-label">{{ $t('etfAccelerator.netFlowLabel') }}</div>` |
| `现货 ETF 的净资金流入（正数）或流出（负数）` | `{{ $t('etfAccelerator.netFlowDesc') }}` |
| `<div class="etf-metric-value unavailable">数据暂未可用</div>` (出现 4 次) | `<div class="etf-metric-value unavailable">{{ $t('etfAccelerator.unavailable') }}</div>` |
| `<div class="etf-metric-label">资产管理规模 (AUM)</div>` (出现 2 次) | `<div class="etf-metric-label">{{ $t('etfAccelerator.aumLabel') }}</div>` |
| `ETF 的总资产管理规模` | `{{ $t('etfAccelerator.aumDesc') }}` |
| `<div class="etf-metric-label">近14日净流入合计</div>` (出现 2 次) | `<div class="etf-metric-label">{{ $t('etfAccelerator.flow14dLabel') }}</div>` |
| `用于判断近期资金方向与 AUM 趋势` | `{{ $t('etfAccelerator.flow14dDesc') }}` |
| `<div class="etf-metric-label">流入/流出速度</div>` | `<div class="etf-metric-label">{{ $t('etfAccelerator.flowSpeedLabel') }}</div>` |
| `<span>近7日均值</span>` | `<span>{{ $t('etfAccelerator.avgRecent') }}</span>` |
| `<span>前7日均值</span>` | `<span>{{ $t('etfAccelerator.avgPrev') }}</span>` |
| `<span>流入趋势</span>` | `<span>{{ $t('etfAccelerator.flowTrendLabel') }}</span>` |
| `<span>AUM 趋势</span>` | `<span>{{ $t('etfAccelerator.aumTrendLabel') }}</span>` |
| `近7日与前7日的均值对比，用于判断流入/流出速度是否减缓` | `{{ $t('etfAccelerator.flowSpeedDesc') }}` |
| `<div class="etf-metric-label">正流入占比</div>` | `<div class="etf-metric-label">{{ $t('etfAccelerator.posRatioLabel') }}</div>` |
| `近周期净流入为正的天数占比` | `{{ $t('etfAccelerator.posRatioDesc') }}` |
| `<strong>判定口径：</strong>顺风 = 净流入为主…` 整段 | `<strong>{{ $t('section.etfAccelerator.ruleNote') }}</strong>{{ $t('section.etfAccelerator.ruleNoteBody') }}` |

替换最后 4 个 `<p class="etf-info-text">` 块（按 etf_accelerator 值分支）：

```vue
<p v-if="stateData.validation.etf_accelerator === '顺风'" class="etf-info-text">
  <strong>{{ $t('etfAccelerator.info.tailwindStrong') }}</strong>{{ $t('etfAccelerator.info.tailwindBody') }}
</p>
<p v-else-if="stateData.validation.etf_accelerator === '逆风'" class="etf-info-text">
  <strong>{{ $t('etfAccelerator.info.headwindStrong') }}</strong>{{ $t('etfAccelerator.info.headwindBody') }}
</p>
<p v-else-if="stateData.validation.etf_accelerator === '钝化'" class="etf-info-text">
  <strong>{{ $t('etfAccelerator.info.bluntedStrong') }}</strong>{{ $t('etfAccelerator.info.bluntedBody') }}
</p>
<p v-else class="etf-info-text">
  <strong>{{ $t('etfAccelerator.info.unknownStrong') }}</strong>{{ $t('etfAccelerator.info.unknownBody') }}
</p>
```

注意：`v-if="… === '顺风'"` 等条件中的中文是后端标识符，**保持原样**。

- [ ] **Step 3: 类型检查 + dev 验证 + 提交**

```bash
cd frontend && pnpm type-check
cd frontend && pnpm dev   # 浏览器人工核对：温度计、ETF 各 metric 的标签和描述都在两种语言下正确
```

```bash
git add frontend/src/App.vue
git commit -m "feat(i18n): migrate risk thermometer and ETF accelerator sections"
```

---

## Task 18: 迁移状态切换信号 section

**Files:**
- Modify: `frontend/src/App.vue` (template, 约 1262-1334 行)

- [ ] **Step 1: 替换 section header 和导言**

```vue
<span class="section-badge core-logic">{{ $t('section.transitions.badge') }}</span>
<h2>{{ $t('section.transitions.title') }}</h2>
…
<p class="signals-intro">
  {{ $t('section.transitions.currentStatePrefix') }}<strong>{{ STATE_KEYS[stateData.state] ? $t(`quadrant.${STATE_KEYS[stateData.state]}.name`) : stateData.state }}</strong>{{ $t('section.transitions.currentStateSuffix') }}
</p>
```

- [ ] **Step 2: 把 `getStateTransitionSignals()` 调用换成 computed 名**

`v-for="(transition, index) in getStateTransitionSignals()"` → `v-for="(transition, index) in stateTransitionSignals"`

- [ ] **Step 3: transition-target 状态名翻译**

```vue
<span class="transition-state" :style="{ color: STATE_STYLES[transition.targetState]?.bgColor || '#1e293b' }">
  {{ STATE_KEYS[transition.targetState] ? $t(`quadrant.${STATE_KEYS[transition.targetState]}.name`) : transition.targetState }}
</span>
```

`<span class="transition-arrow">→</span>` 保持不变（箭头是符号，不翻译）。

- [ ] **Step 4: requirements / validation 标签**

```vue
<div class="requirements-label">{{ $t('section.transitions.requirements') }}</div>
…
<div class="validation-label">{{ $t('section.transitions.validationLabel') }}</div>
```

- [ ] **Step 5: signal-name / signal-desc / signal-details 用 transition 数据中的字段（已经被 Task 12 翻译过）**

无需修改 —— 这三个字段在 `stateTransitionSignals` computed 内已通过 `t()` 注入。

- [ ] **Step 6: 类型检查 + dev 验证 + 提交**

```bash
cd frontend && pnpm type-check
cd frontend && pnpm dev   # 浏览器人工核对：导言、需要条件/校验层标签、3 张 transition card 的目标状态名、信号文案都正确
```

```bash
git add frontend/src/App.vue
git commit -m "feat(i18n): migrate state transition signals section"
```

---

## Task 19: 迁移原始数据 section

**Files:**
- Modify: `frontend/src/App.vue` (template, 约 1338-1369 行)

- [ ] **Step 1: 替换标题、加载提示、来源/周期标签、字段标签**

```vue
<h2>{{ $t('section.rawData.title') }}</h2>
<div v-if="loading && Object.keys(data).length === 0" class="data-loading-overlay">
  <div class="data-loading-spinner">
    <div class="spinner-ring"></div>
    <div class="spinner-ring"></div>
    <div class="spinner-ring"></div>
    <div class="spinner-ring"></div>
  </div>
  <p class="data-loading-text">{{ $t('loading.rawData') }}</p>
</div>
<div class="details-grid" v-if="Object.keys(data).length > 0">
  <template v-for="(item, key) in data" :key="String(key)">
    <div class="detail-card">
      <div class="detail-label">
        <span class="detail-icon">{{ getDataIcon(key as string) }}</span>
        {{ $t(`data.${key}`) }}
      </div>
      <div class="detail-value" :class="key === 'etf_net_flow' && item.value > 0 ? 'positive' : key === 'etf_net_flow' && item.value < 0 ? 'negative' : ''">
        {{ formatValue(item.value, key as string) }}
      </div>
      <div class="detail-provider">{{ $t('data.sourceLabel') }} {{ item.provider }}</div>
      <div class="detail-description">
        <span v-if="item.metadata?.currency" class="detail-meta-item">{{ item.metadata.currency }}</span>
        <span v-if="item.metadata?.period" class="detail-meta-item">{{ $t('data.periodLabel') }} {{ item.metadata.period }}</span>
        <span v-if="item.metadata?.description" class="detail-meta-item">{{ item.metadata.description }}</span>
      </div>
    </div>
  </template>
</div>
```

注意：原模板中是 `{{ DATA_LABELS[key] || key }}`，现在改为 `{{ $t(\`data.${key}\`) }}`。如果 key 没在字典里，vue-i18n 会回落到 fallback 并打印警告，模板上显示 key 字符串本身（这是 Task 7/21 删除 `DATA_LABELS` 后的行为）。

- [ ] **Step 2: 类型检查 + dev 验证 + 提交**

```bash
cd frontend && pnpm type-check
cd frontend && pnpm dev   # 验证「原始数据」标题、loading、各字段名、来源/周期都翻译正确
```

```bash
git add frontend/src/App.vue
git commit -m "feat(i18n): migrate raw data section"
```

---

## Task 20: 全文扫描确认无遗漏中文（除注释）

**Files:**
- Inspect: `frontend/src/App.vue`

- [ ] **Step 1: 列出所有仍含中文的行**

```bash
cd /home/ivanjin/bullbear-dashboard
grep -nP '[\p{Han}]' frontend/src/App.vue | grep -v '^\s*//' | grep -v 'console.warn' | grep -v 'console.error'
```

- [ ] **Step 2: 检查每条结果**

预期剩余的中文应该**只有**这些类别：
- 后端枚举值字面量比对（`=== '牛市进攻'`、`=== '趋势多'`、`case '正常体温'` 等）
- 映射常量定义（`'牛市进攻': 'bullOffensive'` 等）
- HTML 注释（`<!-- 一、核心输出 -->` 等）
- 代码注释（`// 获取价格…`）

如果发现**用户可见**的中文字符串遗漏，按对应表添加到 zh.ts/en.ts 并改用 `$t(...)`。

- [ ] **Step 3: 提交（如果有修补）**

```bash
git add frontend/src/App.vue frontend/src/locales/zh.ts frontend/src/locales/en.ts
git commit -m "feat(i18n): cover remaining missed strings"
```

---

## Task 21: types.ts 清理

**Files:**
- Modify: `frontend/src/types.ts`

- [ ] **Step 1: 删除 DATA_LABELS、QUADRANT_MAP、QuadrantInfo**

把 types.ts 现有内容精简为：

```ts
export interface DataResult {
    data_type: string;
    value: number;
    provider: string;
    metadata?: Record<string, any>;
    timestamp?: string;
}

export interface ApiResponse {
    ok: boolean;
    data: Record<string, DataResult>;
}

export interface ValidationLayer {
    risk_thermometer: string;
    ath_drawdown: number;
    ath_price?: number | null;
    etf_accelerator: string;
    etf_net_flow: number | null;
    etf_aum: number | null;
    etf_flow_14d_sum?: number | null;
    etf_flow_pos_ratio?: number | null;
    etf_flow_recent_avg?: number | null;
    etf_flow_prev_avg?: number | null;
    etf_flow_trend?: 'up' | 'down' | 'flat' | null;
    etf_aum_trend?: 'up' | 'down' | 'flat' | null;
}

export interface StateResult {
    state: string;
    trend: string;
    funding: string;
    risk_level: string;
    confidence: number;
    validation: ValidationLayer;
    metadata?: Record<string, any>;
}

export interface StateApiResponse {
    ok: boolean;
    state: string;
    trend: string;
    funding: string;
    risk_level: string;
    confidence: number;
    validation: ValidationLayer;
    metadata?: Record<string, any>;
}

export const STATE_STYLES: Record<string, { color: string; bgColor: string }> = {
    '牛市进攻': { color: '#ffffff', bgColor: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)' },
    '牛市修复': { color: '#ffffff', bgColor: 'linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%)' },
    '熊市反弹': { color: '#ffffff', bgColor: 'linear-gradient(135deg, #feca57 0%, #ff9ff3 100%)' },
    '熊市消化': { color: '#ffffff', bgColor: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)' },
};

export const RISK_COLORS: Record<string, string> = {
    'HIGH': '🔴',
    'MEDIUM': '🟡',
    'LOW': '🟢',
};
```

（删除：`DATA_LABELS`、`QuadrantInfo`、`QUADRANT_MAP`。`STATE_STYLES` 的 keys 是后端中文标识符，保留不动。）

- [ ] **Step 2: 类型检查 + 提交**

```bash
cd frontend && pnpm type-check
```
预期：通过。如果报错引用了 `DATA_LABELS` 或 `QUADRANT_MAP`，回到 App.vue 把它们换成 i18n 调用。

```bash
git add frontend/src/types.ts
git commit -m "refactor(i18n): drop DATA_LABELS and QUADRANT_MAP from types.ts (moved to locale dictionaries)"
```

---

## Task 22: 生产构建 + 静态预览验证

**Files:**
- 无修改

- [ ] **Step 1: 生产构建**

```bash
cd frontend && pnpm build
```
预期：构建通过，输出 `dist/` 目录。

- [ ] **Step 2: 预览生产产物**

```bash
cd frontend && pnpm preview
```

打开预览地址（通常 http://localhost:4173/），验证：
- 中文模式：所有文案正常
- 切到 EN：所有文案变英文
- 刷新：选择保留
- 控制台无 vue-i18n missing key 警告

- [ ] **Step 3: 提交（无变更则跳过）**

无文件变更则不提交。

---

## Task 23: 人工测试矩阵

**Files:**
- 无修改（只验证）

按下列矩阵浏览器手动跑一遍。

- [ ] **场景 1：浏览器中文初次访问**
  - 清空 localStorage 后 `pnpm dev`
  - 浏览器语言设为 zh-CN
  - 预期：默认中文显示
  - `<html lang="zh-CN">`

- [ ] **场景 2：浏览器英文初次访问**
  - 清空 localStorage
  - 浏览器语言设为 en-US（DevTools → Sensors → Language）
  - 刷新页面
  - 预期：默认英文显示
  - `<html lang="en-US">`

- [ ] **场景 3：切换 + 持久化**
  - 中文模式下点 EN
  - 所有可见文字立即切英文（标题、副标题、刷新按钮、状态摘要、所有 section、所有 tooltip）
  - localStorage 写入 `locale: 'en'`
  - 刷新页面：仍为英文
  - 切回中文，刷新：仍为中文

- [ ] **场景 4：tooltip 内容核对**
  - 鼠标悬停在「风险等级」/「置信度」tooltip 上
  - 中英两种语言下完整显示

- [ ] **场景 5：四象限矩阵**
  - 4 个象限的名字、达成条件文案在两种语言下正确
  - 后端是哪一个 state，对应象限激活态高亮

- [ ] **场景 6：状态切换信号 3 张卡片**
  - 当前状态外的 3 个目标状态卡片
  - 信号名 / 描述 / 详情都在两种语言下正确翻译
  - active / pending 两种状态的 details 文案都已翻译

- [ ] **场景 7：原始数据**
  - 7 个 detail-card 的标签都翻译（BTC 价格 → BTC Price 等）
  - "来源:" / "Source:"、"周期:" / "Period:" 标签翻译

- [ ] **场景 8：边界 — 隐私模式 / localStorage 不可用**
  - Chrome 隐私窗口或 localStorage 禁用
  - 切换语言不会报错（仅不持久化）
  - 刷新后回到默认（按 navigator.language 检测）

- [ ] **场景 9：浏览器控制台**
  - 任一语言下从首页加载到所有 section 渲染完整
  - 控制台无 `[intlify]` warning（missing key 等）
  - 无任何 Vue runtime 错误

如全部通过，进行最终步骤。

---

## Task 24: 最终清理与提交摘要

**Files:**
- Optional modify: 修补遗留问题

- [ ] **Step 1: 检查未提交变更**

```bash
git status
```
应为 clean。

- [ ] **Step 2: 总览本次新增提交**

```bash
git log --oneline main..HEAD 2>/dev/null || git log --oneline -20
```
应能看到约 22 个提交，从 `chore(i18n): add vue-i18n@9` 开始到本任务。

- [ ] **Step 3: 把 commit 串汇报给用户**

把 `git log --oneline` 的本次相关提交贴给用户作为完成摘要。让用户决定是否合入主分支或开 PR。

---

## 整体完成判据

- [ ] `pnpm type-check` 通过
- [ ] `pnpm build` 通过
- [ ] 所有 23 个任务的验证步骤全部勾选
- [ ] 浏览器中英两种语言下，所有用户可见文案正确切换
- [ ] localStorage 持久化生效，刷新后语言保留
- [ ] 控制台无 vue-i18n 缺 key 警告
- [ ] `<html lang>` 随语言更新

---

## 备注

- 英文翻译质量：本计划提供的 en.ts 是初版翻译。在 Task 23 之前或之后，请你（用户）通读 en.ts，对金融术语（多头排列 / Bull stack 等）有更好措辞时直接修改 en.ts —— 类型系统会保护你不漏字段。
- 如果在 Task 7 的映射常量定义之后某个任务需要新映射（极少见，本计划已穷举），同样的方式追加。
- 如果 App.vue 在某个 section 迁移后明显膨胀（每行平均字符大幅上升），可考虑把那个 section 抽到独立子组件 —— 但这是后续重构的事，**不在本计划范围内**。
