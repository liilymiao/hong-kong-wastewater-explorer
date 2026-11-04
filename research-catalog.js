/* Source cards are derived from the same dataset registry used by query pages. */
(function(root){'use strict';
const reference=[
  {
    "verifiedDate": "2026-11-03",
    "id": "covid-weekly",
    "title": {
      "en": "Hong Kong COVID-19 weekly surveillance",
      "zh": "香港 COVID-19 周度监测"
    },
    "status": "loaded",
    "unitOfObservation": {
      "en": "One citywide reporting week",
      "zh": "一个全港监测周"
    },
    "temporalResolution": {
      "en": "Weekly; official Sunday–Saturday weeks",
      "zh": "周度；官方周日到周六监测周"
    },
    "coverage": {
      "start": "2023-01-29",
      "end": "2026-10-17",
      "recordCount": 194,
      "description": {
        "en": "Weekly clinical positivity and wastewater measurements, 2023–2026.",
        "zh": "2023–2026 年的周度临床阳性比例和污水监测值。"
      },
      "strata": []
    },
    "region": {
      "en": "Hong Kong, citywide aggregate",
      "zh": "香港，全港汇总"
    },
    "measurements": [
      {
        "id": "clinical_positivity",
        "label": {
          "en": "PHLSB SARS-CoV-2 specimen positivity",
          "zh": "PHLSB 标本 SARS-CoV-2 阳性比例"
        },
        "unit": "proportion; displayed as %",
        "notes": {
          "en": "Positive SARS-CoV-2 results among respiratory specimens received by PHLSB. The weekly specimen denominator is absent from the loaded CSV.",
          "zh": "PHLSB 接收的呼吸道标本中 SARS-CoV-2 阳性所占比例。已载入 CSV 没有逐周标本总分母。"
        }
      },
      {
        "id": "wastewater",
        "label": {
          "en": "Official wastewater viral-load indicator",
          "zh": "官方污水病毒量指标"
        },
        "unit": "copy/L",
        "notes": {
          "en": "Official 7-day geometric-mean per-capita indicator; retain the published name and unit. Normalisation inputs are not supplied.",
          "zh": "官方七日几何平均人均病毒量指标；保留发布名称及单位，来源未提供归一化输入。"
        }
      }
    ],
    "requiredFields": [
      {
        "id": "week_key",
        "label": {
          "en": "Official week and observation dates",
          "zh": "官方周编号与观测起止日期"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "source_version",
        "label": {
          "en": "Source version, retrieval time and checksum",
          "zh": "来源版本、获取时间与校验值"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "missingness",
        "label": {
          "en": "Missing-value and correction records",
          "zh": "缺测及日期纠错记录"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      }
    ],
    "links": [
      {
        "label": {
          "en": "Hong Kong Department of Health",
          "zh": "香港卫生署"
        },
        "url": "https://data.gov.hk/en-data/dataset/hk-dh-chpsebcddr-covid-express",
        "kind": "source"
      },
      {
        "label": {
          "en": "COVID-19 Express data dictionary",
          "zh": "COVID-19 Express 数据字典"
        },
        "url": "https://www.chp.gov.hk/files/pdf/covidx_spec_en.pdf",
        "kind": "dictionary"
      },
      {
        "label": {
          "en": "COVID-19 Express, week 42 of 2026 (pages 3 and 6)",
          "zh": "2026 年第 42 周 COVID-19 Express（第 3、6 页）"
        },
        "url": "https://www.chp.gov.hk/files/pdf/covid_flux_week42_22_10_2026_eng.pdf",
        "kind": "report"
      },
      {
        "label": {
          "en": "Data files",
          "zh": "数据文件"
        },
        "url": "source_manifest.json",
        "kind": "local_provenance"
      }
    ],
    "access": {
      "en": "Loaded frozen snapshot; the official source may contain later revisions.",
      "zh": "已载入冻结快照；官方来源可能已有后续修订。"
    },
    "fitScope": {
      "en": "Weekly trend review, paired clinical forecasts and unusual-week investigation. District and isolate-level records are absent.",
      "zh": "用于周度趋势、配对临床指标预测与异常周核查。数据不含地区或菌株级记录。"
    }
  },
  {
    "verifiedDate": "2026-11-03",
    "id": "hk-amr-annual",
    "title": {
      "en": "Hong Kong hospital AMR",
      "zh": "香港医院耐药统计"
    },
    "status": "loaded",
    "unitOfObservation": {
      "en": "Published annual specimen–organism–drug–onset stratum, after source deduplication",
      "zh": "按来源去重后的年度标本—菌种—药物—发病地点汇总层"
    },
    "temporalResolution": {
      "en": "Annual",
      "zh": "年度"
    },
    "coverage": {
      "start": "2020",
      "end": "2024",
      "recordCount": 175,
      "description": {
        "en": "175 annual blood-culture records, 2020–2024.",
        "zh": "2020–2024 年的 175 条年度血培养记录。"
      },
      "strata": [
        {
          "en": "Blood, urine, stool, cerebrospinal fluid and lower respiratory specimens",
          "zh": "血液、尿液、粪便、脑脊液及下呼吸道标本"
        }
      ]
    },
    "region": {
      "en": "Hong Kong public hospitals and clinics under the Hospital Authority",
      "zh": "香港医管局辖下公立医院及诊所"
    },
    "measurements": [
      {
        "id": "non_susceptibility",
        "label": {
          "en": "Reported non-susceptibility and 95% interval",
          "zh": "已报告非敏感比例与 95% 区间"
        },
        "unit": "%",
        "notes": {
          "en": "The published series defines non-susceptibility as intermediate or resistant. Keep the published NS% and Wilson interval; retain the definition and report year.",
          "zh": "该监测系列把中介或耐药计入非敏感。保留发布的 NS% 与 Wilson 区间，同时记录定义和报告年份。"
        }
      },
      {
        "id": "counts",
        "label": {
          "en": "Published numerator, denominator and headcount",
          "zh": "发布的分子、分母及患者人数"
        },
        "unit": "reported count",
        "notes": {
          "en": "Headcounts are rounded to hundreds or thousands by table; percentages to one decimal. Keep original text and rounding level rather than recomputing exact rates from rounded counts.",
          "zh": "人数按表取整至百位或千位，百分率保留一位小数。保留原文字串及取整精度，不从取整人数反算精确比例。"
        }
      }
    ],
    "requiredFields": [
      {
        "id": "stratum",
        "label": {
          "en": "Year, specimen, organism, drug and onset stratum",
          "zh": "年份、标本、菌种、药物和发病地点分层"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "reported_statistics",
        "label": {
          "en": "Published NS%, lower/upper interval and confidence method",
          "zh": "发布的非敏感率、区间上下限和区间方法"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "raw_counts",
        "label": {
          "en": "Original numerator/denominator text and rounding precision",
          "zh": "原始分子／分母字串及取整精度"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "publication_status",
        "label": {
          "en": "Reported, suppressed, unavailable or absent status",
          "zh": "已报告、抑制、不可得或未出现状态"
        },
        "unit": null,
        "notes": {
          "en": "Keep § and other symbols. In AST tables § denotes a positive count below 50; in thousand-rounded totals it denotes a positive count below 500. Blank or excluded results are not zero.",
          "zh": "保留 § 等符号。AST 表中 § 表示大于 0 且小于 50；千位取整总人数表中表示大于 0 且小于 500。空白或排除结果保留对应状态。"
        }
      },
      {
        "id": "sample_threshold",
        "label": {
          "en": "Deduplicated AST sample threshold",
          "zh": "去重后 AST 样本量门槛"
        },
        "unit": null,
        "notes": {
          "en": "Published NS% based on fewer than 10 tested isolates is excluded. The 2024 CSF report supplies no AST results under this threshold.",
          "zh": "去重后受检菌株少于 10 的 NS% 被排除；2024 年脑脊液报告因该门槛未提供 AST 结果。"
        }
      },
      {
        "id": "ast_coverage",
        "label": {
          "en": "AST coverage flag and denominator definition",
          "zh": "AST 覆盖标记与分母定义"
        },
        "unit": null,
        "notes": {
          "en": "Retain †† for testing coverage below 70% and distinguish tested isolates from all isolates.",
          "zh": "保留检测覆盖不足 70% 的 †† 标记，区分受检菌株与全部菌株。"
        }
      },
      {
        "id": "breakpoint",
        "label": {
          "en": "Interpretive standard, version and change marker",
          "zh": "判读标准、版本及变更标记"
        },
        "unit": null,
        "notes": {
          "en": "Source notes flag CLSI changes: fluoroquinolones in 2019, piperacillin/tazobactam in 2022, and Acinetobacter colistin in 2020. Do not infer one fixed standard across all years.",
          "zh": "来源脚注标明 CLSI 变更：2019 年氟喹诺酮、2022 年哌拉西林／他唑巴坦、2020 年不动杆菌黏菌素。逐年记录适用标准。"
        }
      },
      {
        "id": "deduplication",
        "label": {
          "en": "Deduplication and onset definitions",
          "zh": "去重规则与发病地点定义"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "provenance",
        "label": {
          "en": "Report URL, year, page and original table label",
          "zh": "报告链接、年份、页码与原表名称"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      }
    ],
    "links": [
      {
        "label": {
          "en": "2024 report overview",
          "zh": "2024 年报告总览"
        },
        "url": "https://www.chp.gov.hk/en/static/109746.html",
        "kind": "source"
      },
      {
        "label": {
          "en": "Blood report",
          "zh": "血液报告"
        },
        "url": "https://www.chp.gov.hk/files/pdf/hospitalauthorityamrdata2024_blood.pdf",
        "kind": "report"
      },
      {
        "label": {
          "en": "Urine report",
          "zh": "尿液报告"
        },
        "url": "https://www.chp.gov.hk/files/pdf/hospitalauthorityamrdata2024_urine.pdf",
        "kind": "report"
      },
      {
        "label": {
          "en": "Stool report",
          "zh": "粪便报告"
        },
        "url": "https://www.chp.gov.hk/files/pdf/hospitalauthorityamrdata2024_stool.pdf",
        "kind": "report"
      },
      {
        "label": {
          "en": "CSF report",
          "zh": "脑脊液报告"
        },
        "url": "https://www.chp.gov.hk/files/pdf/hospitalauthorityamrdata2024_csf.pdf",
        "kind": "report"
      },
      {
        "label": {
          "en": "Lower respiratory report",
          "zh": "下呼吸道报告"
        },
        "url": "https://www.chp.gov.hk/files/pdf/hospitalauthorityamrdata2024_lowerresp.pdf",
        "kind": "report"
      },
      {
        "label": {
          "en": "Blood result tables and footnotes",
          "zh": "血液结果表与脚注"
        },
        "url": "https://www.chp.gov.hk/files/pdf/haamr_blood_key_findings2024.pdf",
        "kind": "result_tables"
      },
      {
        "label": {
          "en": "Urine result tables and footnotes",
          "zh": "尿液结果表与脚注"
        },
        "url": "https://www.chp.gov.hk/files/pdf/haamr_urine_key_findings2024.pdf",
        "kind": "result_tables"
      },
      {
        "label": {
          "en": "AMR methods for the 2022 series",
          "zh": "2022 年 AMR 方法说明"
        },
        "url": "https://www.chp.gov.hk/en/static/107500.html",
        "kind": "methods"
      }
    ],
    "access": {
      "en": "Queryable blood-culture subset with confidence intervals, original counts and quality flags.",
      "zh": "可查询血培养子集，含置信区间、原始计数和质量标记。"
    },
    "fitScope": {
      "en": "Annual AMR context and stratified surveillance questions. Annual aggregates cannot supply weekly clinical targets or matched isolate-level labels.",
      "zh": "用于年度耐药背景及分层监测问题。年度汇总不提供周度临床目标或菌株级配对标签。"
    },
    "topic": "ha"
  },
  {
    "verifiedDate": "2026-11-03",
    "id": "bv-brc",
    "title": {
      "en": "BV-BRC experimental AST",
      "zh": "BV-BRC 实验药敏数据"
    },
    "status": "loaded",
    "unitOfObservation": {
      "en": "Genome–antimicrobial result with evidence provenance",
      "zh": "带证据来源的基因组—抗菌药物结果"
    },
    "temporalResolution": {
      "en": "Record-specific collection and release metadata; availability varies",
      "zh": "按记录提供采集及发布元数据，完整度不一"
    },
    "coverage": {
      "start": "1970",
      "end": "2022",
      "recordCount": 15777,
      "description": {
        "en": "15,777 experimental E. coli–ciprofloxacin AST records in the frozen query.",
        "zh": "冻结查询中含 15,777 条大肠杆菌—环丙沙星实验药敏记录。"
      },
      "strata": []
    },
    "region": {
      "en": "International source records",
      "zh": "国际来源记录"
    },
    "measurements": [
      {
        "id": "phenotype",
        "label": {
          "en": "S/I/R phenotype and MIC where available",
          "zh": "可得的 S/I/R 表型及 MIC"
        },
        "unit": "source-defined",
        "notes": {
          "en": "Keep experimental AMR panels, source phenotype annotations and computational predictions as separate evidence classes.",
          "zh": "区分实验 AMR panel、来源表型注释及计算预测三类证据。"
        }
      },
      {
        "id": "genome",
        "label": {
          "en": "Linked genome and study provenance",
          "zh": "关联基因组及研究来源"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      }
    ],
    "requiredFields": [
      {
        "id": "genome_id",
        "label": {
          "en": "Genome/accession and isolate identifiers",
          "zh": "基因组登录号及分离株标识"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "organism_drug",
        "label": {
          "en": "Taxon and tested antimicrobial",
          "zh": "分类单元及受检药物"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "evidence",
        "label": {
          "en": "Evidence type and original source/publication",
          "zh": "证据类型及原始来源／论文"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "measurement",
        "label": {
          "en": "MIC sign, value and unit; phenotype",
          "zh": "MIC 比较符号、数值、单位及表型"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "standard",
        "label": {
          "en": "Testing standard and standard year",
          "zh": "检测标准及标准年份"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "method",
        "label": {
          "en": "Laboratory method, platform, vendor and version",
          "zh": "实验方法、平台、厂商及版本"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "sampling",
        "label": {
          "en": "Collection date, location and specimen when reported",
          "zh": "已报告的采集日期、地点及标本"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "prediction_flag",
        "label": {
          "en": "Computational-prediction flag and model provenance",
          "zh": "计算预测标记及模型来源"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      }
    ],
    "links": [
      {
        "label": {
          "en": "BV-BRC search",
          "zh": "BV-BRC 检索入口"
        },
        "url": "https://www.bv-brc.org/",
        "kind": "search"
      },
      {
        "label": {
          "en": "AMR phenotype table fields",
          "zh": "AMR 表型表字段"
        },
        "url": "https://www.bv-brc.org/docs/quick_references/organisms_taxon/amr_phenotypes.html",
        "kind": "dictionary"
      },
      {
        "label": {
          "en": "AMR evidence categories",
          "zh": "AMR 证据分类"
        },
        "url": "https://www.bv-brc.org/docs/quick_references/organisms_taxon/antimicrobial_resistance.html",
        "kind": "methods"
      },
      {
        "label": {
          "en": "AMR data sources and protocols",
          "zh": "AMR 数据来源与流程"
        },
        "url": "https://www.bv-brc.org/docs/data_protocols/antimicrobial_resistance.html",
        "kind": "methods"
      }
    ],
    "access": {
      "en": "Queryable experimental AST records and linked genome metadata.",
      "zh": "可查询实验药敏记录及关联基因组元数据。"
    },
    "fitScope": {
      "en": "Candidate evidence for genotype–phenotype research after provenance and assay review. Computational labels require separate analysis from measured phenotypes.",
      "zh": "可用于经来源及检测方法核查后的基因型—表型研究；计算标签与实测表型分开分析。"
    },
    "topic": "bvbrc"
  },
  {
    "verifiedDate": "2026-11-03",
    "id": "ena",
    "title": {
      "en": "European Nucleotide Archive",
      "zh": "欧洲核苷酸档案库"
    },
    "status": "catalog_only",
    "unitOfObservation": {
      "en": "Study, sample, experiment and sequencing run linked by accession",
      "zh": "以登录号关联的研究、样本、实验及测序运行"
    },
    "temporalResolution": {
      "en": "Sample/run metadata; date precision varies by submission",
      "zh": "样本／运行元数据；日期精度由提交记录决定"
    },
    "coverage": {
      "start": null,
      "end": null,
      "recordCount": null,
      "description": {
        "en": "Search studies, sample metadata and sequence files.",
        "zh": "检索研究、样本信息与测序文件。"
      },
      "strata": []
    },
    "region": {
      "en": "International",
      "zh": "国际"
    },
    "measurements": [
      {
        "id": "sequence_reads",
        "label": {
          "en": "Submitted sequence reads and associated files",
          "zh": "提交的测序读段及关联文件"
        },
        "unit": "FASTQ / submitted format",
        "notes": {
          "en": "Advanced search can return raw-read records and file links. Sequence files do not by themselves establish an experimentally measured AMR phenotype.",
          "zh": "高级检索可返回原始读段记录与文件链接。测序文件本身不确立实验测得的耐药表型。"
        }
      },
      {
        "id": "sample_metadata",
        "label": {
          "en": "Study, sample and sequencing metadata",
          "zh": "研究、样本及测序元数据"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      }
    ],
    "requiredFields": [
      {
        "id": "accessions",
        "label": {
          "en": "Study, sample, experiment and run accessions",
          "zh": "研究、样本、实验及运行登录号"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "sample_context",
        "label": {
          "en": "Taxonomy, host, specimen/source and geography",
          "zh": "分类、宿主、标本／来源及地区"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "dates",
        "label": {
          "en": "Collection/release dates and their precision",
          "zh": "采集／发布日期及其精度"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "sequencing",
        "label": {
          "en": "Library strategy/layout and sequencing platform",
          "zh": "文库策略／布局与测序平台"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "files",
        "label": {
          "en": "Raw-file links, sizes and checksums",
          "zh": "原始文件链接、大小及校验值"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "linked_ast",
        "label": {
          "en": "External experimental AST record and isolate match, if needed",
          "zh": "按研究需要关联的实验 AST 记录及菌株匹配"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "provenance",
        "label": {
          "en": "Search query, retrieval date and record version",
          "zh": "检索条件、获取日期及记录版本"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      }
    ],
    "links": [
      {
        "label": {
          "en": "Advanced metadata search",
          "zh": "高级元数据检索"
        },
        "url": "https://www.ebi.ac.uk/ena/browser/advanced-search",
        "kind": "search"
      },
      {
        "label": {
          "en": "Metadata and raw-file retrieval guide",
          "zh": "元数据及原始文件获取说明"
        },
        "url": "https://ena-browser-docs.readthedocs.io/en/latest/browser/search/advanced.html",
        "kind": "methods"
      },
      {
        "label": {
          "en": "ENA Portal API",
          "zh": "ENA Portal API"
        },
        "url": "https://www.ebi.ac.uk/ena/portal/api/swagger-ui/index.html",
        "kind": "api"
      },
      {
        "label": {
          "en": "ENA Browser API",
          "zh": "ENA Browser API"
        },
        "url": "https://www.ebi.ac.uk/ena/browser/api/swagger-ui/index.html",
        "kind": "api"
      },
      {
        "label": {
          "en": "Official retrieval overview",
          "zh": "官方检索与获取概览"
        },
        "url": "https://www.ebi.ac.uk/training/online/courses/ena-quick-tour/searching-and-visualising-data-ena/",
        "kind": "methods"
      }
    ],
    "access": {
      "en": "Search the public archive and download sequence files.",
      "zh": "检索公开档案并下载测序文件。"
    },
    "fitScope": {
      "en": "Identify sequencing cohorts and assess linkage to experimental evidence. Confirm sample matching before combining genome and phenotype records.",
      "zh": "用于寻找测序队列并评估实验资料关联；合并基因组与表型记录前核实样本匹配。"
    }
  },
  {
    "verifiedDate": "2026-11-03",
    "id": "clinical-partner",
    "title": {
      "en": "Clinical data from collaborators",
      "zh": "合作方临床数据"
    },
    "status": "access_request",
    "unitOfObservation": {
      "en": "Clinical reporting period × area × organism × antimicrobial",
      "zh": "临床报告期 × 区域 × 菌种 × 药物"
    },
    "temporalResolution": {
      "en": "Original reporting periods",
      "zh": "原始报告期"
    },
    "coverage": {
      "start": null,
      "end": null,
      "recordCount": null,
      "description": {
        "en": "Clinical counts with dates, organisms, antimicrobials and tested denominators.",
        "zh": "包含日期、菌种、药物和受检分母的临床计数。"
      },
      "strata": []
    },
    "region": {
      "en": "Defined by the input data",
      "zh": "由输入数据确定"
    },
    "measurements": [
      {
        "id": "ast",
        "label": {
          "en": "Measured susceptibility result and assay context",
          "zh": "实测药敏结果及检测背景"
        },
        "unit": "source-defined",
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "clinical_context",
        "label": {
          "en": "Agreed specimen and episode context",
          "zh": "约定的标本及事件背景"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      }
    ],
    "requiredFields": [
      {
        "id": "pseudonymous_keys",
        "label": {
          "en": "Provider-generated specimen/isolate and episode keys",
          "zh": "由提供方生成的标本／菌株及事件代号"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "specimen",
        "label": {
          "en": "Specimen type, collection time and time precision",
          "zh": "标本类型、采集时间及时间精度"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "organism",
        "label": {
          "en": "Organism identification and method",
          "zh": "菌种鉴定及方法"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "antimicrobial",
        "label": {
          "en": "Antimicrobial identity and tested panel",
          "zh": "药物标识及检测面板"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "measurement",
        "label": {
          "en": "MIC/zone value, comparison sign and unit",
          "zh": "MIC／抑菌圈数值、比较符号及单位"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "interpretation",
        "label": {
          "en": "Original S/I/R, standard/version and breakpoint date",
          "zh": "原始 S/I/R、标准／版本及折点日期"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "assay",
        "label": {
          "en": "Assay method, platform and quality-control status",
          "zh": "检测方法、平台及质控状态"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "onset",
        "label": {
          "en": "Care setting and onset definition where agreed",
          "zh": "约定的诊疗场景及发病地点定义"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "availability",
        "label": {
          "en": "Result release time, revision history and missingness",
          "zh": "结果可得时间、修订历史及缺失状态"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "deduplication",
        "label": {
          "en": "Patient/episode deduplication rule and testing denominator",
          "zh": "患者／事件去重规则及受检分母"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "governance",
        "label": {
          "en": "Permitted purpose, access conditions and retention agreement",
          "zh": "许可用途、获取条件及保存约定"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      },
      {
        "id": "linkage",
        "label": {
          "en": "Approved genome/sequence linkage, when part of the study",
          "zh": "研究包含测序时，已批准的基因组／序列关联"
        },
        "unit": null,
        "notes": {
          "en": "",
          "zh": ""
        }
      }
    ],
    "links": [],
    "access": {
      "en": "Request records from a data collaborator or upload clinical CSVs.",
      "zh": "向合作方获取记录，或上传临床 CSV。"
    },
    "fitScope": {
      "en": "Potential source for finer clinical validation once a partner confirms scope, fields and permitted use.",
      "zh": "合作方确认范围、字段及许可用途后，可用于更细粒度临床验证。"
    }
  }
];
const L=(en,zh)=>({en,zh});
const titles={phlsb:L('Hong Kong outpatient AMR','香港门诊耐药统计'),arg:L('European wastewater ARG counts','欧洲污水 ARG 计数'),hk:L('Hong Kong sewage samples & sequencing QC','香港污水样本与测序质控'),ha:L('Hong Kong hospital AMR','香港医院耐药统计'),supply:L('Antimicrobial wholesale supply','抗微生物药物批发供应'),bvbrc:L('Genome–experimental AST cohort','基因组—实验药敏队列'),rainfall:L('Hong Kong rainfall','香港降雨'),flu:L('Hong Kong influenza surveillance','香港流感监测'),global:L('Global Sewage 3','Global Sewage 3')};
const data=()=>({phlsb:root.PHLSB_DATA?.meta,arg:root.EUROPE_ARG_DATA?.meta,hk:root.HK_COMMUNITY_DATA?.meta,...root.ResearchExtensionIndex});
const aliases={'hk-amr-annual':'ha-amr','bv-brc':'bvbrc-ast'};
function card(topic,m){
 const legacy=reference.find(c=>c.topic===topic)||{},source=m.source||{},count=m.record_count??m.independent_sample_count??m.sample_count;
 const start=m.start_date||(m.years?`${Math.min(...m.years)}-01-01`:topic==='hk'?'2021-05':null),end=m.end_date||(m.years?`${Math.max(...m.years)}-12-31`:topic==='hk'?'2022-01':null);
 const unit=m.unit_of_observation||(topic==='arg'?'One biological sample × ARG count matrix row':topic==='hk'?'One published sample QC identifier':'');
 const resolution=topic==='phlsb'||topic==='ha'||topic==='supply'?'Annual':topic==='flu'?'Weekly':topic==='rainfall'?'Daily':topic==='hk'?'Reported campaign / sample identifier':'Source record date';
 const url=source.url||m.source_url||m.article_url;
 const summary=topic==='arg'?L(`${count} samples and ${m.gene_count} ARGs.`,`${count} 个样本，${m.gene_count} 个 ARG。`):topic==='hk'?L(`${count} sample QC records.`,`${count} 条样本质控记录。`):L(`${count??'—'} records${start&&end?' from '+start+' to '+end:''}.`,`${count??'—'} 条记录${start&&end?'，'+start+' 至 '+end:''}。`);
 const publisher={phlsb:L('Hong Kong Department of Health','香港卫生署'),arg:L('Becsei et al. (2024)','Becsei 等（2024）'),hk:L('Ding et al. (2026)','Ding 等（2026）'),ha:L('Hong Kong Department of Health','香港卫生署'),supply:L('Centre for Health Protection','香港卫生防护中心'),bvbrc:L('BV-BRC','BV-BRC'),rainfall:L('Hong Kong Observatory','香港天文台'),flu:L('Centre for Health Protection','香港卫生防护中心'),global:L('Global Sewage 3 (Zenodo)','Global Sewage 3（Zenodo）')};
 const unitZh={phlsb:'年份 × 标本 × 菌种 × 药物或标记',arg:'一个污水样本的 ARG 计数',hk:'一条样本质控记录',ha:'年份 × 菌种 × 药物 × 发病场所',supply:'年份 × 供药部门 × 药物大类',bvbrc:'一条实验药敏记录',rainfall:'一天的站点降雨观测',flu:'一个监测周',global:'样本 × 基因簇计数'};
 const timeZh={Annual:'年度',Weekly:'周度',Daily:'日度','Reported campaign / sample identifier':'采样轮次及样本编号','Source record date':'来源记录日期'};
 const notes=m.scope_note||m.count_explanation||m.normalization_status||'';
 return{...legacy,id:m.dataset_id,topic,title:titles[topic],status:'loaded',verifiedDate:source.retrieved_at_utc||m.retrieved_at_utc||m.retrieved||'',unitOfObservation:L(unit,unitZh[topic]||unit),temporalResolution:L(resolution,timeZh[resolution]||resolution),region:m.region||legacy.region||L(topic==='arg'?'Europe':topic==='bvbrc'||topic==='global'?'International':'Hong Kong',topic==='arg'?'欧洲':topic==='bvbrc'||topic==='global'?'国际':'香港'),coverage:{start,end,recordCount:count,description:summary},display_summary:summary,coverage_notes:notes,access:L('View and download data.','查看并下载数据。'),fitScope:L('Research data selection and export.','研究数据筛选与导出。'),links:[...(url?[{label:publisher[topic],url,kind:'source'}]:[]),...(m.project_url?[{label:L('Sequence archive','测序档案'),url:m.project_url,kind:'archive'}]:[])],source_version:m.source_version||m.dataset_version,source_sha256:source.source_sha256||m.source_sha256};
}
function current(){
 const connected=Object.entries(data()).filter(([,m])=>m?.dataset_id).map(([t,m])=>card(t,m));
 const available=new Set(connected.map(c=>c.id));
 // Fallbacks are used only before the small source index has loaded.
 const fallback=reference.filter(c=>c.topic&&!available.has(aliases[c.id]||c.id)).map(c=>({...c,id:aliases[c.id]||c.id}));
 return[reference.find(c=>c.id==='covid-weekly'),...connected,...fallback,...reference.filter(c=>['ena','clinical-partner'].includes(c.id))].filter(Boolean);
}
root.ResearchCatalogRegistry={current,get(id){return current().find(c=>c.id===(aliases[id]||id))}};
Object.defineProperty(root,'ResearchCatalog',{configurable:true,get:current});
})(window);
