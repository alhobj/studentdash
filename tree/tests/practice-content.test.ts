import {test} from 'node:test';
import assert from 'node:assert/strict';
import map from '../src/data/map.json';
import practice from '../src/data/practice.json';

const exercise = (suffix: string) => {
  const item = practice.find(item => item.nodeId === `ib-2025-structure-${suffix}`);
  assert.ok(item, `Missing guided exercise for Structure ${suffix}`);
  return item;
};
const solution = (suffix: string) => exercise(suffix).workedExplanation.join(' ');

test('the sixteen editorial exercises refer to distinct shared curriculum statements', () => {
  assert.equal(practice.length, 16);
  assert.equal(new Set(practice.map(item => item.id)).size, 16);
  assert.equal(new Set(practice.map(item => item.nodeId)).size, 16);
  const expected = ['1.1.1', '1.2.1', '1.2.2', '1.4.1', '1.4.2', '1.4.3', '1.4.4', '2.1.1', '2.1.2', '2.1.3', '2.2.1', '2.2.4', '2.2.5', '2.2.6', '2.2.8', '2.2.9'];
  assert.deepEqual(practice.map(item => item.nodeId).sort(), expected.map(id => `ib-2025-structure-${id}`).sort());
  for (const item of practice) {
    const node = map.nodes.find(node => node.id === item.nodeId);
    assert.ok(node, item.nodeId);
    assert.equal(node.level, 'shared');
    assert.deepEqual(Object.keys(item).sort(), ['id', 'nodeId', 'title', 'question', 'hints', 'workedExplanation', 'selfCheck', 'transferQuestion', 'transferExplanation'].sort());
    assert.equal(item.hints.length, 2);
    for (const text of [item.title, item.question, item.transferQuestion, ...item.hints, ...item.workedExplanation, ...item.selfCheck, ...item.transferExplanation]) {
      assert.ok(text.trim().length > 0);
      assert.ok(!/<\/?[a-z]/i.test(text), 'Practice is plain text, not embedded HTML');
    }
    assert.ok(item.workedExplanation.length >= 2);
    assert.ok(item.selfCheck.length >= 2);
    assert.ok(item.transferExplanation.length >= 1);
  }
});

test('nuclear and ion exercises conserve proton identity while changing the appropriate particles', () => {
  const aluminium = solution('1.2.1');
  assert.ok(aluminium.includes(`27 − 13 = ${27 - 13} neutrons`));
  assert.ok(aluminium.includes(`13 − 3 = ${13 - 3} electrons`));
  const isotopes = solution('1.2.2');
  assert.ok(isotopes.includes(`35 − 17 = ${35 - 17} neutrons`));
  assert.ok(isotopes.includes(`37 − 17 = ${37 - 17} neutrons`));
  assert.match(exercise('1.2.2').transferExplanation.join(' '), /18 electrons.*17 protons and 20 neutrons/);
  const ions = solution('2.1.1');
  assert.match(ions, /Mg²⁺, a cation/);
  assert.match(ions, /O²⁻, an anion/);
  assert.ok(ions.includes(`12 − 2 = ${12 - 2} electrons`));
  assert.ok(ions.includes(`8 + 2 = ${8 + 2} electrons`));
  assert.match(ions, /Neither nucleus changes/);
});

test('relative and molar mass examples have correct arithmetic and distinct units', () => {
  const relative = solution('1.4.2');
  const relativeMass = 40.1 + 2 * (16.0 + 1.0);
  assert.ok(relative.includes(`= ${relativeMass.toFixed(1)}`));
  assert.match(relative, /Mᵣ = 74\.1, with no unit/);
  assert.match(exercise('1.4.2').transferExplanation.join(' '), /18\.0.*no unit/);
  const molar = solution('1.4.3');
  const molarMass = 12.0 + 2 * 16.0;
  assert.ok(molar.includes(`${molarMass.toFixed(1)} g mol⁻¹`));
  assert.ok(molar.includes(`= ${(0.250 * molarMass).toFixed(1)} g`));
  assert.ok(exercise('1.4.3').transferExplanation.join(' ').includes(`= ${(22.0 / molarMass).toFixed(3)} mol`));
});

