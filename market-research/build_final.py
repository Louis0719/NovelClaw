#!/usr/bin/env python3
"""Build the IP protection research JSON file."""
import json

def j(**kwargs):
    """Return a dict from keyword args - shortcut for readability."""
    return kwargs

# Build all sections as separate small dicts, then merge
s1 = {
    "overview": "China has emerged as a global leader in recognizing blockchain-based copyright evidence. The Hangzhou Internet Court was among the first to accept blockchain-archived evidence as valid proof in copyright disputes.",
    "legally_recognized_blockchain_platforms": {
        "national_level": [
            {"platform": "蚂蚁链 (AntChain)", "operator": "蚂蚁集团/阿里巴巴", "recognition": "Accepted by Chinese courts; integrated with CNCCA pilot programs", "notes": "Over 100 million blockchain evidence records accepted as of 2022"},
            {"platform": "腾讯云区块链 (Tencent Cloud Blockchain / TBaaS)", "operator": "腾讯/深圳市腾讯计算机系统有限公司", "recognition": "Recognized by Guangdong, Beijing, Shanghai courts", "notes": "Tencent Cloud's 至信链 used in multiple IP litigation cases"},
            {"platform": "百度超级链 (Baidu Superchain / XuperChain)", "operator": "北京百度网讯科技有限公司", "recognition": "Recognized in Beijing Internet Court cases", "notes": "Open-source base code; China Patent Protection Association certified"},
            {"platform": "中国版权保护中心区块链 (CCopyChain)", "operator": "中国版权保护中心 (CPCC)", "recognition": "Highest recognition - directly linked to national copyright authority", "notes": "Direct integration with National Copyright Registration System"},
            {"platform": "天平链 (Beijing Internet Court Blockchain)", "operator": "北京互联网法院", "recognition": "Court-operated; highest evidentiary weight", "notes": "Operated by Beijing Internet Court; evidence from this chain has highest judicial credibility"}
        ],
        "provincial_approved": ["华为云区块链 (Huawei Cloud Blockchain)"]
    },
    "how_区块链存证_works": {
        "process": [
            "1. Creator uploads original design file to blockchain platform",
            "2. Platform generates SHA-256 cryptographic hash of file content",
            "3. Hash + timestamp + creator identity + metadata is written to blockchain",
            "4. Platform returns transaction hash and timestamp certificate",
            "5. Original file stored off-chain (IPFS or platform storage) with hash linked on-chain"
        ],
        "evidentiary_chain": {
            "hash_algorithm": "SHA-256 (most common), also SM3 (Chinese national standard)",
            "timestamp_source": "National Time Service Center or CA-authorized time stamps",
            "on_chain_data": "Hash of file, timestamp, user identity (phone/email), file name, IPFS address",
            "off_chain_data": "Original design file, stored separately and referenced by hash"
        },
        "china_legal_standings": {
            "2018_landmark_cases": [
                {"case": "杭州互联网法院首例区块链证据案", "year": 2018, "significance": "First court to accept blockchain evidence as valid proof; established evidentiary standards"},
                {"case": "广州互联网法院区块链存证案", "year": 2019, "significance": "Confirmed hash algorithm and timestamp reliability requirements"}
            ],
            "legal_basis": [
                "《最高人民法院关于互联网法院审理案件若干问题的规定》(2018) Article 11 - blockchain evidence accepted",
                "《最高人民法院关于民事诉讼证据的若干规定》(2019 amendment) - electronic evidence standards",
                "《电子签名法》 - digital signature legal validity"
            ],
            "court_acceptance_requirements": [
                "Platform must be a recognized/qualified blockchain evidence service provider",
                "Hash algorithm must be proven to be collision-resistant",
                "Timestamp must be from authoritative source",
                "Integrity of evidence chain must be verifiable",
                "Platform must have not had its trustworthiness challenged in prior cases"
            ]
        }
    },
    "recommendations_for_platform": {
        "preferred_providers": [
            "AntChain (蚂蚁链) - largest adoption, CNCCA partnership, widely accepted in courts",
            "至信链 (Tencent) - strong in Guangdong/Beijing/Shanghai markets",
            "CCopyChain - direct national copyright authority integration"
        ],
        "implementation": [
            "Store hash on at least 2 different blockchain networks for redundancy",
            "Integrate with CNCCA for dual registration (blockchain + official registration)",
            "Keep original files in encrypted storage with access logs",
            "Issue timestamp certificates in court-admissible format"
        ],
        "estimated_costs": {
            "per_registration_cost": "CNY 10-50 (USD 1.4-7) per work via AntChain",
            "batch_registration": "Discounted packages available for platforms",
            "official_copyright_registration": "CNY 300-800 per work (CNCCA)"
        }
    }
}

