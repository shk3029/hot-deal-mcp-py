const INDUSTRY_CODES = {
  "어디서나": 1,
  "주유": 2,
  "대형마트": 3,
  "편의점": 4,
  "쇼핑": 5,
  "영화/공연": 6,
  "외식/배달": 7,
  "카페": 8,
  "교통": 9,
  "대중교통": 9,
  "병원/약국": 10,
  "공과금": 11,
  "통신": 12,
  "교육/육아": 13,
  "레저": 14,
  "항공": 15,
  "항공/마일리지": 15,
  "공항라운지": 16,
  "공항/공항라운지": 16,
  "뷰티": 17,
  "간편결제": 18,
  "구독": 19,
  "여행/숙박": 20,
  "금융": 21,
  "할인": 22,
  "적립": 23,
  "청소년": 24,
};

const thread = document.querySelector("#thread");
const input = document.querySelector("#json-input");
const errorBox = document.querySelector("#error");
const copyText = document.querySelector("#copy-text");
const toolSelect = document.querySelector("#tool-select");
const toolFields = document.querySelector("#tool-fields");
const toolDescription = document.querySelector("#tool-description");
let manualPreviewMessage = null;
let liveRenderTimer = null;
let toolDefinitions = [];

const TOOL_FIELD_OPTIONS = {
  getCreditCardRecommendationsWithSelector: {
    industry: [
      ["", "미지정 · 업종 선택 위젯"],
      ...Object.entries(INDUSTRY_CODES)
        .filter(([label]) => !["대중교통", "항공/마일리지", "공항/공항라운지"].includes(label))
        .map(([label, value]) => [String(value), `${value} · ${label}`]),
    ],
    annualFee: ["제한없음", "0~1만원", "1~2만원", "2~3만원", "3~4만원", "4~5만원", "5~10만원", "10만원이상"],
    cardType: [["1", "신용카드"], ["2", "체크카드"]],
    sort: ["출시일순", "정확도순", "높은연회비순", "낮은연회비순"],
  },
  getFinancialLifeKnowledgeArticles: {
    category: ["트렌드", "금융", "카드연구소"],
  },
};

const FIELD_LABELS = {
  industry: "업종",
  annualFee: "연회비",
  cardType: "카드 종류",
  sort: "정렬",
  cardName: "카드명",
  category: "카테고리",
};

