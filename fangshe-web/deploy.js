#!/usr/bin/env node
/**
 * 纺设云 - 腾讯云SCF云函数部署脚本
 * 使用 TC3-HMAC-SHA256 签名
 */

const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

// ============ 配置 ============
const CONFIG = {
  secretId: process.env.TENCENT_SECRET_ID || 'your_secret_id_here',
  secretKey: process.env.TENCENT_SECRET_KEY || 'your_secret_key_here',
  region: 'ap-guangzhou',
  functionName: 'hunyuan-generate',
  namespace: 'default',
  handler: 'index.main_handler',
  runtime: 'Nodejs18.x',
  timeout: 60,
  memorySize: 256,
};

// 读取云函数代码
const scfCode = fs.readFileSync(path.join(__dirname, 'scf-handler.js'), 'utf8');

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

// ============ 腾讯云 API 签名 ============
function signRequest(action, payload) {
  const now = new Date();
  const ts = Math.floor(now.getTime() / 1000);
  const date = now.toISOString().split('T')[0];
  const service = 'scf';
  const host = `scf.${CONFIG.region}.myqcloud.com`;

  const payloadHash = sha256(JSON.stringify(payload));

  const httpRequestMethod = 'POST';
  const canonicalUri = '/';
  const canonicalQueryString = '';
  const canonicalHeaders = `content-type:application/json\nhost:${host}\n`;
  const signedHeaders = 'content-type;host';

  const canonicalRequest = [
    httpRequestMethod,
    canonicalUri,
    canonicalQueryString,
    canonicalHeaders,
    signedHeaders,
    payloadHash
  ].join('\n');

  const hashedCanonicalRequest = sha256(canonicalRequest);
  const stringToSign = [
    'TC3-HMAC-SHA256',
    ts,
    `${date}/${service}/tc3_request`,
    hashedCanonicalRequest
  ].join('\n');

  const signature = tc3Sign(CONFIG.secretKey, date, service, stringToSign);

  const authorization = `TC3-HMAC-SHA256 Credential=${CONFIG.secretId}/${date}/${service}/tc3_request, SignedHeaders=${signedHeaders}, Signature=${signature}`;

  return {
    authorization,
    ts,
    host,
    action,
    payload
  };
}

// ============ 发送请求 ============
function callAPI(action, payload) {
  return new Promise((resolve, reject) => {
    const { authorization, ts, host } = signRequest(action, payload);
    const body = JSON.stringify(payload);

    const options = {
      hostname: host,
      port: 443,
      path: '/',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Host': host,
        'X-TC-Action': action,
        'X-TC-Version': '2018-04-16',
        'X-TC-Timestamp': String(ts),
        'X-TC-Region': CONFIG.region,
        'Authorization': authorization,
        'Content-Length': Buffer.byteLength(body)
      }
    };

    console.log(`  📡 调用: ${action}`);
    
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          resolve(result);
        } catch {
          resolve({ raw: data });
        }
      });
    });

    req.on('error', reject);
    req.setTimeout(30000, () => {
      req.destroy();
      reject(new Error('请求超时 (30s)'));
    });

    req.write(body);
    req.end();
  });
}