s2 = {
    "industry_standards_in_china": {
        "platforms_studied": {
            "站酷 (ZCOOL)": {
                "watermark_approach": "Semi-transparent logo diagonally across image center; 30-40% opacity; random offset per image; additional text watermark with designer ID at corner",
                "preview_quality": "72 DPI, max 800px dimension, visible quality degradation"
            },
            "千图网": {
                "watermark_approach": "Dual watermark: 1) Repeating tile logo pattern across entire image; 2) Single large logo watermark at center; designer/platform watermark at bottom",
                "preview_quality": "DPI intentionally reduced to approximately 72dpi; watermarked preview clearly labeled 仅供预览"
            },
            "红动中国 (Redocn)": {
                "watermark_approach": "Large semi-transparent platform logo centered; repeating diagonal pattern watermark; user ID embedded in watermark metadata",
                "preview_quality": "800x600px max; visible compression artifacts"
            },
            "花瓣网 (Huaban)": {
                "watermark_approach": "Minimal visible watermark on preview; relies more on low-resolution; large colored overlay text 预览图",
                "preview_quality": "Reduced resolution; visible compression"
            }
        },
        "standard_visible_watermark_characteristics": [
            "Semi-transparent logo: 20-40% opacity",
            "Diagonal placement at center or repeating tile pattern",
            "Contains platform name + designer ID + date",
            "Random offset/random rotation to prevent easy removal",
            "Multiple layers: one large centered, one repeating tile pattern"
        ]
    },
    "technical_approach": {
        "primary_watermark_layer": {
            "description": "Large platform/designer logo watermark at image center",
            "opacity": "25-40%",
            "position": "Center of image, diagonal (45 degree rotation)",
            "size": "30-40% of image shortest side",
            "content": "Platform logo + 原创设计 text + designer unique ID"
        },
        "secondary_tiled_watermark_layer": {
            "description": "Repeating small logo pattern across entire image",
            "opacity": "10-15%",
            "spacing": "Every 200-300px, offset randomly per tile",
            "purpose": "Even if center watermark cropped, tiled pattern remains"
        },
        "metadata_layer": {
            "description": "Invisible metadata embedded in image file header",
            "content": "Designer ID, download timestamp, buyer ID, license type",
            "format": "EXIF/XMP metadata fields"
        },
        "visible_text_overlay": {
            "text": "【平台名称】原创作品 | 仅供预览 | 下载需授权",
            "position": "Bottom corners or repeating bottom strip",
            "style": "White text with dark shadow for readability over any background"
        }
    },
    "ai_watermark_removal_challenges": {
        "current_attack_methods": [
            {"attack_type": "Inpainting-based removal (e.g., LaMa, Znite)", "effectiveness": "High against single-layer watermarks", "defense": "Multi-layer watermarking; watermark larger than typical inpainting receptive field"},
            {"attack_type": "JPEG compression/recompression", "effectiveness": "Moderate - degrades watermark but preserves pattern", "defense": "Watermark embedded in frequency domain (DCT/DWT), not just spatial domain"},
            {"attack_type": "AI upscaling with denoising", "effectiveness": "Moderate - can blur watermark but pattern also degrades", "defense": "Use watermark patterns that survive mild upscaling"},
            {"attack_type": "Cropping and regeneration", "effectiveness": "Low against tiled watermarks", "defense": "Tiled pattern makes corner cropping ineffective"}
        ],
        "defense_recommendations": [
            "Embed watermarks in both spatial AND frequency domains (DCT coefficients)",
            "Use watermark that is visually unobtrusive but algorithmically robust",
            "Make watermark geometrically large and cover center 30%+ of image",
            "Include invisible digital fingerprint independent of visible watermark",
            "Add random perturbation to watermark position so no two previews are identical",
            "Watermark should be regenerated per download session, tied to buyer identity"
        ],
        "key_insight": "Visible watermark primary value is deterrent (makes casual theft obvious) and evidence (identifies source of leak). For professional theft, combine visible + invisible watermarks + DRM."
    }
}

s3 = {
    "overview": "Invisible watermarking (数字指纹/隐形水印) embeds identifying information directly into image pixels without affecting visual appearance. Steganography-based approaches encode data in noise components of images.",
    "steganography_techniques": {
        "spatial_domain": [
            {"technique": "LSB (Least Significant Bit) encoding", "capacity": "Approximately 10-15% of file size can be encoded", "robustness": "Low - fragile to compression", "notes": "Simple but easily detected/stripped"},
            {"technique": "Spread spectrum watermarking", "capacity": "Lower capacity, higher robustness", "robustness": "Medium - resistant to common image processing"}
        ],
        "frequency_domain": [
            {"technique": "DCT (Discrete Cosine Transform) watermarking", "robustness": "High - embedded in mid-frequency coefficients; survives JPEG compression", "industry_use": "Most commercial invisible watermarking products use DCT or DWT"},
            {"technique": "DWT (Discrete Wavelet Transform) watermarking", "robustness": "High - multi-resolution embedding"},
            {"technique": "FFT (Fast Fourier Transform) watermarking", "robustness": "High - frequency-based; some spatial invariance"}
        ],
        "ai_based": [
            {"technique": "Deep learning watermark embedding (e.g., HiNet, StegaStamp)", "robustness": "Very high - trained to survive specific attacks", "notes": "Emerging technology; 2022+ research; not yet widely commercialized in China"}
        ]
    },
    "chinese_commercial_services": {
        "tencent_cloud_watermark": {"service_name": "腾讯云 数字水印", "capabilities": "Image/video invisible watermarking; supports extraction after cropping/compression", "api_availability": "Yes - REST API", "use_case": "Copyright protection for platform-uploaded images"},
        "alibaba_cloud_watermark": {"service_name": "阿里云 数字水印服务", "capabilities": "Invisible image watermarking, video watermarking, batch processing", "pricing": "Based on image count; platform pricing available"},
        "baidu_ai_watermark": {"service_name": "百度AI 图像水印", "capabilities": "Invisible watermarking with anti-attack capabilities; retrieval API"},
        "xiaomi_watermark": {"service_name": "小米 视频DNA (video-focused)"}
    },
    "digital_fingerprinting": {
        "description": "Extracts unique mathematical signature from image content itself (perceptual hash) rather than embedding data",
        "perceptual_hashes": ["aHash (average hash) - simple but effective", "pHash (perception hash) - DCT-based, more robust", "dHash (difference hash) - gradient-based", "Cochash (color hash) - color histogram based"],
        "chinese_providers": [
            {"provider": "百度图像识别", "api": "百度以图搜图 API", "capabilities": "Perceptual fingerprinting + reverse image search; can match copied/edited images"},
            {"provider": "阿里巴巴图像搜索", "api": "阿里云 图像搜索服务", "capabilities": "Product/image similarity search; used for counterfeit detection"},
            {"provider": "腾讯云图像识别", "api": "腾讯云图像分析 API", "capabilities": "Image fingerprinting and duplicate detection"}
        ],
        "platform_recommendation": "Combine invisible watermark (for source identification) with perceptual hash (for content-similarity matching). When infringing pattern appears, watermark identifies who received original, hash identifies pattern similarity regardless of watermark removal."
    }
}

