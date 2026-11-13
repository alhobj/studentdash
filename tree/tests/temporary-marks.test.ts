import {test} from 'node:test';
import assert from 'node:assert/strict';
import {Card} from '../src/MapView';
test('normal map marks are independent of selection and assessment',()=>{
 let toggles=0,opens=0;
 const data={official:{code:'S1.1.1'},title:'Example',status:'Not reviewed',group:0,marked:true,toggleMark:()=>toggles++,open:()=>opens++};
 const button=Card({data}).props.children[1];
 assert.ok(button.props.className.includes('marked'));
 button.props.onDoubleClick({stopPropagation(){}});
 button.props.onKeyDown({key:'M',preventDefault(){},stopPropagation(){}});
 assert.equal(toggles,2);assert.equal(opens,0);assert.equal(data.status,'Not reviewed');
 button.props.onClick({stopPropagation(){}});
 assert.equal(opens,1);assert.equal(toggles,2);
});


test('pointer selection preserves focus; keyboard focus and marking remain available',()=>{
 const data={official:{code:'S1.1.1'},title:'Example',status:'Not reviewed',group:0,toggleMark(){},open(){}};
 const button=Card({data}).props.children[1];let prevented=0;
 button.props.onMouseDown({button:0,preventDefault(){prevented++;}});
 assert.equal(prevented,1);
 button.props.onMouseDown({button:1,preventDefault(){prevented++;}});
 assert.equal(prevented,1);
});
test('simple-mode cards retain their title and section while hiding self-assessment',()=>{
 const data={official:{code:'S1.1.1'},title:'Example',status:'Not reviewed',group:0,simple:true,toggleMark(){},open(){}};
 const button=Card({data}).props.children[1];
 assert.ok(button.props.className.includes('simple-card'));
 assert.equal(button.props['aria-label'],'S1.1.1 · Example');
 assert.equal(button.props.children[1].props.children,'Example');
 assert.equal(button.props.children[2],false);
});


test('dragging can start on a node card without a no-pan blocker',()=>{
 const data={official:{code:'S1.1.1'},title:'Example',status:'Not reviewed',group:0,simple:true,toggleMark(){},open(){}};
 const button=Card({data}).props.children[1];
 assert.equal(button.props.className.split(/\s+/).includes('nopan'),false);
 assert.ok(button.props.className.split(/\s+/).includes('nodrag'));
});
