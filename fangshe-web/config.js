/**
 * 纺设云 - API 配置
 *
 * 【重要】请复制 .env.example 为 .env 并填写实际配置
 * 配置参考: .env.example
 */

// 方案1: 腾讯混元2.0 (推荐，免费额度)
export const HUNYUAN_CONFIG = {
  enabled: true,  // 设为 true 启用
  apiUrl: 'https://hunyuan.tencentcloudapi.com',
  secretId: process.env.TXY_SECRET_ID || 'your_secret_id_here',
  secretKey: process.env.TXY_SECRET_KEY || 'your_secret_key_here',
  region: process.env.TXY_REGION || 'ap-guangzhou',
};

// 方案2: 自建服务器（Node.js部署）
export const SELF_HOSTED_CONFIG = {
  enabled: false,  // 设为 true 启用
  apiUrl: 'http://localhost:3000',  // 替换为您的服务器地址
};

// 方案3: 第三方API（如需要）
export const THIRD_PARTY_CONFIG = {
  enabled: false,
  provider: 'dreamina',  // 或 'midjourney', 'stable Diffusion'
  apiKey: process.env.THIRD_PARTY_API_KEY || 'your_api_key_here',
  apiUrl: 'https://api.example.com',
};

// 当前使用的方案
export const CURRENT_CONFIG = HUNYUAN_CONFIG; // 改为 HUNYUAN_CONFIG 启用混元
