<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { type DataResult, type StateApiResponse, STATE_STYLES, RISK_COLORS } from './types';
import TradingViewChart from './components/TradingViewChart.vue';
import { useI18n } from 'vue-i18n';
import { setLocale, type AppLocale } from './locales';

const { t } = useI18n();

function onSetLocale(loc: AppLocale) {
  setLocale(loc);
}

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

// 检测是否为开发环境（localhost）
const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE_URL = isDevelopment ? 'http://localhost:8000' : '';

const data = ref<Record<string, DataResult>>({});
const stateData = ref<StateApiResponse | null>(null);
const loading = ref(true);
const stateLoading = ref(false);
const initialLoad = ref(true);
const error = ref<string | null>(null);

const DATA_TYPES = ['btc_price', 'total_market_cap', 'stablecoin_market_cap', 'ma50', 'ma200', 'etf_net_flow', 'etf_aum'];

// 从静态文件读取数据
const fetchDataFromStatic = async () => {
  try {
    const response = await fetch(`${import.meta.env.BASE_URL}data/all_data.json`);
    if (!response.ok) {
      throw new Error(`Failed to fetch static data: ${response.status}`);
    }
    const json = await response.json();
    if (json.ok && json.data) {
      // 将数据转换为 DataResult 格式
      for (const [type, result] of Object.entries(json.data)) {
        data.value[type] = result as DataResult;
      }
      return true;
    }
    return false;
  } catch (e: any) {
    console.warn('无法从静态文件读取数据:', e);
    return false;
  }
};

// 从API获取数据
const fetchDataFromAPI = async () => {
  try {
    const promises = DATA_TYPES.map(async (type) => {
      const response = await fetch(`${API_BASE_URL}/api/data/${type}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch ${type}: ${response.status}`);
      }
      const json = await response.json();
      data.value[type] = json as DataResult;
      return { type, result: json as DataResult };
    });
    await Promise.all(promises);
    return true;
  } catch (e: any) {
    console.warn('无法从API获取数据:', e);
    return false;
  }
};

const fetchData = async () => {
  error.value = null;
  
  // 如果是开发环境，优先使用API；否则使用静态文件
  if (isDevelopment) {
    const apiSuccess = await fetchDataFromAPI();
    if (!apiSuccess) {
      // API失败时尝试静态文件
      await fetchDataFromStatic();
    }
  } else {
    // 生产环境优先使用静态文件
    const staticSuccess = await fetchDataFromStatic();
    if (!staticSuccess) {
      error.value = t('errors.dataLoadFailed');
    }
  }
};

// 从静态文件读取状态
const fetchStateFromStatic = async () => {
  try {
    const response = await fetch(`${import.meta.env.BASE_URL}data/state.json`);
    if (!response.ok) {
      throw new Error(`Failed to fetch static state: ${response.status}`);
    }
    const json = await response.json();
    if (json.ok) {
      stateData.value = json as StateApiResponse;
      return true;
    }
    return false;
  } catch (e: any) {
    console.warn('无法从静态文件读取状态:', e);
    return false;
  }
};

// 从API获取状态
const fetchStateFromAPI = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/state`);
    if (!response.ok) {
      throw new Error(`Failed to fetch state: ${response.status}`);
    }
    const json = await response.json();
    stateData.value = json as StateApiResponse;
    return true;
  } catch (e: any) {
    console.warn('无法从API获取状态:', e);
    return false;
  }
};

const fetchState = async () => {
  stateLoading.value = true;
  try {
    // 如果是开发环境，优先使用API；否则使用静态文件
    if (isDevelopment) {
      const apiSuccess = await fetchStateFromAPI();
      if (!apiSuccess) {
        // API失败时尝试静态文件
        await fetchStateFromStatic();
      }
    } else {
      // 生产环境优先使用静态文件
      const staticSuccess = await fetchStateFromStatic();
      if (!staticSuccess) {
        if (!error.value) {
          error.value = t('errors.stateLoadFailed');
        }
      }
    }
  } catch (e: any) {
    console.error('Failed to fetch state:', e);
    if (!error.value) {
      error.value = `${t('errors.stateFetchPrefix')}: ${e.message || t('errors.unknownError')}`;
    }
  } finally {
    stateLoading.value = false;
  }
};

// 格式化 ETF 数据，显示 B（十亿）或 T（万亿）单位
const formatETFValue = (value: number): string => {
  const absValue = Math.abs(value);
  if (absValue >= 1_000_000_000_000) {
    // 万亿 (Trillion)
    const trillions = absValue / 1_000_000_000_000;
    return `${value >= 0 ? '+' : '-'}$${trillions.toFixed(2)}T`;
  } else if (absValue >= 1_000_000_000) {
    // 十亿 (Billion)
    const billions = absValue / 1_000_000_000;
    return `${value >= 0 ? '+' : '-'}$${billions.toFixed(2)}B`;
  } else if (absValue >= 1_000_000) {
    // 百万 (Million)
    const millions = absValue / 1_000_000;
    return `${value >= 0 ? '+' : '-'}$${millions.toFixed(2)}M`;
  } else {
    return `${value >= 0 ? '+' : '-'}$${absValue.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
  }
};

const formatRatioPercent = (value: number | null | undefined, digits = 1): string => {
  if (value === null || value === undefined) return '—';
  return `${(value * 100).toFixed(digits)}%`;
};

const getTrendBadge = (trend: string | null | undefined) => {
  if (trend === 'up')   return { text: t('trendBadge.up'),      className: 'positive', icon: '📈' };
  if (trend === 'down') return { text: t('trendBadge.down'),    className: 'negative', icon: '📉' };
  if (trend === 'flat') return { text: t('trendBadge.flat'),    className: 'neutral',  icon: '➖' };
  return { text: t('trendBadge.unknown'), className: 'neutral', icon: '—' };
};

const formatValue = (value: number, type: string) => {
  if (type.includes('market_cap') || type.includes('etf_aum')) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
      notation: 'compact',
    }).format(value);
  }
  if (type.includes('etf_net_flow')) {
    // ETF net flow can be negative, show with sign
    const sign = value >= 0 ? '+' : '';
    return `${sign}$${Math.abs(value).toLocaleString('en-US', { maximumFractionDigits: 0, notation: 'compact' })}`;
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
};

const formatPercent = (value: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value / 100);
};

const getSlopeEmoji = (slope: number) => {
  if (slope > 0) return '📈';
  if (slope < 0) return '📉';
  return '➡️';
};

const getDataIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    btc_price: '₿',
    total_market_cap: '🌐',
    stablecoin_market_cap: '💵',
    ma50: '📈',
    ma200: '📊',
    etf_net_flow: '📊',
    etf_aum: '💰',
  };
  return iconMap[type] || '📋';
};

const getRiskThermometerColor = (thermometer: string) => {
  switch (thermometer) {
    case '正常体温':
      return '#10b981';
    case '低/中烧':
      return '#f59e0b';
    case '高烧威胁':
      return '#ef4444';
    case '生命体征极差':
      return '#dc2626';
    default:
      return '#6b7280';
  }
};

// 价格与均线（MA50/MA200）的关系
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

// 趋势结构结论
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

// 趋势质量判定
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

// 资金组合模式信息（基于斜率）
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

// 计算状态切换信号（从当前状态切换到目标状态）
interface TransitionSignal {
  name: string;
  description: string;
  active: boolean;
  details: string;
}

interface Transition {
  targetState: string;
  targetTrend: string;
  targetFunding: string;
  signals: TransitionSignal[];
  validationSignals: TransitionSignal[]; // 校验层信号，不计入需要条件
  activeCount: number;
  totalCount: number;
  progress: number;
}

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

const getETFAcceleratorColor = (accelerator: string) => {
  switch (accelerator) {
    case '顺风':
      return '#10b981';
    case '逆风':
      return '#ef4444';
    case '钝化':
      return '#6b7280';
    default:
      return '#6b7280';
  }
};

const loadAllData = async () => {
  loading.value = true;
  initialLoad.value = true;
  error.value = null;
  data.value = {};
  stateData.value = null;
  
  // 并行执行，不互相等待，让数据可以逐步显示
  const statePromise = fetchState().then(() => {
    // 状态数据加载完成后立即隐藏初始加载动画，让内容可以显示
    initialLoad.value = false;
  });
  
  const dataPromise = fetchData();
  
  // 等待两个请求都完成
  try {
    await Promise.all([statePromise, dataPromise]);
  } finally {
    loading.value = false;
  }
};

/** 从 stateData.state 派生四象限显示信息，UI 唯一消费入口 */
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

onMounted(() => {
  loadAllData();
});
</script>