test('classification, covalent attraction and dipole explanations retain their key conditions', () => {
  assert.match(solution('1.1.1'), /O₂.*same element/);
  assert.match(solution('1.1.1'), /fixed ratio 1:2/);
  assert.match(solution('1.1.1'), /relative amounts can vary/);
  const covalent = solution('2.2.1');
  assert.match(covalent, /shared electron pair is attracted to both positively charged hydrogen nuclei/);
  assert.match(covalent, /electrons repel each other/);
  assert.match(covalent, /two electrons, not an octet/);
  const polarity = solution('2.2.6');
  assert.match(exercise('2.2.6').question, /linear.*180°.*bent.*104\.5°/);
  assert.match(polarity, /vector sum is zero/);
  assert.match(polarity, /dipoles do not cancel.*water is polar/);
  assert.match(exercise('2.2.6').transferExplanation.join(' '), /cancel by symmetry.*non-polar despite having polar bonds/);
});

test('mole counting distinguishes molecules, atoms and ionic formula units', () => {
  const avogadro = 6.02e23;
  const carbonDioxideAmount = 0.500;
  const molecules = carbonDioxideAmount * avogadro;
  const oxygenAtoms = 2 * molecules;
  assert.match(exercise('1.4.1').question, /0\.500 mol of CO₂.*6\.02 × 10²³ mol⁻¹.*rounded/);
  const counting = solution('1.4.1');
  assert.ok(counting.includes(`= ${(molecules / 1e23).toFixed(2)} × 10²³ CO₂ molecules`));
  assert.ok(counting.includes(`= ${(oxygenAtoms / 1e23).toFixed(2)} × 10²³ oxygen atoms`));
  assert.match(counting, /amount of substance, not mass/);
  assert.match(counting, /0\.500 mol of CO₂ molecules but 1\.00 mol of oxygen atoms/);
  const transfer = exercise('1.4.1').transferExplanation.join(' ');
  assert.ok(transfer.includes(`= ${(0.100 * avogadro / 1e22).toFixed(2)} × 10²² NaCl formula units`));
  assert.match(transfer, /extended ionic lattice, not.*discrete NaCl molecules/);
});

test('empirical and molecular formulas follow atom amounts and a whole-number mass multiplier', () => {
  assert.match(exercise('1.4.4').question, /4\.80 g of carbon and 0\.800 g of hydrogen.*molar mass is 56\.0 g mol⁻¹.*Aᵣ\(C\) = 12\.0 and Aᵣ\(H\) = 1\.00/);
  const carbonAmount = 4.80 / 12.0;
  const hydrogenAmount = 0.800 / 1.00;
  const rawCarbonRatio = carbonAmount / Math.min(carbonAmount, hydrogenAmount);
  const rawHydrogenRatio = hydrogenAmount / Math.min(carbonAmount, hydrogenAmount);
  assert.ok(Math.abs(rawCarbonRatio - 1) < 1e-12);
  assert.ok(Math.abs(rawHydrogenRatio - 2) < 1e-12);
  const carbonRatio = Math.round(rawCarbonRatio);
  const hydrogenRatio = Math.round(rawHydrogenRatio);
  const empiricalUnitMass = carbonRatio * 12.0 + hydrogenRatio * 1.00;
  assert.deepEqual([carbonRatio, hydrogenRatio], [1, 2]);
  const molecularMultiplier = 56.0 / empiricalUnitMass;
  assert.equal(molecularMultiplier, 4);
  assert.deepEqual([carbonRatio * molecularMultiplier, hydrogenRatio * molecularMultiplier], [4, 8]);
  const formula = solution('1.4.4');
  assert.ok(formula.includes(`= ${carbonAmount.toFixed(3)} mol`));
  assert.ok(formula.includes(`= ${hydrogenAmount.toFixed(3)} mol`));
  assert.match(formula, /C:H = 1:2.*CH₂, the empirical formula/);
  assert.ok(formula.includes(`56.0 ÷ ${empiricalUnitMass.toFixed(1)} = ${molecularMultiplier}`));
  assert.match(formula, /C₄H₈.*four carbon atoms and eight hydrogen atoms per molecule/);
  assert.match(formula, /mass ratio alone does not give their number ratio/);
  const transfer = exercise('1.4.4').transferExplanation.join(' ');
  assert.ok(transfer.includes(`42.0 ÷ ${empiricalUnitMass.toFixed(1)} = ${42.0 / empiricalUnitMass}`));
  assert.match(transfer, /C₃H₆.*both subscripts multiplied by three/);
});

