# 加密市场状态机 - 代码实现逻辑

本文档详细说明当前代码的实际实现逻辑，与 `videologic.md` 中的视频逻辑说明相对应。

---

## 一、核心架构

状态机通过**两个输入维度**确定四象限状态，并通过**两个校验层**评估风险与加速度：

```
输入维度（确定象限）
├── 趋势结构 (Trend Structure)
└── 资金姿态 (Funding Posture)

校验层（评估风险）
├── 风险温度计 (Risk Thermometer)
└── ETF 加速器 (ETF Accelerator)
```

**实现位置**：`backend/bullbear_backend/state_machine/engine.py`

---

## 二、输入维度 1：趋势结构 (Trend Structure)

### 2.1 数据来源

- **MA50（中期节奏线）**：50日移动平均线
- **MA200（长期生命线）**：200日移动平均线
- **BTC 当前价格**：实时 BTC/USDT 价格

**数据提供方**：Binance API（公开免费）

**实现位置**：
- 数据获取：`backend/bullbear_backend/data/providers/binance.py`
- 数据源：`backend/bullbear_backend/data/sources/ma.py`

### 2.2 历史数据获取

**方法**：`_get_historical_data()`

- 从 Binance 获取最近 200 根日K线数据
- 计算历史 MA50 和 MA200 值（用于斜率计算）
- 提取历史价格数据（用于 ATH 计算）

**实现逻辑**：
```python
# 获取200根K线
klines = provider.get_klines(limit=200)
closing_prices = [float(candle[4]) for candle in klines]

# 计算历史MA值
for i in range(len(closing_prices)):
    if i >= 49:  # MA50需要至少50天
        ma50_history.append(sum(closing_prices[i-49:i+1]) / 50)
    if i >= 199:  # MA200需要至少200天
        ma200_history.append(sum(closing_prices[i-199:i+1]) / 200)
```

### 2.3 斜率计算

**方法**：`_calculate_slope(values, periods=10)`

**计算方法**：使用**线性回归**和**对数坐标**

**计算公式**：
```
1. 转换为对数坐标：log_values = [log(v) for v in values]
2. 线性回归：slope = Σ((x[i] - x_mean) × (log_y[i] - log_y_mean)) / Σ((x[i] - x_mean)²)
3. 转换为百分比：slope_percent = slope × 100
```

**实现细节**：
- 使用最近 10 天的历史 MA 值
- 将数值转换为对数坐标（`log(value)`）
- 在对数坐标上应用线性回归计算斜率
- 斜率表示对数空间中的每日变化率
- 转换为百分比：`斜率百分比 = 对数斜率 × 100`
- 返回单位：`%/天`（例如：0.1 表示每天平均上涨 0.1%）

**为什么使用对数坐标**：
- 对数坐标可以更好地处理不同价格水平下的变化
- 对数坐标的斜率表示百分比变化率，在不同价格水平下具有可比性
- 线性回归提供更稳定的斜率估计，减少异常值的影响

**代码实现**：
```python
# 转换为对数坐标
log_values = [math.log(v) for v in recent]

# 线性回归
x = list(range(n))  # 时间索引 [0, 1, 2, ..., n-1]
x_mean = sum(x) / n
log_y_mean = sum(log_values) / n

numerator = sum((x[i] - x_mean) * (log_values[i] - log_y_mean) for i in range(n))
denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
slope_log = numerator / denominator

# 转换为百分比
slope_percent = slope_log * 100
```

### 2.4 趋势判断

**方法**：`_determine_trend_with_slope()`

**判断规则**（基于 videologic.md）：

1. **多头排列（趋势多）**：
   - `价格在 MA200 上方` 且
   - `MA200 走平或向上（斜率 >= 0）`
   - **趋势质量判定**：`MA50 在 MA200 上方` 说明中期趋势跟得上，市场有推动力

