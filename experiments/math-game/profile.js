/* Original fictional activities. Subject vocabulary and authored routes stay here. */
window.MATH_GAME_PROFILE = (() => {
  const field = (label, answer, unit = '', tolerance = 0.001) => ({label, answer, unit, tolerance});
  const step = (title, prompt, fields, hint, explanation, model = null) => ({title, prompt, fields, hint, explanation, model});
  return {
    id: 'meridian-math-ai-sl-v1', title: 'Pattern Quest', storageKey: 'studentdash-pattern-quest-v1',
    districts: [
      {id:'number',name:'Number market',guide:'Nia',role:'Market keeper',color:'#7ea68b',x:170,y:145,resource:'topic-1.html'},
      {id:'functions',name:'Function foundry',guide:'Jun',role:'Clockmaker',color:'#d4a470',x:480,y:125,resource:'topic-2.html'},
      {id:'geometry',name:'Surveyor’s harbour',guide:'Mira',role:'Surveyor',color:'#83aeca',x:790,y:145,resource:'topic-3.html'},
      {id:'statistics',name:'Data gardens',guide:'Sol',role:'Town researcher',color:'#b39bcc',x:260,y:420,resource:'topic-4.html'},
      {id:'calculus',name:'Change observatory',guide:'Kaia',role:'Engineer',color:'#cc8e8a',x:690,y:420,resource:'topic-5.html'}
    ],
    equipment: {ledger:'Pattern ledger',graph:'Graph board',compass:'Surveying compass',data:'Data lens',tangent:'Tangent ruler',lamp:'Amber desk lamp',plant:'Studio fern'},
    shop: [{id:'lamp',cost:12},{id:'plant',cost:16}],
    quests: [
      {id:'market',district:'number',title:'Reopen the night market',requires:[],reward:{credits:16,tool:'ledger',card:'Percentages'},story:'Nia has a stall full of lanterns and a ledger with missing prices. Restore the price board before the market opens.',steps:[
        step('The missing discount','A lantern costs 80 credits. The opening discount is 15%. Calculate the discount, then the sale price.',[field('Discount',12,'credits'),field('Sale price',68,'credits')],'15% is 0.15. Subtract the discount from the original price.','Discount = 80 × 0.15 = 12; sale price = 80 − 12 = 68 credits.'),
        step('A pattern of lanterns','The first arch uses 7 lanterns. Each new arch uses 4 more than the previous one. How many lanterns does the sixth arch use?',[field('Sixth term',27,'lanterns')],'There are five increases between the first and sixth terms.','u₆ = 7 + (6 − 1) × 4 = 27. The common difference is 4.'),
        step('Fund the next market','A fictional fund starts with 500 credits and grows by 4% annually, compounded once per year. No payments or fees. Find its value after two years.',[field('Final value',540.8,'credits',0.01)],'Multiply by 1.04 twice; do not just add 8%.','500 × 1.04² = 540.80 credits. The second increase also applies to the first year’s growth.')
      ]},
      {id:'scale',district:'number',title:'Restore the scale archive',requires:['market'],reward:{credits:18,card:'Powers & scale'},story:'Nia’s archive records very large and very small quantities. Make its labels readable again.',steps:[
        step('A compact label','Write 4,200,000 as a × 10ⁿ, with 1 ≤ a < 10.',[field('Coefficient a',4.2),field('Exponent n',6)],'Move the decimal point until one non-zero digit remains before it.','4,200,000 = 4.2 × 10⁶.'),
        step('Reverse the power','The model is 2ˣ = 32. Find x.',[field('Exponent x',5)],'List powers of 2: 2, 4, 8, 16, …','2⁵ = 32. A logarithm asks which exponent produces a given value.'),
        step('Check the approximation','A length of exactly 48 m is reported as 50 m. Calculate the absolute percentage error relative to 48 m.',[field('Percentage error',100*2/48,'%',0.01)],'Use |approximation − exact value| ÷ |exact value| × 100.','|50 − 48| / 48 × 100 = 4.1667%, approximately 4.17%.')
      ]},
      {id:'clock',district:'functions',title:'Restart the town clock',requires:['market'],reward:{credits:18,tool:'graph',card:'Linear models'},story:'Jun’s clock tracks a delivery cart, but its graph has faded. Reconstruct the rule from its recorded positions.',steps:[
        step('Find the rate','A cart follows y = mx + b. Its position is y = 3 at x = 0 and y = 11 at x = 4. Set m and b to pass through both points.',[field('Gradient m',2),field('Intercept b',3)],'The rise is 8 over a run of 4. The intercept is the value at x = 0.','m = (11 − 3) / (4 − 0) = 2; b = 3. The model is y = 2x + 3.','line'),
        step('Use the rule','For the cart model y = 2x + 3, find y when x = 6.',[field('Position y',15)],'Replace x with 6, multiply, then add.','y = 2(6) + 3 = 15.'),
        step('Find the meeting','Two carts follow y = 2x + 3 and y = −x + 12. Find the x-coordinate and y-coordinate where their paths meet.',[field('Meeting x',3),field('Meeting y',9)],'Set the expressions equal: 2x + 3 = −x + 12.','3x = 9 gives x = 3; substitution gives y = 9.')
      ]},
      {id:'arch',district:'functions',title:'Design the gateway arch',requires:['clock'],reward:{credits:20,card:'Quadratic models'},story:'Jun needs a model of the new gateway. Explore how the vertex determines its highest point.',steps:[
        step('Move the vertex','Use y = −(x − h)² + k. Place the highest point at (3, 9).',[field('Horizontal shift h',3),field('Vertical shift k',9)],'The vertex of this form is (h, k).','The vertex is (3, 9). The negative coefficient makes it a maximum.','quadratic'),
        step('Find the ground','For y = −(x − 3)² + 9, give the smaller and larger x-intercepts.',[field('Smaller intercept',0),field('Larger intercept',6)],'Set y = 0. Then (x − 3)² = 9.','x − 3 = ±3 gives x = 0 or 6.'),
        step('Check the clearance','In the same idealized arch model, x and y are measured in metres. What is the height at x = 1?',[field('Height',5,'m')],'Calculate −(1 − 3)² + 9.','y = −4 + 9 = 5 m. This mathematical model does not certify structural safety.')
      ]},
      {id:'survey',district:'geometry',title:'Reconnect the harbour',requires:[],reward:{credits:16,tool:'compass',card:'Distance & bearings'},story:'Mira is mapping a new footpath. Help her measure distances before the bridge crew arrives.',steps:[
        step('Across the map','The docks are at A(1, 2) and B(7, 10). Find their straight-line distance in map units.',[field('Distance',10,'units')],'The horizontal and vertical changes are 6 and 8. Apply Pythagoras.','Distance = √(6² + 8²) = 10 units.'),
        step('Meet halfway','Find the midpoint of A(1, 2) and B(7, 10).',[field('Midpoint x',4),field('Midpoint y',6)],'Average the x-coordinates and the y-coordinates separately.','Midpoint = ((1 + 7)/2, (2 + 10)/2) = (4, 6).'),
        step('Measure the beacon','On level ground, a beacon is observed at an elevation angle of 45° from 20 m away horizontally. The observer’s eye height is 1.5 m. Find the total beacon height.',[field('Height',21.5,'m',0.01)],'Use 20 tan(45°), then add the eye height.','Height = 20 tan(45°) + 1.5 = 21.5 m. Angles are in degrees.')
      ]},
      {id:'shelter',district:'geometry',title:'Build the harbour shelter',requires:['survey'],reward:{credits:18,card:'Shape & space'},story:'Mira wants enough shade and a water tank for the harbour. Work from an idealized plan.',steps:[
        step('The triangular roof','Two sides of a triangular roof are 6 m and 8 m with an included angle of 30°. Find its area.',[field('Area',12,'m²')],'Use ½ab sin(C), with the angle in degrees.','Area = ½ × 6 × 8 × sin(30°) = 12 m².'),
        step('The water tank','A cylindrical tank has radius 2 m and height 3 m. Find its volume. Give a decimal answer within 0.02 m³.',[field('Volume',12*Math.PI,'m³',0.02)],'The circular base has area πr². Multiply by height.','V = π × 2² × 3 = 12π ≈ 37.70 m³.'),
        step('Divide the service area','Two shelters are at (2, 5) and (8, 5). Their equal-distance boundary is a vertical line. What is its x-coordinate?',[field('Boundary x',5)],'The perpendicular bisector passes through the midpoint.','The midpoint is (5, 5). Every point on x = 5 is equally distant from the two shelters.')
      ]},
      {id:'garden',district:'statistics',title:'Read the garden records',requires:[],reward:{credits:16,tool:'data',card:'Data summaries'},story:'Sol is comparing fictional plant-growth records. Help distinguish a typical value from an unusual one.',steps:[
        step('Choose a centre','The five recorded heights are 2, 4, 4, 5 and 20 cm. Find their mean and median.',[field('Mean',7,'cm'),field('Median',4,'cm')],'Add all five heights and divide by five; the median is the middle ordered value.','Mean = 35/5 = 7 cm; median = 4 cm. The high value pulls the mean upwards.'),
        step('Compare spread','For the ordered data 2, 4, 6, 8, 10, 12, use the medians of the lower three and upper three values as Q₁ and Q₃. Find the interquartile range.',[field('Interquartile range',6)],'Q₁ = 4 and Q₃ = 10. Subtract.','IQR = 10 − 4 = 6. The quartile convention is specified because software conventions can differ.'),
        step('Use a fitted line','A fitted height model is y = 2x + 1 for observed days 1 to 5. Predict the height on day 4.',[field('Predicted height',9,'cm')],'Substitute x = 4 into the fitted line.','Prediction = 2(4) + 1 = 9 cm. A fitted association alone does not establish causation.')
      ]},
      {id:'chance',district:'statistics',title:'Prepare the probability fair',requires:['garden'],reward:{credits:20,card:'Probability models'},story:'Sol is opening a fair where visitors compare exact probabilities with what might happen in a small sample.',steps:[
        step('Two independent draws','A bag contains 3 blue and 2 gold tokens. Draw twice, replacing and mixing the first token before the second draw. Find P(two blue tokens).',[field('Probability',0.36)],'Replacement keeps each blue probability at 3/5; multiply for independence.','P(BB) = (3/5)² = 0.36.'),
        step('Count the arrangements','Three independent fair coin tosses are made. Find the probability of exactly two heads.',[field('Probability',0.375)],'There are three orders with two heads, each with probability 1/8.','P(X = 2) = 3 × (½)³ = 3/8 = 0.375.'),
        step('A symmetric model','A measurement follows a normal distribution with mean 50 and standard deviation 10. What is P(X ≤ 50)?',[field('Probability',0.5)],'A normal distribution is symmetric about its mean.','Half the total probability lies below the mean, so P(X ≤ 50) = 0.5.')
      ]},
      {id:'motion',district:'calculus',title:'Align the observatory tracker',requires:['clock'],reward:{credits:20,tool:'tangent',card:'Rates of change'},story:'Kaia’s tracker follows a moving light. Compare average change with the rate at one instant.',steps:[
        step('An average rate','For f(x) = x², calculate the average rate of change from x = 1 to x = 3.',[field('Average rate',4)],'Use (f(3) − f(1)) / (3 − 1).','Average rate = (9 − 1)/2 = 4.'),
        step('A tangent at one point','For f(x) = x², place the tangent at x = 3 and enter its gradient.',[field('Point x',3),field('Tangent gradient',6)],'The derivative of x² is 2x.','f′(3) = 2 × 3 = 6. The tangent gradient describes an instantaneous rate.','tangent'),
        step('A stationary point','For f(x) = x² − 6x + 5, find the x-coordinate where the gradient is zero.',[field('Stationary x',3)],'Set f′(x) = 2x − 6 equal to zero.','2x − 6 = 0 gives x = 3. Since f″(x) = 2 > 0, this point is a minimum.')
      ]},
      {id:'park',district:'calculus',title:'Open the riverside park',requires:['motion','survey'],reward:{credits:24,card:'Optimization & area'},story:'Kaia and Mira are designing a park. Use a model to make the most of a fixed length of fence.',steps:[
        step('Make room to grow','A rectangular enclosure uses 40 m of fence for three sides against a wall. Set width w perpendicular to the wall for maximum area, then enter its length l. Both widths use fence: 2w + l = 40.',[field('Width w',10,'m'),field('Length l',20,'m')],'A = w(40 − 2w). Its derivative is 40 − 4w.','A′ = 0 gives w = 10 and l = 20. The maximum area is 200 m².','enclosure'),
        step('An exact area','Find the area under y = 2x from x = 0 to x = 3.',[field('Area',9,'square units')],'Integrate 2x to get x², or use a triangle of base 3 and height 6.','∫₀³ 2x dx = [x²]₀³ = 9 square units.'),
        step('Estimate a curved edge','Use one trapezoid to estimate the area under y = x² + 1 between x = 0 and x = 4.',[field('Estimated area',36,'square units')],'Width is 4 and the endpoint heights are 1 and 17.','Estimate = 4(1 + 17)/2 = 36. The exact integral is 76/3 ≈ 25.33; this one-strip estimate overestimates the curved area.')
      ]}
    ]
  };
})();
