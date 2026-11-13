import {test} from 'node:test';
import assert from 'node:assert/strict';
import map from '../src/data/map.json';

// These boundaries were separately read from the guide's SL/HL headings.
// Values are [last shared statement number, last statement number].
const ranges:Record<string,[number,number]>={
  'Structure 1.1':[3,3], 'Structure 1.2':[2,3], 'Structure 1.3':[5,7],
  'Structure 1.4':[6,6], 'Structure 1.5':[4,4], 'Structure 2.1':[3,3],
  'Structure 2.2':[10,16], 'Structure 2.3':[2,3], 'Structure 2.4':[5,6],
  'Structure 3.1':[6,10], 'Structure 3.2':[6,12],
  'Reactivity 1.1':[4,4], 'Reactivity 1.2':[2,5], 'Reactivity 1.3':[5,5],
  'Reactivity 1.4':[0,4], 'Reactivity 2.1':[5,5], 'Reactivity 2.2':[5,13],
  'Reactivity 2.3':[4,7], 'Reactivity 3.1':[8,17], 'Reactivity 3.2':[11,16],
  'Reactivity 3.3':[3,3], 'Reactivity 3.4':[5,13],
};
const find=(code:string)=>{
  const node=map.nodes.find(n=>n.official.code===code);
  assert.ok(node,code);
  return node;
};

test('all 165 numbered understandings occur once with the guide’s SL/HL boundaries',()=>{
  assert.equal(map.version,'2.0');
  assert.equal(map.nodes.length,165);
  assert.equal(new Set(map.nodes.map(n=>n.official.code)).size,165);
  assert.equal(map.nodes.filter(n=>n.level==='shared').length,104);
  assert.equal(map.nodes.filter(n=>n.level==='HL').length,61);
  for(const [topic,[shared,last]] of Object.entries(ranges)){
    for(let i=1;i<=last;i++){
      const node=find(`${topic}.${i}`);
      assert.equal(node.level,i<=shared?'shared':'HL',node.official.code);
      assert.equal(node.id,`ib-2025-${topic.toLowerCase().replace(' ','-')}.${i}`);
    }
  }
});

test('every understanding records the supplied edition, source and both page conventions',()=>{
  const source=map.resources.find(r=>r.id==='ib-chemistry-guide-2025')!;
  assert.equal(source.edition,'Published February 2023; first assessment 2025');
  assert.equal(source.sha256,'2f43a8bbedefe7654de4ae23d3e6451d2205f9bac660a26f18c1ca660407eb56');
  for(const node of map.nodes){
    const source=node.official;
    assert.equal(node.objective,source.statement);
    assert.equal(source.sourceId,'ib-chemistry-guide-2025');
    assert.ok(source.pdfPages.every(p=>p>=39&&p<=70));
    assert.deepEqual(source.printedPages,source.pdfPages.map(p=>p-6));
    assert.equal(source.pdfPage,source.pdfPages[0]);
    assert.equal(source.printedPage,source.printedPages[0]);
    assert.ok(source.statementParts.every(p=>['normal','sub','super'].includes(p.script)));
    assert.ok(node.editorial.title.includes('not official'));
  }
  assert.deepEqual(find('Structure 1.1.1').official.pdfPages,[39]);
  assert.deepEqual(find('Reactivity 3.4.13').official.pdfPages,[70]);
});

test('multi-paragraph understandings and cross-page bullets are complete without guidance leakage',()=>{
  assert.equal(find('Structure 1.1.1').official.statement,
    'Elements are the primary constituents of matter, which cannot be chemically broken down into simpler substances. Compounds consist of atoms of different elements chemically bonded together in a fixed ratio. Mixtures contain more than one element or compound in no fixed ratio, which are not chemically bonded and so can be separated by physical methods.');
  assert.equal(find('Structure 2.2.6').official.statement,
    'Molecular polarity depends on both bond polarity and molecular geometry.');
  assert.equal(find('Structure 2.2.9').official.statement,
    'Given comparable molar mass, the relative strengths of intermolecular forces are generally: London (dispersion) forces < dipole–dipole forces < hydrogen bonding.');
  assert.ok(!find('Structure 3.1.4').official.statement.includes('Describe and explain'));
  assert.ok(!find('Structure 3.1.5').official.statement.includes('Deduce equations'));
  assert.ok(find('Reactivity 2.2.10').official.statement.includes('rate-determining step'));
  assert.ok(find('Reactivity 2.3.5').official.statement.includes('non-equilibrium concentrations'));
  const buffer=find('Reactivity 3.1.17').official;
  assert.deepEqual(buffer.pdfPages,[64,65]);
  assert.deepEqual(buffer.printedPages,[58,59]);
  assert.equal(buffer.statementParts.filter(p=>p.script==='sub').map(p=>p.text).join(','),'a,b');
  assert.ok(buffer.statement.endsWith('the ratio of the concentration of acid or base to the concentration of the conjugate base or acid.'));
  assert.equal((buffer.statement.match(/•/g)||[]).length,2);
  assert.equal((find('Reactivity 2.1.2').official.statement.match(/•/g)||[]).length,2);
});

test('chemical scripts and stacked fractions preserve their scientific meaning',()=>{
  assert.ok(find('Structure 1.3.3').official.statement.includes('2n²'));
  assert.ok(find('Structure 1.4.2').official.statement.includes('¹²C'));
  assert.ok(find('Structure 2.2.12').official.statement.includes('C₆H₆'));
  assert.ok(find('Structure 3.2.10').official.statement.includes('¹H NMR'));
  assert.ok(find('Structure 1.5.4').official.statement.includes('(P₁V₁)/T₁ = (P₂V₂)/T₂'));
  assert.ok(find('Reactivity 3.2.12').official.statement.includes('H⁺(aq) + e⁻ ⇌ ½H₂(g)'));
  const pH=find('Reactivity 3.1.4').official.statementParts;
  assert.ok(pH.some(p=>p.script==='sub'&&p.text==='10'));
  assert.ok(pH.some(p=>p.script==='super'&&p.text==='–pH'));
  assert.ok(find('Reactivity 3.2.13').official.statementParts.some(p=>p.script==='sub'&&p.text==='cell'));
});

test('all relationships are explicitly pedagogical and cannot redefine official statements',()=>{
  for(const edge of map.edges){
    assert.ok(edge.provenance.includes('not an official IB relationship'));
  }
  assert.ok(map.nodes.every(n=>!n.id.startsWith('ct-')));
});