function setError(message = "") {
  errorBox.hidden = !message;
  errorBox.textContent = message;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function spacing(value) {
  return `${Number(value || 0) * 4}px`;
}

function optionPair(option) {
  return Array.isArray(option) ? option : [option, option];
}

function createField(toolName, name, property, required) {
  const wrapper = el("div", "tool-field");
  const label = el("label", "field-label", `${FIELD_LABELS[name] || name}${required ? " *" : ""}`);
  label.htmlFor = `tool-param-${name}`;

  const configuredOptions = TOOL_FIELD_OPTIONS[toolName]?.[name];
  const options = configuredOptions || property.enum;
  let control;
  if (Array.isArray(options)) {
    control = document.createElement("select");
    options.map(optionPair).forEach(([value, text]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = text;
      control.append(option);
    });
  } else {
    control = document.createElement("input");
    control.type = property.type === "integer" ? "number" : "text";
    control.placeholder = required ? "필수 입력" : "미입력 시 생략";
  }
  control.id = `tool-param-${name}`;
  control.className = "form-control";
  control.dataset.param = name;
  control.dataset.type = property.type || "string";
  control.dataset.required = String(required);

  const help = el("p", "tool-field-help", property.description || "");
  wrapper.append(label, control, help);
  return wrapper;
}

function renderToolForm() {
  const definition = toolDefinitions.find((tool) => tool.name === toolSelect.value);
  toolFields.replaceChildren();
  if (!definition) return;
  toolDescription.textContent = definition.description;
  const properties = definition.inputSchema?.properties || {};
  const required = new Set(definition.inputSchema?.required || []);
  if (!Object.keys(properties).length) {
    toolFields.append(el("div", "no-parameters", "입력 파라미터가 없는 Tool입니다."));
    return;
  }
  Object.entries(properties).forEach(([name, property]) => {
    toolFields.append(createField(definition.name, name, property, required.has(name)));
  });
}

function collectToolArguments() {
  const argumentsValue = {};
  toolFields.querySelectorAll("[data-param]").forEach((control) => {
    const value = control.value.trim();
    if (value === "") return;
    argumentsValue[control.dataset.param] =
      control.dataset.type === "integer" ? Number(value) : value;
  });
  return argumentsValue;
}

async function runSelectedTool() {
  const definition = toolDefinitions.find((tool) => tool.name === toolSelect.value);
  if (!definition) return;
  const argumentsValue = collectToolArguments();
  addUserMessage(`${definition.title} · 직접 호출`);
  await callTool(definition.name, argumentsValue);
}

async function loadToolDefinitions() {
  try {
    const response = await fetch("/api/tools");
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Tool 목록 조회에 실패했습니다.");
    toolDefinitions = data.tools || [];
    toolSelect.replaceChildren();
    toolDefinitions.forEach((definition) => {
      const option = document.createElement("option");
      option.value = definition.name;
      option.textContent = `${definition.title} (${definition.name})`;
      toolSelect.append(option);
    });
    renderToolForm();
  } catch (error) {
    setError(error.message);
  }
}

function applyLayout(node, spec) {
  if (spec.gap !== undefined) node.style.gap = spacing(spec.gap);
  if (spec.flex !== undefined) {
    node.style.flex = spec.flex === "auto" ? "1 1 auto" : String(spec.flex);
  }
  if (spec.width !== undefined) {
    node.style.width = typeof spec.width === "number" ? `${spec.width}px` : spec.width;
  }
  if (spec.align) node.classList.add(`w-align-${spec.align}`);
  if (spec.padding) {
    if (spec.padding.x !== undefined) {
      node.style.paddingLeft = spacing(spec.padding.x);
      node.style.paddingRight = spacing(spec.padding.x);
    }
    if (spec.padding.y !== undefined) {
      node.style.paddingTop = spacing(spec.padding.y);
      node.style.paddingBottom = spacing(spec.padding.y);
    }
  }
  if (spec.textAlign) node.style.textAlign = spec.textAlign;
}

function renderChildren(parent, children = []) {
  children.forEach((child) => parent.append(renderWidget(child)));
}

function renderWidget(spec) {
  if (typeof spec === "string") {
    return el("div", "w-caption", spec);
  }
  if (!spec || typeof spec !== "object") {
    return document.createTextNode("");
  }

  let node;
  switch (spec.type) {
    case "Card":
      node = el("div", "w-card");
      renderChildren(node, spec.children);
      break;
    case "Col":
      node = el("div", "w-col");
      renderChildren(node, spec.children);
      break;
    case "Row":
      node = el("div", "w-row");
      renderChildren(node, spec.children);
      break;
    case "Text":
      node = el("div", "w-text", spec.value || "");
      if (spec.weight === "semibold") node.classList.add("w-semibold");
      if (spec.size) node.classList.add(`w-size-${spec.size}`);
      if (spec.maxLines) {
        node.classList.add("w-clamp");
        node.style.webkitLineClamp = spec.maxLines;
      }
      break;
    case "Caption":
      node = el("div", "w-caption", spec.value || "");
      break;
    case "Badge":
      node = el("span", `w-badge w-badge-${spec.color || "success"}`, spec.label || "");
      break;
    case "Image":
      node = document.createElement("img");
      node.className = `w-image ${spec.radius ? `w-radius-${spec.radius}` : ""}`;
      node.src = spec.src || "";
      node.alt = spec.alt || "";
      node.width = Number(spec.width || 112);
      node.height = Number(spec.height || 72);
      node.style.objectFit = spec.fit || "contain";
      break;
    case "Button":
      node = el("button", "w-button", spec.label || "");
      node.type = "button";
      if (spec.variant === "outline") node.classList.add("w-button-outline");
      if (spec.variant === "ghost") node.classList.add("w-button-ghost");
      if (spec.block) node.classList.add("w-button-block");
      if (spec.uniform) node.classList.add("w-button-uniform");
      if (spec.iconEnd === "chevron-right") {
        node.setAttribute("aria-label", spec.label || "카드 상세 보기");
        node.append(el("span", "chevron"));
      }
      node.addEventListener("click", () => handleAction(spec.onClickAction));
      break;
    case "Divider":
      node = el("div", "w-divider");
      break;
    case "ListView":
      node = el("div", "w-list-view");
      renderChildren(node, (spec.children || []).slice(0, spec.limit || undefined));
      break;
    case "ListViewItem":
      node = el("div", "w-list-item");
      renderChildren(node, spec.children);
      if (spec.onClickAction) {
        node.classList.add("w-clickable");
        node.addEventListener("click", () => handleAction(spec.onClickAction));
      }
      break;
    default:
      node = el("div", "w-col");
      renderChildren(node, spec.children);
  }
  applyLayout(node, spec);
  return node;
}

function unwrapPayload(value) {
  let current = value;
  for (let depth = 0; depth < 5; depth += 1) {
    if (typeof current === "string") {
      current = JSON.parse(current);
      continue;
    }
    if (current?.payload?.widget !== undefined) return current.payload;
    if (current?.widget !== undefined) return current;
    if (current?.result?.content?.[0]?.text !== undefined) {
      current = current.result.content[0].text;
      continue;
    }
    if (current?.content?.[0]?.text !== undefined) {
      current = current.content[0].text;
      continue;
    }
    break;
  }
  if (!current || current.widget === undefined) {
    throw new Error("widget 프로퍼티를 찾지 못했습니다.");
  }
  return current;
}

function addUserMessage(text) {
  const message = el("div", "message user-message");
  message.append(el("div", "user-bubble", text));
  thread.append(message);
  message.scrollIntoView({ behavior: "smooth", block: "center" });
}

function addAssistantWidget(payload) {
  const message = el("div", "message assistant-message");
  const meta = el("div", "assistant-meta");
  meta.append(el("span", "assistant-logo"));
  meta.append(document.createTextNode("Kakao Tools · 신한카드"));
  const host = el("div", "widget-host");
  if (payload.widget) host.append(renderWidget(payload.widget));
  else host.append(el("div", "w-caption", "widget: null"));
  message.append(meta, host);
  thread.append(message);
  copyText.textContent = payload.copy_text || "";
  input.value = JSON.stringify(payload, null, 2);
  message.scrollIntoView({ behavior: "smooth", block: "center" });
}

function updateManualPreview(payload) {
  if (!manualPreviewMessage || !manualPreviewMessage.isConnected) {
    manualPreviewMessage = el("div", "message assistant-message manual-preview-message");
    const meta = el("div", "assistant-meta");
    meta.append(el("span", "assistant-logo"));
    meta.append(document.createTextNode("JSON 실시간 미리보기"));
    manualPreviewMessage.append(meta, el("div", "widget-host"));
    thread.append(manualPreviewMessage);
  }

  const host = manualPreviewMessage.querySelector(".widget-host");
  host.replaceChildren(
    payload.widget
      ? renderWidget(payload.widget)
      : el("div", "w-caption", "widget: null"),
  );
  copyText.textContent = payload.copy_text || "";
  manualPreviewMessage.scrollIntoView({ behavior: "smooth", block: "center" });
}

function addLoading() {
  const message = el("div", "message assistant-message");
  message.dataset.loading = "true";
  const loading = el("div", "loading-message");
  loading.append(el("span"), el("span"), el("span"));
  message.append(loading);
  thread.append(message);
  message.scrollIntoView({ behavior: "smooth", block: "center" });
  return message;
}

async function callTool(name, argumentsValue) {
  setError();
  const loading = addLoading();
  try {
    const response = await fetch("/api/tools/call", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, arguments: argumentsValue }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Tool 호출에 실패했습니다.");
    loading.remove();
    addAssistantWidget(unwrapPayload(data));
  } catch (error) {
    loading.remove();
    setError(error.message);
  }
}

async function handleAction(action) {
  const target = action?.payload?.target;
  if (!target) return;
  if (target.type === "sendUserMessage") {
    const text = target.properties?.text || "";
    addUserMessage(text);
    if (Object.hasOwn(INDUSTRY_CODES, text)) {
      await callTool("getCreditCardRecommendationsWithSelector", {
        industry: INDUSTRY_CODES[text],
        annualFee: "제한없음",
        cardType: 1,
        sort: "출시일순",
      });
      return;
    }
    if (text.endsWith(" 혜택 알려줘")) {
      await callTool("getCreditCardDetail", {
        cardName: text.slice(0, -" 혜택 알려줘".length),
      });
      return;
    }
    setError(`후속 발화에 연결할 Tool 규칙이 없습니다: ${text}`);
    return;
  }
  const url = target.pcUrl || target.url;
  if (url) window.open(url, "_blank", "noopener,noreferrer");
}

function renderInput() {
  try {
    setError();
    const payload = unwrapPayload(JSON.parse(input.value));
    updateManualPreview(payload);
  } catch (error) {
    setError(error.message);
  }
}

function scheduleLiveRender() {
  window.clearTimeout(liveRenderTimer);
  liveRenderTimer = window.setTimeout(renderInput, 250);
}

function toggleSection(button) {
  const body = document.getElementById(button.dataset.toggleSection);
  if (!body) return;
  const willExpand = body.hidden;
  body.hidden = !willExpand;
  button.setAttribute("aria-expanded", String(willExpand));
  button.textContent = willExpand ? "접기" : "펼치기";
}

async function startRecommendation() {
  addUserMessage("카드 추천해줘");
  await callTool("getCreditCardRecommendationsWithSelector", {
    industry: null,
    annualFee: "제한없음",
    cardType: 1,
    sort: "출시일순",
  });
}

function reset() {
  thread.replaceChildren();
  manualPreviewMessage = null;
  input.value = "";
  copyText.textContent = "";
  setError();
  startRecommendation();
}

document.querySelector("#render-button").addEventListener("click", renderInput);
document.querySelector("#call-tool-button").addEventListener("click", runSelectedTool);
toolSelect.addEventListener("change", renderToolForm);
input.addEventListener("input", scheduleLiveRender);
document.querySelectorAll("[data-toggle-section]").forEach((button) => {
  button.addEventListener("click", () => toggleSection(button));
});
document.querySelector("#reset-button").addEventListener("click", reset);
document.querySelector("#initial-call-button").addEventListener("click", startRecommendation);

fetch("/api/health")
  .then((response) => response.json())
  .then((data) => {
    document.querySelector("#source-badge").textContent = `DATA: ${data.dataSource.toUpperCase()}`;
  })
  .catch(() => {
    document.querySelector("#source-badge").textContent = "API 연결 실패";
  });

loadToolDefinitions();
startRecommendation();
