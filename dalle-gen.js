/**
 * DALL-E 3 图片生成脚本 (via ohmygpt.com)
 * 用法: node dalle-gen.js "提示词" [输出文件]
 *
 * 【重要】请设置环境变量或复制 .env.example
 */

require('dotenv').config();
const https = require('https');
const fs = require('fs');
const path = require('path');

const API_KEY = process.env.IMG_API_KEY || 'your_img_api_key_here';
const BASE_URL = process.env.IMG_API_BASE || 'https://api.ohmygpt.com';

function httpPost(endpoint, body) {
  return new Promise((resolve, reject) => {
    const bodyStr = JSON.stringify(body);
    const url = new URL(endpoint, BASE_URL);
    const options = {
      hostname: url.hostname,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Length': Buffer.byteLength(bodyStr),
      },
    };
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch (e) { reject(new Error(`JSON parse error: ${data}`)); }
      });
    });
    req.on('error', reject);
    req.write(bodyStr);
    req.end();
  });
}

async function generate(prompt, outputFile) {
  console.log(`生成图片: ${prompt.substring(0, 50)}...`);
  const result = await httpPost('/v1/images/generations', {
    model: 'dall-e-3',
    prompt,
    n: 1,
    size: '1024x1024',
    response_format: 'b64_json',
  });
  if (result.data && result.data[0] && result.data[0].b64_json) {
    const imgData = Buffer.from(result.data[0].b64_json, 'base64');
    const outPath = outputFile || `dalle_${Date.now()}.png`;
    fs.writeFileSync(outPath, imgData);
    console.log(`✅ 已保存: ${outPath}`);
  } else {
    console.error('生成失败:', JSON.stringify(result, null, 2));
  }
}

const prompt = process.argv[2];
if (!prompt) {
  console.log('用法: node dalle-gen.js "提示词" [输出文件]');
  process.exit(1);
}
const outFile = process.argv[3];
generate(prompt, outFile).catch(console.error);