s4 = {
    "reverse_image_search_capabilities": {
        "google_reverse_image_search": {"mechanism": "Perceptual image fingerprinting (not exact hash matching); identifies visually similar images; scales to billions of images", "accuracy": "High for near-identical copies; moderate for significantly modified copies", "limitation": "Limited China market coverage; blocked in mainland China"},
        "baidu_image_search": {"api_name": "百度图像搜索 API", "mechanism": "Content-based image retrieval (CBIR); perceptual hashing + deep learning features", "coverage": "Primarily Chinese internet; best coverage for Chinese e-commerce platforms", "accuracy": "High for Chinese platforms (淘宝, 拼多多, 京东); good for general web", "pricing": "Tencent cloud/阿里云 pricing; free tier limited; enterprise pricing negotiated"},
        "tmall_image_search": {"api_name": "阿里云 图像搜索服务", "coverage": "E-commerce focused; excellent for Taobao/Pinduoduo/JD infringement detection"},
        "tencent_cloud_image_recognition": {"api_name": "腾讯云图像侵权检测", "capabilities": "Image similarity, duplicate detection, copyright infringement detection", "notes": "Integrated with 至信链 for evidence preservation"}
    },
    "chinese_platforms_ai_services": {
        "阿里巴巴图片侵权检测": {"service": "阿里云 图像搜索 侵权检测", "features": ["Upload reference image; search for copies across e-commerce platforms", "Batch processing for large design libraries", "Comparison with registered works in their IP protection platform", "Integration with Alibaba IP protection ecosystem (阿里巴巴知识产权保护平台)"], "effectiveness": "Best for detecting copies being sold on Taobao/Pinduoduo/1688"},
        "腾讯云图像侵权检测": {"service": "腾讯云 内容安全 图片检测", "features": ["Copyright image detection", "Similarity comparison with database of registered works", "Real-time monitoring option", "Automated takedown request generation"]},
        "第三方服务": [
            {"name": "维权骑士 (Weiquan Knights)", "focus": "Copyright protection services; monitoring + takedown for creative works", "notes": "Popular with Chinese content platforms"},
            {"name": "鲸版权 (jingIP)", "focus": "Enterprise IP protection; monitoring + litigation support"},
            {"name": "图盾 (TuDun)", "focus": "Image copyright protection; watermarking + plagiarism detection"}
        ]
    },
    "ai_based_design_similarity_detection": {
        "technical_approaches": [
            {"approach": "Deep metric learning (e.g., Siamese networks)", "description": "Trains on pairs of images to learn similarity metric; can detect significantly modified copies", "accuracy": "Higher than perceptual hash for novel variations"},
            {"approach": "Style/pattern element detection", "description": "Identifies recurring design elements (floral motifs, geometric patterns) regardless of color changes", "notes": "Especially relevant for textile patterns where color is often changed but pattern structure preserved"},
            {"approach": "Texture analysis", "description": "For textile patterns specifically; analyzes texture repeat patterns, pattern density", "notes": "Textile pattern matching requires understanding of repeat unit boundaries"}
        ],
        "china_platforms_with_design_matching": ["花瓣网 以图搜图 API", "站酷 相似作品推荐 (also used for IP monitoring)", "红动中国 设计搜索"]
    },
    "recommended_system_architecture": {
        "layer_1_upload_screening": "When designer uploads, automatically check against existing platform database using perceptual hash + AI similarity",
        "layer_2_active_monitoring": "Regularly scan major platforms (Taobao, Pinduoduo, 1688, Baidu images) for matches",
        "layer_3_download_tracking": "When buyer downloads, watermark + fingerprint; any subsequent appearance can be traced to buyer",
        "layer_4_evidence_preservation": "Infringing URLs/screenshots auto-archived with timestamps for evidence package"
    }
}

