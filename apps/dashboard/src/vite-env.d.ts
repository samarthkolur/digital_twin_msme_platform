/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_CONFIG_URL: string;
  readonly VITE_COPILOT_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
