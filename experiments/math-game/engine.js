/* Profile-driven local game state. No access to Studentdash assessment records. */
(function (root) {
  'use strict';
  const copy = value => JSON.parse(JSON.stringify(value));
  const object = value => value && typeof value === 'object' && !Array.isArray(value);
  function createEngine(profile, storage) {
    const quests = profile.quests, quest = id => quests.find(q => q.id === id);
    const ids = quests.map(q => q.id), tools = Object.keys(profile.equipment);
    const fresh = () => ({version:1, profile:profile.id, credits:0, completed:[], independent:[],
      tools:[], placed:[], purchased:[], drafts:{}, notes:{}});
    const list = (value, allowed) => Array.isArray(value) && new Set(value).size === value.length && value.every(v => allowed.includes(v));
    let state = fresh(), storageError = '';
    function missing(id, s = state) { return quest(id).requires.filter(required => !s.completed.includes(required)); }
    function validate(raw) {
      if (!object(raw) || raw.version !== 1 || raw.profile !== profile.id) throw Error('This file is not a compatible Pattern Quest save.');
      if (!Number.isInteger(raw.credits) || raw.credits < 0 || raw.credits > 100000 ||
        !list(raw.completed, ids) || !list(raw.independent, raw.completed) || !list(raw.tools, tools) ||
        !list(raw.placed, raw.tools) || raw.placed.length > 3 || !list(raw.purchased, profile.shop.map(x => x.id)) ||
        raw.purchased.some(id => !raw.tools.includes(id)) || !object(raw.drafts) || !object(raw.notes)) throw Error('Invalid game progress.');
      if (raw.completed.some(id => missing(id, raw).length)) throw Error('Completed quests have missing prerequisites.');
      const earnedTools = quests.filter(q => raw.completed.includes(q.id) && q.reward.tool).map(q => q.reward.tool);
      if (!list(raw.tools, [...earnedTools, ...raw.purchased]) || earnedTools.some(t => !raw.tools.includes(t))) throw Error('Invalid equipment collection.');
      const credits = quests.filter(q => raw.completed.includes(q.id)).reduce((sum, q) => sum + q.reward.credits, 0)
        - profile.shop.filter(item => raw.purchased.includes(item.id)).reduce((sum, item) => sum + item.cost, 0);
      if (credits !== raw.credits) throw Error('Credits do not match completed quests and purchases.');
      for (const [id, draft] of Object.entries(raw.drafts)) {
        const q = quest(id);
        if (!q || !object(draft) || missing(id, raw).length || !Number.isInteger(draft.stage) || draft.stage < 0 || draft.stage >= q.steps.length ||
          typeof draft.assisted !== 'boolean' || typeof draft.passed !== 'boolean' || !Array.isArray(draft.values) ||
          draft.values.length !== q.steps[draft.stage].fields.length || draft.values.some(v => typeof v !== 'string' || v.length > 64)) throw Error('Invalid unfinished investigation.');
        if (draft.passed && !answersCorrect(q.steps[draft.stage], draft.values)) throw Error('Invalid completed step.');
      }
      if (Object.entries(raw.notes).some(([id, note]) => !raw.completed.includes(id) || typeof note !== 'string' || note.length > 2000)) throw Error('Invalid notebook entry.');
      // Explicit projection discards unknown imported fields.
      return copy({version:1, profile:profile.id, credits:raw.credits, completed:raw.completed, independent:raw.independent,
        tools:raw.tools, placed:raw.placed, purchased:raw.purchased, drafts:raw.drafts, notes:raw.notes});
    }
    function answersCorrect(step, values) {
      return values.length === step.fields.length && step.fields.every((f, i) => {
        const text = values[i].trim();
        return text !== '' && Number.isFinite(Number(text)) && Math.abs(Number(text) - f.answer) <= f.tolerance + 1e-10;
      });
    }
    try { const raw = storage.getItem(profile.storageKey); if (raw) state = validate(JSON.parse(raw)); }
    catch { storageError = 'Browser save unavailable or invalid. Your session still works; export before leaving.'; }
    function save() {
      try { storage.setItem(profile.storageKey, JSON.stringify(state)); storageError = ''; }
      catch { storageError = 'Browser storage is unavailable. Export your save before closing this page.'; }
    }
    function start(id) {
      const q = quest(id);
      if (!q || missing(id).length) throw Error('Complete the required investigations first.');
      if (!state.drafts[id]) state.drafts[id] = {stage:0, assisted:false, passed:false, values:q.steps[0].fields.map(() => '')};
      save(); return copy(state.drafts[id]);
    }
    function record(id, values) {
      const d = state.drafts[id];
      if (!d || !Array.isArray(values) || values.length !== quest(id).steps[d.stage].fields.length || values.some(v => typeof v !== 'string' || v.length > 64)) throw Error('Invalid controls.');
      d.values = [...values]; d.passed = false; save();
    }
    function check(id) {
      const d = state.drafts[id];
      if (!d) throw Error('Start an investigation first.');
      d.passed = answersCorrect(quest(id).steps[d.stage], d.values);
      if (!d.passed) d.assisted = true;
      save(); return d.passed;
    }
    function hint(id) { if (!state.drafts[id]) throw Error('Start an investigation first.'); state.drafts[id].assisted = true; save(); }
    function advance(id) {
      const d = state.drafts[id], q = quest(id);
      if (!d || !d.passed) throw Error('Check a correct answer before continuing.');
      if (d.stage + 1 < q.steps.length) {
        d.stage++; d.values = q.steps[d.stage].fields.map(() => ''); d.passed = false; save(); return false;
      }
      if (!state.completed.includes(id)) {
        state.completed.push(id); state.credits += q.reward.credits;
        if (q.reward.tool && !state.tools.includes(q.reward.tool)) state.tools.push(q.reward.tool);
      }
      if (!d.assisted && !state.independent.includes(id)) state.independent.push(id);
      delete state.drafts[id]; save(); return true;
    }
    function buy(id) {
      const item = profile.shop.find(item => item.id === id);
      if (!item || state.tools.includes(id)) throw Error('This item is unavailable or already owned.');
      if (state.credits < item.cost) throw Error('Not enough credits yet. All investigations and hints remain free.');
      state.credits -= item.cost; state.tools.push(id); state.purchased.push(id); save();
    }
    function place(id) {
      if (!state.tools.includes(id)) throw Error('Collect this item first.');
      if (state.placed.includes(id)) state.placed = state.placed.filter(tool => tool !== id);
      else { if (state.placed.length >= 3) throw Error('Remove an item to free one of your three studio slots.'); state.placed.push(id); }
      save();
    }
    function note(id, text) {
      if (!state.completed.includes(id) || typeof text !== 'string' || text.length > 2000) throw Error('Notes belong to completed investigations and can contain up to 2,000 characters.');
      state.notes[id] = text; save();
    }
    function importSave(text) {
      if (typeof text !== 'string' || text.length > 500000) throw Error('Save file is too large.');
      const incoming = validate(JSON.parse(text)); state = incoming; save();
    }
    return {read:() => copy(state), error:() => storageError, missing, start, record, check, hint, advance, buy, place, note,
      validate, importSave, exportSave:() => JSON.stringify(state, null, 2), reset:() => {state = fresh(); save();}};
  }
  root.createQuestEngine = createEngine;
})(typeof window !== 'undefined' ? window : globalThis);