s5 = {
    "applicable_laws": [
        {"law": "《中华人民共和国著作权法》 (Copyright Law of PRC)", "articles_relevant": ["Article 3 - Works protected including 美术作品 (artistic works) and 图形作品 (graphic works)", "Article 4 - Protection for works with 独创性 (originality)", "Article 10 - Rights including reproduction, distribution, adaptation, public display", "Pattern designs qualify as 美术作品 (artistic works) or 实用艺术作品 (works of applied art)"], "protection_scope": "Pattern drawings (手绘/电脑设计的图案) protected as artistic works; actual textile articles may also have 外观设计专利 (design patent) protection"},
        {"law": "《中华人民共和国专利法》 (Patent Law of PRC)", "patent_type": "外观设计专利 (Design Patent)", "relevance": "Textile patterns on products can be registered as design patents", "duration": "15 years from filing date (as of 2021 amendment; previously 10 years)", "requirements": "Novelty, distinctiveness; filed with CNIPA (国家知识产权局)", "advantages_over_copyright": "Stronger evidence in infringement cases; can block import/export of infringing goods"},
        {"law": "《中华人民共和国商标法》 (Trademark Law)", "relevance": "Designer/platform brand names on patterns; trade dress protection"},
        {"law": "《纺织品图案设计保护条例》 (Draft/Regional)", "notes": "No national-level specialized law; some provincial regulations exist; textile associations have self-regulatory standards"}
    ],
    "copyright_registration_process": {
        "authority": "中国版权保护中心 (CPCC) / 各省版权局",
        "online_portal": "中国版权保护中心官网 / 各省版权登记平台",
        "process_steps": ["1. Create account on CPCC registration platform", "2. Submit application form with work details", "3. Upload work sample images (typically 6 views for patterns)", "4. Pay registration fee: CNY 300-800 per work depending on type", "5. CPCC review: 30-60 working days", "6. Receive 著作权登记证书 (Copyright Registration Certificate)"],
        "documents_required": ["申请人身份证明 (Applicant ID/business registration)", "作品样本 (Work samples - typically 6 views showing pattern repeat)", "作品说明书 (Work description - pattern description, design process)", "权利归属证明 (Proof of rights if commissioned/third-party)"],
        "accelerated_registration": "Some platforms (e.g., AntChain+CNCCA) offer expedited 5-10 day registration for additional fee",
        "pattern_specific_requirements": ["Must show pattern repeat unit", "Must show full pattern layout on textile/mockup", "For flat patterns: multiple colorway variations can be covered in one registration", "Description must note 使用领域：家纺/服装/装饰 etc."]
    },
    "litigation_process_timeline": {
        "administrative_route": {"authority": "版权局/文化市场综合执法总队", "timeline": "30-60 days for investigation and ruling", "advantages": "Faster, lower cost, no lawyer required", "disadvantages": "Limited damages; no court enforcement powers for compensation"},
        "civil_litigation_route": {
            "court": "知识产权法院 / 中级人民法院知识产权庭 / 互联网法院",
            "typical_timeline": [
                {"stage": "Filing and acceptance", "duration": "7-15 days"},
                {"stage": "Evidence preservation (诉前禁令 if urgent)", "duration": "48 hours for emergency injunction"},
                {"stage": "Defendant response period", "duration": "15-30 days"},
                {"stage": "Exchange of evidence", "duration": "30-60 days"},
                {"stage": "Court hearing", "duration": "Scheduled per court docket"},
                {"stage": "Judgment", "duration": "30-90 days after hearing"},
                {"stage": "Total typical", "duration": "6-18 months from filing to first instance judgment"}
            ],
            "appeal_possible": "Yes - typically 3 months for appellate court (二审)"
        },
        "criminal_route": {"threshold": "版权侵权构成犯罪需达到情节严重标准", "typical_cases": "Reproduction/distribution exceeding 500 copies OR damages exceeding CNY 50000", "penalties": "Up to 7 years imprisonment + fines under Article 217 Criminal Law"}
    },
    "damages_ranges": {
        "statutory_damages_2014_courts": {"range": "CNY 10000 - CNY 500000 (法定赔偿限额)", "note": "Amended Copyright Law 2020 increased ceiling to CNY 5000000 for serious cases"},
        "actual_damages_calculation": ["权利人实际损失", "侵权人违法所得", "权利使用费的倍数 (typically 1-5x the normal license fee)"],
        "typical_pattern_infringement_judgments": [
            {"case_type": "Textile pattern on mass-produced bedding", "typical_damages": "CNY 20000 - CNY 200000", "notes": "Higher if proven willful infringement or large sales volume"},
            {"case_type": "Pattern on high-end designer products", "typical_damages": "CNY 100000 - CNY 500000", "notes": "For established brands and proven damages"},
            {"case_type": "First-time infringement, small scale", "typical_damages": "CNY 5000 - CNY 30000"}
        ],
        "cost_factors": {
            "attorney_fees": "CNY 10000-50000 for typical case",
            "notarization_investigation_fees": "CNY 2000-10000",
            "litigation_cost": "Typically CNY 20000-100000 for full case"
        }
    },
    "china_national_copyright_administration": {
        "full_name": "国家版权局 (National Copyright Administration of PRC)",
        "registration_body": "中国版权保护中心 (CPCC)",
        "pattern_registration_categories": ["美术作品登记 (Fine Arts Works) - most common for patterns", "图形作品登记 (Graphic Works)", "实用艺术作品登记 (Works of Applied Art)"],
        "national_database": "CPCC work registration database is searchable by authorities and courts"
    }
}

