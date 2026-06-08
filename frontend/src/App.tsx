import { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  generateInterviewReport,
  getInterviewReport,
  getModelConfig,
  saveModelConfig,
  sendInterviewMessage,
  uploadDocument,
  InterviewReport,
  PublicModelConfig,
} from './api';

type ChatMessage = {
  role: 'user' | 'assistant' | 'system';
  content: string;
};

type UploadedDocument = {
  document_id: string;
  name: string;
  size: number;
  status: string;
  chunk_count?: number;
  indexed_chunks?: number;
  metadata?: Record<string, unknown>;
};

const INTERVIEW_ID = 'local-demo-interview';

const initialMessages: ChatMessage[] = [
  {
    role: 'system',
    content: '欢迎进入模拟面试作战台。先在右侧保存 DeepSeek API Key 与 Base URL，再开始一轮真实追问。',
  },
  {
    role: 'assistant',
    content: '我会以移动端架构师面试官身份，每次只追问一个问题。你可以先发送自我介绍，或上传简历/JD 后再开始。',
  },
];

const interviewPrompts = [
  '请从移动端架构师岗位开始，先让我做 2 分钟自我介绍。',
  '围绕 Flutter/Android 架构治理问我一个高阶问题。',
  '请模拟 AI Native App 工程化方向的系统设计追问。',
];

