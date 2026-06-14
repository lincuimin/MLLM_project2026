// 主导出文件

export { BrowserAutomation } from './core/browser-automation.js';
export { VLMService, type VLMAnalysisResult, type ElementAnalysis, type InteractiveArea } from './services/vlm-service.js';
export { LLMService, type LLMPlan, type ActionStep } from './services/llm-service.js';
export {
    MultimodalWebAgent,
    type ExecutionResult,
    type FailureRecord,
} from './agent/multimodal-web-agent.js';

// 默认导出Agent类
import { MultimodalWebAgent } from './agent/multimodal-web-agent.js';
export default MultimodalWebAgent;