2. **空头排列（趋势空）**：
   - `价格在 MA200 下方` 且
   - `MA200 趋势向下（斜率 < 0）`
   - **趋势质量判定**：`价格 < MA50 < MA200` 是典型的空头排列，此时的反弹仅视为压力位修复而非反转

3. **降级规则**（当斜率数据不足或条件不满足时）：
   - 如果历史数据不足 10 天，斜率设为 0.0
   - 如果价格在 MA200 上方但 MA200 下降，仍判定为趋势多（但较弱）
   - 如果价格在 MA200 下方但 MA200 上升，仍判定为趋势空（但较弱）

**实现位置**：`backend/bullbear_backend/state_machine/engine.py:249-291`

---

## 三、输入维度 2：资金姿态 (Funding Posture)

### 3.1 数据来源

- **稳定币市值 (Stablecoin Market Cap)**：USDT、USDC、DAI 等主要稳定币的总市值
- **加密总市值 (Total Market Cap)**：所有加密货币的总市值

**数据提供方**：CoinGecko API（公开免费）

**实现位置**：
- 数据获取：`backend/bullbear_backend/data/providers/coingecko.py`
- 数据源：`backend/bullbear_backend/data/sources/stablecoin_market_cap.py`、`total_market_cap.py`

### 3.2 资金姿态判断

**方法**：`_determine_funding()`

**判断逻辑**：根据 videologic.md，使用四种组合模式判断资金姿态

**计算公式**：
```
稳定币占比 = (稳定币市值 / 加密总市值) × 100%
稳定币斜率 = 使用线性回归和对数坐标计算稳定币市值的历史斜率
总市值斜率 = 使用线性回归和对数坐标计算总市值的历史斜率
```

**四种组合模式**（基于 videologic.md）：

1. **Stable ↑ + Total ↑ → 增量进攻（偏进攻/偏牛）**
   - 稳定币市值上升（斜率 > 0）
   - 总市值上升（斜率 > 0）
   - 结果：`资金进攻`

2. **Stable ↓ + Total ↑ → 强力进攻（最强进攻状态）**
   - 稳定币市值下降（斜率 < 0）
   - 总市值上升（斜率 > 0）
   - 结果：`资金进攻`

3. **Stable ↑ + Total ↓ → 去风险防守（典型去风险/防守）**
   - 稳定币市值上升（斜率 > 0）
   - 总市值下降（斜率 < 0）
   - 结果：`资金防守`

4. **Stable ↓ + Total ↓ → 深度防守/撤退（更强的防守/彻底熊）**
   - 稳定币市值下降（斜率 < 0）
   - 总市值下降（斜率 < 0）
   - 结果：`资金防守`

**历史数据管理**：
- 使用类级别的缓存存储历史稳定币市值和总市值数据
- 最多保存最近 30 天的数据
- 每次 `evaluate()` 调用时更新缓存

**降级处理**：
- 如果历史数据不足 7 天，使用简化判断：
  - `稳定币占比 < 8.0%` → 资金进攻
  - `稳定币占比 >= 8.0%` → 资金防守

**实现说明**：
- 代码已实现完整的历史数据判断逻辑（基于斜率计算）
- 使用类级别的缓存存储历史稳定币市值和总市值数据
- 只有在历史数据不足 7 天时才会降级到阈值判断

**实现位置**：`backend/bullbear_backend/state_machine/engine.py:306-381`

---

## 四、校验层 1：风险温度计 (Risk Thermometer)

### 4.1 数据来源

- **ATH（历史最高价）**：从历史价格数据中提取的最高价格
- **BTC 当前价格**：实时 BTC/USDT 价格

### 4.2 ATH 回撤率计算

**方法**：`_calculate_risk_thermometer()`

**计算公式**：
```
ATH回撤率 = (ATH - 当前价格) / ATH × 100%
```