test('ionic examples distinguish attraction, repulsion and the simplest neutral lattice ratio', () => {
  // The signs, rather than an electron's previous owner, determine attraction or repulsion.
  assert.ok(+1 * -1 < 0);
  assert.ok(+1 * +1 > 0);
  const bonding = solution('2.1.2');
  assert.match(bonding, /positive Na⁺ ions attract negative Cl⁻ ions/);
  assert.match(bonding, /transfer event itself is not the bond/);
  assert.match(bonding, /surrounding Cl⁻ ions in different directions/);
  assert.match(bonding, /Two Na⁺ ions repel because they have like charges/);
  assert.match(exercise('2.1.2').transferExplanation.join(' '), /Mg²⁺ and O²⁻ attract.*two Mg²⁺ ions repel/);

  // Search charge neutrality independently; the first positive solution is the simplest ratio.
  const simplestNeutralRatio = (cationCharge: number, anionCharge: number) => {
    for (let cations = 1; cations <= Math.abs(anionCharge); cations++) {
      for (let anions = 1; anions <= cationCharge; anions++) {
        if (cations * cationCharge + anions * anionCharge === 0) return [cations, anions];
      }
    }
    throw new Error('No neutral ratio');
  };
  assert.deepEqual(simplestNeutralRatio(+2, -1), [1, 2]);
  assert.deepEqual(simplestNeutralRatio(+3, -2), [2, 3]);
  const lattice = solution('2.1.3');
  assert.match(lattice, /\+2 \+ 2 × \(−1\) = 0.*ratio is 1:2/);
  assert.match(lattice, /empirical formula is MgCl₂/);
  assert.match(lattice, /three-dimensional lattice.*not isolated MgCl₂ molecules/);
  assert.match(exercise('2.1.3').transferExplanation.join(' '), /two Al³⁺ contribute \+6 and three O²⁻ contribute −6.*ratio is 2:3.*Al₂O₃/);
});

test('VSEPR examples count lone pairs as domains but name shape from atom positions', () => {
  // Each single bond uses one pair; the remaining valence pairs are lone pairs on the central atom.
  const methanePairs = (4 + 4 * 1) / 2;
  const ammoniaPairs = (5 + 3 * 1) / 2;
  const waterPairs = (6 + 2 * 1) / 2;
  assert.equal(methanePairs, 4);
  assert.equal(ammoniaPairs - 3, 1);
  assert.equal(waterPairs - 2, 2);
  assert.match(exercise('2.2.4').question, /CH₄.*four bonding pairs and no lone pairs.*NH₃.*three bonding pairs and one lone pair/);
  assert.match(exercise('2.2.4').transferQuestion, /H₂O.*two bonding pairs and two lone pairs/);
  const vsepr = solution('2.2.4');
  assert.match(vsepr, /CH₄ has four electron domains, all bonding.*shape are both tetrahedral.*109\.5°/);
  assert.match(vsepr, /NH₃ also has four electron domains: three bonding and one lone pair/);
  assert.match(vsepr, /hydrogen positions give a trigonal pyramidal molecular shape/);
  assert.match(vsepr, /H–N–H angle is therefore somewhat smaller than 109\.5°/);
  assert.match(exercise('2.2.4').transferExplanation.join(' '), /four electron domains.*approximately tetrahedral.*bent molecular shape, not a linear one/);
});