// ============ 部署流程 ============
async function deploy() {
  console.log('🚀 纺设云 - 腾讯云SCF云函数部署\n');
  console.log(`📛 函数名: ${CONFIG.functionName}`);
  console.log(`📍 区域: ${CONFIG.region}`);
  console.log(`⏱️ 超时: ${CONFIG.timeout}s`);
  console.log(`💾 内存: ${CONFIG.memorySize}MB`);
  console.log('');

  // 检查函数是否存在
  console.log('1️⃣ 检查现有函数...');
  let functionExists = false;
  
  try {
    const checkResult = await callAPI('GetFunction', {
      FunctionName: CONFIG.functionName,
      Namespace: CONFIG.namespace
    });
    
    if (checkResult.Response && checkResult.Response.FunctionName === CONFIG.functionName) {
      console.log('  ✅ 函数已存在，将执行更新');
      functionExists = true;
    } else {
      console.log('  ℹ️ 函数不存在，将创建新函数');
    }
  } catch (e) {
    console.log(`  ⚠️ 检查失败: ${e.message}，继续尝试创建`);
  }

  // 准备代码包
  console.log('\n2️⃣ 打包代码...');
  const wrapperCode = `
exports.main_handler = async (event, context) => {
  ${scfCode}
};
  `.trim();
  
  // 打包为 zip (gzip压缩)
  const gzipped = zlib.gzipSync(Buffer.from(wrapperCode));
  const zipBase64 = gzipped.toString('base64');
  console.log(`  📦 代码包: ${(gzipped.length / 1024).toFixed(1)}KB (压缩后)`);

  try {
    if (functionExists) {
      console.log('\n3️⃣ 更新云函数代码...');
      const updateResult = await callAPI('UpdateFunctionCode', {
        FunctionName: CONFIG.functionName,
        ZipFile: zipBase64,
        Handler: CONFIG.handler,
        Namespace: CONFIG.namespace
      });

      if (updateResult.Response) {
        console.log('  ✅ 代码更新成功!');
      } else if (updateResult.Error) {
        console.log(`  ❌ 更新失败: ${updateResult.Error.Message}`);
        return;
      }
    } else {
      console.log('\n3️⃣ 创建云函数...');
      const createResult = await callAPI('CreateFunction', {
        FunctionName: CONFIG.functionName,
        Handler: CONFIG.handler,
        Runtime: CONFIG.runtime,
        Code: {
          ZipFile: zipBase64
        },
        Description: '纺设云定制 - AI生图云函数 (混元2.0)',
        Timeout: CONFIG.timeout,
        MemorySize: CONFIG.memorySize,
        Namespace: CONFIG.namespace
      });

      if (createResult.Response) {
        console.log('  ✅ 云函数创建成功!');
      } else if (createResult.Error) {
        console.log(`  ❌ 创建失败: ${createResult.Error.Message}`);
        
        // 可能是配额不足，尝试使用免费配额配置
        if (createResult.Error.Message && createResult.Error.Message.includes('配额')) {
          console.log('\n  💡 提示: 云函数配额可能已用完');
          console.log('  请前往控制台手动创建: https://console.cloud.tencent.com/scf');
        }
        return;
      }
    }

    // 配置环境变量 (可选)
    console.log('\n4️⃣ 配置环境变量...');
    try {
      await callAPI('PutFunctionConfiguration', {
        FunctionName: CONFIG.functionName,
        Environment: {
          Variables: [
            { Key: 'NODE_ENV', Value: 'production' }
          ]
        },
        Namespace: CONFIG.namespace
      });
      console.log('  ✅ 环境变量配置完成');
    } catch (e) {
      console.log(`  ⚠️ 环境变量配置跳过: ${e.message}`);
    }

    console.log('\n5️⃣ 创建API网关触发器...');
    const triggerName = `hunyuan-apigw-${Date.now()}`;
    
    try {
      const triggerResult = await callAPI('CreateTrigger', {
        FunctionName: CONFIG.functionName,
        TriggerName: triggerName,
        Type: 'apigw',
        TriggerDesc: JSON.stringify({
          api陵号: triggerName,
          integratedResponse: true,
          requestParallelism: 1
        }),
        Namespace: CONFIG.namespace
      });

      if (triggerResult.Response) {
        console.log('  ✅ API网关触发器创建成功!');
      } else if (triggerResult.Error) {
        if (triggerResult.Error.Message && triggerResult.Error.Message.includes('already exists')) {
          console.log('  ℹ️ 触发器已存在，跳过');
        } else {
          console.log(`  ⚠️ 触发器: ${triggerResult.Error.Message}`);
        }
      }
    } catch (e) {
      console.log(`  ⚠️ 触发器创建跳过: ${e.message}`);
    }

    console.log('\n' + '='.repeat(50));
    console.log('✅ 部署完成!\n');
    console.log('📋 下一步操作:');
    console.log('  1. 访问 https://console.cloud.tencent.com/scf');
    console.log('  2. 找到函数: ' + CONFIG.functionName);
    console.log('  3. 点击「触发管理」→「API网关」');
    console.log('  4. 复制「访问地址」(格式: https://service-xxx.gz-xxxx.myqcloud.com)');
    console.log('  5. 把地址发给我，我帮您填入 config.js');
    console.log('='.repeat(50));

  } catch (e) {
    console.error('\n❌ 部署失败:', e.message);
    console.log('\n💡 备选方案 - 手动部署:');
    console.log('  1. 打开 https://console.cloud.tencent.com/scf');
    console.log('  2. 新建函数');
    console.log('     - 名称: hunyuan-generate');
    console.log('     - 运行时: Node.js 18.x');
    console.log('     - 入口: index.main_handler');
    console.log('  3. 上传 scf-handler.js 代码');
    console.log('  4. 创建API网关触发器');
    console.log('  5. 把访问地址发给我');
  }
}

// 运行
deploy().then(() => {
  process.exit(0);
}).catch(e => {
  console.error('❌ 错误:', e);
  process.exit(1);
});
