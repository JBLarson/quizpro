// static/js/api.js
// Manages API keys, selects AI model, and sends prompts to the backend or LLM API.

// In-memory variables to store the current API key and selected model
let apiKey = '';
let selectedModel = '';

// setApiKey: stores the API key in-memory and persists it in sessionStorage
function setApiKey(key) {
  apiKey = key;
  sessionStorage.setItem('quizpro_api_key', key);
}

// getApiKey: retrieves the API key from memory or sessionStorage
function getApiKey() {
  return apiKey || sessionStorage.getItem('quizpro_api_key') || '';
}

// setModel: updates the in-memory selectedModel variable
function setModel(model) {
  selectedModel = model;
}

// getModel: returns the currently selected AI model for quiz generation
function getModel() {
  return selectedModel;
}

// sendPrompt: placeholder function to send a prompt payload to the LLM service
// prompt: combined slide text + user preferences
// model: string label of the target LLM (e.g., 'openai', 'deepseek')
async function sendPrompt(prompt, model = getModel()) {
  // TODO: Implement fetch POST to /quiz or external LLM endpoint
  return { response: 'Sample response from ' + model };
}

// Export functions for use in main.js
export { setApiKey, getApiKey, setModel, getModel, sendPrompt }; 