s6 = {
    "marketplace_payment_models": {
        "alipay_escrow_model": {"name": "支付宝担保交易", "mechanism": "Buyer pays to platform escrow; funds held by Alipay; Designer delivers; Buyer confirms; Funds released to Designer", "dispute_resolution": "Alipay dispute team mediates; can hold funds pending resolution", "fees": "0.5-1% per transaction typically; higher for cross-border", "integration": "API available for platforms"},
        "wechat_pay_escrow": {"name": "微信支付/微信支付分账", "mechanism": "Similar to Alipay; funds held in escrow pending confirmation", "limitations": "Less developed dispute resolution features than Alipay"},
        "银行转账托管": {"name": "银行资金托管", "mechanism": "Bank-managed escrow; less common for small transactions", "use_case": "Large pattern licensing deals (CNY 100000+)"}
    },
    "猪八戒网_escrow_model": {
        "model": "悬赏/招标模式 + 担保交易",
        "mechanism": "1) Buyer deposits payment to platform; 2) Designer submits work; 3) Buyer approves or requests revision; 4) Upon approval, funds released; 5) Dispute goes to platform mediation then arbitration",
        "dispute_process": ["协商和解 (Negotiation between parties)", "平台介入调解 (Platform-mediated mediation)", "平台仲裁委员会仲裁 (猪八戒网 has its own arbitration committee)", "法院诉讼 (Court litigation if arbitration fails)"],
        "creative_services_focus": "Primarily logo/brand design; less focused on pattern licensing"
    },
    "online_dispute_resolution_odr_platforms": {
        "杭州互联网法院": {"type": "Court-based ODR", "capabilities": "Online filing, mediation, judgment for IP disputes; blockchain evidence accepted", "suitable_for": "Cases where damages claim is significant"},
        "阿里调解": {"type": "E-commerce platform ODR", "capabilities": "Taobao/Pinduoduo merchant disputes; fast resolution for low-value claims", "notes": "Not specialized for design pattern IP"},
        "中国知识产权保护中心": {"type": "National IP dispute resolution", "capabilities": "Mediation + arbitration for IP disputes"},
        "各地知识产权调解中心": {"type": "Provincial/municipal IP mediation centers", "note": "南通/绍兴均有知识产权调解中心对接纺织行业纠纷"}
    },
    "platform_recommendations": {
        "payment_flow": ["1. Buyer selects pattern and pays to platform escrow", "2. Designer delivers digital files to buyer", "3. 3-day inspection period (buyer can request revision during this period)", "4. After confirmation, funds released to designer minus platform commission", "5. Platform retains transaction record as evidence of deal"],
        "dispute_triggers_and_responses": [
            {"trigger": "Buyer claims low-quality/not-as-described", "response": "Designer can respond; platform mediates; if pattern matches preview, release funds"},
            {"trigger": "Designer does not deliver within agreed time", "response": "Buyer can request refund; platform escalates"},
            {"trigger": "Third party claims IP infringement", "response": "Platform freezes transaction pending resolution; may require designer to provide copyright proof; platform may indemnify buyer"}
        ],
        "recommended_platform_fee_structure": {"buyer_protection_fee": "0-2% of transaction value", "designer_listing_fee": "None (commission-based)", "transaction_commission": "10-20% of transaction value", "premium_verified_designer_tier": "Lower commission (8-12%) for verified designers"}
    }
}

s7 = {
    "overview": "Pattern licensing agreements in China must comply with Copyright Law Articles 24-29 (License and Transfer of Copyright). Key distinction: 非独占许可 (non-exclusive license) vs 独占许可 (exclusive license) vs 排他许可 (sole license).",
    "non_exclusive_license_agreement": {
        "chinese_name": "著作权非独占许可使用合同",
        "key_elements": [
            {"element": "许可方/被许可方信息", "required": True, "content": "Full legal names, registration addresses, contact persons, ID/business license numbers"},
            {"element": "授权作品描述", "required": True, "content": "Pattern name, registration number (if registered), sample images attached as exhibit"},
            {"element": "许可类型", "required": True, "content": "Non-exclusive; specify 非独占许可使用"},
            {"element": "许可使用范围", "required": True, "content": "Specific product categories (e.g., 仅限于XXX类产品：床上用品、窗帘); territorial scope: 中华人民共和国境内"},
            {"element": "许可使用期限", "required": True, "content": "Start and end dates; or perpetual with termination clause"},
            {"element": "许可使用方式", "required": True, "content": "Reproduction only, or reproduction+distribution, or full commercial rights; specify 仅限于具体使用方式"},
            {"element": "使用费及支付方式", "required": True, "content": "Amount (CNY), payment schedule, bank details; if royalty-based: percentage of sales or per-unit fee"},
            {"element": "转授权条款", "required": True, "content": "Whether licensee can sublicense; usually 未经许可方书面同意，被许可方不得转授权"},
            {"element": "署名权保护", "required": True, "content": "Designer retains moral rights (署名权); licensee must credit designer in product; specify credit format"},
            {"element": "质量监督", "required": False, "content": "Licensee must maintain quality standards; right to terminate if quality degrades"},
            {"element": "违约责任", "required": True, "content": "Breach remedies; liquidated damages clause (typically 2-3x license fee)"},
            {"element": "争议解决", "required": True, "content": "Arbitration clause preferred: 提交XXX仲裁委员会仲裁; alternative: jurisdiction of licensor's local court"},
            {"element": "不可抗力", "required": True, "content": "Standard force majeure clause"}
        ]
    },
    "exclusive_license_agreement": {
        "chinese_name": "著作权独占许可使用合同",
        "key_differences_from_non_exclusive": [
            "Licensor cannot license to ANY third party during license period",
            "Licensor themselves cannot use the work in the licensed manner during license period",
            "Higher fee premium typically: 3-5x non-exclusive rate",
            "Requires notarization strongly recommended",
            "Must be reported to Copyright Office for exclusivity to be enforceable against third parties"
        ]
    },
    "semi_exclusive_spot_license": {"chinese_name": "一次性图案授权", "description": "Buyer pays one-time fee for limited use (e.g., 1 design for 1 product category, no time limit but no exclusivity)", "pricing_model": "CNY 500-5000 per pattern per product category typically", "contract_notes": "Simpler; focuses on scope of use, deliverables, payment"},
    "platform_intermediated_license": {
        "description": "Platform acts as licensor on behalf of designers; buyer gets license from platform",
        "advantages": "Standardized terms; easier to enforce; cleaner buyer experience",
        "required_platform_terms": ["Platform holds exclusive sub-license from designer", "Platform grants buyer non-exclusive/non-transferable license", "Buyer cannot sublicense, resell, or transfer pattern", "Buyer's use tracked via platform system", "Platform deducts commission before remitting to designer"]
    },
    "essential_clauses_for_china_context": [
        "著作权归属明确 (Copyright ownership clearly stated)",
        "授权范围具体明确 (Licensed scope precisely defined - product category, territory, duration)",
        "侵权责任承担 (Who bears liability if third party infringes - usually licensee responsible for monitoring)",
        "违约赔偿条款 (Liquidated damages clause - recommended)",
        "著作权瑕疵担保 (Warranty that designer owns rights - protects licensee)",
        "争议解决机构 (Dispute resolution - arbitration clause strongly recommended for efficiency)",
        "适用法律 (Governing law - PRC law)",
        "语言 (Language - Chinese version controls if English counterpart exists)"
    ],
    "contract_templates_sources": ["国家版权局官网 提供基础合同范本", "中国知识产权局网站有专利许可合同范本", "阿里巴巴知识产权平台 提供平台交易合同模板", "猪八戒网 提供设计服务合同模板"]
}