**实现逻辑**：
1. 从历史价格数据中找出最高价（包括当前价格）
2. 如果历史数据为空，使用当前价格作为 ATH
3. 计算回撤率（正值表示当前价格低于 ATH）

**风险等级判断**（基于 videologic.md）：
- `< 20%`：**正常体温**（36-37度，可大胆进攻）
- `20% ~ 35%`：**低/中烧**（37-39度，市场难受，需要修复）
- `> 35%`：**高烧威胁**（熊市主导概率大增）
- `> 60%`：**生命体征极差**（深出清阶段，处于快死透的区间）

**实现位置**：`backend/bullbear_backend/state_machine/engine.py:269-318`

---

## 五、校验层 2：ETF 加速器 (ETF Accelerator)

### 5.1 数据来源

- **ETF 净资金流 (Net Flow)**：从 Farside Investors 网站抓取
- **ETF 资产管理规模 (AUM)**：从 yfinance API 获取

**数据提供方**：
- Net Flow：Farside Investors（通过 `cloudscraper` 和 `pandas.read_html()` 抓取）
- AUM：yfinance（汇总 10 个主要比特币现货 ETF 的 `totalAssets`）

**实现位置**：
- 数据获取：`backend/bullbear_backend/data/providers/farside.py`
- 数据源：`backend/bullbear_backend/data/sources/etf_net_flow.py`、`etf_aum.py`

### 5.2 ETF 加速器判断

**方法**：`_calculate_etf_accelerator()`

**判断逻辑**：

#### 5.2.1 数据不足时的降级处理

如果历史数据不足 7 天：
- `|净资金流| < $10M` → **钝化**
- `净资金流 > 0` → **顺风**
- `净资金流 < 0` → **逆风**

#### 5.2.2 持续流入/流出判断（需要至少 7 天历史数据）

**顺风（持续流入）**：
- 至少 14 天（2周）持续流入
- 70% 以上的天数为正流入
- 最近一周平均流入为正

**逆风（持续流出）**：
- 至少 14 天（2周）持续流出
- 70% 以上的天数为负流出
- 最近一周平均流出为负

#### 5.2.3 钝化判断（流出速度减缓）

如果历史数据 >= 14 天：
- 比较前半段和后半段的平均流出
- 如果后半段平均流出 < 前半段平均流出 × 50%，判定为**钝化**

如果平均净流入接近 0（`|平均净流入| < $10M`）：
- 判定为**钝化**

#### 5.2.4 混合信号处理

如果以上条件都不满足：
- 使用当天的净资金流作为判断依据
- `净资金流 > 0` → **顺风**
- `净资金流 < 0` → **逆风**

**实现位置**：`backend/bullbear_backend/state_machine/engine.py:435-541`

---

## 六、核心切换逻辑（何时转牛？）

**说明**：此部分基于 videologic.md 中的"核心切换逻辑"，描述了从"熊市消化"转为更健康状态需要观察的信号。**注意**：当前代码实现中尚未实现这些切换逻辑的自动检测，这些信号仅供参考和未来扩展。

### 6.1 转牛信号（需要至少 3 个同时出现）

根据 videologic.md，从"熊市消化"转为更健康状态需要至少看到以下信号中的 **3 个同时出现**：

1. **收复均线**：
   - 比特币先收复 MA50，再收复 MA200 并站稳
   - 判断条件：`价格 > MA50` 且 `价格 > MA200` 且 `MA200 斜率 >= 0`

2. **止跌确认**：
   - 价格止跌并重新站回 MA50
   - 判断条件：`价格 > MA50` 且 `价格斜率 > 0`（价格开始上升）

3. **资金回流**：
   - 稳定币市值停止上升，并趋势性走平或回落（说明资金愿意重新承担风险）
   - 判断条件：`稳定币市值斜率 <= 0`（稳定币市值不再上升）

4. **ETF 转正**：
   - ETF 从持续净流出转为持续净流入超过 **2-4 周**，且 **AUM 回升**
   - 判断条件：
     - `ETF 加速器状态 = "顺风"`（持续净流入）
     - `AUM 当前值 > AUM 历史平均值`（AUM 回升）