export function App() {
  const [modelConfig, setModelConfig] = useState<PublicModelConfig | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('https://api.deepseek.com');
  const [chatModel, setChatModel] = useState('deepseek-chat');
  const [reasonerModel, setReasonerModel] = useState('deepseek-reasoner');
  const [configMessage, setConfigMessage] = useState('正在读取后端模型配置...');
  const [input, setInput] = useState('请你作为面试官，开始一场移动端架构师模拟面试。');
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [loading, setLoading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');
  const [uploadedDocuments, setUploadedDocuments] = useState<UploadedDocument[]>([]);
  const [report, setReport] = useState<InterviewReport | null>(null);
  const [generatedReport, setGeneratedReport] = useState('');
  const [reportMessage, setReportMessage] = useState('完成几轮对话后，可基于当前 conversation 与候选人资料生成复盘报告。');

  const readiness = useMemo(() => {
    const documentsReady = uploadedDocuments.length > 0;
    return [
      { label: 'DeepSeek Runtime', done: Boolean(modelConfig?.configured), detail: modelConfig?.configured ? modelConfig.api_key_preview ?? '已保存' : '等待保存 Key' },
      { label: 'RAG Source', done: documentsReady, detail: documentsReady ? `${uploadedDocuments.length} 份资料` : '可先上传简历/JD' },
      { label: 'Interview Loop', done: messages.some((message) => message.role === 'user'), detail: loading ? '模型追问中' : '可开始对话' },
    ];
  }, [loading, messages, modelConfig, uploadedDocuments.length]);

  useEffect(() => {
    getModelConfig()
      .then((config) => {
        setModelConfig(config);
        setBaseUrl(config.base_url);
        setChatModel(config.chat_model);
        setReasonerModel(config.reasoner_model);
        setConfigMessage(config.configured ? '已读取后端保存的模型配置。' : '后端可用，请输入 API Key 完成配置。');
      })
      .catch(() => setConfigMessage('后端未启动或配置接口不可用，请确认 FastAPI 服务运行在 8000 端口。'));
  }, []);

  async function handleSaveConfig(event: FormEvent) {
    event.preventDefault();
    setConfigMessage('保存中...');
    try {
      const saved = await saveModelConfig({
        api_key: apiKey,
        base_url: baseUrl,
        chat_model: chatModel,
        reasoner_model: reasonerModel,
      });
      setModelConfig(saved);
      setApiKey('');
      setConfigMessage('模型配置已保存到后端本地 runtime；API Key 不会写入前端代码或 Git。');
    } catch (error) {
      setConfigMessage(error instanceof Error ? error.message : '保存失败');
    }
  }

  async function handleSend() {
    if (!input.trim() || loading) return;
    const userMessage: ChatMessage = { role: 'user', content: input.trim() };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput('');
    setLoading(true);
    try {
      const content = await sendInterviewMessage({
        content: userMessage.content,
        conversation: nextMessages,
        documentIds: uploadedDocuments.map((document) => document.document_id),
      });
      setMessages((current) => [...current, { role: 'assistant', content }]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        { role: 'assistant', content: error instanceof Error ? error.message : '请求失败' },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(file?: File) {
    if (!file) return;
    setUploadMessage('上传中...');
    try {
      const result = await uploadDocument(file);
      setUploadedDocuments((current) => [
        ...current,
        {
          document_id: result.document_id,
          name: result.filename ?? file.name,
          size: result.size ?? file.size,
          status: result.status ?? 'uploaded',
          chunk_count: result.chunk_count,
          indexed_chunks: result.indexed_chunks,
          metadata: result.metadata,
        },
      ]);
      setUploadMessage(`已上传并索引：${file.name}（${result.indexed_chunks ?? 0}/${result.chunk_count ?? 0} chunks）。`);
    } catch (error) {
      setUploadMessage(error instanceof Error ? error.message : '上传失败');
    }
  }

  async function handleGenerateReport() {
    setReportMessage('正在基于当前对话生成复盘报告...');
    try {
      const content = await generateInterviewReport({
        interviewId: INTERVIEW_ID,
        conversation: messages,
        documentIds: uploadedDocuments.map((document) => document.document_id),
      });
      setGeneratedReport(content);
      setReportMessage('复盘报告已生成。');
    } catch (error) {
      setReportMessage(error instanceof Error ? error.message : '生成报告失败');
    }
  }

  async function handleLoadReport() {
    setReportMessage('读取结构化报告占位中...');
    try {
      const payload = await getInterviewReport(INTERVIEW_ID);
      setReport(payload);
      setReportMessage('已读取结构化报告占位。');
    } catch (error) {
      setReportMessage(error instanceof Error ? error.message : '读取报告失败');
    }
  }

  return (
    <main className="shell">
      <section className="hero-panel">
        <div className="hero-copy-block">
          <p className="eyebrow">AI Interview Cockpit</p>
          <h1>模拟面试助手</h1>
          <p className="hero-copy">
            面向移动端架构师与 AI Native App 求职场景，把模型配置、资料入口、实时追问和复盘报告集中到一个前端作战台。
          </p>
          <div className="hero-actions">
            <a href="#interview">开始模拟</a>
            <a className="ghost-link" href="#runtime">配置模型</a>
          </div>
        </div>
        <div className="status-grid">
          {readiness.map((item) => (
            <div className={item.done ? 'ready' : ''} key={item.label}>
              <span>{item.label}</span>
              <strong>{item.detail}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="workspace" id="interview">
        <section className="interview-card">
          <div className="card-head">
            <div>
              <p className="eyebrow">Live Interview</p>
              <h2>对话式模拟面试</h2>
            </div>
            <span className={modelConfig?.configured ? 'live-dot ok' : 'live-dot'}>
              {modelConfig?.configured ? '模型已配置' : '待配置模型'}
            </span>
          </div>

          <div className="prompt-row">
            {interviewPrompts.map((prompt) => (
              <button className="prompt-chip" key={prompt} onClick={() => setInput(prompt)} type="button">
                {prompt}
              </button>
            ))}
          </div>

          <div className="chat-window">
            {messages.map((message, index) => (
              <div className={`bubble ${message.role}`} key={`${message.role}-${index}`}>
                <span>{message.role === 'user' ? '候选人' : message.role === 'assistant' ? '面试官' : '系统'}</span>
                <p>{message.content}</p>
              </div>
            ))}
            {loading && <div className="bubble assistant thinking"><span>面试官</span><p>正在组织下一轮追问...</p></div>}
          </div>

          <div className="composer">
            <textarea
              aria-label="面试输入"
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.metaKey && event.key === 'Enter') handleSend();
              }}
              value={input}
            />
            <button onClick={handleSend} disabled={loading || !input.trim()} type="button">
              {loading ? '等待中' : '发送'}
            </button>
          </div>
          <p className="shortcut">提示：按 ⌘ + Enter 发送；每轮只保留一个明确追问，更接近真实面试节奏。</p>
        </section>

        <aside className="side-panel">
          <form className="config-card" id="runtime" onSubmit={handleSaveConfig}>
            <p className="eyebrow">Model Runtime</p>
            <h2>DeepSeek 配置</h2>
            <p className="panel-copy">API Key 只从前端输入并提交给后端保存；源码中不包含任何密钥。</p>
            <label>
              API Key
              <input
                autoComplete="off"
                onChange={(event) => setApiKey(event.target.value)}
                placeholder={modelConfig?.api_key_preview ?? 'sk-...'}
                required={!modelConfig?.configured}
                type="password"
                value={apiKey}
              />
            </label>
            <label>
              Base URL
              <input value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} />
            </label>
            <label>
              Chat Model
              <input value={chatModel} onChange={(event) => setChatModel(event.target.value)} />
            </label>
            <label>
              Reasoner Model
              <input value={reasonerModel} onChange={(event) => setReasonerModel(event.target.value)} />
            </label>
            <button type="submit">保存模型配置</button>
            {configMessage && <p className="note">{configMessage}</p>}
          </form>

          <div className="config-card upload-card">
            <p className="eyebrow">RAG Source</p>
            <h2>资料上传</h2>
            <label className="file-drop">
              <span>上传简历 / JD / 项目材料</span>
              <input type="file" onChange={(event) => handleUpload(event.target.files?.[0])} />
            </label>
            {uploadedDocuments.length > 0 && (
              <ul className="document-list">
                {uploadedDocuments.map((document) => (
                  <li key={document.document_id}>
                    <span>{document.name}</span>
                    <strong>
                      {Math.ceil(document.size / 1024)} KB · {document.status} · {document.indexed_chunks ?? 0} chunks
                    </strong>
                  </li>
                ))}
              </ul>
            )}
            <p className="note">上传后会保存 document_id，并在面试追问与报告生成中作为 RAG 上下文传给后端。</p>
            {uploadMessage && <p className="note strong">{uploadMessage}</p>}
          </div>
        </aside>
      </section>

      <section className="report-panel" id="report">
        <div>
          <p className="eyebrow">Interview Report</p>
          <h2>复盘报告</h2>
          <p>{generatedReport || report?.summary || reportMessage}</p>
        </div>
        <div className="score-grid">
          {Object.entries(report?.scores ?? {
            technical_accuracy: 0,
            communication: 0,
            project_depth: 0,
            position_match: 0,
          }).map(([label, score]) => (
            <div key={label}>
              <span>{label.replaceAll('_', ' ')}</span>
              <strong>{Number(score)}</strong>
            </div>
          ))}
        </div>
        <button onClick={handleGenerateReport} type="button">生成当前面试报告</button>
        <button className="secondary-button" onClick={handleLoadReport} type="button">读取结构化占位</button>
      </section>
    </main>
  );
}
