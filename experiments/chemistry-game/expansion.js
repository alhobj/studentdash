/* Chemistry-specific models and original scenarios. No formal assessment evidence. */
window.GAME_PROFILE.models={
  calorimeter(values){
    const final=values[0],energy=100*4.18*(final-20);
    return {values:{energy},lines:[`100.0 g water · initial temperature 20.0 °C`,`Final temperature ${final.toFixed(1)} °C · ΔT ${(final-20).toFixed(1)} °C`,`Energy gained by water: ${energy.toFixed(0)} J`],fraction:(final-20)/15,gauge:'Temperature rise'};
  },
  rateTrial(values){
    const concentration=values[0],time=120*0.1/concentration;
    return {values:{time},lines:[`Initial concentration: ${concentration.toFixed(2)} mol dm⁻³`,`Time to a fixed endpoint: ${time.toFixed(1)} s`,`Relative rate: ${(concentration/0.1).toFixed(1)} × baseline`],fraction:concentration/0.3,gauge:'Relative rate (model)'};
  },
  titration(values){
    const baseVolume=values[0],excess=0.1*baseVolume/1000-0.1*25/1000,volume=(25+baseVolume)/1000;
    const pH=Math.abs(excess)<1e-12?7:excess<0?-Math.log10(-excess/volume):14+Math.log10(excess/volume);
    return {values:{baseVolume,pH},lines:[`Acid: 25.00 cm³, 0.100 mol dm⁻³`,`Base delivered: ${baseVolume.toFixed(2)} cm³ at 0.100 mol dm⁻³`,`Calculated pH: ${pH.toFixed(2)}`,Math.abs(excess)<1e-12?'Equivalence: equal amounts of H⁺ and OH⁻.':excess<0?'Acid remains in excess.':'Base is in excess.'],fraction:pH/14,gauge:'pH (0–14)'};
  }
};
window.GAME_PROFILE.adventures.push(
  {
    id:'patterns',district:'S3',section:'S3.1',npc:'Mira · archive curator',title:'Put the periodic archive in order',
    story:'Mira found mixed-up display labels. Restore their order using atomic number and nuclear attraction. Move each label up or down; no dragging is required.',
    requires:{completed:['atoms']},reward:{credits:16,tool:'thermometer'},rewardText:'Mira gives you a thermometer from the archive stores. Place it on the bench to visit the Energy station.',
    steps:[
      {kind:'order',title:'Follow increasing atomic number',context:'Arrange these period 3 elements from smallest to largest atomic number.',items:['Na · Z = 11','Mg · Z = 12','Al · Z = 13','Si · Z = 14'],initialOrder:[2,0,3,1],hint:'Atomic number counts protons. Start at 11 and increase.',explanation:'Na → Mg → Al → Si follows increasing proton count.'},
      {kind:'order',title:'Compare isoelectronic ions',context:'All three ions have 10 electrons. Arrange them from largest to smallest ionic radius.',items:['Na⁺ · 11 protons','Mg²⁺ · 12 protons','Al³⁺ · 13 protons'],initialOrder:[2,1,0],hint:'With the same electron count, more protons attract the electrons more strongly and reduce the radius.',explanation:'Na⁺ > Mg²⁺ > Al³⁺. This comparison holds for this isoelectronic series.'},
      {title:'Label the outer shells',context:'Count outer-shell electrons in these neutral ground-state atoms: Na (2,8,1), Mg (2,8,2), Al (2,8,3).',fields:[{label:'Na outer electrons',target:1,min:0,max:8},{label:'Mg outer electrons',target:2,min:0,max:8},{label:'Al outer electrons',target:3,min:0,max:8}],hint:'Use the last number in each shell arrangement.',explanation:'Across these elements, the outer-shell count increases from 1 to 3.'}
    ]
  },
  {
    id:'heat',district:'R1',section:'R1.1',npc:'Kaia · energy technician',title:'Calibrate the energy station',
    story:'Kaia lends you an insulated cup to explore calorimetry. Use q = mcΔT. This ideal model ignores heat lost to the room and heat absorbed by the equipment.',
    requires:{completed:['weigh','patterns'],bench:['thermometer']},reward:{credits:20,tool:'calorimeter'},rewardText:'Kaia gives you an insulated-cup calorimeter for your equipment collection.',
    steps:[
      {kind:'order',title:'Plan the observations',context:'Order the simplified measurement sequence. The thermometer is already secured in the cup.',items:['Add a measured mass of water','Record the initial temperature','Transfer heat to the water','Record the highest final temperature'],initialOrder:[1,3,0,2],hint:'The water must be present before its initial temperature is measured; measure again after transferring heat.',explanation:'The temperature change requires both an initial and a final reading for a known water mass.'},
      {title:'Tune the temperature rise',context:'Set the final temperature so 100.0 g of water gains 2090 J. Use c = 4.18 J g⁻¹ K⁻¹ and initial temperature 20.0 °C.',model:'calorimeter',goal:{key:'energy',target:2090,tolerance:1},fields:[{label:'Final water temperature / °C',kind:'range',initial:20,min:20,max:35,step:0.1}],hint:'ΔT = 2090 ÷ (100 × 4.18) = 5.0 °C. Add this to 20.0 °C.',explanation:'The final temperature is 25.0 °C, giving a 5.0 K temperature rise and q = 2090 J.'},
      {title:'Account for the heat source',context:'The water gains +2090 J. Assume energy flows only between the source and the water. Enter the energy change of the source, including its sign.',fields:[{label:'Energy change of source / J',target:-2090,min:-5000,max:5000,step:10}],hint:'Energy is conserved. The source loses what the water gains.',explanation:'The source changes by −2090 J. This is energy transferred, not a molar enthalpy.'}
    ]
  },
  {
    id:'rates',district:'R2',section:'R2.2',npc:'Jun · reactor maintenance',title:'Investigate the reactor clock',
    story:'Compare fictional reaction-clock trials. The model assumes endpoint time is inversely proportional to initial concentration over this small range. This is a model for these trials, not a universal rate law.',
    requires:{completed:['mixing']},reward:{credits:18,tool:'stopwatch'},rewardText:'Jun gives you a stopwatch for future timed investigations.',
    steps:[
      {title:'Reach the endpoint in half the time',context:'The baseline trial at 0.10 mol dm⁻³ takes 120 s. Adjust concentration until the model predicts 60 s. Other conditions remain fixed.',model:'rateTrial',goal:{key:'time',target:60,tolerance:0.01},fields:[{label:'Initial concentration / mol dm⁻³',kind:'range',initial:0.1,min:0.1,max:0.3,step:0.01}],hint:'In this model, doubling the concentration halves the endpoint time.',explanation:'0.20 mol dm⁻³ gives 60 s under the model assumptions.'},
      {title:'Control the next trial',context:'The baseline uses 50 cm³ total solution at 25 °C. You want to change only concentration. Set the volume and temperature for the comparison.',fields:[{label:'Total volume / cm³',target:50,min:10,max:100},{label:'Temperature / °C',target:25,min:10,max:60}],hint:'Keep volume and temperature equal to the baseline.',explanation:'50 cm³ and 25 °C hold those variables constant.'},
      {title:'Calculate an average rate',context:'In another fictional trial, reactant concentration falls from 0.100 to 0.080 mol dm⁻³ in 20 s. Enter the positive average disappearance rate.',fields:[{label:'Average rate / mol dm⁻³ s⁻¹',target:0.001,min:0,max:0.1,step:0.001}],hint:'Use (0.100 − 0.080) ÷ 20.',explanation:'The positive average disappearance rate is 0.001 mol dm⁻³ s⁻¹.'}
    ]
  },
  {
    id:'titration',district:'R3',section:'R3.1',npc:'Bo · water analyst',title:'Restore the titration desk',
    story:'Bo needs a strong-acid/strong-base model for visitors. Place a pipette and burette from the supply desk. The simulation assumes HCl and NaOH fully dissociate at 25 °C and ideal dilute-solution behaviour.',
    requires:{completed:['solution','ions'],bench:['pipette','burette']},reward:{credits:22},rewardText:'The titration desk is restored and your analysis record is added to the journal.',
    steps:[
      {kind:'order',title:'Plan the measured transfer',context:'The burette has already been correctly rinsed, filled and its tip cleared. Arrange the next steps. Use a pipette filler.',items:['Rinse the pipette with the acid solution','Transfer the measured acid aliquot to the flask','Record the initial burette reading','Add titrant while mixing'],initialOrder:[3,1,0,2],hint:'Prepare the pipette before transferring. Record the burette reading before delivering titrant.',explanation:'The acid volume and change in burette reading determine the quantities compared.'},
      {title:'Find equivalence',context:'Deliver 0.100 mol dm⁻³ NaOH to 25.00 cm³ of 0.100 mol dm⁻³ HCl. Adjust the delivered volume until the amounts are equal. This model permits moving the control backward to explore; real delivered titrant cannot be removed.',model:'titration',goal:{key:'baseVolume',target:25,tolerance:0.001},fields:[{label:'Base delivered / cm³',kind:'range',initial:0,min:0,max:50,step:0.1}],hint:'HCl and NaOH react 1:1. Equal concentrations need equal volumes at equivalence.',explanation:'At 25.00 cm³ the amounts are equal and the ideal solution has pH 7 at 25 °C. This is not true for every titration.'},
      {title:'Analyse a different sample',context:'An unknown HCl sample of 25.0 cm³ requires 18.5 cm³ of 0.100 mol dm⁻³ NaOH. Calculate the HCl concentration; the reaction ratio is 1:1.',fields:[{label:'HCl concentration / mol dm⁻³',target:0.074,min:0,max:1,step:0.001}],hint:'Use c(acid) = 0.100 × 18.5 ÷ 25.0.',explanation:'The acid concentration is 0.0740 mol dm⁻³.'}
    ]
  }
);
Object.assign(window.GAME_PROFILE.gameplay.equipment,{thermometer:'Thermometer',calorimeter:'Cup calorimeter',stopwatch:'Stopwatch',burette:'Burette'});
window.GAME_PROFILE.gameplay.shop.push({id:'burette',cost:24});
window.GAME_PROFILE.adventurePeople.push({name:'KAIA',label:'Kaia · energy station',x:95,y:350,quest:'heat',color:'#df986d'},{name:'BO',label:'Bo · titration desk',x:855,y:350,quest:'titration',color:'#d499ac'});