s8 = {
    "international_platforms": {
        "spoonflower_us": {"model": "Design-on-demand marketplace; pattern licensing + physical product sales", "ip_approach": ["Designers retain copyright; Spoonflower gets non-exclusive license to print and sell", "DMCA takedown system for infringement on platform", "Terms of service prohibit infringement", "Designers can report suspected infringement on other products"], "enforcement": "Primarily reactive; relies on designer reports and DMCA notices"},
        "korean_platforms": {"notable": "Korean pattern licensing platforms (various Naver-backed design stores)", "ip_approach": "Strong designer verification; Korean copyright law enforcement relatively robust; some platforms require registration certificate before listing"},
        "japanese_platforms": {"notable": "Tokyo Pattern Bank, Japanese design cooperatives", "ip_approach": "Strict designer verification; some use 日本著作権家协会 for registration; watermarks standard"}
    },
    "china_textile_industry_associations": {
        "南通市纺织工业协会": {"location": "Nantong, Jiangsu (叠石桥家纺城 region)", "ip_services": "IP consultation, dispute mediation, industry standards development"},
        "中国家纺行业协会": {"location": "National", "ip_services": "Industry IP standards; coordinates with government on IP enforcement"},
        "绍兴市纺织行业协会": {"location": "Shaoxing, Zhejiang", "ip_services": "IP training, member services"}
    },
    "nantong_textile_ip_measures": {
        "叠石桥家纺城": {"region": "海门区/通州区, Nantong - largest home textile hub in China", "ip_initiatives": ["家纺版权保护中心 (Home Textile Copyright Protection Center) - local-level", "与南通市版权局合作 (Cooperation with Nantong Copyright Bureau)", "快速维权通道 (Fast-track rights protection) for industry members", "定期版权培训 (Regular copyright training for merchants)"], "statistics": "As of early 2020s, estimated 30%+ of design disputes in this region involve online pattern copying"},
        "ip_enforcement_stats": {"nanjing_ip_court_textile_cases": "Significant portion of IP cases involve textile/garment IP disputes", "淘宝侵权投诉处理": "Taobao has specialized IP complaint process; pattern owners can file 侵权投诉 directly on product pages"}
    },
    "design_platforms_ip_management": [
        {"platform": "站酷 (ZCOOL)", "ip_measures": ["水印防护 (Visible watermarking)", "原创认证服务 (Originality certification)", "平台维权协助 (Platform rights protection assistance)", "与第三方维权机构合作 (Partnerships with third-party IP firms)"]},
        {"platform": "千图网/包图网", "ip_measures": ["付费版权保障 (Paid copyright guarantee for commercial use)", "全库监测服务 (Full library monitoring) - premium feature", "下线维权服务 (Takedown + enforcement service)"]}
    ]
}

