/* Original parameterized retrieval tasks, one per district. */
window.MATH_GAME_PROFILE.makeChallengeSet=function(random=Math.random){
 const pick=(lo,hi)=>lo+Math.floor(random()*(hi-lo+1)),q=(topic,title,prompt,answer,hint,explanation)=>({topic,title,prompt,answer,hint,explanation,label:'Your answer',tolerance:0.001});
 const price=pick(4,16)*10,rate=pick(1,5)*5,m=pick(1,5),b=pick(-4,8),x=pick(1,6),scale=pick(1,5),a=pick(2,12),k=pick(1,6),t=pick(1,5);
 return [
 q('Number market','Apply a discount',`A fictional item costs ${price} credits. Reduce its price by ${rate}%. What is the new price?`,price*(1-rate/100),'Multiply by one minus the percentage written as a decimal.',`${price} × (1 − ${rate}/100) = ${Number((price*(1-rate/100)).toFixed(2))} credits.`),
 q('Function foundry','Read a linear model',`For y = ${m}x ${b<0?'− '+Math.abs(b):'+ '+b}, find y when x = ${x}.`,m*x+b,'Multiply the input by the gradient, then add the intercept.',`y = ${m} × ${x} + (${b}) = ${m*x+b}.`),
 q('Surveyor’s harbour','Cross the courtyard',`A rectangular courtyard measures ${3*scale} m by ${4*scale} m. Find its diagonal length in metres.`,5*scale,'Use Pythagoras: square the sides, add, then take the square root.',`√(${3*scale}² + ${4*scale}²) = ${5*scale} m.`),
 q('Data gardens','Find a median',`The ordered observations are ${a}, ${a+2}, ${a+4}, ${a+7}, ${a+9}. Find the median.`,a+4,'The median is the middle value in ordered data.',`The third value, ${a+4}, is the median.`),
 q('Change observatory','Read an instantaneous rate',`For f(x) = ${k}x², find f′(${t}).`,2*k*t,'The derivative is 2kx; evaluate it at the requested input.',`f′(x) = ${2*k}x, so f′(${t}) = ${2*k*t}.`)
 ];
};