<template>
  <div class="container">
    <header>
      <h1>📊 {{ $t('app.title') }}</h1>
      <p class="subtitle">{{ $t('app.subtitle') }}</p>
      <button @click="loadAllData" :disabled="loading" class="refresh-btn">
        {{ loading ? $t('actions.loading') : `${$t('actions.refreshIcon')} ${$t('actions.refresh')}` }}
      </button>
      <div v-if="currentQuadrant" class="status-summary">
        <p class="status-primary">{{ $t('status.currentLabel') }}{{ currentQuadrant.name }}</p>
        <p class="status-secondary">{{ currentQuadrant.trend }}{{ $t('status.separator') }}{{ currentQuadrant.flow }}</p>
      </div>
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
    </header>

    <main>
      <div v-if="error" class="error">
        {{ error }}
      </div>

      <!-- 初始加载动画 -->
      <div v-if="initialLoad && !stateData" class="loading-container">
        <div class="loading-spinner">
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
        </div>
        <div class="loading-text">
          <p class="loading-title">{{ $t('loading.title') }}</p>
          <p class="loading-subtitle">{{ $t('loading.subtitle') }}</p>
        </div>
      </div>

      <!-- 状态机展示 -->
      <div class="state-section">
        <!-- 当前状态概览 -->
        <div v-if="stateData && stateData.ok" class="state-header fade-in">
          <div class="state-box" :style="{ background: STATE_STYLES[stateData.state]?.bgColor || '#1e293b' }">
            <div class="state-name">{{ STATE_KEYS[stateData.state] ? $t(`quadrant.${STATE_KEYS[stateData.state]}.name`) : stateData.state }}</div>
            <div class="state-details">
              {{ TREND_KEYS[stateData.trend] ? $t(`trend.${TREND_KEYS[stateData.trend]}`) : stateData.trend }}
              | {{ FUNDING_KEYS[stateData.funding] ? $t(`funding.${FUNDING_KEYS[stateData.funding]}`) : stateData.funding }}
            </div>
          </div>
          <div class="state-metrics">
            <div class=”metric-item”>
              <span class=”metric-label”>{{ $t('metric.risk.label') }}</span>
              <span class=”metric-value”>{{ RISK_COLORS[stateData.risk_level] || '⚪' }} {{ stateData.risk_level }}</span>
              <div class=”metric-tooltip”>
                <span class=”tooltip-icon”>ℹ️</span>
                <div class=”tooltip-content”>
                  <strong>{{ $t('metric.risk.tooltipTitle') }}</strong><br>
                  • {{ $t('metric.risk.high') }}<br>
                  • {{ $t('metric.risk.medium') }}<br>
                  • {{ $t('metric.risk.low') }}
                </div>
              </div>
            </div>
            <div class=”metric-item”>
              <span class=”metric-label”>{{ $t('metric.confidence.label') }}</span>
              <span class=”metric-value”>{{ (stateData.confidence * 100).toFixed(1) }}%</span>
              <div class=”metric-tooltip”>
                <span class=”tooltip-icon”>ℹ️</span>
                <div class=”tooltip-content”>
                  <strong>{{ $t('metric.confidence.tooltipTitle') }}</strong><br>
                  • {{ $t('metric.confidence.item1') }}<br>
                  • {{ $t('metric.confidence.item2') }}<br>
                  • {{ $t('metric.confidence.item3') }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 一、核心输出：四象限状态矩阵 -->
        <div v-if="stateData && stateData.ok" class="quadrant-section fade-in">
          <div class="section-header">
            <span class="section-badge core-output">{{ $t('badge.coreOutput') }}</span>
            <h2>{{ $t('section.quadrant.title') }}</h2>
          </div>
          <p class="section-description">{{ $t('section.quadrant.description') }}</p>
          <div class="quadrant-chart-container">
            <div class="quadrant-chart">
              <!-- Y轴标签（趋势方向） -->
              <div class="axis-y-label top">{{ $t('axis.trendUp') }}</div>
              <div class="axis-y-label bottom">{{ $t('axis.trendDown') }}</div>

              <!-- X轴标签（资金姿态） -->
              <div class="axis-x-label left">{{ $t('axis.fundingLeft') }}</div>
              <div class="axis-x-label right">{{ $t('axis.fundingRight') }}</div>
              
              <!-- 中心分割线（仅水平线） -->
              <div class="axis-line horizontal"></div>
              
              <!-- 四象限 -->
              <div class="quadrant-wrapper">
                <!-- 左上角：趋势多 + 资金防守 = 牛市修复 -->
                <div
                  class="quadrant quadrant-2"
                  :class="{ active: stateData.state === '牛市修复' }"
                >
                  <div class="quadrant-content">
                    <div class="quadrant-icon">📈</div>
                    <div class="quadrant-name">{{ $t('quadrant.bullRecovery.name') }}</div>
                    <div class="quadrant-risk">MEDIUM RISK</div>
                    <!-- 达成条件指示灯 -->
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
                  </div>
                  <div v-if="stateData.state === '牛市修复'" class="active-indicator">
                    <div class="pulse-ring"></div>
                    <div class="pulse-ring delay-1"></div>
                    <div class="pulse-ring delay-2"></div>
                  </div>
                </div>
                
                <!-- 右上角：趋势多 + 资金进攻 = 牛市进攻 -->
                <div
                  class="quadrant quadrant-1"
                  :class="{ active: stateData.state === '牛市进攻' }"
                >
                  <div class="quadrant-content">
                    <div class="quadrant-icon">🔥</div>
                    <div class="quadrant-name">{{ $t('quadrant.bullOffensive.name') }}</div>
                    <div class="quadrant-risk">HIGH RISK</div>
                    <!-- 达成条件指示灯 -->
                    <div class="condition-indicator">
                      <div class="condition-item" :class="{ met: stateData.trend === '趋势多' }">
                        <span class="condition-icon">{{ stateData.trend === '趋势多' ? '✅' : '⏳' }}</span>
                        <span class="condition-text">{{ $t('trend.bull') }}</span>
                      </div>
                      <div class="condition-item" :class="{ met: stateData.funding === '资金进攻' }">
                        <span class="condition-icon">{{ stateData.funding === '资金进攻' ? '✅' : '⏳' }}</span>
                        <span class="condition-text">{{ $t('funding.offensive') }}</span>
                      </div>
                    </div>
                  </div>
                  <div v-if="stateData.state === '牛市进攻'" class="active-indicator">
                    <div class="pulse-ring"></div>
                    <div class="pulse-ring delay-1"></div>
                    <div class="pulse-ring delay-2"></div>
                  </div>
                </div>
                
                <!-- 左下角：趋势空 + 资金防守 = 熊市消化 -->
                <div
                  class="quadrant quadrant-4"
                  :class="{ active: stateData.state === '熊市消化' }"
                >
                  <div class="quadrant-content">
                    <div class="quadrant-icon">🩸</div>
                    <div class="quadrant-name">{{ $t('quadrant.bearDigest.name') }}</div>
                    <div class="quadrant-risk">LOW RISK</div>
                    <!-- 达成条件指示灯 -->
                    <div class="condition-indicator">
                      <div class="condition-item" :class="{ met: stateData.trend === '趋势空' }">
                        <span class="condition-icon">{{ stateData.trend === '趋势空' ? '✅' : '⏳' }}</span>
                        <span class="condition-text">{{ $t('trend.bear') }}</span>
                      </div>
                      <div class="condition-item" :class="{ met: stateData.funding === '资金防守' }">
                        <span class="condition-icon">{{ stateData.funding === '资金防守' ? '✅' : '⏳' }}</span>
                        <span class="condition-text">{{ $t('funding.defensive') }}</span>
                      </div>
                    </div>
                  </div>
                  <div v-if="stateData.state === '熊市消化'" class="active-indicator">
                    <div class="pulse-ring"></div>
                    <div class="pulse-ring delay-1"></div>
                    <div class="pulse-ring delay-2"></div>
                  </div>
                </div>
                
                <!-- 右下角：趋势空 + 资金进攻 = 熊市反弹 -->
                <div
                  class="quadrant quadrant-3"
                  :class="{ active: stateData.state === '熊市反弹' }"
                >
                  <div class="quadrant-content">
                    <div class="quadrant-icon">⚡</div>
                    <div class="quadrant-name">{{ $t('quadrant.bearBounce.name') }}</div>
                    <div class="quadrant-risk">MEDIUM RISK</div>
                    <!-- 达成条件指示灯 -->
                    <div class="condition-indicator">
                      <div class="condition-item" :class="{ met: stateData.trend === '趋势空' }">
                        <span class="condition-icon">{{ stateData.trend === '趋势空' ? '✅' : '⏳' }}</span>
                        <span class="condition-text">{{ $t('trend.bear') }}</span>
                      </div>
                      <div class="condition-item" :class="{ met: stateData.funding === '资金进攻' }">
                        <span class="condition-icon">{{ stateData.funding === '资金进攻' ? '✅' : '⏳' }}</span>
                        <span class="condition-text">{{ $t('funding.offensive') }}</span>
                      </div>
                    </div>
                  </div>
                  <div v-if="stateData.state === '熊市反弹'" class="active-indicator">
                    <div class="pulse-ring"></div>
                    <div class="pulse-ring delay-1"></div>
                    <div class="pulse-ring delay-2"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 二、判断规则与数学公式 -->
        
        <!-- 硬规则1：趋势结构 -->
        <div v-if="stateData && stateData.ok && stateData.metadata" class="trend-analysis-section fade-in">
          <div class="section-header">
            <span class="section-badge hard-rule">{{ $t('section.trendStructure.badge') }}</span>
            <h2>{{ $t('section.trendStructure.title') }}</h2>
          </div>
          <p class="section-description">{{ $t('section.trendStructure.description') }}</p>
          
          <!-- 趋势结构结论 -->
          <div v-if="trendConclusion" class="trend-conclusion-card">
            <div class="trend-conclusion-header">
              <span class="trend-conclusion-icon">{{ trendConclusion?.icon }}</span>
              <h3>{{ $t('section.trendStructure.conclusionTitle') }}</h3>
            </div>
            <div class="trend-conclusion-content">
              <div class="trend-conclusion-name" :style="{ color: trendConclusion?.color }">
                {{ trendConclusion?.name }}
              </div>
              <div class="trend-conclusion-desc">
                {{ trendConclusion?.description }}
              </div>
              <div v-if="stateData.trend" class="trend-conclusion-trend">
                {{ $t('section.trendStructure.systemJudgment') }}<strong>{{ TREND_KEYS[stateData.trend] ? $t(`trend.${TREND_KEYS[stateData.trend]}`) : stateData.trend }}</strong>
              </div>
            </div>
          </div>
          
          <div class="trend-analysis-grid">
            <div class="trend-card">
              <div class="trend-card-header">
                <span class="trend-icon">📊</span>
              <h3>{{ $t('trendCard.priceMARelation') }}</h3>
              </div>
              <div v-if="priceMARelation" class="trend-content">
                <div class="trend-status" :class="priceMARelation?.statusClass">
                  <span class="trend-indicator">
                    {{ priceMARelation?.statusClass === 'positive' ? '📈' : priceMARelation?.statusClass === 'negative' ? '📉' : '⚖️' }}
                  </span>
                  <span class="trend-text">
                    {{ priceMARelation?.statusText }}
                  </span>
                </div>
                <div class="trend-detail">
                  {{ $t('trendCard.diff50Label') }}: {{ (() => { const rel = priceMARelation; if (!rel) return '0.00'; return (rel.diff50 > 0 ? '+' : '') + rel.diff50.toFixed(2); })() }}%
                </div>
                <div class="trend-detail">
                  {{ $t('trendCard.diff200Label') }}: {{ (() => { const rel = priceMARelation; if (!rel) return '0.00'; return (rel.diff200 > 0 ? '+' : '') + rel.diff200.toFixed(2); })() }}%
                </div>
                <div class="trend-description">
                  {{ priceMARelation?.summary }}
                </div>
              </div>
              <div v-else class="trend-content">
                <div class="trend-unavailable">{{ $t('trendCard.unavailable') }}</div>
              </div>
            </div>
            
            <div class="trend-card">
              <div class="trend-card-header">
                <span class="trend-icon">📈</span>
                <h3>{{ $t('trendCard.ma50Trend') }}</h3>
              </div>
              <div v-if="stateData.metadata?.ma50_slope !== undefined" class="trend-content">
                <div class="trend-status" :class="stateData.metadata.ma50_slope >= 0 ? 'positive' : 'negative'">
                  <span class="trend-indicator">{{ getSlopeEmoji(stateData.metadata.ma50_slope) }}</span>
                  <span class="trend-text">
                    {{ stateData.metadata.ma50_slope >= 0 ? $t('trendCard.ma50FlatUp') : $t('trendCard.ma50Down') }}
                  </span>
                </div>
                <div class="trend-detail">
                  {{ $t('trendCard.slopeLabel') }}: {{ stateData.metadata.ma50_slope > 0 ? '+' : '' }}{{ stateData.metadata.ma50_slope.toFixed(2) }}%{{ $t('trendCard.perDay') }}
                </div>
                <div class="trend-description">
                  {{ $t('trendCard.ma50Description') }}
                </div>
              </div>
              <div v-else class="trend-content">
                <div class="trend-unavailable">{{ $t('trendCard.unavailable') }}</div>
              </div>
            </div>
            
            <div class="trend-card">
              <div class="trend-card-header">
                <span class="trend-icon">📈</span>
                <h3>{{ $t('trendCard.ma200Trend') }}</h3>
              </div>
              <div v-if="stateData.metadata?.ma200_slope !== undefined" class="trend-content">
                <div class="trend-status" :class="stateData.metadata.ma200_slope >= 0 ? 'positive' : 'negative'">
                  <span class="trend-indicator">{{ getSlopeEmoji(stateData.metadata.ma200_slope) }}</span>
                  <span class="trend-text">
                    {{ stateData.metadata.ma200_slope >= 0 ? $t('trendCard.ma200FlatUp') : $t('trendCard.ma200Down') }}
                  </span>
                </div>
                <div class="trend-detail">
                  {{ $t('trendCard.slopeLabel') }}: {{ stateData.metadata.ma200_slope > 0 ? '+' : '' }}{{ stateData.metadata.ma200_slope.toFixed(2) }}%{{ $t('trendCard.perDay') }}
                </div>
                <div class="trend-description">
                  {{ stateData.metadata.ma200_slope >= 0 ? $t('trendCard.ma200BullCondition') : $t('trendCard.ma200BearCondition') }}
                </div>
              </div>
              <div v-else class="trend-content">
                <div class="trend-unavailable">{{ $t('trendCard.unavailable') }}</div>
              </div>
            </div>
            
            <div class="trend-card" v-if="trendQuality">
              <div class="trend-card-header">
                <span class="trend-icon">⭐</span>
                <h3>{{ $t('trendCard.quality') }}</h3>
              </div>
              <div class="trend-content">
                <div class="trend-status" :class="trendQuality?.type === 'good' ? 'positive' : 'negative'">
                  <span class="trend-indicator">{{ trendQuality?.type === 'good' ? '✅' : '⚠️' }}</span>
                  <span class="trend-text">{{ trendQuality?.text }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 硬规则2：资金姿态 -->
        <div v-if="stateData && stateData.ok && stateData.metadata" class="funding-analysis-section fade-in">
          <div class="section-header">
            <span class="section-badge hard-rule">{{ $t('section.fundingPosture.badge') }}</span>
            <h2>{{ $t('section.fundingPosture.title') }}</h2>
          </div>
          <p class="section-description">{{ $t('section.fundingPosture.description') }}</p>
          
          <!-- 资金姿态变化程度 -->
          <div v-if="stateData.metadata?.stablecoin_slope !== undefined || stateData.metadata?.total_slope !== undefined" class="funding-change-card">
            <div class="funding-change-header">
              <span class="funding-change-icon">📊</span>
              <h3>{{ $t('section.fundingPosture.changeTitle') }}</h3>
            </div>
            <div class="funding-change-intro">
              <p>{{ $t('section.fundingPosture.changeIntro') }}</p>
              <p v-if="(stateData.metadata?.stablecoin_slope === 0 || stateData.metadata?.total_slope === 0) && stateData.metadata?.stablecoin_slope !== undefined" class="data-warning">
                {{ $t('section.fundingPosture.dataWarning') }}
              </p>
            </div>
            <div class="funding-change-grid">
              <div v-if="stateData.metadata?.stablecoin_slope !== undefined" class="funding-change-item">
                <div class="change-label">{{ $t('fundingChange.stablecoinTrendLabel') }}</div>
                <div class="change-value" :class="stateData.metadata.stablecoin_slope > 0 ? 'positive' : 'negative'">
                  <span class="change-icon">{{ stateData.metadata.stablecoin_slope > 0 ? '📈' : '📉' }}</span>
                  <span>{{ stateData.metadata.stablecoin_slope > 0 ? '+' : '' }}{{ stateData.metadata.stablecoin_slope.toFixed(3) }}%/天</span>
                </div>
                <div class="change-desc">
                  <strong>{{ stateData.metadata.stablecoin_slope > 0 ? $t('fundingChange.upMore') : $t('fundingChange.downLess') }}：</strong>
                  {{ stateData.metadata.stablecoin_slope > 0 ? $t('fundingChange.stablecoinUpDesc') : $t('fundingChange.stablecoinDownDesc') }}
                </div>
              </div>
              <div v-if="stateData.metadata?.total_slope !== undefined" class="funding-change-item">
                <div class="change-label">{{ $t('fundingChange.totalTrendLabel') }}</div>
                <div class="change-value" :class="stateData.metadata.total_slope > 0 ? 'positive' : 'negative'">
                  <span class="change-icon">{{ stateData.metadata.total_slope > 0 ? '📈' : '📉' }}</span>
                  <span>{{ stateData.metadata.total_slope > 0 ? '+' : '' }}{{ stateData.metadata.total_slope.toFixed(3) }}%/天</span>
                </div>
                <div class="change-desc">
                  <strong>{{ stateData.metadata.total_slope > 0 ? $t('fundingChange.upMore') : $t('fundingChange.downLess') }}：</strong>
                  {{ stateData.metadata.total_slope > 0 ? $t('fundingChange.totalUpDesc') : $t('fundingChange.totalDownDesc') }}
                </div>
              </div>
              <div v-if="stateData.metadata?.stablecoin_ratio !== undefined" class="funding-change-item">
                <div class="change-label">{{ $t('fundingChange.stablecoinRatioLabel') }}</div>
                <div class="change-value">
                  <span class="change-icon">💵</span>
                  <span>{{ stateData.metadata.stablecoin_ratio.toFixed(2) }}%</span>
                </div>
                <div class="change-desc">
                  <div v-if="stateData.metadata?.stablecoin_ratio_gap !== undefined && stateData.metadata?.stablecoin_ratio_gap !== null" style="margin-bottom: 0.5rem;">
                    <span class="ratio-change-indicator">⚖️</span>
                    <span>{{ $t('fundingChange.thresholdGap') }} {{ stateData.metadata.stablecoin_ratio_gap > 0 ? '+' : '' }}{{ stateData.metadata.stablecoin_ratio_gap.toFixed(2) }}%</span>
                  </div>
                  <div v-if="stateData.metadata?.stablecoin_ratio_change !== undefined && stateData.metadata?.stablecoin_ratio_change !== null" style="margin-bottom: 0.5rem;">
                    <span class="ratio-change-indicator">{{ stateData.metadata.stablecoin_ratio_change < 0 ? '⬇️' : stateData.metadata.stablecoin_ratio_change > 0 ? '⬆️' : '➡️' }}</span>
                    <span :class="stateData.metadata.stablecoin_ratio_change < 0 ? 'positive' : stateData.metadata.stablecoin_ratio_change > 0 ? 'negative' : ''">
                      {{ $t('fundingChange.changeLabel') }} {{ stateData.metadata.stablecoin_ratio_change > 0 ? '+' : '' }}{{ stateData.metadata.stablecoin_ratio_change.toFixed(2) }}%
                    </span>
                  </div>
                  <strong>{{ $t('fundingChange.explanationStrong') }}</strong>{{ $t('fundingChange.explanationBody') }}
                </div>
              </div>
            </div>
            <div v-if="fundingPatternInfo" class="funding-combination">
              <div class="combination-label">{{ $t('section.fundingPosture.currentCombination') }}</div>
              <div class="combination-pattern">
                {{ fundingPatternInfo?.pattern }} - {{ fundingPatternInfo?.name }}
              </div>
            </div>
          </div>
          
          <div class="funding-info-card">
            <div class="funding-info-header">
              <span class="funding-icon">💵</span>
              <h3>{{ $t('section.fundingPosture.patternsTitle') }}</h3>
            </div>
            <div class="funding-patterns">
              <div class="funding-pattern-item" :class="{ active: fundingPatternInfo?.pattern === 'Stable ↑ + Total ↑' }">
                <div class="pattern-indicator">Stable ↑ + Total ↑</div>
                <div class="pattern-name">{{ $t('fundingPattern.incrementalOffensive.name') }}</div>
                <div class="pattern-desc">{{ $t('fundingPattern.incrementalOffensive.desc') }}</div>
              </div>
              <div class="funding-pattern-item" :class="{ active: fundingPatternInfo?.pattern === 'Stable ↓ + Total ↑' }">
                <div class="pattern-indicator">Stable ↓ + Total ↑</div>
                <div class="pattern-name">{{ $t('fundingPattern.strongOffensive.name') }}</div>
                <div class="pattern-desc">{{ $t('fundingPattern.strongOffensive.descPre') }}<strong>{{ $t('fundingPattern.strongOffensive.descStrong') }}</strong></div>
              </div>
              <div class="funding-pattern-item" :class="{ active: fundingPatternInfo?.pattern === 'Stable ↑ + Total ↓' }">
                <div class="pattern-indicator">Stable ↑ + Total ↓</div>
                <div class="pattern-name">{{ $t('fundingPattern.deriskDefensive.name') }}</div>
                <div class="pattern-desc">{{ $t('fundingPattern.deriskDefensive.desc') }}</div>
              </div>
              <div class="funding-pattern-item" :class="{ active: fundingPatternInfo?.pattern === 'Stable ↓ + Total ↓' }">
                <div class="pattern-indicator">Stable ↓ + Total ↓</div>
                <div class="pattern-name">{{ $t('fundingPattern.deepDefensive.name') }}</div>
                <div class="pattern-desc">{{ $t('fundingPattern.deepDefensive.desc') }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 检验层A：风险温度计 -->
        <div v-if="stateData && stateData.ok && stateData.validation" class="validation-section fade-in">
          <div class="section-header">
            <span class="section-badge validation-layer">{{ $t('section.riskThermometer.badge') }}</span>
            <h2>{{ $t('section.riskThermometer.title') }}</h2>
          </div>
          <p class="section-description">{{ $t('section.riskThermometer.description') }}</p>
          
          <div class="validation-card">
            <div class="thermometer" :style="{ color: getRiskThermometerColor(stateData.validation.risk_thermometer) }">
              <div class="thermometer-label">{{ THERMOMETER_KEYS[stateData.validation.risk_thermometer] ? $t(`thermometer.${THERMOMETER_KEYS[stateData.validation.risk_thermometer]}`) : stateData.validation.risk_thermometer }}</div>
              <div class="thermometer-value">{{ stateData.validation.ath_drawdown.toFixed(2) }}%</div>
              <div v-if="stateData.validation.ath_price !== null && stateData.validation.ath_price !== undefined" class="thermometer-ath">
                {{ $t('section.riskThermometer.athLabel') }} ${{ stateData.validation.ath_price.toLocaleString('en-US', { maximumFractionDigits: 0 }) }}
              </div>
            </div>
            <div class="thermometer-info">
              <p>{{ $t('section.riskThermometer.formula') }}</p>
              <ul>
                <li>{{ $t('thermometer.rangeUnder20') }}</li>
                <li>{{ $t('thermometer.range20To35') }}</li>
                <li>{{ $t('thermometer.rangeOver35') }}</li>
                <li>{{ $t('thermometer.rangeOver60') }}</li>
              </ul>
            </div>
          </div>
        </div>

        <!-- 检验层B：ETF加速器 -->
        <div v-if="stateData && stateData.ok && stateData.validation" class="validation-section fade-in">
          <div class="section-header">
            <span class="section-badge validation-layer">{{ $t('section.etfAccelerator.badge') }}</span>
            <h2>{{ $t('section.etfAccelerator.title') }}</h2>
          </div>
          <p class="section-description">{{ $t('section.etfAccelerator.description') }}</p>
          
          <div class="validation-card">
            <div class="etf-status" :style="{ color: getETFAcceleratorColor(stateData.validation.etf_accelerator) }">
              <div class="etf-label">{{ ETF_ACCEL_KEYS[stateData.validation.etf_accelerator] ? $t(`etfAccelerator.${ETF_ACCEL_KEYS[stateData.validation.etf_accelerator]}`) : (stateData.validation.etf_accelerator || $t('etfAccelerator.unknown')) }}</div>
              <div class="etf-metrics">
                <div v-if="stateData.validation.etf_net_flow !== null && stateData.validation.etf_net_flow !== undefined" class="etf-metric-item">
                  <div class="etf-metric-label">{{ $t('etfAccelerator.netFlowLabel') }}</div>
                  <div class="etf-metric-value">
                    <span class="etf-icon">{{ stateData.validation.etf_net_flow > 0 ? '📈' : '📉' }}</span>
                    <span :class="stateData.validation.etf_net_flow > 0 ? 'positive' : 'negative'">
                      <span class="etf-full-value">{{ stateData.validation.etf_net_flow >= 0 ? '+' : '-' }}${{ Math.abs(stateData.validation.etf_net_flow).toLocaleString('en-US', { maximumFractionDigits: 0 }) }}</span>
                      <span class="etf-compact-value">({{ formatETFValue(stateData.validation.etf_net_flow) }})</span>
                    </span>
                  </div>
                  <div class="etf-metric-desc">{{ $t('etfAccelerator.netFlowDesc') }}</div>
                </div>
                <div v-else class="etf-metric-item">
                  <div class="etf-metric-label">{{ $t('etfAccelerator.netFlowLabel') }}</div>
                  <div class="etf-metric-value unavailable">{{ $t('etfAccelerator.unavailable') }}</div>
                </div>
                <div v-if="stateData.validation.etf_aum !== null && stateData.validation.etf_aum !== undefined" class="etf-metric-item">
                  <div class="etf-metric-label">{{ $t('etfAccelerator.aumLabel') }}</div>
                  <div class="etf-metric-value">
                    <span class="etf-full-value">${{ stateData.validation.etf_aum.toLocaleString('en-US', { maximumFractionDigits: 0 }) }}</span>
                    <span class="etf-compact-value">({{ formatETFValue(stateData.validation.etf_aum) }})</span>
                  </div>
                  <div class="etf-metric-desc">{{ $t('etfAccelerator.aumDesc') }}</div>
                </div>
                <div v-else class="etf-metric-item">
                  <div class="etf-metric-label">{{ $t('etfAccelerator.aumLabel') }}</div>
                  <div class="etf-metric-value unavailable">{{ $t('etfAccelerator.unavailable') }}</div>
                </div>
                <div v-if="stateData.validation.etf_flow_14d_sum !== null && stateData.validation.etf_flow_14d_sum !== undefined" class="etf-metric-item">
                  <div class="etf-metric-label">{{ $t('etfAccelerator.flow14dLabel') }}</div>
                  <div class="etf-metric-value">
                    <span class="etf-icon">{{ stateData.validation.etf_flow_14d_sum > 0 ? '📈' : stateData.validation.etf_flow_14d_sum < 0 ? '📉' : '➖' }}</span>
                    <span :class="stateData.validation.etf_flow_14d_sum > 0 ? 'positive' : stateData.validation.etf_flow_14d_sum < 0 ? 'negative' : ''">
                      <span class="etf-full-value">{{ stateData.validation.etf_flow_14d_sum >= 0 ? '+' : '-' }}${{ Math.abs(stateData.validation.etf_flow_14d_sum).toLocaleString('en-US', { maximumFractionDigits: 0 }) }}</span>
                      <span class="etf-compact-value">({{ formatETFValue(stateData.validation.etf_flow_14d_sum) }})</span>
                    </span>
                  </div>
                  <div class="etf-metric-desc">{{ $t('etfAccelerator.flow14dDesc') }}</div>
                </div>
                <div v-else class="etf-metric-item">
                  <div class="etf-metric-label">{{ $t('etfAccelerator.flow14dLabel') }}</div>
                  <div class="etf-metric-value unavailable">{{ $t('etfAccelerator.unavailable') }}</div>
                </div>
                <div class="etf-metric-item">
                  <div class="etf-metric-label">{{ $t('etfAccelerator.flowSpeedLabel') }}</div>
                  <div class="etf-metric-subrow">
                    <span>{{ $t('etfAccelerator.avgRecent') }}</span>
                    <span v-if="stateData.validation.etf_flow_recent_avg !== null && stateData.validation.etf_flow_recent_avg !== undefined" :class="stateData.validation.etf_flow_recent_avg > 0 ? 'positive' : stateData.validation.etf_flow_recent_avg < 0 ? 'negative' : ''">
                      {{ formatETFValue(stateData.validation.etf_flow_recent_avg) }}
                    </span>
                    <span v-else class="unavailable">—</span>
                  </div>
                  <div class="etf-metric-subrow">
                    <span>{{ $t('etfAccelerator.avgPrev') }}</span>
                    <span v-if="stateData.validation.etf_flow_prev_avg !== null && stateData.validation.etf_flow_prev_avg !== undefined" :class="stateData.validation.etf_flow_prev_avg > 0 ? 'positive' : stateData.validation.etf_flow_prev_avg < 0 ? 'negative' : ''">
                      {{ formatETFValue(stateData.validation.etf_flow_prev_avg) }}
                    </span>
                    <span v-else class="unavailable">—</span>
                  </div>
                  <div class="etf-metric-subrow">
                    <span>{{ $t('etfAccelerator.flowTrendLabel') }}</span>
                    <span :class="getTrendBadge(stateData.validation.etf_flow_trend).className">
                      {{ getTrendBadge(stateData.validation.etf_flow_trend).icon }} {{ getTrendBadge(stateData.validation.etf_flow_trend).text }}
                    </span>
                  </div>
                  <div class="etf-metric-subrow">
                    <span>{{ $t('etfAccelerator.aumTrendLabel') }}</span>
                    <span :class="getTrendBadge(stateData.validation.etf_aum_trend).className">
                      {{ getTrendBadge(stateData.validation.etf_aum_trend).icon }} {{ getTrendBadge(stateData.validation.etf_aum_trend).text }}
                    </span>
                  </div>
                  <div class="etf-metric-desc">
                    {{ $t('etfAccelerator.flowSpeedDesc') }}
                  </div>
                </div>
                <div class="etf-metric-item">
                  <div class="etf-metric-label">{{ $t('etfAccelerator.posRatioLabel') }}</div>
                  <div class="etf-metric-value">
                    <span class="etf-icon">📊</span>
                    <span>{{ formatRatioPercent(stateData.validation.etf_flow_pos_ratio, 0) }}</span>
                  </div>
                  <div class="etf-metric-desc">{{ $t('etfAccelerator.posRatioDesc') }}</div>
                </div>
              </div>
              <div class="etf-rule-note">
                <strong>{{ $t('section.etfAccelerator.ruleNote') }}</strong>
                {{ $t('section.etfAccelerator.ruleNoteBody') }}
              </div>
            </div>
            <div class="etf-info">
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
            </div>
          </div>
        </div>

        <!-- 三、核心切换逻辑 -->
        <div v-if="stateData && stateData.ok" class="bull-signals-section fade-in">
          <div class="section-header">
            <span class="section-badge core-logic">{{ $t('section.transitions.badge') }}</span>
            <h2>{{ $t('section.transitions.title') }}</h2>
          </div>
          <div class="bull-signals-info">
            <p class="signals-intro">
              {{ $t('section.transitions.currentStatePrefix') }}<strong>{{ STATE_KEYS[stateData.state] ? $t(`quadrant.${STATE_KEYS[stateData.state]}.name`) : stateData.state }}</strong>{{ $t('section.transitions.currentStateSuffix') }}
            </p>
            <div class="transitions-grid">
              <div 
                v-for="(transition, index) in stateTransitionSignals" 
                :key="index"
                class="transition-card"
              >
                <div class="transition-header">
                  <div class="transition-target">
                    <span class="transition-arrow">→</span>
                    <span class="transition-state" :style="{ color: STATE_STYLES[transition.targetState]?.bgColor || '#1e293b' }">
                      {{ STATE_KEYS[transition.targetState] ? $t(`quadrant.${STATE_KEYS[transition.targetState]}.name`) : transition.targetState }}
                    </span>
                  </div>
                  <div class="transition-progress">
                    <div class="progress-bar">
                      <div 
                        class="progress-fill" 
                        :style="{ width: `${transition.progress}%`, background: STATE_STYLES[transition.targetState]?.bgColor || '#1e293b' }"
                      ></div>
                    </div>
                    <span class="progress-text">{{ transition.activeCount }}/{{ transition.totalCount }}</span>
                  </div>
                </div>
                <div class="transition-requirements">
                  <div class="requirements-label">{{ $t('section.transitions.requirements') }}</div>
                  <div class="signals-list">
                    <div 
                      v-for="(signal, sigIndex) in transition.signals" 
                      :key="sigIndex"
                      class="signal-item"
                      :class="{ active: signal.active }"
                    >
                      <span class="signal-check">{{ signal.active ? '✅' : '⏳' }}</span>
                      <div class="signal-content">
                        <div class="signal-name-small">{{ signal.name }}</div>
                        <div class="signal-desc-small">{{ signal.description }}</div>
                        <div class="signal-details-small">{{ signal.details }}</div>
                      </div>
                    </div>
                  </div>
                  <!-- 校验层（不计入需要条件） -->
                  <div v-if="transition.validationSignals && transition.validationSignals.length > 0" class="validation-signals-section">
                    <div class="validation-label">{{ $t('section.transitions.validationLabel') }}</div>
                    <div class="signals-list">
                      <div 
                        v-for="(signal, sigIndex) in transition.validationSignals" 
                        :key="`validation-${sigIndex}`"
                        class="signal-item validation-signal"
                        :class="{ active: signal.active }"
                      >
                        <span class="signal-check">{{ signal.active ? '✅' : '⏳' }}</span>
                        <div class="signal-content">
                          <div class="signal-name-small">{{ signal.name }}</div>
                          <div class="signal-desc-small">{{ signal.description }}</div>
                          <div class="signal-details-small">{{ signal.details }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 原始数据 -->
      <div class="details-section" :class="{ 'fade-in': !initialLoad }">
        <h2>📊 原始数据</h2>
        <div v-if="loading && Object.keys(data).length === 0" class="data-loading-overlay">
          <div class="data-loading-spinner">
            <div class="spinner-ring"></div>
            <div class="spinner-ring"></div>
            <div class="spinner-ring"></div>
            <div class="spinner-ring"></div>
          </div>
          <p class="data-loading-text">正在加载原始数据...</p>
        </div>
        <div class="details-grid" v-if="Object.keys(data).length > 0">    
          <!-- 原始数据源信息-->
          <template v-for="(item, key) in data" :key="String(key)">
            <div class="detail-card">
            <div class="detail-label">
              <span class="detail-icon">{{ getDataIcon(key as string) }}</span>
              {{ $t(`data.${String(key)}`) }}
            </div>
            <div class="detail-value" :class="key === 'etf_net_flow' && item.value > 0 ? 'positive' : key === 'etf_net_flow' && item.value < 0 ? 'negative' : ''">
              {{ formatValue(item.value, key as string) }}
            </div>
            <div class="detail-provider">来源: {{ item.provider }}</div>
            <div class="detail-description">
              <span v-if="item.metadata?.currency" class="detail-meta-item">{{ item.metadata.currency }}</span>
              <span v-if="item.metadata?.period" class="detail-meta-item">周期: {{ item.metadata.period }}</span>
              <span v-if="item.metadata?.description" class="detail-meta-item">{{ item.metadata.description }}</span>
            </div>
          </div>
          </template>
        </div>
      </div>

      <div class="chart-section" v-if="!initialLoad || stateData">
        <TradingViewChart />
      </div>
    </main>
  </div>
</template>

<style scoped>
:global(body) {
  margin: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
  background-color: #0f172a;
  color: #e2e8f0;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

header {
  position: relative;
  margin-bottom: 3rem;
  border-bottom: 1px solid #1e293b;
  padding-bottom: 1rem;
}

h1 {
  font-size: 2.5rem;
  font-weight: 700;
  color: #f8fafc;
  margin: 0 0 0.5rem 0;
}

.subtitle {
  color: #94a3b8;
  margin: 0 0 1rem 0;
}

.refresh-btn {
  background-color: #3b82f6;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 1rem;
}

.refresh-btn:hover:not(:disabled) {
  background-color: #2563eb;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.status-summary {
  margin-top: 10px;
  text-align: center;
}

.status-primary {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #f1f5f9;
}

.status-secondary {
  margin: 4px 0 0;
  font-size: 13px;
  color: #cbd5e1;
  opacity: 0.7;
}

/* 状态机展示 */
.state-section {
  margin-bottom: 3rem;
}

.state-header {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.state-box {
  padding: 1.25rem;
  border-radius: 0.75rem;
  text-align: center;
  color: white;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
}

.state-name {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0.375rem;
}

.state-details {
  font-size: 0.875rem;
  opacity: 0.9;
}

.state-metrics {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  justify-content: center;
}

.metric-item {
  background-color: #1e293b;
  padding: 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid #334155;
}

.metric-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #94a3b8;
  margin-bottom: 0.5rem;
}

.metric-tooltip {
  position: relative;
  display: inline-block;
}

.tooltip-icon {
  cursor: help;
  font-size: 0.875rem;
  color: #64748b;
  transition: color 0.2s;
}

.tooltip-icon:hover {
  color: #94a3b8;
}

.tooltip-content {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-bottom: 0.5rem;
  padding: 0.75rem;
  background-color: #0f172a;
  border: 1px solid #334155;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  color: #94a3b8;
  line-height: 1.6;
  white-space: normal;
  width: 280px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s;
  z-index: 1000;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}

.metric-tooltip:hover .tooltip-content {
  opacity: 1;
  pointer-events: auto;
}

.tooltip-content strong {
  color: #f1f5f9;
  display: block;
  margin-bottom: 0.5rem;
}

.metric-value {
  display: block;
  font-size: 1.25rem;
  font-weight: 700;
  color: #f1f5f9;
}

/* 章节标题样式 */
.section-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.section-badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.section-badge.core-output {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.section-badge.hard-rule {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.section-badge.validation-layer {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.section-badge.core-logic {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
}

.section-header h2 {
  font-size: 1.5rem;
  color: #f1f5f9;
  margin: 0;
  flex: 1;
}

.section-description {
  font-size: 0.875rem;
  color: #94a3b8;
  margin: 0 0 1.5rem 0;
  padding-left: calc(0.75rem + 1rem + 0.75rem + 0.75rem); /* badge width + gap + padding */
  line-height: 1.6;
}

/* 校验层 */
.validation-section {
  margin-bottom: 3rem;
}

.validation-section .section-header {
  margin-bottom: 1rem;
}

.validation-section .section-description {
  margin-bottom: 1.5rem;
}

.validation-card {
  background-color: #1e293b;
  border-radius: 0.75rem;
  padding: 1.5rem;
  border: 1px solid #334155;
  margin-top: 1rem;
}

.validation-card h3 {
  margin: 0 0 1rem 0;
  font-size: 1.25rem;
  color: #f1f5f9;
}

.thermometer, .etf-status {
  text-align: center;
  padding: 1rem;
  margin-bottom: 1rem;
}

.thermometer-label, .etf-label {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.thermometer-value, .etf-value {
  font-size: 2rem;
  font-weight: 700;
}

.thermometer-ath {
  margin-top: 0.35rem;
  font-size: 0.85rem;
  color: #94a3b8;
}
.thermometer-info, .etf-info {
  font-size: 0.875rem;
  color: #94a3b8;
  line-height: 1.6;
}

.etf-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}

.etf-metric-item {
  background-color: #0f172a;
  padding: 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid #334155;
}

.etf-metric-label {
  font-size: 0.7rem;
  color: #64748b;
  margin-bottom: 0.4rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.etf-metric-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: 0.2rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.etf-full-value {
  font-size: 1.25rem;
  font-weight: 700;
}

.etf-compact-value {
  font-size: 0.95rem;
  font-weight: 600;
  opacity: 0.8;
}

.etf-metric-value.unavailable {
  font-size: 0.9rem;
  color: #64748b;
  font-weight: 400;
}

.etf-icon {
  font-size: 1.1rem;
}

.etf-metric-value .positive {
  color: #10b981;
}

.etf-metric-value .negative {
  color: #ef4444;
}

.etf-metric-desc {
  font-size: 0.7rem;
  color: #64748b;
  line-height: 1.35;
}

.etf-metric-subrow {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.78rem;
  color: #cbd5f5;
  margin-bottom: 0.25rem;
}

.etf-metric-subrow .unavailable {
  color: #64748b;
}

.etf-metric-subrow .positive {
  color: #10b981;
}

.etf-metric-subrow .negative {
  color: #ef4444;
}

.etf-metric-subrow .neutral {
  color: #94a3b8;
}

.etf-info-text {
  margin: 0;
  line-height: 1.6;
}

.etf-info-text strong {
  color: #f1f5f9;
}

.etf-rule-note {
  margin-top: 0.75rem;
  font-size: 0.8rem;
  color: #94a3b8;
  line-height: 1.5;
}

.thermometer-info ul {
  margin: 0.5rem 0 0 1.5rem;
  padding: 0;
}

.thermometer-info li {
  margin: 0.25rem 0;
}

/* 四象限图 */
.quadrant-section {
  margin-bottom: 3rem;
}

.quadrant-section .section-header {
  margin-bottom: 0.75rem;
}

.quadrant-section .section-description {
  margin-bottom: 1.5rem;
}

.quadrant-chart-container {
  background-color: #1e293b;
  border-radius: 1rem;
  padding: 2.5rem 1.5rem 2rem 3rem;
  border: 1px solid #334155;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
}

.quadrant-chart {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  max-width: 500px;
  margin: 0 auto;
  padding-bottom: 40px;
}

/* 坐标轴标签 */
.axis-y-label {
  position: absolute;
  left: -3.5rem;
  font-size: 1.125rem;
  font-weight: 700;
  color: #f1f5f9;
  white-space: nowrap;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  text-align: center;
}

.axis-y-label.top {
  top: 0.5rem;
  height: auto;
}

.axis-y-label.bottom {
  bottom: 3em;
  height: auto;
}

.axis-x-label {
  position: absolute;
  bottom: 0.1rem;
  font-size: 1.125rem;
  font-weight: 700;
  color: #f1f5f9;
  white-space: nowrap;
}

.axis-x-label.left {
  left: 0.5rem;
  text-align: left;
}

.axis-x-label.right {
  right: 0.5rem;
  text-align: right;
}

/* 中心分割线（仅水平线） */
.axis-line {
  position: absolute;
  z-index: 0;
  pointer-events: none;
}

.axis-line.horizontal {
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  transform: translateY(-50%);
  background: linear-gradient(to right, transparent, #475569, transparent);
}

/* 四象限容器 */
.quadrant-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 0;
  background-color: #0f172a;
  border-radius: 0.5rem;
  overflow: hidden;
}

/* 单个象限 */
.quadrant {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  cursor: pointer;
  z-index: 2;
}

.quadrant::before {
  content: '';
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 0.3s;
  background: radial-gradient(circle at center, rgba(255, 255, 255, 0.1), transparent);
}

.quadrant:hover::before {
  opacity: 1;
}

.quadrant-1 {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 50%, #dc4a63 100%);
  border-top-right-radius: 0.5rem;
}

.quadrant-2 {
  background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 50%, #3a9480 100%);
  border-top-left-radius: 0.5rem;
}

.quadrant-3 {
  background: linear-gradient(135deg, #feca57 0%, #ff9ff3 50%, #ff8ce8 100%);
  border-bottom-right-radius: 0.5rem;
}

.quadrant-4 {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 50%, #fcc5d7 100%);
  border-bottom-left-radius: 0.5rem;
}

.quadrant.active {
  transform: scale(1.02);
  z-index: 10;
  box-shadow: 
    0 0 0 4px rgba(59, 130, 246, 0.6),
    0 0 30px rgba(59, 130, 246, 0.4),
    inset 0 0 20px rgba(255, 255, 255, 0.1);
}

.quadrant-content {
  position: relative;
  z-index: 2;
  text-align: center;
  color: white;
  padding: 1rem;
}

.quadrant-icon {
  font-size: 2rem;
  margin-bottom: 0.375rem;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.quadrant-name {
  font-size: 1.125rem;
  font-weight: 700;
  margin-bottom: 0.375rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.quadrant-risk {
  font-size: 0.75rem;
  font-weight: 600;
  opacity: 0.9;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  margin-bottom: 0.5rem;
}

/* 达成条件指示灯 */
.condition-indicator {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.condition-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.7rem;
  opacity: 0.7;
  transition: all 0.3s;
}

.condition-item.met {
  opacity: 1;
  font-weight: 600;
}

.condition-icon {
  font-size: 0.875rem;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
}

.condition-text {
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* 活动指示器（脉冲动画） */
.active-indicator {
  position: absolute;
  inset: -10px;
  z-index: 1;
  pointer-events: none;
}

.pulse-ring {
  position: absolute;
  inset: 0;
  border: 3px solid rgba(59, 130, 246, 0.6);
  border-radius: inherit;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.pulse-ring.delay-1 {
  animation-delay: 0.5s;
  border-color: rgba(59, 130, 246, 0.4);
}

.pulse-ring.delay-2 {
  animation-delay: 1s;
  border-color: rgba(59, 130, 246, 0.2);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0;
    transform: scale(1.1);
  }
}

/* 非活动象限的样式 */
.quadrant:not(.active) {
  opacity: 0.6;
  filter: grayscale(20%);
}

.quadrant:not(.active):hover {
  opacity: 0.8;
  filter: grayscale(0%);
}

/* 趋势结构分析 */
.trend-analysis-section {
  margin-bottom: 3rem;
}

.trend-analysis-section .section-header {
  margin-bottom: 0.75rem;
}

.trend-analysis-section .section-description {
  margin-bottom: 1.5rem;
}

/* 趋势结构结论卡片 */
.trend-conclusion-card {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 0.75rem;
  padding: 1.5rem;
  border: 2px solid #334155;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}

.trend-conclusion-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.trend-conclusion-icon {
  font-size: 2rem;
}

.trend-conclusion-header h3 {
  font-size: 1.25rem;
  color: #f1f5f9;
  margin: 0;
  font-weight: 700;
}

.trend-conclusion-content {
  padding-left: 2.75rem;
}

.trend-conclusion-name {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.trend-conclusion-desc {
  font-size: 0.875rem;
  color: #94a3b8;
  margin-bottom: 0.75rem;
  line-height: 1.6;
}

.trend-conclusion-trend {
  font-size: 0.875rem;
  color: #64748b;
  padding-top: 0.75rem;
  border-top: 1px solid #334155;
}

.trend-conclusion-trend strong {
  color: #f1f5f9;
  font-size: 1rem;
}

.trend-analysis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.trend-card {
  background-color: #1e293b;
  border-radius: 0.75rem;
  padding: 1.5rem;
  border: 1px solid #334155;
}

.trend-card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.trend-icon {
  font-size: 1.5rem;
}

.trend-card-header h3 {
  font-size: 1.125rem;
  color: #f1f5f9;
  margin: 0;
}

.trend-content {
  margin-top: 1rem;
}

.trend-status {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 0.75rem;
}

.trend-status.positive {
  background-color: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.trend-status.negative {
  background-color: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.trend-indicator {
  font-size: 1.5rem;
}

.trend-text {
  font-size: 1rem;
  font-weight: 600;
  color: #f1f5f9;
  flex: 1;
}

.trend-detail {
  font-size: 0.875rem;
  color: #94a3b8;
  margin-bottom: 0.5rem;
}

.trend-description {
  font-size: 0.75rem;
  color: #64748b;
  line-height: 1.5;
}

.trend-unavailable {
  font-size: 0.875rem;
  color: #64748b;
  text-align: center;
  padding: 1rem;
}

/* 资金姿态分析 */
.funding-analysis-section {
  margin-bottom: 3rem;
}

.funding-analysis-section .section-header {
  margin-bottom: 0.75rem;
}

.funding-analysis-section .section-description {
  margin-bottom: 1.5rem;
}

.funding-info-card {
  background-color: #1e293b;
  border-radius: 0.75rem;
  padding: 1.5rem;
  border: 1px solid #334155;
}

.funding-info-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.funding-icon {
  font-size: 1.5rem;
}

.funding-info-header h3 {
  font-size: 1.125rem;
  color: #f1f5f9;
  margin: 0;
}

.funding-patterns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.funding-pattern-item {
  background-color: #0f172a;
  border-radius: 0.5rem;
  padding: 1rem;
  border: 1px solid #334155;
  transition: all 0.3s;
}

.funding-pattern-item.active {
  border-color: #3b82f6;
  background-color: rgba(59, 130, 246, 0.1);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
}

.pattern-indicator {
  font-size: 0.875rem;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 0.5rem;
}

.pattern-name {
  font-size: 1rem;
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: 0.5rem;
}

.pattern-desc {
  font-size: 0.75rem;
  color: #64748b;
  line-height: 1.5;
}

.pattern-desc strong {
  color: #f1f5f9;
}

/* 资金姿态变化程度 */
.funding-change-card {
  background-color: #1e293b;
  border-radius: 0.75rem;
  padding: 1.5rem;
  border: 1px solid #334155;
  margin-bottom: 1.5rem;
}

.funding-change-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.funding-change-intro {
  font-size: 0.75rem;
  color: #64748b;
  line-height: 1.5;
  margin-bottom: 1.5rem;
  padding: 0.75rem;
  background-color: rgba(59, 130, 246, 0.05);
  border-radius: 0.5rem;
  border-left: 3px solid rgba(59, 130, 246, 0.3);
}

.funding-change-intro p {
  margin: 0;
}

.funding-change-intro .data-warning {
  margin-top: 0.5rem;
  color: #f59e0b;
  font-size: 0.7rem;
}

.slope-warning {
  color: #f59e0b;
  font-size: 0.875rem;
  margin-left: 0.5rem;
  cursor: help;
}

.detail-warning-text {
  font-size: 0.7rem;
  color: #f59e0b;
  margin-top: 0.25rem;
  display: block;
}

.funding-change-icon {
  font-size: 1.5rem;
}

.funding-change-header h3 {
  font-size: 1.125rem;
  color: #f1f5f9;
  margin: 0;
}

.funding-change-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.funding-change-item {
  background-color: #0f172a;
  border-radius: 0.5rem;
  padding: 1rem;
  border: 1px solid #334155;
}

.change-label {
  font-size: 0.875rem;
  color: #94a3b8;
  margin-bottom: 0.75rem;
}

.change-value {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.change-value.positive {
  color: #10b981;
}

.change-value.negative {
  color: #ef4444;
}

.change-icon {
  font-size: 1.25rem;
}

.change-desc {
  font-size: 0.75rem;
  color: #64748b;
  line-height: 1.5;
  margin-top: 0.5rem;
}

.change-desc strong {
  color: #f1f5f9;
}

.funding-combination {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #334155;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.combination-label {
  font-size: 0.875rem;
  color: #94a3b8;
}

.combination-pattern {
  font-size: 1rem;
  font-weight: 700;
  color: #3b82f6;
  padding: 0.5rem 1rem;
  background-color: rgba(59, 130, 246, 0.1);
  border-radius: 0.375rem;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

/* 稳定币占比卡片 */
.funding-ratio-card {
  background-color: #1e293b;
  border-radius: 0.75rem;
  padding: 1.5rem;
  border: 1px solid #334155;
  margin-bottom: 1.5rem;
}

.funding-ratio-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.funding-ratio-header h3 {
  font-size: 1.125rem;
  color: #f1f5f9;
  margin: 0;
}

.funding-ratio-content {
  padding-left: 2.25rem;
}

.funding-ratio-value {
  font-size: 2rem;
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: 0.75rem;
}

.funding-ratio-change {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  margin-bottom: 0.75rem;
}

.ratio-change-indicator {
  font-size: 1rem;
}

.funding-ratio-change .positive {
  color: #10b981;
}

.funding-ratio-change .negative {
  color: #ef4444;
}

.funding-ratio-desc {
  font-size: 0.75rem;
  color: #64748b;
  line-height: 1.5;
}

/* 转牛信号 */
.bull-signals-section {
  margin-bottom: 3rem;
}

.bull-signals-section .section-header {
  margin-bottom: 0.75rem;
}

.bull-signals-section .section-description {
  margin-bottom: 1.5rem;
}

.bull-signals-info {
  background-color: #1e293b;
  border-radius: 0.75rem;
  padding: 1.5rem;
  border: 1px solid #334155;
}

.signals-intro {
  font-size: 0.875rem;
  color: #94a3b8;
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.signals-intro strong {
  color: #f1f5f9;
}

.signals-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.signal-card {
  background-color: #0f172a;
  border-radius: 0.5rem;
  padding: 1rem;
  border: 1px solid #334155;
  transition: all 0.3s;
}

.signal-card.active {
  border-color: #10b981;
  background-color: rgba(16, 185, 129, 0.1);
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.3);
}

.signal-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.signal-number {
  width: 24px;
  height: 24px;
  background-color: #334155;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  color: #f1f5f9;
}

.signal-card.active .signal-number {
  background-color: #10b981;
}

.signal-icon {
  font-size: 1.25rem;
}

.signal-name {
  font-size: 1rem;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0;
  flex: 1;
}

.signal-description {
  font-size: 0.875rem;
  color: #94a3b8;
  margin-bottom: 0.5rem;
  line-height: 1.5;
}

.signal-details {
  font-size: 0.75rem;
  color: #64748b;
  line-height: 1.4;
  padding-top: 0.5rem;
  border-top: 1px solid #334155;
}

/* 状态切换信号 */
.transitions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
}

.transition-card {
  background-color: #0f172a;
  border-radius: 0.75rem;
  padding: 1.5rem;
  border: 1px solid #334155;
  transition: all 0.3s;
}

.transition-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #334155;
}

.transition-target {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.transition-arrow {
  font-size: 1.5rem;
  color: #64748b;
}

.transition-state {
  font-size: 1.125rem;
  font-weight: 700;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  background-color: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.transition-progress {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.progress-bar {
  width: 100px;
  height: 8px;
  background-color: #334155;
  border-radius: 9999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 9999px;
  transition: width 0.3s;
}

.progress-text {
  font-size: 0.875rem;
  color: #94a3b8;
  font-weight: 600;
  min-width: 50px;
  text-align: right;
}

.transition-requirements {
  margin-top: 1rem;
}

.requirements-label {
  font-size: 0.875rem;
  color: #94a3b8;
  margin-bottom: 1rem;
  font-weight: 600;
}

.signals-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.signal-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  background-color: #1e293b;
  border-radius: 0.5rem;
  border: 1px solid #334155;
  transition: all 0.3s;
}

.signal-item.active {
  border-color: #10b981;
  background-color: rgba(16, 185, 129, 0.1);
}

.signal-check {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.signal-content {
  flex: 1;
}

.signal-name-small {
  font-size: 0.875rem;
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: 0.25rem;
}

.signal-desc-small {
  font-size: 0.75rem;
  color: #94a3b8;
  margin-bottom: 0.25rem;
  line-height: 1.4;
}

.signal-details-small {
  font-size: 0.7rem;
  color: #64748b;
  line-height: 1.3;
}

/* 校验层信号 */
.validation-signals-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #334155;
}

.validation-label {
  font-size: 0.875rem;
  color: #94a3b8;
  margin-bottom: 1rem;
  font-weight: 600;
  font-style: italic;
}

.validation-signal {
  opacity: 0.85;
}

.validation-signal.active {
  opacity: 1;
}

/* 详细数据 */
.details-section {
  margin-bottom: 3rem;
  position: relative;
}

.details-section h2 {
  font-size: 1.5rem;
  color: #f1f5f9;
  margin-bottom: 1.5rem;
}

.details-section .data-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(15, 23, 42, 0.95);
  border-radius: 0.75rem;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  backdrop-filter: blur(4px);
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  position: relative;
}

.detail-card {
  background-color: #1e293b;
  border-radius: 0.5rem;
  padding: 1rem;
  border: 1px solid #334155;
}

.detail-label {
  font-size: 0.875rem;
  color: #94a3b8;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.detail-icon {
  font-size: 1rem;
}

.detail-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: 0.25rem;
}

.detail-value.positive {
  color: #10b981;
}

.detail-value.negative {
  color: #ef4444;
}

.detail-slope {
  font-size: 0.75rem;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.slope-indicator {
  font-size: 1rem;
}

.detail-slope .positive {
  color: #10b981;
}

.detail-slope .negative {
  color: #ef4444;
}

.detail-description {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.5rem;
  line-height: 1.4;
}

.detail-provider {
  font-size: 0.7rem;
  color: #64748b;
  margin-top: 0.25rem;
  padding: 0.25rem 0.5rem;
  background-color: rgba(59, 130, 246, 0.1);
  border-radius: 0.25rem;
  display: inline-block;
}

.detail-meta-item {
  display: block;
  margin-top: 0.25rem;
}

/* 原始数据 */
.data-section {
  margin-bottom: 3rem;
}

.data-section h2 {
  font-size: 1.5rem;
  color: #f1f5f9;
  margin-bottom: 1.5rem;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.card {
  background-color: #1e293b;
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  border: 1px solid #334155;
  transition: transform 0.2s;
}

.card:hover {
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.card h3 {
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8;
  margin: 0;
}

.card-badge {
  background-color: #3b82f6;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.value {
  font-size: 2.25rem;
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: 1rem;
}

.value.positive {
  color: #10b981;
}

.value.negative {
  color: #ef4444;
}

.meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  color: #64748b;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.period {
  background-color: #0f172a;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
}

.description {
  font-size: 0.75rem;
  color: #64748b;
  font-style: italic;
}

.provider {
  background-color: #0f172a;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
}

.error {
  background-color: #ef444420;
  color: #fca5a5;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #ef4444;
  margin-bottom: 2rem;
}

/* 加载动画容器 */
.loading-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: rgba(15, 23, 42, 0.95);
  z-index: 1000;
  backdrop-filter: blur(4px);
}

/* 加载动画 */
.loading-spinner {
  position: relative;
  width: 80px;
  height: 80px;
  margin-bottom: 2rem;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 4px solid transparent;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
}

.spinner-ring:nth-child(1) {
  animation-delay: -0.45s;
  border-top-color: #3b82f6;
}

.spinner-ring:nth-child(2) {
  animation-delay: -0.3s;
  border-top-color: #60a5fa;
  width: 70%;
  height: 70%;
  top: 15%;
  left: 15%;
}

.spinner-ring:nth-child(3) {
  animation-delay: -0.15s;
  border-top-color: #93c5fd;
  width: 50%;
  height: 50%;
  top: 25%;
  left: 25%;
}

.spinner-ring:nth-child(4) {
  border-top-color: #dbeafe;
  width: 30%;
  height: 30%;
  top: 35%;
  left: 35%;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.loading-text {
  text-align: center;
}

.loading-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #f1f5f9;
  margin: 0 0 0.5rem 0;
  animation: pulse-text 2s ease-in-out infinite;
}

.loading-subtitle {
  font-size: 1rem;
  color: #94a3b8;
  margin: 0;
}

@keyframes pulse-text {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

/* 淡入动画 */
.fade-in {
  animation: fadeIn 0.6s ease-out forwards;
  opacity: 0;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 为不同部分添加不同的延迟，实现逐步显示效果 */
.state-header.fade-in {
  animation-delay: 0s;
}

.quadrant-section.fade-in {
  animation-delay: 0.05s;
}

.trend-analysis-section.fade-in {
  animation-delay: 0.1s;
}

.funding-analysis-section.fade-in {
  animation-delay: 0.15s;
}

.validation-section.fade-in {
  animation-delay: 0.2s;
}

.bull-signals-section.fade-in {
  animation-delay: 0.25s;
}

/* 原始数据加载覆盖层 */
.data-loading-overlay {
  position: relative;
  background-color: rgba(15, 23, 42, 0.8);
  border-radius: 0.75rem;
  padding: 3rem;
  margin-bottom: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.data-loading-spinner {
  position: relative;
  width: 60px;
  height: 60px;
  margin-bottom: 1rem;
}

.data-loading-text {
  font-size: 1rem;
  color: #94a3b8;
  margin: 0;
}

@media (max-width: 768px) {
  .state-header {
    grid-template-columns: 1fr;
  }

  .quadrant-grid {
    height: 300px;
  }

  .quadrant-label {
    font-size: 1rem;
  }
}

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
</style>