s9 = {
    "preview_vs_download_quality_control": {
        "preview_images": {"resolution": "72-96 DPI, max 1000px on longest side", "format": "JPEG with visible compression artifacts", "watermark": "Multi-layer visible watermark (see Section 2)", "color_space": "sRGB; no CMYK (prevents print production use)", "metadata_stripped": "Remove EXIF camera data; retain only watermark metadata"},
        "full_resolution_files": {"resolution": "300 DPI, full original resolution", "format": "Original format (PSD/AI/EPS/TIFF) OR high-quality JPEG", "color_space": "Original color space preserved (may include CMYK)", "delivery_method": "Authenticated download only (see below)"}
    },
    "download_authentication": {
        "one_time_download_links": {"mechanism": "Generate unique download URL per transaction; URL contains buyer ID hash + file ID + timestamp + HMAC signature; link expires after single use OR 24 hours", "example_url_structure": "https://api.platform.com/download/{file_id}?buyer={hash}&ts={timestamp}&sig={hmac}", "effectiveness": "Prevents casual sharing of links; technical users can still screenshot/copy"},
        "expiring_links": {"duration": "15 minutes to 7 days typically", "recommendation": "3-day expiry after first download; buyer can request new link", "additional_security": "Combine with IP address binding (link only works from downloader's IP)"},
        "session_based_download": {"mechanism": "User must be logged in; download logged with user ID + timestamp + IP + device fingerprint", "advantage": "Tied to user account; easier to trace leaks"}
    },
    "user_behavior_tracking_for_leak_identification": {
        "data_points_collected_per_download": ["Buyer account ID and real-name (if verified)", "Timestamp of download", "IP address", "Device fingerprint (browser, OS, screen resolution)", "Session ID", "Downloaded file hash", "Network path (direct vs via referrer)"],
        "watermark_tied_to_downloader_identity": ["Each download embeds unique invisible watermark linking to buyer ID", "Even if image is photographed/recopy-scanned, watermark survives in photo", "Example: Steganographic encoding of buyer_id + timestamp in image noise", "Two identical-looking images from two buyers will have different invisible watermarks"],
        "analytics_for_leak_detection": {"if_infringing_pattern_found_online": "Extract invisible watermark then decode buyer ID to identify who leaked", "pattern_similarity_matching": "AI detects pattern appearing elsewhere; cross-reference with downloader database", "alert_system": "Automated alert when new pattern match found on monitored platforms"}
    },
    "digital_rights_management_options": {
        "basic_drm": {"approach": "Authenticated download with tracking only", "suitable_for": "Small platforms; low-to-medium value patterns"},
        "advanced_drm": {"approaches": ["DRM-encrypted PDF/files (limited viewing; no print screen in secure viewer)", "Secure viewer with screenshots disabled (browser-based secure image viewer)", "For textile CAD files: encrypted CAD formats with hardware-locked licenses"], "suitable_for": "High-value pattern libraries; enterprise licensing"},
        "cad_file_protection": {"formats": "纹织CAD文件 (.blo, .fp, .jc3, .awd from popular Chinese CAD systems like 纹织大师, 针织宝)", "protection_methods": ["CAD licensing server (hardware USB key or software license server)", "Encrypted file format with viewer-only license", "Most Chinese fabric design software has built-in protection modules"], "note": "Most important for high-value jacquard/embroidery designs"}
    },
    "technical_stack_recommendation": {"low_cost_tier": "Visible watermarking + download tracking + buyer watermarking + manual monitoring", "medium_cost_tier": "+ Invisible steganographic watermark + automated platform monitoring API (Baidu/Tencent)", "high_cost_tier": "+ Perceptual hash database + AI similarity matching + secure viewer + CAD DRM"}
}

s10 = {
    "reporting_and_takedown": {
        "platform_takedown_workflow": ["1. Rights holder submits complaint (with copyright registration OR blockchain timestamp OR other proof)", "2. Platform reviews: 1-3 business days (or 24 hours for urgent)", "3. If valid: Platform removes infringing content AND issues strike to infringer", "4. Repeat offenders: Account suspension/termination", "5. Serious infringement: Platform may forward to copyright authorities"],
        "taobao_ip_protection_workflow": {"complaint_types": ["专利投诉 (Patent complaint)", "著作权投诉 (Copyright complaint)", "商标投诉 (Trademark complaint)"], "response_time": "Typically 3-5 working days", "required_evidence": "Copyright registration certificate OR official verification letter"},
        "baidu_takedown": {"mechanism": "Baidu Content Management Platform for IP complaints", "response_time": "5-10 working days"}
    },
    "designer_verification_real_name": {
        "required_verification_levels": [
            {"level": "基础认证 (Basic)", "requirements": "Phone number + ID card (real-name via 支付宝/微信 实名认证 API)", "access": "Upload patterns; basic listing"},
            {"level": "高级认证 (Advanced)", "requirements": "Business license (for companies) OR verified identity + portfolio review", "access": "All features; higher sales limits; platform endorsement badge"},
            {"level": "权威认证 (Premium)", "requirements": "Copyright registration certificate OR design patent certificate + platform review", "access": "Premium placement; lower commission; proactive enforcement support"}
        ],
        "chinese_real_name_apis": [
            {"provider": "阿里云 实名认证API", "service": "身份要素核验 API (Identity factor verification)", "note": "Integration via Alibaba Cloud; verifies name + ID number + phone number"},
            {"provider": "腾讯云 实名认证", "service": "身份认证API"},
            {"provider": "公安部人口数据库", "access": "Via authorized third-party services only; not direct"}
        ]
    },
    "community_moderation_model": {
        "reporting_incentives": ["Report confirmed infringement to reporter gets platform credits", "Designer verification badge tied to community standing", "Regular contributors get premium features"],
        "community_patrol": ["Designated community moderators (patrol for obvious copying)", "Design peer review system (designers review each other's originality)", "Flag system for users to report suspicious content"],
        "designer_rating_ip_factor": ["Platform can include 原创度评分 in designer profile", "Based on: copyright registrations, dispute history, peer reviews", "High-score designers: better search ranking, lower commission"]
    },
    "automated_enforcement_system": {
        "content_moderation_on_upload": ["When designer uploads: AI check against existing platform pattern database", "Flag high-similarity patterns for manual review before publishing", "Reduce 洗稿 (pattern plagiarism) on platform"],
        "proactive_monitoring": ["Weekly automated scan of Taobao/Pinduoduo/1688 for patterns matching platform database", "Google Alerts + Baidu Alerts for designer names + pattern names", "Quarterly comprehensive scan"],
        "escalation_path": ["Minor infringement: Takedown + warning", "Repeat infringement: Account suspension", "Commercial-scale infringement: Legal action + platform lawsuit OR referral to rights holder"]
    }
}

