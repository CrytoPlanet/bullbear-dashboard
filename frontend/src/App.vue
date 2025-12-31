<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { type DataResult, DATA_LABELS } from './types';

const data = ref<Record<string, DataResult>>({});
const loading = ref(true);
const error = ref<string | null>(null);

const DATA_TYPES = ['btc_price', 'total_market_cap', 'stablecoin_market_cap', 'ma50', 'ma200'];

const fetchData = async () => {
  loading.value = true;
  error.value = null;
  data.value = {};
  
  try {
    const promises = DATA_TYPES.map(async (type) => {
      const response = await fetch(`http://localhost:8000/api/data/${type}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch ${type}: ${response.status}`);
      }
      const json = await response.json();
      // json is { ok: true, ...DataResult }
      return { type, result: json as DataResult }; 
    });

    const results = await Promise.all(promises);
    
    results.forEach(({ type, result }) => {
      data.value[type] = result;
    });
    
  } catch (e: any) {
    error.value = e.message || 'Failed to fetch data';
    console.error(e);
  } finally {
    loading.value = false;
  }
};

const formatValue = (value: number, type: string) => {
  if (type.includes('market_cap')) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
      notation: 'compact',
    }).format(value);
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
};

onMounted(() => {
  fetchData();
});
</script>

<template>
  <div class="container">
    <header>
      <h1>Crypto Market Dashboard</h1>
      <button @click="fetchData" :disabled="loading" class="refresh-btn">
        {{ loading ? 'Loading...' : 'Refresh' }}
      </button>
    </header>

    <main>
      <div v-if="error" class="error">
        {{ error }}
      </div>

      <div v-else-if="loading && !data" class="loading">
        Loading market data...
      </div>

      <div v-else-if="data" class="grid">
        <div v-for="(item, key) in data" :key="key" class="card">
          <h2>{{ DATA_LABELS[key] || key }}</h2>
          <div class="value">{{ formatValue(item.value, key as string) }}</div>
          <div class="meta">
            <span class="provider">{{ item.provider }}</span>
            <span v-if="item.metadata?.currency" class="currency">{{ item.metadata.currency }}</span>
          </div>
        </div>
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
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 3rem;
  border-bottom: 1px solid #1e293b;
  padding-bottom: 1rem;
}

h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #f8fafc;
  margin: 0;
}

.refresh-btn {
  background-color: #3b82f6;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background-color: #2563eb;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.card h2 {
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8;
  margin: 0 0 0.5rem 0;
}

.value {
  font-size: 2.25rem;
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: 1rem;
}

.meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #64748b;
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
}

.loading {
  text-align: center;
  color: #94a3b8;
  font-size: 1.125rem;
}
</style>

