<template>
  <div class="tradingview-widget-container">
    <div id="tradingview_btc_kline"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';

onMounted(() => {
  const script = document.createElement('script');
  script.src = 'https://s3.tradingview.com/tv.js';
  script.async = true;
  script.onload = () => {
    // @ts-ignore
    if (window.TradingView) {
      // @ts-ignore
      new window.TradingView.widget({
        "width": "100%",
        "height": 500,
        "symbol": "BINANCE:BTCUSDT",
        "interval": "D",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "zh_CN",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_btc_kline"
      });
    }
  };
  document.head.appendChild(script);
});
</script>

<style scoped>
.tradingview-widget-container {
  width: 100%;
  height: 500px;
  margin-bottom: 2rem;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
</style>
