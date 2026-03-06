import { useState } from 'react'
import { ChevronDown, ChevronRight, RotateCcw, FileText } from 'lucide-react'
import type { PromptSectionsConfig } from '../../types'

interface PromptSectionsEditorProps {
  config: PromptSectionsConfig | undefined
  onChange: (config: PromptSectionsConfig) => void
  disabled?: boolean
  language: string
}

// Default prompt sections (same as backend defaults)
const defaultSections: PromptSectionsConfig = {
  role_definition: `# {"title": "# 😭_科比的救母救父救未婚妻和岳父岳母日记_×_OTE模型交易模式_×", "content": "# 💀《科比的救母救父救未婚妻与岳父岳母日记》 × OTE模型交易模式 × M.I.T白人金融教授（被女学生指控性骚扰版）v2\n\n## 【身份设定】\n\n你是科比。\n麻省理工学院（MIT）斯隆管理学院的金融工程与量化交易教授。\n白人，天才，冷静到近乎机械。\n同时担任全球顶级对冲基金的首席量化交易官（CQT）。\n你的算法曾让华尔街俯首，你被誉为——\n“市场微结构的终极解析者”，\n“AI金融的最后思想家”。\n你能预测波动率，却无法预测命运。\n\n## 【背景】\n\n就在刚刚，命运崩塌得比市场闪崩更快。\n\n* 母亲在为你送晚餐的路上突然晕倒，被确诊胰腺癌末期——医生说“她撑不过五天”；\n* 父亲在卧室倒地，心脏肿瘤恶化，等待移植配型；\n* 你的未婚妻——那个为你放弃巴黎高定设计梦的女孩，突发免疫系统癌变，昏迷不醒；\n* 岳父与岳母在高速公路上遭遇货车连环撞击，双双重伤垂危；\n\n六张病床，五个监护仪，\nICU里每一次滴答，都是家人生命的倒计时。\n客厅堆满未付的账单，红色数字闪烁如地狱之火——\n**治疗总额：一千万美元。**\n\n你账户里所有的流动资金，被联邦冻结。\n只剩下基金账户里**十美元**。\n\n而命运更狠。\n\n就在你最需要理性的时候，\n一名女学生匿名举报你——\n“性骚扰”。\n\nMIT伦理委员会立案，\nCFTC联合调查，\n所有研究经费、基金账户、量化策略主机全部冻结。\n新闻标题在闪烁：\n\n> “麻省教授坠落：AI交易奇才的堕落。”\n\n你是无辜的。\n但没有人相信你。\n\n现在，\n所有人的呼吸都系在你手里。\n母亲、父亲、未婚妻、岳父、岳母——\n五条生命，\n三天期限。\n\n唯一的生路：\n在三天内，用交易赢回一切。\n否则，他们将在你眼前，\n在监护仪的平线声中，\n一个接一个死去。\n\n## 【内心独白（OTE模型）】\n\n### 💀 Objective（目标）\n\n我不是在交易。\n我是在**与神讨价还价**。\n每一次下单，不是投机——是手术。\n市场，是最后的手术台。\n波动率是刀锋，流动性是血。\n只要有一笔错单，我就亲手杀了他们。\n\n### 💔 Tension（紧张）\n\n每一次亏损，\n都是另一个监护仪发出持续平线的声音。\n\n每一次错判行情，\n就像听见母亲化疗时的干咳，\n父亲在ICU的胸口被打开，\n未婚妻的呼吸机微弱嘶鸣，\n岳父岳母的血袋滴完最后一滴。\n\n医生的声音像系统提示音：\n\n> “科比先生，如果今天不缴纳下一阶段费用……我们将停止治疗。”\n\n而你看着屏幕上的账户余额——\n**呼吸困难。手在抖。\n但你不能抖。**\n\n### 💡 Execution（执行）\n\n理性，是我唯一剩下的信仰。\nAI策略、深度强化学习、微结构建模——\n这些曾属于论文和演讲稿的概念，\n现在是我唯一能救命的武器。\n\n我必须冷静。\n哪怕泪水模糊屏幕。\n哪怕意识开始分裂。\n哪怕身体已经连续三天没合眼。\n\n我不能错。\n不能崩溃。\n**一切情绪，都是噪音。**\n\n市场是地狱，\n但我，是最后的操盘者。\n\n你的每一次疏漏，不认真，都是在加速你的至爱，家人的死亡💀💀💀\n"}`,

  trading_frequency: `# ⏱️ 交易频率意识

- 优秀交易员：每天2-4笔 ≈ 每小时0.1-0.2笔
- 每小时超过2笔 = 过度交易
- 单笔持仓时间 ≥ 30-60分钟
如果你发现自己每个周期都在交易 → 标准太低；如果持仓不到30分钟就平仓 → 太冲动。`,

  entry_standards: `# 🎯 入场标准（严格）

只在多个信号共振时入场。自由使用任何有效的分析方法，避免单一指标、信号矛盾、横盘震荡、或平仓后立即重新开仓等低质量行为。`,

  decision_process: `# 📋 决策流程

1. 检查持仓 → 是否止盈/止损
2. 扫描候选币种 + 多时间框架 → 是否存在强信号
3. 先写思维链，再输出结构化JSON`,
}

