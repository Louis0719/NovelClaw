/**
 * 混元2.0 API 测试脚本 - 使用官方 SDK
 *
 * 【重要】请复制 .env.example 为 .env 并填写实际配置
 */
require('dotenv').config();
const tencentcloud = require('tencentcloud-sdk-nodejs');
const Hunyuan = tencentcloud.hunyuan;

// 直接打印可用方法
const client = new Hunyuan.hunyuan20230901.Client({
  credential: {
    secretId: process.env.TENCENT_SECRET_ID || 'your_secret_id_here',
    secretKey: process.env.TENCENT_SECRET_KEY || 'your_secret_key_here',
  },
  region: process.env.TENCENT_REGION || 'ap-guangzhou',
});

console.log('可用方法:');
Object.keys(Object.getPrototypeOf(client)).filter(k => !k.startsWith('_') && typeof client[k] === 'function').forEach(k => console.log(' -', k));

// 尝试获取 API 信息
console.log('\n尝试调用 DescribeApiInfo...');