test('bond polarity follows the electronegativity difference and keeps charges partial', () => {
  const carbon = 2.6, oxygen = 3.4, fluorine = 4.0;
  assert.match(exercise('2.2.5').question, /C = 2\.6, O = 3\.4 and F = 4\.0/);
  assert.ok(fluorine - carbon > oxygen - carbon);
  const bonds = solution('2.2.5');
  assert.ok(bonds.includes(`3.4 − 2.6 = ${(oxygen - carbon).toFixed(1)}`));
  assert.ok(bonds.includes(`4.0 − 2.6 = ${(fluorine - carbon).toFixed(1)}`));
  assert.ok(bonds.includes(`4.0 − 4.0 = ${(fluorine - fluorine).toFixed(1)}`));
  assert.match(bonds, /Cδ⁺–Oδ⁻/);
  assert.match(bonds, /Cδ⁺–Fδ⁻.*C–F more polar than C–O/);
  assert.match(bonds, /Equal atoms share.*equally.*non-polar/);
  assert.match(bonds, /partial charges.*not full ionic charges/);
  const transfer = exercise('2.2.5').transferExplanation.join(' ');
  assert.ok(transfer.includes(`3.2 − 2.2 = ${(3.2 - 2.2).toFixed(1)}`));
  assert.match(transfer, /Hδ⁺–Clδ⁻/);
});

test('intermolecular-force identification includes dispersion, donor conditions and induction', () => {
  const forces = solution('2.2.8');
  assert.match(forces, /All three pure samples have London \(dispersion\) forces/);
  assert.match(forces, /non-polar CH₄.*only intermolecular attractions/);
  assert.match(forces, /HCl also has dipole–dipole attractions.*does not have hydrogen bonding.*H is bonded to Cl rather than N, O or F/);
  assert.match(forces, /NH₃ has London forces, dipole–dipole attractions and hydrogen bonding/);
  assert.match(forces, /N–H hydrogen on one molecule.*nitrogen lone pair on another/);
  assert.match(forces, /distort the Ar electron cloud and induce a dipole/);
  assert.match(forces, /permanent HCl dipole.*induced Ar dipole is dipole-induced dipole attraction/);
  assert.match(forces, /distinct from the covalent.*bonds within the molecules/);
  assert.match(exercise('2.2.8').transferExplanation.join(' '), /does not form hydrogen bonds with itself.*no H directly bonded to N, O or F.*London forces and dipole–dipole attractions/);
});

test('the boiling comparison retains comparable masses, constant pressure and molecular integrity', () => {
  // Supplied rounded molar masses follow the formula atom counts (C=12, H=1, F=19, O=16).
  const masses = {ethane: 2 * 12 + 6, fluoromethane: 12 + 3 + 19, methanol: 12 + 4 + 16};
  assert.deepEqual(Object.values(masses), [30, 34, 32]);
  const question = exercise('2.2.9').question;
  assert.ok(question.includes(`C₂H₆ (molar mass ${masses.ethane} g mol⁻¹`));
  assert.ok(question.includes(`CH₃F (${masses.fluoromethane} g mol⁻¹`));
  assert.ok(question.includes(`CH₃OH (${masses.methanol} g mol⁻¹`));
  assert.match(question, /molar masses are comparable.*same external pressure/);
  const comparison = solution('2.2.9');
  assert.match(comparison, /C–H bonds do not provide hydrogen-bond donors/);
  assert.match(comparison, /CH₃OH can form hydrogen bonds through its O–H group and the oxygen lone pairs/);
  assert.match(comparison, /C₂H₆ < CH₃F < CH₃OH.*same external pressure/);
  assert.match(comparison, /molecules retain their covalent bonds.*does not require breaking the O–H covalent bond/);
  assert.match(comparison, /conditional trend, not a universal ranking/);
  assert.match(exercise('2.2.9').transferExplanation.join(' '), /assumes comparable molar masses.*more polarizable.*molecular shape also matters/);
});
