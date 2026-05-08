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
