/**
 * 纺设云定制 - AI生图后端服务
 * 使用 Cloudflare Workers 或 Node.js 部署
 * 
 * 腾讯混元2.0 文生图 API
 * 文档: https://cloud.tencent.com/document/api/柄号/1682
 */

const https = require('https');
const crypto = require('crypto');

// ============ 配置（请替换为您自己的密钥）============
const CONFIG = {
  secretId: process.env.TENCENT_SECRET_ID || 'your_secret_id_here',      // ✅ 已配置
  secretKey: process.env.TENCENT_SECRET_KEY || 'your_secret_key_here',        // ✅ 已配置
  region: 'ap-guangzhou',
};

// ============ 签名函数 ============
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

// ============ 构建签名 ============
function buildAuth(action, payload) {
  const now = new Date();
  const ts = Math.floor(now.getTime() / 1000);
  const date = now.toISOString().split('T')[0];
  const service = 'hunyuan';
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
    ts
  };
}

// ============ 发送请求 ============
function httpsPost(endpoint, params, headers) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(params);
    const url = new URL(endpoint);

    const options = {
      hostname: url.hostname,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        ...headers,
      },
      timeout: 60000,
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
    req.on('timeout', () => { req.destroy(); reject(new Error('请求超时')); });
    req.write(body);
    req.end();
  });
}

// ============ 混元文生图 ============
async function generateImage(prompt, productType, styleTags) {
  const PRODUCT_MAP = {
    bijou: 'bedding four-piece set quilt cover pillowcase',
    pillow: 'pillow cushion',
    curtain: 'curtain window drapery',
    cushion: 'throw pillow cushion',
    blanket: 'blanket throw',
    tablecloth: 'tablecloth placemat',
  };

  const prod = PRODUCT_MAP[productType] || 'home textile fabric';
  const style = styleTags?.length ? styleTags.join(', ') : 'high quality fabric texture';
  
  const params = {
    Prompt: `${prompt}, ${prod}, seamless pattern, detailed texture, ${style}, 4K`,
    NegativePrompt: 'low quality, blurry, watermark, text, logo, deformed, ugly, bad anatomy, extra fingers',
    Width: 1024,
    Height: 1024,
    Style: 'photo',
    CfgScale: 7.5,
    Steps: 25,
  };

  const { auth, ts } = buildAuth('GenerateImages', params);

  const data = await httpsPost('https://hunyuan.tencentcloudapi.com', params, {
    'Authorization': auth,
    'X-TC-Action': 'GenerateImages',
    'X-TC-Version': '2023-09-01',
    'X-TC-Timestamp': String(ts),
    'X-TC-Region': CONFIG.region,
  });

  if (!data?.Response) throw new Error(`API异常: ${JSON.stringify(data)}`);
  const { Error: err, Images, TaskId } = data.Response;
  if (err) throw new Error(`混元错误: ${err.Code} - ${err.Message}`);

  if (Images?.length > 0) {
    return { status: 'completed', images: Images.map((img, i) => ({ url: img.Url || img.ImageUrl, index: i })), taskId: TaskId };
  }

  if (TaskId) {
    return { status: 'pending', taskId: TaskId, pollInterval: 3000 };
  }

  throw new Error('混元API返回无可用数据');
}

// ============ 查询任务 ============
async function queryTask(taskId) {
  const params = { TaskId: taskId };
  const { auth, ts } = buildAuth('QueryImages', params);

  const data = await httpsPost('https://hunyuan.tencentcloudapi.com', params, {
    'Authorization': auth,
    'X-TC-Action': 'QueryImages',
    'X-TC-Version': '2023-09-01',
    'X-TC-Timestamp': String(ts),
    'X-TC-Region': CONFIG.region,
  });

  if (!data?.Response) return { taskId, status: 'failed', images: [], error: JSON.stringify(data) };
  const { Error: err, Images, Status } = data.Response;
  if (err) return { taskId, status: 'failed', images: [], error: err.Message };

  const statusMap = { 0: 'pending', 1: 'completed', 2: 'failed' };
  return {
    taskId,
    status: statusMap[Status] || 'pending',
    images: Images?.map((img, i) => ({ url: img.Url || img.ImageUrl, index: i })) || [],
  };
}

// ============ Express 服务器（Node.js部署）============
// 使用: node generate.js
const http = require('http');

const server = http.createServer(async (req, res) => {
  // CORS 头
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  if (req.method !== 'POST' || !req.url.startsWith('/generate')) {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not Found' }));
    return;
  }

  let body = '';
  req.on('data', chunk => body += chunk);
  req.on('end', async () => {
    try {
      const { action, prompt, productType, styleTags, taskId } = JSON.parse(body);

      if (action === 'query') {
        const result = await queryTask(taskId);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ code: 0, data: result }));
        return;
      }

      // generate
      const result = await generateImage(prompt, productType || 'bijou', styleTags || []);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ code: 0, data: result }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ code: -1, msg: err.message }));
    }
  });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`🎨 纺设云定制 AI生图服务已启动: http://localhost:${PORT}`);
  console.log(`📡 调用方式: POST ${PORT}/generate`);
  console.log(`   参数: { prompt, productType, styleTags }`);
});