### 6.2 未来实现方向

这些切换逻辑可以作为状态机的扩展功能，用于：
- 检测市场状态的转换信号
- 提供更细粒度的市场状态判断
- 生成市场转换预警

**参考位置**：`docs/videologic.md` 第三部分

---

## 七、状态映射

### 6.1 四象限映射

**方法**：`_map_to_state()`

| 趋势结构 | 资金姿态 | 市场状态 | 中文名称 |
|---------|---------|---------|---------|
| BULLISH | OFFENSIVE | BULL_OFFENSIVE | 牛市进攻 |
| BULLISH | DEFENSIVE | BULL_DEFENSIVE | 牛市修复 |
| BEARISH | OFFENSIVE | BEAR_OFFENSIVE | 熊市反弹 |
| BEARISH | DEFENSIVE | BEAR_DEFENSIVE | 熊市消化 |

**实现位置**：`backend/bullbear_backend/state_machine/engine.py:428-439`

### 7.2 风险等级映射

**方法**：`_get_risk_level()`

| 市场状态 | 风险等级 |
|---------|---------|
| BULL_OFFENSIVE | HIGH |
| BULL_DEFENSIVE | MEDIUM |
| BEAR_OFFENSIVE | MEDIUM |
| BEAR_DEFENSIVE | LOW |

**实现位置**：`backend/bullbear_backend/state_machine/engine.py:556-564`

---

## 八、置信度计算

### 8.1 置信度公式

**方法**：`_calculate_confidence()`

**计算公式**：
```
趋势置信度 = min(1.0, (MA排列清晰度 × 5 + 斜率置信度 × 0.5))
资金置信度 = min(1.0, |稳定币占比变化| / 8.0)
总置信度 = min(1.0, (趋势置信度 + 资金置信度) / 2.0)
```

**详细计算**：

1. **MA 排列清晰度**：
   ```
   MA排列清晰度 = |MA50 - MA200| / MA200
   ```

2. **斜率置信度**：
   ```
   平均斜率强度 = (|MA50斜率| + |MA200斜率|) / 2
   斜率置信度 = min(1.0, 平均斜率强度 / 0.5)
   ```
   （0.5%/天 = 最大置信度）

3. **资金置信度**：
   ```
   资金强度 = |稳定币占比变化| / 8.0
   资金置信度 = min(1.0, 资金强度)
   ```

**实现位置**：`backend/bullbear_backend/state_machine/engine.py:566-596`

---

## 九、数据流程

### 9.1 主流程

**方法**：`evaluate()`

1. **获取当前数据**：
   - BTC 价格
   - MA50、MA200
   - 总市值、稳定币市值

2. **获取历史数据**：
   - 历史价格（用于 ATH 计算）
   - 历史 MA50、MA200（用于斜率计算）

3. **计算趋势结构**：
   - 计算 MA50、MA200 斜率
   - 判断趋势方向（多头/空头）

4. **计算资金姿态**：
   - 计算稳定币占比
   - 判断资金姿态（进攻/防守）

5. **映射到市场状态**：
   - 根据趋势和资金姿态确定四象限状态

6. **计算校验层**：
   - 风险温度计（ATH 回撤率）
   - ETF 加速器（净资金流、AUM）

7. **计算置信度**：
   - 基于趋势清晰度和资金信号强度

8. **返回结果**：
   - `StateResult` 对象，包含所有计算结果

**实现位置**：`backend/bullbear_backend/state_machine/engine.py:41-116`

---

## 十、关键参数

### 10.1 斜率计算参数

- **历史数据周期**：10 天（`periods=10`）
- **最小历史数据要求**：10 天（用于斜率计算）

### 10.2 资金姿态参数

