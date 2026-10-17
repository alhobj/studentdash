/* Original procedural pixel art: layered village scenery, no external assets. */
window.paintVillageScene=function(c,r){
 const p=r.palette;
 const box=(x,y,w,h,color)=>{c.fillStyle=color;c.fillRect(Math.round(x),Math.round(y),w,h);};
 const shade=(hex,n)=>'#'+[1,3,5].map(i=>Math.max(0,Math.min(255,parseInt(hex.slice(i,i+2),16)+n)).toString(16).padStart(2,'0')).join('');
 const ink='#334436',wood='#855737',lightWood='#d0a069',stone='#b6ad88';
 function path(x,y,w,h){box(x-2,y-2,w+4,h+4,shade(p.path,-35));box(x,y,w,h,p.path);box(x,y,w,3,shade(p.path,20));
  for(let yy=y+8;yy<y+h-4;yy+=16)for(let xx=x+6+(Math.floor(yy/16)%2)*9;xx<x+w-6;xx+=24){box(xx,yy,9,2,shade(p.path,-17));box(xx+2,yy-2,5,2,shade(p.path,14));}}
 function pot(x,y,color){box(x-10,y,20,5,'#653f32');box(x-8,y+5,16,13,'#b4774d');box(x-5,y+6,3,9,'#d9a36e');box(x-2,y-16,4,18,'#456a3d');for(const [dx,dy]of [[-9,-9],[5,-15],[-6,-23]]){box(x+dx,y+dy,9,6,'#6e934e');box(x+dx+2,y+dy-3,5,5,color);}}
 function tree(x,y){box(x-22,y+24,48,10,shade(p.ground,-20));box(x-6,y-1,12,34,'#654a32');box(x-3,y,4,32,'#a47b48');box(x+4,y+21,9,8,'#654a32');
  const green=r.theme==='garden'?p.detail:'#66874b';
  const rows=[[-46,18],[-40,34],[-32,44],[-24,48],[-14,44],[-5,32]];
  for(const [dy,w]of rows){box(x-w/2-2,y+dy,w+4,12,shade(green,-30));box(x-w/2,y+dy-2,w,10,green);}
  for(const [dx,dy,w,h]of [[-9,-44,17,6],[-17,-34,22,7],[-20,-23,15,6],[-5,-28,15,7],[7,-17,12,6],[-9,-9,16,5]]){box(x+dx,y+dy,w,h,shade(green,dx<0?24:10));box(x+dx+3,y+dy,4,2,shade(green,38));}
 }
 function crate(x,y,w=42,h=28){box(x,y,w,h,'#61452f');box(x+3,y+3,w-6,h-6,wood);for(let j=6;j<h-3;j+=7)box(x+3,y+j,w-6,2,'#ac7949');box(x+6,y+3,4,h-6,lightWood);box(x+w-10,y+3,4,h-6,lightWood);}
 function windowPane(x,y,w=42,h=34){box(x-3,y-3,w+6,h+8,'#614e3c');box(x,y,w,h,p.window);box(x+3,y+3,w-6,5,shade(p.window,15));box(x+w/2-2,y,4,h,wood);box(x,y+h/2-2,w,3,wood);box(x-5,y+h, w+10,5,lightWood);}
 function pond(x){box(x,100,300,180,shade(p.ground,-28));box(x+4,104,292,172,'#9d9770');box(x+8,108,284,164,p.water);box(x+12,112,276,5,shade(p.water,-20));
  for(let j=0;j<30;j++){const xx=x+18+(j*47)%258,yy=124+(j*23)%134;box(xx,yy,12+(j%3)*8,2,j%2?'#82b8b3':'#4f8c9c');box(xx+4,yy+3,7,2,'#538ea1');}
  for(const [xx,yy]of [[x+36,143],[x+208,232],[x+110,200]]){box(xx,yy,16,7,'#496f42');box(xx+3,yy-3,8,5,'#82a957');box(xx+8,yy-5,4,4,'#f4ccad');}
  for(let i=0;i<5;i++){box(x+8+i*63,95,15,8,stone);box(x+10+i*63,96,8,2,'#d6c99e');}
 }
 function machine(x,y,w,h){box(x+5,y+5,w,h,shade(p.ground,-22));box(x,y,w,h,'#554d40');box(x+4,y+4,w-8,h-8,p.roof);for(let yy=y+10;yy<y+h-10;yy+=12)box(x+8,yy,w-16,3,shade(p.roof,17));
  box(x+12,y+18,w-24,32,'#384b49');box(x+18,y+24,w-36,17,p.window);for(let i=0;i<3;i++)box(x+18+i*24,y+62,10,9,i===0?'#efbc66':'#829d83');box(x+20,y+h-18,7,18,'#b99c68');box(x+w-27,y+h-18,7,18,'#b99c68');}
 box(0,0,960,576,p.ground);
 let seed=71429;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
 for(let j=0;j<650;j++){const x=Math.floor(random()*960),y=Math.floor(random()*576);box(x,y,3,2,j%3?shade(p.ground,9):shade(p.ground,-10));if(j%4===0){box(x+2,y-3,2,4,shade(p.ground,18));box(x+6,y-1,2,3,shade(p.ground,12));}}

 path(448,280,64,116);if(r.exits.left)path(0,332,480,64);if(r.exits.right)path(480,332,480,64);
 if(r.exits.up){const nx=r.northExitX||480;path(nx-14,0,28,364);path(nx,332,480-nx,64);}if(r.exits.down)path(448,364,64,212);
 // Scenery follows the existing solid footprints; exits remain clear.
 if(r.theme==='water'){pond(20);pond(640);for(let j=0;j<6;j++){box(112+j*27,248,25,26,wood);box(113+j*27,249,22,3,lightWood);}box(110,245,170,4,'#c2a475');}
 if(r.theme==='garden'){for(const x of [70,200,720,850])for(const y of [160,450])tree(x,y);for(let i=0;i<9;i++)if(i!==4)pot(90+i*96,510,i%2?'#e9bb73':'#dba2ad');}
 if(r.theme==='factory'){for(const x of [90,740]){machine(x,100,120,140);box(x+45,60,25,50,'#60554b');box(x+42,60,31,8,'#a18e73');for(let i=0;i<4;i++)box(x+47,75+i*8,21,2,'#88725d');crate(x,445);crate(x+47,445);crate(x+20,475);}}
 if(r.theme==='energy'){for(const x of [65,740]){machine(x,100,150,170);box(x+30,180,90,58,'#523c33');box(x+38,188,74,42,'#b76d3d');box(x+48,201,18,23,'#e6ad58');box(x+74,194,20,30,'#f2cc7b');for(let i=0;i<5;i++)box(x+35+i*17,180,4,58,'#564d42');}for(let x=80;x<900;x+=100){box(x,488,35,10,'#81775b');box(x+4,484,25,8,'#b4a77c');}}
 if(r.theme==='archive'){for(const x of [65,735])for(const y of [110,180,450]){box(x+4,y+4,150,48,shade(p.ground,-19));crate(x,y,150,48);for(let i=0;i<9;i++){const color=['#bb8263','#9ca879','#8ba5b1','#c9ae76'][i%4];box(x+9+i*15,y+8,10,27,color);box(x+11+i*15,y+11,6,2,shade(color,25));}box(x+3,y+36,144,5,lightWood);}pot(285,216,'#d8badf');pot(680,465,'#dec08b');}
 if(r.theme==='stars'){for(const x of [150,800]){box(x-37,265,78,9,shade(p.ground,-19));box(x-4,177,8,93,'#b89b74');for(let i=0;i<5;i++){box(x-8-i*5,240+i*6,7,6,wood);box(x+2+i*5,240+i*6,7,6,wood);}box(x-45,150,90,24,'#57647a');box(x-41,153,82,6,'#a5b4bb');box(x+24,135,25,38,'#b29b70');box(x+29,140,15,26,'#82b8c0');}for(let i=0;i<18;i++)box((i*151+35)%960,420+(i*23)%100,2,2,'#dfc991');}
 if(r.theme==='market'){for(const x of [70,730]){crate(x,120,160,90);box(x-3,98,166,8,wood);for(let i=0;i<8;i++){box(x+i*20,106,20,34,i%2?'#e7d0a0':p.accent);box(x+i*20,136,20,7,i%2?'#cbb489':shade(p.accent,-20));}box(x+10,185,140,9,lightWood);for(let i=0;i<7;i++){box(x+17+i*18,170,12,12,i%2?'#a8b46c':'#d79765');box(x+19+i*18,168,5,3,'#64824a');}}}
 // Cottage facade: stone footing, plaster, beams, tiled pitched roof and warm windows.
 box(354,116,266,174,shade(p.ground,-26));box(350,160,260,120,'#5c493a');box(355,165,250,110,'#dac394');
 for(let y=170;y<270;y+=18)box(355,y,250,2,'#c4aa7f');
 box(350,260,260,20,'#948e77');for(let x=355;x<605;x+=25){box(x,262,22,6,'#bcb095');box(x+6,271,18,6,'#aaa18a');}
 for(const x of [355,445,510,600])box(x,168,6,92,wood);
 const roof=p.roof;
 for(let row=0;row<11;row++){const inset=(10-row)*5,x=338+inset,y=96+row*7,w=284-2*inset;box(x-2,y,w+4,9,'#554332');box(x,y,w,7,roof);box(x,y,w,2,shade(roof,22));for(let xx=x+((row%2)*12);xx<x+w-3;xx+=24)box(xx,y+2,2,5,shade(roof,-23));}
 box(335,173,290,7,'#5d4938');box(339,173,282,3,'#c39a61');
 box(556,88,24,42,'#786450');for(let y=90;y<125;y+=8)box(558,y,20,2,'#b29977');box(552,84,32,7,'#c0ab87');
 windowPane(377,193,48,38);windowPane(535,193,48,38);
 box(456,218,48,62,'#604735');box(462,222,36,58,wood);box(465,225,30,21,p.window);box(478,225,3,21,lightWood);box(464,250,32,3,'#b78a52');box(490,257,3,4,'#f0cc76');box(451,279,58,6,'#c7b68d');
 pot(365,254,'#e7ba84');pot(594,254,'#e7ba84');
 // Theme-specific roof emblem.
 box(465,132,30,25,shade(roof,-28));box(469,136,22,17,'#e7d7ad');
 if(r.theme==='stars'){box(478,137,4,15,p.roof);box(473,142,14,4,p.roof);}
 else if(r.theme==='water'){box(476,138,7,10,'#548e9d');box(473,144,13,6,'#548e9d');}
 else{box(474,139,12,3,p.roof);box(478,141,4,8,p.roof);box(474,148,12,3,p.roof);}
};
window.paintVillagePerson=function(c,{x,y,coat,accent,facing='down',pace=0}){
 const b=(dx,dy,w,h,color)=>{c.fillStyle=color;c.fillRect(Math.round(x+dx),Math.round(y+dy),w,h);};
 const dark='#3e3940',hair='#665044',skin='#edc09a';
 b(-12,24,26,6,'#52604a');b(-9,-15,18,19,dark);b(-7,-12,14,17,skin);b(-10,-18,20,8,hair);b(-8,-18,15,3,'#8a6950');b(-10,-10,4,8,hair);b(7,-10,3,6,hair);
 b(-11,3,22,19,dark);b(-9,4,18,17,coat);b(-7,4,4,5,'#faf0cc');b(3,4,4,5,'#faf0cc');b(-1,8,2,13,'#abb6a0');
 b(-14,5-pace,5,14,dark);b(-12,5-pace,4,11,coat);b(-12,16-pace,4,4,skin);b(9,5+pace,5,14,dark);b(9,5+pace,4,11,coat);b(9,16+pace,4,4,skin);
 b(-7,22+pace,6,8,'#44525c');b(2,22-pace,6,8,'#44525c');b(-8,28+pace,8,3,dark);b(2,28-pace,8,3,dark);
 if(facing==='up'){b(-7,-10,14,13,hair);b(-5,7,10,12,accent);b(-3,9,6,3,'#d8c39c');}
 else{b(4,12,4,4,accent);if(facing!=='right')b(-5,-5,2,3,dark);if(facing!=='left')b(4,-5,2,3,dark);b(-2,1,4,1,'#bb8269');}
};
