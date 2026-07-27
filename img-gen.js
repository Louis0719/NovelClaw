#!/usr/bin/env node
/**
 * 多后端图生图脚本 (最终版)
 * 用法: node img-gen.js "提示词" [输出文件] [尺寸]
 *
 * 【重要】请设置环境变量或复制 .env.example
 */

require('dotenv').config();
const https = require('https');
const http = require('http');
const fs = require('fs');

// API Keys (从环境变量读取)
const HUNYUAN_KEY = process.env.HUNYUAN_API_KEY || 'your_hunyuan_api_key_here';
const IMG_KEY = process.env.IMG_API_KEY || 'your_img_api_key_here';
const IMG_BASE = process.env.IMG_API_BASE || 'https://api.ohmygpt.com';

const args = process.argv.slice(2);
const prompt = args[0];
if (!prompt) {
    console.log('用法: node img-gen.js "提示词" [输出文件] [尺寸]');
    process.exit(1);
}