- **稳定币占比阈值**：8.0%（仅用于历史数据不足时的降级判断）
- **历史数据要求**：至少 7 天（用于斜率计算）
- **判断规则**：基于历史数据斜率计算，使用四种组合模式

### 10.3 ETF 加速器参数

- **历史数据周期**：30 天（用于趋势分析）
- **最小持续天数**：14 天（2周）
- **一致性阈值**：70%（同方向天数占比）
- **钝化阈值**：±$10M（净资金流绝对值）

### 10.4 风险温度计参数（基于 videologic.md）

- **正常体温**：< 20%（36-37度，可大胆进攻）
- **低/中烧**：20% ~ 35%（37-39度，市场难受，需要修复）
- **高烧威胁**：> 35%（熊市主导概率大增）
- **生命体征极差**：> 60%（深出清阶段，处于快死透的区间）

---

## 十一、数据源说明

### 11.1 BTC 价格和 MA

- **提供方**：Binance API
- **端点**：`/api/v3/klines`
- **数据源类**：`BinanceProvider`
- **实现位置**：`backend/bullbear_backend/data/providers/binance.py`

### 11.2 市场市值

- **提供方**：CoinGecko API
- **端点**：`/api/v3/global`
- **数据源类**：`CoinGeckoProvider`
- **实现位置**：`backend/bullbear_backend/data/providers/coingecko.py`

### 11.3 ETF 数据

- **Net Flow**：
  - **提供方**：Farside Investors
  - **URL**：`https://farside.co.uk/bitcoin-etf-flow-all-data/`
  - **抓取方法**：`cloudscraper` + `pandas.read_html()`
  
- **AUM**：
  - **提供方**：yfinance
  - **ETF 列表**：IBIT, FBTC, BITB, ARKB, BTCO, EZBC, BRRR, HODL, BTCW, GBTC
  - **数据字段**：`totalAssets`

**实现位置**：`backend/bullbear_backend/data/providers/farside.py`

---

## 十二、与视频逻辑的差异

### 12.1 斜率计算

- **视频逻辑**：百分比变化率 `(当前值 - N天前的值) / N天前的值 × 100%`
- **代码实现**：百分比变化率，归一化为每天的变化率
- **差异**：代码实现与视频逻辑一致，但增加了归一化处理

### 12.2 资金姿态判断

- **视频逻辑**：需要历史数据计算稳定币占比变化，使用四种组合模式
- **代码实现**：已实现完整的历史数据判断逻辑，使用斜率计算稳定币和总市值的变化趋势，应用四种组合模式
- **差异**：代码实现与视频逻辑一致，已支持历史数据判断

### 12.3 ETF 加速器

- **视频逻辑**：持续流入/流出需要 2-4 周
- **代码实现**：至少 14 天（2周），70% 天数同方向
- **差异**：代码实现与视频逻辑基本一致

### 12.4 核心切换逻辑

- **视频逻辑**：列出了4个转牛信号，需要至少3个同时出现
- **代码实现**：当前代码中尚未实现这些切换逻辑的自动检测
- **差异**：这些信号仅供参考和未来扩展，不在当前状态机的核心判断逻辑中

---

## 十三、代码文件结构

```
backend/bullbear_backend/
├── state_machine/
│   ├── engine.py          # 状态机核心逻辑
│   └── types.py           # 类型定义
├── data/
│   ├── fetcher.py         # 数据获取器
│   ├── providers/         # 数据提供方
│   │   ├── binance.py     # Binance API
│   │   ├── coingecko.py   # CoinGecko API
│   │   └── farside.py     # Farside Investors + yfinance
│   └── sources/           # 数据源
│       ├── btc_price.py
│       ├── ma.py
│       ├── total_market_cap.py
│       ├── stablecoin_market_cap.py
│       ├── etf_net_flow.py
│       └── etf_aum.py
└── main.py                # FastAPI 入口
```

---

**最后更新**：2025年

**版本**：1.0