exec_recs = {
    "immediate_priority_actions": [
        "1. Implement visible watermarking with 3 layers: center logo + tiled pattern + buyer-ID text overlay",
        "2. Set up download tracking: user ID + timestamp + IP in encrypted log per download",
        "3. Integrate with Alipay escrow for payment protection",
        "4. Establish basic DMCA-equivalent takedown workflow",
        "5. Require designer real-name verification (at minimum phone+ID)"
    ],
    "medium_term_actions": [
        "1. Integrate AntChain or 至信链 for blockchain evidence preservation",
        "2. Implement invisible steganographic watermark per download",
        "3. Set up automated platform monitoring (Baidu image search API)",
        "4. Develop standard contract templates for non-exclusive licensing",
        "5. Register platform works with CNCCA for key designs"
    ],
    "long_term_actions": [
        "1. Build AI-powered pattern similarity detection system",
        "2. Apply for design patents for high-value unique pattern systems",
        "3. Establish industry cooperation with Nantong/Shaoxing industry associations",
        "4. Develop secure viewer for high-value CAD pattern downloads",
        "5. Consider community enforcement incentive program"
    ],
    "estimated_costs_and_timeline": {
        "basic_setup": {"cost_range": "CNY 50000-150000 (initial development)", "timeline": "2-3 months", "includes": "Watermarking system, download tracking, basic escrow, takedown workflow"},
        "intermediate_setup": {"cost_range": "CNY 200000-500000", "timeline": "4-6 months", "includes": "+ Blockchain evidence, invisible watermarking, automated monitoring, contract templates"},
        "enterprise_setup": {"cost_range": "CNY 500000-2000000", "timeline": "6-12 months", "includes": "+ AI similarity detection, secure viewer, CAD DRM, community enforcement system, industry partnerships"}
    }
}

key_terms = {
    "chinese": ["区块链版权保护 著作权", "区块链存证 法院 举证", "图片水印 防泄露 技术", "隐形水印 数字指纹", "图像隐写术 版权保护", "图片侵权 检测 系统", "AI 图像查重 版权", "纺织品图案 著作权 保护", "家纺花型 侵权 维权", "设计平台 托管 付款 担保", "著作权许可使用合同 模板", "南通 叠石桥 版权 保护", "阿里巴巴 图片侵权 检测", "腾讯云 数字水印 API", "百度 图像搜索 API 侵权"],
    "english": ["blockchain copyright protection China", "blockchain evidence court China copyright", "invisible watermark image steganography", "textile pattern IP protection China", "design platform copyright enforcement", "fabric pattern plagiarism detection"]
}

contacts = {
    "alibaba_ip_protection": "阿里巴巴知识产权保护平台 (阿里云 IP保护服务)",
    "tencent_blockchain": "腾讯云 至信链 - enterprise inquiry via Tencent Cloud",
    "antchain": "蚂蚁链 - enterprise/blockchain copyright services via Ant Group",
    "baidu_ai": "百度AI开放平台 - 图像识别相关API",
    "cncca": "中国版权保护中心 - registration inquiries"
}

key_refs = ["《中华人民共和国著作权法》(2020 Amendment) - Primary copyright law", "《中华人民共和国专利法》(2020 Amendment) - Design patent protection", "《最高人民法院关于审理著作权民事纠纷案件适用法律若干问题的解释》(2020)", "《最高人民法院关于互联网法院审理案件若干问题的规定》(2018)", "《最高人民法院关于民事诉讼证据的若干规定》(2019)", "《电子签名法》(2019 Amendment)", "《信息网络传播权保护条例》", "CNCCA Registration Procedures: http://www.ccopyright.com.cn"]

# Now build the final data dict
data = {
    "metadata": {"title": "IP Protection Mechanisms for Chinese B2B Textile Pattern Design Marketplace", "scope": "Home textile pattern marketplace connecting designers with merchants (Nantong/Shaoxing)", "compiled_date": "2026-07-27", "timezone": "GMT+8", "sources_note": "Research compiled from Chinese legal databases, industry practices, platform research, and published case law"},
    "section_1_blockchain_copyright": s1,
    "section_2_visible_watermarking": s2,
    "section_3_invisible_fingerprint_watermarking": s3,
    "section_4_ai_plagiarism_detection": s4,
    "section_5_legal_framework_textile_patterns_china": s5,
    "section_6_escrow_dispute_resolution": s6,
    "section_7_contract_templates_pattern_licensing": s7,
    "section_8_industry_ip_practices": s8,
    "section_9_technical_file_protection": s9,
    "section_10_community_enforcement": s10,
    "executive_recommendations": exec_recs,
    "key_legal_references": key_refs,
    "key_search_terms": key_terms,
    "contact_information_for_platform_integration": contacts
}

# Write to file
output_path = "/Users/wushixiaoshenxian/openclaw-workspace/market-research/phase3_ip_protection.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Written successfully")

# Verify
with open(output_path, 'r', encoding='utf-8') as f:
    verify = json.load(f)
print(f"Verified: valid JSON with {len(verify)} top-level keys")
print(f"Keys: {list(verify.keys())}")
