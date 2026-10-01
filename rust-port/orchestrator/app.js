const $ = id => document.getElementById(id);
let selectedAgent = null, loading = false, cachedState = null;
function error(message) { $('error').textContent = message; $('error').hidden = !message; }
async function api(path, body) {
  const response = await fetch(path, body === undefined ? {} : {
    method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}
function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}
function usage(data) {
  if (data.status !== 'available') {
    $('plan').textContent = data.status === 'loading' ? 'Loading…' : 'Unavailable';
    $('weekly-value').textContent = '—'; $('wallet').textContent = '—'; $('weekly-meter').value = 0;
    $('reset').textContent = data.error || 'Reading AdaL account usage';
    return;
  }
  $('plan').textContent = data.plan;
  $('wallet').textContent = typeof data.wallet_balance === 'number' ? `$${data.wallet_balance.toFixed(2)}` : '—';
  const percent = data.weekly?.percentage;
  $('weekly-value').textContent = typeof percent === 'number' ? `${percent.toFixed(2)}%` : 'No weekly limit';
  $('weekly-meter').value = typeof percent === 'number' ? Math.min(100, Math.max(0, percent)) : 0;
  $('reset').textContent = data.weekly?.resets_at ? `Resets ${new Date(data.weekly.resets_at).toLocaleString()}` : 'Reported by AdaL';
  if (data.weekly?.limited) $('reset').textContent = data.weekly.guidance || 'Weekly usage limit reached';
  $('usage-updated').textContent = `Account · updated ${new Date(data.updated_at*1000).toLocaleTimeString()}`;
}
async function details(id) {
  selectedAgent = id;
  $('events').hidden = true; $('details').hidden = false;
  const agent = [...cachedState.workers, ...(cachedState.lead ? [cachedState.lead] : [])].find(a => a.id === id);
  $('detail-title').textContent = agent ? (agent.title || 'Dispatcher') : 'Activity';
  try {
    const log = await api(`/api/log?id=${encodeURIComponent(id)}`);
    $('details').textContent = [agent?.task ? `ASSIGNMENT\n${agent.task}` : '',
      agent?.report ? `REPORT\n${agent.report}` : '',
      agent?.result?.error ? `ERROR\n${agent.result.error}` : '', `LOG\n${log.text || 'Starting…'}`].filter(Boolean).join('\n\n');
  } catch (e) { $('details').textContent = e.message; }
}
function card(agent, lead) {
  const element = node('button', undefined, `agent${selectedAgent === agent.id ? ' selected' : ''}`);
  const top = node('div', undefined, 'agent-top');
  top.append(node('h3', lead ? 'GPT-6 Sol' : 'GLM-5.3 Flash'),
    node('span', agent.integrated ? (agent.verified ? 'verified' : 'integrated') : agent.status, `agent-state ${agent.status}`));
  element.append(top, node('p', lead ? 'Dispatcher · plans & reviews only' : `${agent.task_id} · ${agent.role} · ${agent.title}`, 'kind'));
  const progress = lead ? `Turn ${cachedState.run?.turns || 0} · ${agent.status === 'running' ? 'Dispatching / reviewing' : cachedState.workers.some(w => w.status === 'running') ? 'Waiting for worker result' : 'Turn ended'}` :
    agent.rejected ? 'Rejected · correction will be delegated' : agent.result?.error || agent.allowed_files.length + ' assigned files · docs & worklog required';
  element.append(node('p', progress));
  element.onclick = () => selectedAgent === agent.id ? (selectedAgent = null, refresh()) : details(agent.id);
  return element;
}
async function refresh() {
  if (loading) return;
  loading = true;
  try {
    const state = await api('/api/state'); cachedState = state;
    const run = state.run;
    $('status').textContent = run ? run.status : 'Idle';
    $('status').className = `status ${run?.status || ''}`;
    $('start').disabled = run?.status === 'running' || !!state.active_jobs;
    $('stop').disabled = !run || !['running','paused','blocked'].includes(run.status);
    usage(state.usage || {status:'unavailable'});
    const finished = state.workers.filter(w => w.integrated).length;
    $('run-count').textContent = `${finished} / ${state.workers.length} tasks`;
    $('turns').textContent = run ? `Lead turn ${run.turns} · ${state.workers.filter(w => w.status === 'running').length} workers active` : 'GPT-6 Sol dispatches · GLM works';
    $('inbox').textContent = `${state.inbox.length} waiting`;
    $('run-note').textContent = run?.summary || (run ? `PR #4 · ${run.source_head?.slice(0,10) || ''} · ${run.pending_push ? 'Push pending' : 'Automatic verified publication'}` : 'M0–M4 gates preserved. Two workers maximum. AdaL subscription credits.');
    $('agents').replaceChildren();
    if (state.lead) $('agents').append(card(state.lead,true));
    for (const worker of state.workers) $('agents').append(card(worker,false));
    if (!state.lead && !state.workers.length) $('agents').append(node('p','Ready. Start continues the next eligible task in the port plan.','empty'));
    if (selectedAgent) await details(selectedAgent);
    else {
      $('detail-title').textContent = 'Activity'; $('events').hidden = false; $('details').hidden = true;
      $('events').replaceChildren();
      for (const event of [...state.events].reverse()) {
        const item = node('div',undefined,'event');
        item.append(node('time',new Date(event.time*1000).toLocaleTimeString()),node('p',event.text));
        $('events').append(item);
      }
      if (!state.events.length) $('events').append(node('p','No work started. The lead only dispatches and reviews; workers do all implementation.','empty'));
    }
    $('connection').textContent = 'Connected';
  } catch (e) { $('connection').textContent = 'Disconnected'; error(e.message); }
  finally { loading = false; }
}
async function control(path,body) {
  try { error(''); $('start').disabled = true; await api(path,body); await refresh(); }
  catch (e) { error(e.message); await refresh(); }
}
$('start').onclick = () => control('/api/start',{});
$('stop').onclick = () => control('/api/control',{action:'stop'});
refresh(); setInterval(refresh,2500);
