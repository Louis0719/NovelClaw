/**
 * 混元2.0 文生图 - 修正版
 * 正确的 API: TextToImageLite
 * 分辨率格式: "768:768", "720:1280", "1080:1920" 等
 * 
 * 【重要】请复制 .env.example 为 .env 并填写实际配置
 */
require('dotenv').config();
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');

const CONFIG = {
  secretId: process.env.TENCENT_SECRET_ID || 'your_secret_id_here',
  secretKey: process.env.TENCENT_SECRET_KEY || 'your_secret_key_here',
  region: process.env.TENCENT_REGION || 'ap-guangzhou',
};

function sha256(data) {
  return crypto.createHash('sha256').update(data, 'utf8').digest('hex');
}

function hmacSha256(key, msg) {
  return crypto.createHmac('sha256', key).update(msg, 'utf8').digest('hex');
}

function tc3Sign(secretKey, date, service, strToSign) {
  const kDate = hmacSha256('TC3' + secretKey, date);
  const kService = hmacSha256(kDate, service);
  const kSigning = hmacSha256(kService, 'tc3_request');
  return hmacSha256(kSigning, strToSign);
}

function buildAuth() {
  const now = new Date();
  const ts = Math.floor(now.getTime() / 1000);
  const date = now.toISOString().split('T')[0];
  const service = 'hunyuan';
  const payload = {};
  const hashedPayload = sha256(JSON.stringify(payload));

  const signedHeaders = 'content-type;host';
  const canonicalHeaders = `content-type:application/json\nhost:${service}.tencentcloudapi.com\n`;

  const canonicalRequest = [
    'POST', '/', '',
    canonicalHeaders,
    signedHeaders,
    hashedPayload
  ].join('\n');

  const hashedCanonReq = sha256(canonicalRequest);
  const stringToSign = [
    'TC3-HMAC-SHA256',
    ts,
    `${date}/${service}/tc3_request`,
    hashedCanonReq
  ].join('\n');

  const sig = tc3Sign(CONFIG.secretKey, date, service, stringToSign);

  return {
    auth: `TC3-HMAC-SHA256 Credential=${CONFIG.secretId}/${date}/${service}/tc3_request, SignedHeaders=${signedHeaders}, Signature=${sig}`,
    ts, date
  };
}

function request(action, payload) {
  return new Promise((resolve, reject) => {
    const { auth, ts, date } = buildAuth();
    const body = JSON.stringify(payload);

    const options = {
      hostname: 'hunyuan.tencentcloudapi.com',
      path: '/',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        'Authorization': auth,
        'Host': 'hunyuan.tencentcloudapi.com',
        'X-TC-Action': action,
        'X-TC-Version': '2023-09-01',
        'X-TC-Timestamp': String(ts),
        'X-TC-Region': CONFIG.region
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch { resolve({ raw: data }); }
      });
    });

    req.on('error', reject);
    req.setTimeout(60000, () => { req.destroy(); reject(new Error('timeout')); });
    req.write(body);
    req.end();
  });
}

function download(url, file) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const opts = { hostname: urlObj.hostname, path: urlObj.pathname, method: 'GET' };
    const req = https.request(opts, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        download(res.headers.location, file).then(resolve).catch(reject);
        return;
      }
      const stream = fs.createWriteStream(file);
      res.pipe(stream);
      stream.on('finish', () => resolve(file));
    });
    req.on('error', reject);
    req.end();
  });
}

async function main() {
  const prompt = process.argv[2] || '一个精致的奶油色系床品四件套，高档纯棉面料，细腻印花图案，温馨卧室场景，温暖治愈风格';
  const outFile = process.argv[3] || 'hunyuan-output.png';

  console.log('📝 Prompt:', prompt);

  console.log('🚀 提交 TextToImageLite...');
  const result = await request('TextToImageLite', {
    Prompt: prompt,
    NegativePrompt: 'low quality, blurry, watermark, text, logo, deformed, ugly, bad anatomy',
    Resolution: '1080:1920',  // 小红书封面 9:16
    RspImgType: 'url',
    LogoAdd: 0,  // 不加水印
  });

  console.log('📦 返回:', JSON.stringify(result, null, 2));

  if (result.Response) {
    const { Error, ResultImage } = result.Response;
    if (Error) {
      console.error('❌ 错误:', Error.Code, '-', Error.Message);
    } else if (ResultImage) {
      console.log('✅ 生成成功!');
      if (ResultImage.startsWith('http')) {
        console.log('🔗 图片URL:', ResultImage);
        await download(ResultImage, outFile);
        console.log('📥 已保存到:', outFile);
      } else {
        // base64
        fs.writeFileSync(outFile, Buffer.from(ResultImage, 'base64'));
        console.log('📥 Base64图片已保存到:', outFile);
      }
    } else {
      console.log('📋 响应结构:', JSON.stringify(result.Response, null, 2));
    }
  }
}

main().catch(console.error);
