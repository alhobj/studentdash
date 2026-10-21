/* Bounded, portable learner-owned planning and investigation records. */
(()=>{'use strict';
const prefix='studentdash.learning.v1:',key=s=>typeof s==='string'&&s.length>0&&s.length<=220&&!/[\u0000-\u001f]/.test(s)&&!['__proto__','constructor','prototype'].includes(s);
const string=(v,max=4000)=>{if(typeof v!=='string'||v.length>max)throw Error('Invalid saved learning text.');return v;};
function validate(raw){
 if(!raw||raw.schema!==1)throw Error('Unsupported learning record.');
 for(const value of [raw.plans,raw.notebooks])if(value!==undefined&&(!value||typeof value!=='object'||Array.isArray(value)))throw Error('Invalid learning record collections.');
 const plans={},notebooks={};
 for(const [id,p]of Object.entries(raw.plans||{})){if(!key(id)||!p||!Array.isArray(p.nodes)||p.nodes.length>1000||p.nodes.some(n=>!key(n))||!Number.isInteger(p.minutes)||p.minutes<5||p.minutes>90||!/^\d{4}-\d{2}-\d{2}$/.test(p.date)||!Number.isFinite(Date.parse(p.date)))throw Error('Invalid revision plan.');const done={};for(const [k,v]of Object.entries(p.done||{})){if(!key(k)||typeof v!=='boolean')throw Error('Invalid revision checklist.');done[k]=v;}plans[id]={title:string(p.title,160),date:p.date,minutes:p.minutes,nodes:p.nodes,done};}
 for(const [id,n]of Object.entries(raw.notebooks||{})){if(!key(id)||!Array.isArray(n.rows)||n.rows.length>60)throw Error('Invalid investigation readings.');notebooks[id]={prediction:string(n.prediction||''),conclusion:string(n.conclusion||''),rows:n.rows.map(row=>{if(!Number.isFinite(row.x)||!Number.isFinite(row.y))throw Error('Invalid measurement.');const params={};for(const[k,v]of Object.entries(row.params||{})){if(!key(k)||!Number.isFinite(v))throw Error('Invalid measurement setting.');params[k]=v;}if(Object.keys(params).length>20)throw Error('Too many settings.');return {x:row.x,y:row.y,params};}),check:string(n.check||'',100),checked:n.checked===true};}
 if(Object.keys(plans).length>30||Object.keys(notebooks).length>100)throw Error('Too many saved learning records.');
 let practice=null;if(raw.practice){if(!window.StudentPractice)throw Error('Open a subject learning page to import practice evidence.');practice=StudentPractice.validate(raw.practice);}
 return {schema:1,plans,notebooks,practice};
}
function read(scope){if(!key(scope))throw Error('Invalid learning record key.');const raw=localStorage.getItem(prefix+scope);return raw?validate(JSON.parse(raw)):{schema:1,plans:{},notebooks:{},practice:null};}
function save(scope,record){if(!key(scope))throw Error('Invalid learning record key.');localStorage.setItem(prefix+scope,JSON.stringify(validate(record)));}
window.StudentLearningState={prefix,key,validate,read,save};
})();
