"use strict";
const content = document.querySelector("#content");
const connection = document.querySelector("#connection");
const labels = {interview:"Interview", exploration:"Exploration", requirements:"Requirements", verification:"Verification design", plan:"Plan", approval:"Awaiting approval", authorization:"Ready for authorization", implementer:"Implementation", candidate:"Capture candidate", verifier:"Independent verification", human_review:"Ready for your review", delivery:"Awaiting merge", complete:"Delivered", paused:"Paused", blocked:"Blocked", recovery:"Needs reconciliation", limit:"Execution limit", record_error:"Record needs attention"};
const stages = ["interview", "exploration", "requirements", "verification", "plan"];
const sections = ["overview", "requirements", "verification", "plan", "candidates", "history"];
let currentTask, lastSignature = "", selectedRevision = {}, lastRefresh, searchValue = "", filterValue = "active";

function el(tag, attrs = {}, ...children) {
  const element = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key.startsWith("on")) element.addEventListener(key.slice(2), value);
    else if (key === "class") element.className = value;
    else element.setAttribute(key, value);
  }
  children.flat(Infinity).filter(x => x !== null && x !== undefined).forEach(child => element.append(child instanceof Node ? child : document.createTextNode(String(child))));
  return element;
}
const titleCase = value => value.charAt(0).toUpperCase() + value.slice(1).replaceAll("_", " ");
const date = value => new Date(value).toLocaleString(undefined, {month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"});
const route = (id, section = "overview") => `#task=${encodeURIComponent(id)}&view=${section}`;
function candidateCurrent(task, candidate) {
  return candidate && task.state.authorization && !task.state.authorization.needs_implementation && stages.every(stage=>candidate.revisions[stage]===task.state.approved[stage]?.sha256);
}
function artifactStatus(state, artifact) {
  if(state.approved[artifact.stage]?.sha256===artifact.sha256)return state.approved[artifact.stage].decision;
  const parents=Object.fromEntries(stages.slice(0,stages.indexOf(artifact.stage)).filter(s=>state.approved[s]).map(s=>[s,state.approved[s].sha256]));
  if(artifact.decision==="approved" || artifact.decision==="skipped" || JSON.stringify(parents)!==JSON.stringify(artifact.parents))return "superseded";
  return artifact.decision;
}
function badge(value) {
  const good = ["approved", "pass", "complete", "resolved", "accepted"].includes(value);
  const bad = ["rejected", "fail", "blocked", "recovery", "unverified", "record_error"].includes(value);
  return el("span", {class:`badge ${good ? "good" : bad ? "bad" : "wait"}`}, labels[value] || titleCase(value));
}
async function api(path) {
  const response = await fetch(path, {cache:"no-store"});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Unable to read task records");
  return data;
}

// A deliberately small Markdown renderer. All source text becomes text nodes;
// links are limited to HTTP(S) and never open local or executable URLs.
function inline(text) {
  const fragment = document.createDocumentFragment();
  const pattern = /(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/g;
  let offset = 0;
  for (const match of text.matchAll(pattern)) {
    fragment.append(document.createTextNode(text.slice(offset, match.index)));
    const token = match[0];
    if (token.startsWith("`")) fragment.append(el("code", {}, token.slice(1, -1)));
    else if (token.startsWith("**")) fragment.append(el("strong", {}, token.slice(2, -2)));
    else {
      const parts = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      if (/^https?:\/\//i.test(parts[2])) fragment.append(el("a", {href:parts[2],target:"_blank",rel:"noopener noreferrer"}, parts[1]));
      else fragment.append(document.createTextNode(token));
    }
    offset = match.index + token.length;
  }
  fragment.append(document.createTextNode(text.slice(offset)));
  return fragment;
}
function markdown(text) {
  const article = el("article", {class:"document"});
  const lines = text.split("\n");
  let paragraph = [], list = null, code = null;
  const flush = () => { if (paragraph.length) article.append(el("p", {}, inline(paragraph.join(" ")))); paragraph = []; list = null; };
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.startsWith("```")) { flush(); if (code !== null) { article.append(el("pre", {}, code.join("\n"))); code = null; } else code = []; continue; }
    if (code !== null) { code.push(line); continue; }
    if (/^\s*\|.*\|\s*$/.test(line) && i + 1 < lines.length && /^\s*\|?[\s:|-]+\|/.test(lines[i+1])) {
      flush(); const cells = row => row.trim().replace(/^\||\|$/g, "").split("|").map(x=>x.trim());
      const table = el("table", {}, el("thead", {}, el("tr", {}, cells(line).map(c=>el("th", {}, inline(c))))));
      const body = el("tbody"); i += 2;
      while (i < lines.length && /^\s*\|/.test(lines[i])) { body.append(el("tr", {}, cells(lines[i]).map(c=>el("td", {}, inline(c))))); i++; }
      i--; table.append(body); article.append(el("div", {class:"table-wrap"}, table)); continue;
    }
    const heading = line.match(/^(#{1,6})\s+(.+)/);
    if (heading) { flush(); article.append(el("h" + heading[1].length, {}, inline(heading[2]))); continue; }
    const item = line.match(/^\s*(?:[-*]|\d+\.)\s+(.+)/);
    if (item) { if (paragraph.length) flush(); if (!list) { list = el(/^\s*\d/.test(line)?"ol":"ul"); article.append(list); } list.append(el("li", {}, inline(item[1]))); continue; }
    if (line.startsWith("> ")) { flush(); article.append(el("blockquote", {}, inline(line.slice(2)))); continue; }
    if (!line.trim()) flush(); else { list = null; paragraph.push(line); }
  }
  flush(); if (code !== null) article.append(el("pre", {}, code.join("\n")));
  return article;
}
function empty(title, body) { return el("div", {class:"empty"}, el("h2", {}, title), el("p", {}, body)); }
function pageHeading(eyebrow, title, intro) { return [el("div", {class:"eyebrow"}, eyebrow), el("h1", {}, title), intro ? el("p", {class:"intro"}, intro) : null]; }

function renderIndex(tasks) {
  document.querySelector("#navigation").replaceChildren();
  document.querySelector("#breadcrumb").textContent = "Your workspace";
  document.title = "Tasks · Method";
  const list = el("div", {class:"task-list"});
  const search = el("input", {type:"search",placeholder:"Find a task or repository…", "aria-label":"Find a task", value:searchValue});
  const filter = el("select", {"aria-label":"Filter tasks"}, ["active", "all", "attention", "complete"].map(v=>el("option", {value:v}, {active:"Active tasks",all:"All tasks",attention:"Needs attention",complete:"Delivered"}[v])));
  filter.value = filterValue;
  function rows() {
    const visible = tasks.filter(t => {
      const match = `${t.task?.title || t.id} ${t.task?.repository.name || ""}`.toLowerCase().includes(search.value.toLowerCase());
      return match && (filter.value === "all" || (filter.value === "active" && t.status !== "complete") || (filter.value === "complete" && t.status === "complete") || (filter.value === "attention" && ["approval", "authorization", "human_review", "blocked", "recovery", "limit", "delivery", "record_error"].includes(t.status)));
    }).sort((a,b)=>(b.updated||"").localeCompare(a.updated||""));
    list.replaceChildren(...visible.map(t => el("a", {class:"task-row",href:route(t.id)}, el("div", {}, el("div", {class:"task-title"}, t.task?.title || t.id), el("div", {class:"task-meta"}, `${t.task?.repository.name || "Record error"}  /  ${t.next_action || t.error}`)), badge(t.status), el("time", {}, t.updated ? date(t.updated) : ""))));
    if (!visible.length) list.append(empty(tasks.length ? "Nothing here just yet." : "Good work starts with a clear idea.", tasks.length ? "Try another filter or search." : "Invoke $method in Codex or /method in Claude Code, from a clean checkout. Your tasks and their history will appear here."));
  }
  search.addEventListener("input", ()=>{searchValue=search.value;rows();});
  filter.addEventListener("change", ()=>{filterValue=filter.value;rows();});
  content.replaceChildren(...pageHeading("A PLACE FOR THE WORK", "One considered step at a time.", "Your tasks, decisions, and evidence. Everything you need to pick up where you left off."), el("div", {class:"filters"}, search, filter), list);
  rows();
}

function progression(task) {
  const state = task.state;
  return el("ol", {class:"stages", "aria-label":"Task progress"}, [...stages, "implementer", "verifier", "human_review", "delivery"].map(stage=>{
    const approved = state.approved[stage];
    const candidate=state.candidates.at(-1);
    const done = approved || (stage==="implementer" && candidateCurrent(task,candidate)) || (stage==="verifier" && candidateCurrent(task,candidate) && candidate.verification?.ready) || (stage==="human_review" && state.accepted) || (stage==="delivery" && state.delivery);
    const waitingArtifact = state.artifacts.filter(a=>!state.approved[a.stage] && a.decision==="pending").at(-1);
    const active = task.status===stage || (task.status==="approval" && waitingArtifact?.stage===stage);
    return el("li", {class:done?"done":active?"current":""}, {verification:"Verify design",implementer:"Implement",verifier:"Verify",human_review:"Review",delivery:"Merge"}[stage] || labels[stage], el("span", {class:"stage-status"}, approved?.decision==="skipped"?"Waived":done?"Done":active?"Current":""));
  }));
}
function overview(task) {
  const state=task.state;
  const documents = el("section", {}, el("h2", {}, "The working record"));
  for (const stage of stages) {
    const artifact = state.artifacts.filter(a=>a.stage===stage).at(-1);
    documents.append(el("a", {class:"artifact-link",href:route(task.id,stage)}, labels[stage], el("span", {}, artifact?`Revision ${artifact.revision} · ${artifactStatus(state,artifact)}`:"Not started")));
  }
  const candidate=state.candidates.at(-1);
  const facts=el("dl", {class:"facts"}, [["Repository",state.task.repository.name],["Target branch",state.task.target],["Baseline",state.task.baseline.slice(0,12)],["Current candidate",candidate?.commit.slice(0,12)||"Not captured"],["Workspace",state.task.workspace]].map(([key,value])=>el("div", {}, el("dt", {}, key),el("dd", {}, value))));
  const auth=state.authorization;
  if(auth) facts.append(el("div", {},el("dt", {},"Execution budget"),el("dd", {},`${auth.rounds_used} / ${auth.rounds} verification rounds · ${Math.round(auth.used_seconds/60)} / ${auth.minutes} recorded minutes`)));
  content.append(progression(task),el("div", {class:"overview-grid"},documents,el("section", {},el("h2", {},"At a glance"),facts)));
  if(state.delivery) content.append(el("div", {class:"attention"},el("div", {class:"eyebrow"},"DELIVERY PROVENANCE"),el("p", {},state.delivery.mode==="observed"?"Target-branch ancestry observed":"Merge confirmed by you"),el("small", {},state.delivery.evidence)));
}

async function artifactView(task, section) {
  const artifacts=task.state.artifacts.filter(a=>a.stage===section);
  if(!artifacts.length){content.append(empty("This part is still ahead.",`The ${labels[section].toLowerCase()} artifact will appear here when it is submitted.`));return;}
  const key=`${task.id}/${section}`;
  const selected=artifacts.find(a=>a.revision===selectedRevision[key]) || artifacts.at(-1);
  const approved=task.state.approved[section];
  const isApproved=approved?.sha256===selected.sha256;
  const latest=selected===artifacts.at(-1);
  const chooser=el("select", {"aria-label":"Artifact revision",onchange:e=>{selectedRevision[key]=Number(e.target.value);lastSignature="";refresh();}}, artifacts.map(a=>el("option", {value:a.revision},`Revision ${a.revision}${a===artifacts.at(-1)?" · latest":""}`)));
  chooser.value=String(selected.revision);
  content.append(el("div", {class:"doc-toolbar"},badge(latest?artifactStatus(task.state,selected):"historical"),el("span", {},date(selected.at)),el("code", {},selected.sha256.slice(0,12)),chooser));
  if(!latest || !isApproved && selected.decision==="approved") content.append(el("div", {class:"historical"},"Historical or superseded revision. Its approval does not authorize the current work."));
  if(selected.human) content.append(el("details", {},el("summary", {},"Decision and provenance"),el("p", {},selected.human.instruction),el("small", {},selected.human.source||"Recorded from the task conversation")));
  const response=await api(`/api/tasks/${task.id}/artifacts/${selected.path.split("/").at(-1)}`);
  content.append(markdown(response.text));
  if(section==="requirements" || section==="verification") {
    const candidate=task.state.candidates.at(-1);
    const current=candidateCurrent(task,candidate);
    const report=current && latest && isApproved?candidate.verification:null;
    content.append(el("div", {class:"section-top"},el("h2", {},"Evidence coverage"),el("small", {},report?`Candidate ${candidate.commit.slice(0,12)}`:"No current verification")));
    const verification=task.state.artifacts.filter(a=>a.stage==="verification").at(-1);
    for(const criterion of selected.criteria) {
      const scenarios=section==="verification"?[criterion]:verification?.criteria.filter(s=>s.requirements.includes(criterion.id))||[];
      const block=el("section", {class:"criterion"},el("div", {class:"criterion-head"},el("code", {},criterion.id),el("strong", {},criterion.text)));
      for(const scenario of scenarios) {
        const result=report?.results.find(r=>r.id===scenario.id);
        block.append(el("p", {},el("code", {},scenario.id)," ",badge(result?.outcome||"unverified")," ",result?.observed||scenario.text));
        for(const id of result?.evidence||[]) block.append(el("button", {class:"evidence-link",onclick:()=>showEvidence(task.id,id)},"View evidence "+id.slice(0,6)));
      }
      if(!scenarios.length) block.append(el("small", {},"Verification scenarios not yet submitted."));
      content.append(block);
    }
  }
}

async function showEvidence(taskId,id,kind="evidence") {
  const previous=document.activeElement;
  const panel=el("div", {class:"modal",role:"dialog","aria-modal":"true","aria-label":kind==="diffs"?"Candidate diff":"Run evidence"});
  const backdrop=el("div", {class:"modal-backdrop"},panel);
  const close=()=>{backdrop.remove();previous?.focus();};
  const button=el("button", {onclick:close},"Close");
  panel.append(button,el("h2", {},kind==="diffs"?"Candidate diff":"Recorded evidence"),el("p", {},"Loading…"));
  document.body.append(backdrop); button.focus();
  backdrop.addEventListener("keydown",e=>{if(e.key==="Escape")close();if(e.key==="Tab"){e.preventDefault();button.focus();}});
  backdrop.addEventListener("click",e=>{if(e.target===backdrop)close();});
  try{const data=await api(`/api/tasks/${taskId}/${kind}/${id}`);panel.lastChild.replaceWith(el("pre", {},data.text));}catch(error){panel.lastChild.textContent=error.message;}
}
function candidatesView(task) {
  if(!task.state.candidates.length){content.append(empty("An exact version, when it’s ready.","Candidates appear after an authorized implementation run has finished and Method captures a checkpoint commit."));return;}
  for(const [index,candidate] of [...task.state.candidates].reverse().entries()) {
    const report=candidate.verification;
    const historical=index>0 || !candidateCurrent(task,candidate);
    const block=el("section", {class:"candidate"},el("div", {class:"candidate-label"},el("h2", {},index===0?"Latest candidate":"Earlier candidate"),badge(historical?"historical":task.state.accepted?.commit===candidate.commit?"accepted":report?.ready?"human_review":report?"fail":"unverified")),el("div", {class:"candidate-meta"},el("code", {},candidate.commit)," · ",date(candidate.at)),el("button", {class:"evidence-link",onclick:()=>showEvidence(task.id,candidate.id,"diffs")},"Inspect baseline-to-candidate diff"));
    if(historical)block.append(el("div", {class:"historical"},"Historical evidence for this exact candidate and its preparation revisions. It does not verify the current work."));
    if(report){block.append(el("div", {class:"section-top"},el("h3", {},"Review")),el("p", {},report.review),el("h3", {},"Implementation & tradeoffs"),el("p", {},report.tradeoffs),el("h3", {},"Try this candidate"),el("pre", {},report.launch));if(report.limitations)block.append(el("p", {},"Remaining uncertainty: "+report.limitations));
      for(const result of report.results)block.append(el("div", {class:"criterion"},el("div", {class:"criterion-head"},el("code", {},result.id),badge(result.outcome)),el("p", {},result.observed),(result.evidence||[]).map(id=>el("button", {class:"evidence-link",onclick:()=>showEvidence(task.id,id)},"View evidence "+id.slice(0,6)))));
      for(const finding of report.findings)block.append(el("details", {},el("summary", {},`${finding.id} · ${finding.severity} · ${finding.status}`),el("p", {},finding.description),finding.resolution?el("p", {},finding.resolution):null));
    }
    content.append(block);
  }
}
function historyView(task) {
  content.append(el("p", {class:"intro"},"The original decisions and observations stay here, including rejected revisions and unsuccessful attempts."));
  content.append(el("ol", {class:"timeline"},[...task.events].reverse().map(event=>el("li", {},el("time", {},date(event.at)),el("div", {},el("strong", {},titleCase(event.kind.replaceAll("-"," "))),event.data.instruction?el("p", {},event.data.instruction):null,event.data.reason?el("p", {},event.data.reason):null,el("details", {},el("summary", {},"Inspect recorded event"),el("pre", {},JSON.stringify(event,null,2))))))));
}
async function renderTask(task, section) {
  document.querySelector("#breadcrumb").replaceChildren(el("a", {href:"#"},"Tasks")," / ",task.task.repository.name);
  document.title=`${task.task.title} · Method`;
  document.querySelector("#navigation").replaceChildren(...sections.map(s=>el("a", {href:route(task.id,s),class:s===section?"active":"",...(s===section?{"aria-current":"page"}:{})},titleCase(s))));
  content.replaceChildren(el("div", {class:"eyebrow"},`${task.task.repository.name} / ${task.id.slice(0,8)}`),el("div", {class:"heading"},el("h1", {},task.task.title),badge(task.status)));
  if(section==="overview") content.append(el("p", {class:"intro"},task.task.goal));
  content.append(el("section", {class:"attention"},el("div", {class:"eyebrow"},"THE NEXT STEP"),el("p", {},task.next_action),el("small", {},"Inspect here. Give instructions and decisions in your Method conversation.")));
  if(section==="overview")overview(task);
  else if([...stages].includes(section))await artifactView(task,section);
  else if(section==="candidates")candidatesView(task);
  else historyView(task);
}
let refreshing=false;
async function refresh() {
  if(refreshing)return;
  refreshing=true;
  const hash=location.hash;
  try {
    const params=new URLSearchParams(hash.slice(1));
    const id=params.get("task"),section=params.get("view")||"overview";
    const tasks=await api("/api/tasks");
    document.querySelector("#task-count").textContent=tasks.filter(t=>t.status!=="complete").length;
    const task=id?await api(`/api/tasks/${encodeURIComponent(id)}`):null;
    if(location.hash!==hash)return;
    const signature=JSON.stringify([hash,task||tasks,selectedRevision]);
    if(signature!==lastSignature){const scroll=window.scrollY;currentTask=task;if(task)await renderTask(task,sections.includes(section)||stages.includes(section)?section:"overview");else renderIndex(tasks);lastSignature=signature;window.scrollTo(0,scroll);}
    lastRefresh=new Date();connection.textContent=`Updated ${lastRefresh.toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})}`;connection.className="";
  } catch(error) {
    connection.textContent=`Connection unavailable${lastRefresh?" · last update "+lastRefresh.toLocaleTimeString():""}`;connection.className="offline";
    if(!lastSignature)content.replaceChildren(empty("The record is unavailable.",error.message+". Check that the local Method server is running."));
  } finally {refreshing=false;if(location.hash!==hash)refresh();}
}
window.addEventListener("hashchange",()=>{lastSignature="";window.scrollTo(0,0);refresh();});
document.addEventListener("visibilitychange",()=>{if(!document.hidden)refresh();});
setInterval(()=>{if(!document.hidden)refresh();},4000);
refresh();
