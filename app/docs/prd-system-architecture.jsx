import React, { useState } from 'react';
import { FileText, Mail, Table, Presentation, Image, MessageCircle, Mic, FileEdit, ArrowDown, CheckCircle, AlertCircle, Settings, Layers, Target, ClipboardList } from 'lucide-react';

export default function PRDSystemArchitecture() {
  const [selectedLayer, setSelectedLayer] = useState(null);
  const [selectedInput, setSelectedInput] = useState(null);

  const inputTypes = [
    { id: 'email', icon: Mail, label: '이메일', color: 'bg-blue-500', difficulty: '⭐⭐⭐' },
    { id: 'excel', icon: Table, label: '엑셀/CSV', color: 'bg-green-500', difficulty: '⭐⭐' },
    { id: 'ppt', icon: Presentation, label: 'PPT', color: 'bg-orange-500', difficulty: '⭐⭐⭐' },
    { id: 'image', icon: Image, label: '이미지', color: 'bg-purple-500', difficulty: '⭐⭐⭐⭐' },
    { id: 'chat', icon: MessageCircle, label: '메신저', color: 'bg-yellow-500', difficulty: '⭐⭐⭐⭐' },
    { id: 'audio', icon: Mic, label: '음성녹취', color: 'bg-red-500', difficulty: '⭐⭐⭐⭐⭐' },
    { id: 'doc', icon: FileEdit, label: '기존문서', color: 'bg-indigo-500', difficulty: '⭐⭐' },
    { id: 'text', icon: FileText, label: '텍스트', color: 'bg-gray-500', difficulty: '⭐⭐' },
  ];

  const layers = [
    {
      id: 'layer1',
      name: 'Layer 1: 파싱',
      subtitle: 'Type-Specific Parsing',
      color: 'from-blue-400 to-blue-600',
      icon: Settings,
      description: '파일 형식별 전문 파서로 텍스트 추출',
      details: [
        '파일 형식 자동 감지',
        '메타데이터 추출 (작성자, 날짜)',
        '구조 분석 (헤더, 테이블, 리스트)',
        '이미지 OCR / 음성 STT 변환'
      ]
    },
    {
      id: 'layer2',
      name: 'Layer 2: 정규화',
      subtitle: 'Intelligent Normalization',
      color: 'from-purple-400 to-purple-600',
      icon: Layers,
      description: '핵심 엔진 - 구조화된 요구사항으로 변환',
      details: [
        '요구사항 분류 (FR / NFR / Constraints)',
        'User Story 형식 변환',
        '신뢰도 점수 (0.0 ~ 1.0) 부여',
        '누락 정보 & 가정사항 기록'
      ],
      highlight: true
    },
    {
      id: 'layer3',
      name: 'Layer 3: 검증',
      subtitle: 'Quality Validation',
      color: 'from-amber-400 to-amber-600',
      icon: CheckCircle,
      description: '품질 검증 및 PM 검토 분기',
      details: [
        '완전성 / 일관성 / 추적성 검증',
        '신뢰도 > 80%: 자동 승인',
        '신뢰도 < 80%: PM 검토 요청',
        '충돌 요구사항 감지'
      ]
    },
    {
      id: 'layer4',
      name: 'Layer 4: PRD 생성',
      subtitle: 'Document Generation',
      color: 'from-emerald-400 to-emerald-600',
      icon: Target,
      description: '최종 PRD 문서 자동 생성',
      details: [
        '표준 PRD 템플릿 적용',
        'User Stories + Acceptance Criteria',
        '타임라인 & 마일스톤',
        '미해결 사항 목록'
      ]
    }
  ];

  const inputDetails = {
    email: {
      title: '이메일 스레드 처리',
      strategies: ['스레드 시간순 재구성', '발신자 역할 추론', '결정/논의 구분', '최종 합의 추적']
    },
    excel: {
      title: '엑셀/CSV 처리',
      strategies: ['컬럼명 자동 매핑', '값 정규화 (우선순위, 상태)', '병합 셀 처리', '다중 시트 통합']
    },
    ppt: {
      title: 'PPT 처리',
      strategies: ['슬라이드별 구조 분석', '제목→카테고리 매핑', '이미지/다이어그램 처리', '발표 노트 포함']
    },
    image: {
      title: '이미지 처리',
      strategies: ['UI 스크린샷 인식', '마킹/주석 해석', 'Before/After 패턴', '텍스트와 조합 분석']
    },
    chat: {
      title: '메신저 대화 처리',
      strategies: ['대화 세션 구분', '줄임말/이모지 해석', '노이즈 필터링', '맥락 기반 재구성']
    },
    audio: {
      title: '음성 녹취 처리',
      strategies: ['STT 오류 교정', '화자 분리', '구어체 정제', '지시어 맥락 파악']
    },
    doc: {
      title: '기존 문서 수정',
      strategies: ['변경 유형 분류 (ADD/MODIFY/DELETE)', 'Diff 생성', '영향 분석', '버전 추적']
    },
    text: {
      title: '텍스트/메모 처리',
      strategies: ['문단/리스트 구조 분석', '의도 추론', '긴급도 키워드 탐지', '참조 링크 추출']
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-emerald-400 bg-clip-text text-transparent mb-2">
            PRD 자동 생성 시스템
          </h1>
          <p className="text-slate-400">다양한 입력 형식을 표준 PRD로 변환하는 4단계 파이프라인</p>
        </div>

        {/* Input Types */}
        <div className="mb-6">
          <div className="text-center mb-3">
            <span className="text-sm text-slate-400 uppercase tracking-wider">입력 (자유 형식)</span>
          </div>
          <div className="grid grid-cols-4 md:grid-cols-8 gap-2">
            {inputTypes.map((input) => {
              const Icon = input.icon;
              const isSelected = selectedInput === input.id;
              return (
                <button
                  key={input.id}
                  onClick={() => setSelectedInput(isSelected ? null : input.id)}
                  className={`p-3 rounded-lg transition-all duration-300 flex flex-col items-center gap-1
                    ${isSelected 
                      ? `${input.color} ring-2 ring-white shadow-lg scale-105` 
                      : 'bg-slate-700/50 hover:bg-slate-700'}`}
                >
                  <Icon size={20} />
                  <span className="text-xs">{input.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Input Details */}
        {selectedInput && (
          <div className="mb-6 p-4 bg-slate-800/50 rounded-xl border border-slate-700 animate-fadeIn">
            <div className="flex items-center gap-3 mb-3">
              <div className={`p-2 rounded-lg ${inputTypes.find(i => i.id === selectedInput).color}`}>
                {React.createElement(inputTypes.find(i => i.id === selectedInput).icon, { size: 20 })}
              </div>
              <div>
                <h3 className="font-semibold">{inputDetails[selectedInput].title}</h3>
                <span className="text-xs text-slate-400">
                  난이도: {inputTypes.find(i => i.id === selectedInput).difficulty}
                </span>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {inputDetails[selectedInput].strategies.map((strategy, idx) => (
                <div key={idx} className="text-xs bg-slate-700/50 rounded px-2 py-1.5 text-slate-300">
                  • {strategy}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Arrow */}
        <div className="flex justify-center mb-4">
          <ArrowDown className="text-slate-500 animate-bounce" />
        </div>

        {/* Processing Layers */}
        <div className="space-y-3">
          {layers.map((layer, index) => {
            const Icon = layer.icon;
            const isSelected = selectedLayer === layer.id;
            return (
              <div key={layer.id}>
                <button
                  onClick={() => setSelectedLayer(isSelected ? null : layer.id)}
                  className={`w-full p-4 rounded-xl transition-all duration-300 text-left
                    ${layer.highlight ? 'ring-2 ring-purple-400/50' : ''}
                    ${isSelected 
                      ? `bg-gradient-to-r ${layer.color} shadow-xl` 
                      : 'bg-slate-800/80 hover:bg-slate-700/80'}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${isSelected ? 'bg-white/20' : 'bg-slate-700'}`}>
                        <Icon size={20} />
                      </div>
                      <div>
                        <div className="font-semibold">{layer.name}</div>
                        <div className="text-xs text-slate-300 opacity-80">{layer.subtitle}</div>
                      </div>
                    </div>
                    {layer.highlight && (
                      <span className="text-xs bg-purple-500/30 text-purple-200 px-2 py-1 rounded-full">
                        핵심
                      </span>
                    )}
                  </div>
                  
                  {isSelected && (
                    <div className="mt-4 pt-4 border-t border-white/20 animate-fadeIn">
                      <p className="text-sm mb-3 opacity-90">{layer.description}</p>
                      <div className="grid grid-cols-2 gap-2">
                        {layer.details.map((detail, idx) => (
                          <div key={idx} className="flex items-start gap-2 text-sm">
                            <CheckCircle size={14} className="mt-0.5 flex-shrink-0" />
                            <span className="opacity-90">{detail}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </button>
                
                {index < layers.length - 1 && (
                  <div className="flex justify-center py-2">
                    <ArrowDown size={16} className="text-slate-600" />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Output */}
        <div className="flex justify-center my-4">
          <ArrowDown className="text-slate-500" />
        </div>

        <div className="p-5 rounded-xl bg-gradient-to-r from-emerald-500/20 to-blue-500/20 border border-emerald-500/30">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-emerald-500 rounded-lg">
              <ClipboardList size={24} />
            </div>
            <div>
              <h3 className="font-bold text-lg">PRD 문서 (최종 출력)</h3>
              <p className="text-sm text-slate-400">표준화된 제품 요구사항 문서</p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { title: '개요', desc: '배경 / 목표 / 범위' },
              { title: '기능 요구사항', desc: 'User Stories + AC' },
              { title: '비기능 요구사항', desc: '성능 / 보안 / 확장성' },
              { title: '제약 & 일정', desc: '의존성 / 마일스톤' }
            ].map((section, idx) => (
              <div key={idx} className="bg-slate-800/50 rounded-lg p-3">
                <div className="font-medium text-sm text-emerald-400">{section.title}</div>
                <div className="text-xs text-slate-400">{section.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Key Principles */}
        <div className="mt-8 grid md:grid-cols-3 gap-4">
          <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
            <div className="text-blue-400 font-semibold mb-2">🎯 입력 원칙</div>
            <p className="text-sm text-slate-400">사용자에게 형식을 강요하지 않는다. 시스템이 해석의 부담을 진다.</p>
          </div>
          <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
            <div className="text-purple-400 font-semibold mb-2">🔄 정규화 원칙</div>
            <p className="text-sm text-slate-400">외부는 자유, 내부는 표준. 변환 과정의 모든 결정을 기록한다.</p>
          </div>
          <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
            <div className="text-emerald-400 font-semibold mb-2">✅ 검증 원칙</div>
            <p className="text-sm text-slate-400">자동화 + 사람 검토 하이브리드. 불확실함을 숨기지 않는다.</p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-slate-500 text-sm">
          클릭하여 각 레이어와 입력 형식의 상세 정보를 확인하세요
        </div>
      </div>
    </div>
  );
}
