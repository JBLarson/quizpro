// API key/model handling and LLM calls for QuizPro

let apiKey = '';
let selectedModel = '';

function setApiKey(key) {
  apiKey = key;
  sessionStorage.setItem('quizpro_api_key', key);
}

function getApiKey() {
  return apiKey || sessionStorage.getItem('quizpro_api_key') || '';
}

function setModel(model) {
  selectedModel = model;
}

function getModel() {
  return selectedModel;
}

// Placeholder: send prompt to LLM API
async function sendPrompt(prompt, model = getModel()) {
  // TODO: Implement API call
  return { response: 'Sample response from ' + model };
}

export { setApiKey, getApiKey, setModel, getModel, sendPrompt }; 