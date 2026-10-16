/* Original teaching scenarios. Gates are game-design proposals, not IB prerequisites. */
window.GAME_PROFILE.adventures = [
  {
    id: 'weigh', district: 'S1', section: 'S1.1', npc: 'Jun', title: 'A balance for the seed library',
    story: 'Jun needs labelled samples for the campus seed library. Put your balance on a workbench, then measure the sample without counting its container.',
    requires: { bench: ['balance'] }, reward: { credits: 12, tool: 'flask' },
    rewardText: 'Jun gives you a volumetric flask. Place it on your bench to prepare solutions later.',
    steps: [
      { title: 'Tare the empty container', context: 'The empty container reads 12.40 g. Press Tare to zero the balance with the container still on the pan.', visual:'balance', actions:[{label:'Press tare',values:[0]}], fields: [{label:'Reading after tare / g', initial:12.40, target:0, min:0, max:30, step:0.01}], hint:'Taring sets the current container reading to zero.', explanation:'Taring removes the container contribution from subsequent displayed readings.' },
      { title: 'Recover the sample mass', context: 'Without taring, container + sample reads 18.65 g. The empty container is 12.40 g.', fields:[{label:'Sample mass / g',target:6.25,min:0,max:30,step:0.01}], hint:'Subtract the empty container mass from the combined mass.', explanation:'18.65 − 12.40 = 6.25 g.' },
      { title: 'Make the second label', context:'A tared balance now reads 4.80 g after another sample is added.',fields:[{label:'Mass to put on the label / g',target:4.80,min:0,max:30,step:0.01}],hint:'The balance was already tared: the reading is the sample mass.',explanation:'Record 4.80 g; do not subtract the container again.' }
    ]
  },
  {
    id:'atoms',district:'S1',section:'S1.2',npc:'Mira · archive curator',title:'Rebuild the isotope display',
    story:'Mira needs three particle models for the archive. Adjust the proton, neutron and electron counts. The dots are a counting model, not electron orbits or a scale drawing.',
    requires:{archive:true},reward:{credits:16},rewardText:'The Materials workshop is now open. Meet Sol to assemble charge-balanced formula units.',
    steps:[
      {title:'Neutral carbon-12',context:'Atomic number Z = 6; mass number A = 12; charge = 0.',visual:'atom',fields:[{label:'Protons',target:6,min:0,max:20},{label:'Neutrons',target:6,min:0,max:20},{label:'Electrons',target:6,min:0,max:20}],hint:'Protons = Z. Neutrons = A − Z. Neutral atoms have equal proton and electron counts.',explanation:'6 protons, 6 neutrons and 6 electrons make neutral carbon-12.'},
      {title:'Neutral carbon-14',context:'Change the model to carbon-14: Z = 6; A = 14; charge = 0.',visual:'atom',fields:[{label:'Protons',target:6,min:0,max:20},{label:'Neutrons',target:8,min:0,max:20},{label:'Electrons',target:6,min:0,max:20}],hint:'An isotope changes neutron count, not the identity of the element.',explanation:'Carbon-14 has 8 neutrons. The proton count remains 6.'},
      {title:'A sodium ion',context:'Build sodium-23 with charge +1: Z = 11; A = 23.',visual:'atom',fields:[{label:'Protons',target:11,min:0,max:20},{label:'Neutrons',target:12,min:0,max:20},{label:'Electrons',target:10,min:0,max:20}],hint:'Positive charge means fewer electrons than protons. Neutrons = 23 − 11.',explanation:'11 protons, 12 neutrons, 10 electrons. Losing an electron does not change the element.'}
    ]
  },
  {
    id:'ions',district:'S2',section:'S2.1',npc:'Sol · materials technician',title:'Restore the materials display',
    story:'Sol needs the smallest whole-number ratios for three ionic solids. Add ion tiles until charge balances. These are formula units in extended lattices, not separate molecules.',
    requires:{completed:['atoms']},reward:{credits:18,tool:'magneticStirrer'},rewardText:'Sol repairs a magnetic stirrer for your lab. Place it to unlock the dissolving investigation.',
    steps:[
      {title:'Sodium chloride',context:'Use Na⁺ and Cl⁻ tiles.',visual:'ions',charges:[1,-1],fields:[{label:'Na⁺ ions',target:1,min:0,max:6},{label:'Cl⁻ ions',target:1,min:0,max:6}],hint:'Use the smallest positive counts whose charges add to zero.',explanation:'NaCl has a 1:1 ratio. The formula describes an ionic lattice.'},
      {title:'Magnesium chloride',context:'Use Mg²⁺ and Cl⁻ tiles.',visual:'ions',charges:[2,-1],fields:[{label:'Mg²⁺ ions',target:1,min:0,max:6},{label:'Cl⁻ ions',target:2,min:0,max:6}],hint:'One +2 ion needs two −1 ions.',explanation:'MgCl₂ has one magnesium ion for every two chloride ions.'},
      {title:'Aluminium oxide',context:'Use Al³⁺ and O²⁻ tiles.',visual:'ions',charges:[3,-2],fields:[{label:'Al³⁺ ions',target:2,min:0,max:6},{label:'O²⁻ ions',target:3,min:0,max:6}],hint:'The smallest common charge magnitude is 6: two +3 ions and three −2 ions.',explanation:'Al₂O₃: +6 and −6 balance. Larger multiples are neutral too, but are not the simplest ratio.'}
    ]
  },
  {
    id:'solution',district:'S1',section:'S1.4',npc:'Nia',title:'Prepare the reference solution',
    story:'Use your restored water supply and glassware to plan a reference solution. The flask capacity is the final solution volume, not the amount of water added.',
    requires:{flags:['distillation'],completed:['weigh'],bench:['flask']},reward:{credits:18},rewardText:'Reference-solution recipe added to your discoveries.',
    steps:[
      {title:'Convert the final volume',context:'Prepare 250 cm³ of solution at 0.100 mol dm⁻³. Use 1000 cm³ = 1 dm³.',fields:[{label:'Final volume / dm³',target:0.250,min:0,max:2,step:0.001}],hint:'Divide the volume in cm³ by 1000.',explanation:'250 cm³ = 0.250 dm³.'},
      {title:'Calculate the amount',context:'Target concentration is 0.100 mol dm⁻³ and final volume is 0.250 dm³. Use n = cV.',fields:[{label:'Amount / mol',target:0.025,min:0,max:1,step:0.001}],hint:'Multiply 0.100 by 0.250.',explanation:'n = 0.0250 mol.'},
      {title:'Plan the mass',context:'For this NaCl calculation, use molar mass 58.44 g mol⁻¹. You need 0.0250 mol. Use m = nM.',fields:[{label:'Mass / g',target:1.461,min:0,max:10,step:0.001,tolerance:0.005}],hint:'Multiply 0.0250 by 58.44; about 1.46 g.',explanation:'Weigh approximately 1.46 g, dissolve, transfer quantitatively, then make the total solution volume up to the mark. This model does not assess laboratory technique.'}
    ]
  },
  {
    id:'mixing',district:'S2',section:'S1.1',npc:'Sol',title:'Investigate stirring',
    story:'Use the restored magnetic stirrer to compare two fictional dissolving trials. Same substance, water volume, particle size and temperature; only stirring differs. These observations do not measure equilibrium solubility.',
    requires:{completed:['ions'],bench:['magneticStirrer']},reward:{credits:12},rewardText:'A controlled-comparison record is added to your journal.',
    steps:[
      {title:'Compare dissolving times',context:'A 5.0 g sample dissolves in 120 s without stirring and 40 s with stirring.',fields:[{label:'Time saved / s',target:80,min:0,max:200}],hint:'Subtract the stirred time from the unstirred time.',explanation:'Stirring saves 80 s in these fictional trials.'},
      {title:'Calculate an average rate',context:'The stirred 5.0 g sample dissolves in 40 s. Use mass divided by time.',fields:[{label:'Average dissolving rate / g s⁻¹',target:0.125,min:0,max:2,step:0.001}],hint:'5.0 ÷ 40 = 0.125.',explanation:'The average rate is 0.125 g s⁻¹. This is not a claim of a constant instantaneous rate.'},
      {title:'Keep the next comparison fair',context:'Repeat both trials with 50 cm³ water at 25 °C. The unstirred sample is 5.0 g. Choose the stirred sample mass so stirring remains the only changed factor.',fields:[{label:'Stirred sample mass / g',target:5,min:0,max:20,step:0.1}],hint:'Keep the mass equal in both trials.',explanation:'Use 5.0 g in both. Faster dissolving does not establish a greater final solubility.'}
    ]
  }
];
window.GAME_PROFILE.gameplay.equipment = {balance:'Balance',pipette:'Pipette',stirrer:'Stirring rod',flask:'Volumetric flask',magneticStirrer:'Magnetic stirrer'};
window.GAME_PROFILE.adventurePeople = [{name:'MIRA',label:'Mira · isotope archive',x:345,y:205,quest:'atoms',color:'#bdabd8'},{name:'SOL',label:'Sol · materials workshop',x:585,y:235,quest:'ions',color:'#dcaf75'}];