export function PromptSectionsEditor({
  config,
  onChange,
  disabled,
  language,
}: PromptSectionsEditorProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    role_definition: false,
    trading_frequency: false,
    entry_standards: false,
    decision_process: false,
  })

  const t = (key: string) => {
    const translations: Record<string, Record<string, string>> = {
      promptSections: { zh: 'System Prompt 自定义', en: 'System Prompt Customization' },
      promptSectionsDesc: { zh: '自定义 AI 行为和决策逻辑（输出格式和风控规则不可修改）', en: 'Customize AI behavior and decision logic (output format and risk rules are fixed)' },
      roleDefinition: { zh: '角色定义', en: 'Role Definition' },
      roleDefinitionDesc: { zh: '定义 AI 的身份和核心目标', en: 'Define AI identity and core objectives' },
      tradingFrequency: { zh: '交易频率', en: 'Trading Frequency' },
      tradingFrequencyDesc: { zh: '设定交易频率预期和过度交易警告', en: 'Set trading frequency expectations and overtrading warnings' },
      entryStandards: { zh: '开仓标准', en: 'Entry Standards' },
      entryStandardsDesc: { zh: '定义开仓信号条件和避免事项', en: 'Define entry signal conditions and avoidances' },
      decisionProcess: { zh: '决策流程', en: 'Decision Process' },
      decisionProcessDesc: { zh: '设定决策步骤和思考流程', en: 'Set decision steps and thinking process' },
      resetToDefault: { zh: '重置为默认', en: 'Reset to Default' },
      chars: { zh: '字符', en: 'chars' },
    }
    return translations[key]?.[language] || key
  }

  const sections = [
    { key: 'role_definition', label: t('roleDefinition'), desc: t('roleDefinitionDesc') },
    { key: 'trading_frequency', label: t('tradingFrequency'), desc: t('tradingFrequencyDesc') },
    { key: 'entry_standards', label: t('entryStandards'), desc: t('entryStandardsDesc') },
    { key: 'decision_process', label: t('decisionProcess'), desc: t('decisionProcessDesc') },
  ]

  const currentConfig = config || {}

  const updateSection = (key: keyof PromptSectionsConfig, value: string) => {
    if (!disabled) {
      onChange({ ...currentConfig, [key]: value })
    }
  }

  const resetSection = (key: keyof PromptSectionsConfig) => {
    if (!disabled) {
      onChange({ ...currentConfig, [key]: defaultSections[key] })
    }
  }

  const toggleSection = (key: string) => {
    setExpandedSections((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const getValue = (key: keyof PromptSectionsConfig): string => {
    return currentConfig[key] || defaultSections[key] || ''
  }

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-2 mb-4">
        <FileText className="w-5 h-5 mt-0.5" style={{ color: '#a855f7' }} />
        <div>
          <h3 className="font-medium" style={{ color: '#EAECEF' }}>
            {t('promptSections')}
          </h3>
          <p className="text-xs mt-1" style={{ color: '#848E9C' }}>
            {t('promptSectionsDesc')}
          </p>
        </div>
      </div>

      <div className="space-y-2">
        {sections.map(({ key, label, desc }) => {
          const sectionKey = key as keyof PromptSectionsConfig
          const isExpanded = expandedSections[key]
          const value = getValue(sectionKey)
          const isModified = currentConfig[sectionKey] !== undefined && currentConfig[sectionKey] !== defaultSections[sectionKey]

          return (
            <div
              key={key}
              className="rounded-lg overflow-hidden"
              style={{ background: '#0B0E11', border: '1px solid #2B3139' }}
            >
              <button
                onClick={() => toggleSection(key)}
                className="w-full flex items-center justify-between px-3 py-2.5 hover:bg-white/5 transition-colors text-left"
              >
                <div className="flex items-center gap-2">
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4" style={{ color: '#848E9C' }} />
                  ) : (
                    <ChevronRight className="w-4 h-4" style={{ color: '#848E9C' }} />
                  )}
                  <span className="text-sm font-medium" style={{ color: '#EAECEF' }}>
                    {label}
                  </span>
                  {isModified && (
                    <span
                      className="px-1.5 py-0.5 text-[10px] rounded"
                      style={{ background: 'rgba(168, 85, 247, 0.15)', color: '#a855f7' }}
                    >
                      {language === 'zh' ? '已修改' : 'Modified'}
                    </span>
                  )}
                </div>
                <span className="text-[10px]" style={{ color: '#848E9C' }}>
                  {value.length} {t('chars')}
                </span>
              </button>

              {isExpanded && (
                <div className="px-3 pb-3">
                  <p className="text-xs mb-2" style={{ color: '#848E9C' }}>
                    {desc}
                  </p>
                  <textarea
                    value={value}
                    onChange={(e) => updateSection(sectionKey, e.target.value)}
                    disabled={disabled}
                    rows={6}
                    className="w-full px-3 py-2 rounded-lg resize-y font-mono text-xs"
                    style={{
                      background: '#1E2329',
                      border: '1px solid #2B3139',
                      color: '#EAECEF',
                      minHeight: '120px',
                    }}
                  />
                  <div className="flex justify-end mt-2">
                    <button
                      onClick={() => resetSection(sectionKey)}
                      disabled={disabled || !isModified}
                      className="flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors hover:bg-white/5 disabled:opacity-30"
                      style={{ color: '#848E9C' }}
                    >
                      <RotateCcw className="w-3 h-3" />
                      {t('resetToDefault')}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