window.GAME_PROFILE.models.gasVolume=values=>{
 const volume=values[0],pressure=0.010*8.314*300/volume;
 return {values:{pressure},lines:[`Ideal gas · amount fixed at 0.010 mol · temperature fixed at 300 K`,`Volume: ${volume.toFixed(3)} dm³`,`Pressure: ${pressure.toFixed(2)} kPa`],fraction:pressure/250,gauge:'Pressure',piston:volume/0.5};
};
window.GAME_PROFILE.models.gasTemperature=values=>{
 const temperature=values[0],pressure=0.010*8.314*temperature/0.250;
 return {values:{pressure},lines:[`Ideal gas · amount fixed at 0.010 mol · volume fixed at 0.250 dm³`,`Temperature: ${temperature.toFixed(0)} K`,`Pressure: ${pressure.toFixed(2)} kPa`],fraction:pressure/200,gauge:'Pressure',piston:0.5};
};
window.GAME_PROFILE.adventures.push({
 id:'gas-piston',district:'S1',section:'S1.5',npc:'Jun · apparatus repair',title:'Repair the gas-piston display',
 story:'A sealed piston display has lost its calibration labels. Explore an ideal gas with fixed amount using pV = nRT. The drawing shows changing gas volume, not the size of individual particles. Real gases can depart from this model.',
 requires:{completed:['atoms','weigh']},reward:{credits:18,tool:'gasSyringe'},rewardText:'Jun gives you a gas syringe for the laboratory collection.',
 steps:[
  {title:'Compress at constant temperature',context:'At 300 K, 0.010 mol occupies 0.250 dm³ at about 99.77 kPa. Move the piston until the pressure doubles to about 199.54 kPa. Use R = 8.314 kPa dm³ mol⁻¹ K⁻¹.',model:'gasVolume',goal:{key:'pressure',target:199.536,tolerance:0.1},fields:[{label:'Volume / dm³',kind:'range',initial:0.250,min:0.1,max:0.5,step:0.005}],hint:'At constant amount and temperature, halving the volume doubles the pressure.',explanation:'The required volume is 0.125 dm³. The particles have not become smaller.'},
  {title:'Heat at constant volume',context:'The piston is now fixed at 0.250 dm³. Set the temperature so the pressure reaches about 133.02 kPa.',model:'gasTemperature',goal:{key:'pressure',target:133.024,tolerance:0.1},fields:[{label:'Temperature / K',kind:'range',initial:300,min:250,max:500,step:1}],hint:'Pressure is proportional to absolute temperature. The required temperature is 400 K.',explanation:'400 K gives approximately 133.02 kPa at fixed amount and volume.'},
  {title:'Use the correct temperature scale',context:'The room temperature is 25.0 °C. Convert it to kelvin before using the ideal-gas equation. Use T / K = temperature / °C + 273.15.',fields:[{label:'Temperature / K',target:298.15,min:0,max:500,step:0.01}],hint:'Add 273.15 to 25.0.',explanation:'25.0 °C = 298.15 K. Gas-law proportionalities use absolute temperature.'}
 ]
});
window.GAME_PROFILE.gameplay.equipment.gasSyringe='Gas syringe';
