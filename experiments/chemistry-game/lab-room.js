/* Original pixel sprites, drawn locally without downloaded assets. */
window.GAME_PROFILE.labSprites={
 balance:['..........','..w...w...','..wwwww...','....w.....','.wwwwwww..','....w.....','....w.....','..ddddd...','..dbbbd...','..ddddd...'],
 flask:['...gg.....','...gg.....','...gg.....','..g..g....','..g..g....','.g....g...','.gbbbbg...','gbbbbbbg..','gggggggg..','..........'],
 pipette:['....g.....','....g.....','....g.....','...ggg....','...gbg....','...ggg....','....g.....','....b.....','....g.....','....g.....'],
 stirrer:['......g...','.....g....','.....g....','....g.....','....g.....','...g......','...g......','..g.......','..g.......','..........'],
 magneticStirrer:['..g...g...','..g...g...','..gbbbg...','..gbbbg...','..ggggg...','..........','.ddddddd..','.dwwwwwd..','.dcrcrcd..','.ddddddd..'],
 thermometer:['....w.....','....wr....','....w.....','....wr....','....w.....','....wr....','....r.....','...rrr....','...rrr....','....r.....'],
 calorimeter:['...w......','...w......','.ggwgggg..','.gwwwwwg..','.gwbbwwg..','.gwbbwwg..','.gwwwwwg..','.ggggggg..','..........','..........'],
 stopwatch:['...ccc....','....c.....','..wwwww...','.wwddwww..','.wwdwwww..','.wwdddww..','.wwwwwww..','..wwwww...','..........','..........'],
 burette:['...gg.....','...gb.w...','...gb.....','...gb.w...','...gb.....','...gb.w...','...gg.....','..cccc....','...g......','...b......'],
 gasSyringe:['....w.....','....w.....','..ggwgg...','..gwwwg...','..g...g...','..g...g...','..g...g...','..ggggg...','....g.....','..........']
};
window.paintLabRoom=function(canvas,state,profile){
 canvas.width=600;canvas.height=350;canvas.setAttribute('aria-label','Your laboratory: '+(state.waterSystem?'restored water still':'broken water still')+'; workbench: '+(state.bench.map(id=>profile.gameplay.equipment[id]).join(', ')||'empty'));
 const ctx=canvas.getContext('2d');const rect=(x,y,w,h,color)=>{ctx.fillStyle=color;ctx.fillRect(x,y,w,h);};
 const label=(text,x,y,color='#e9efda')=>{ctx.fillStyle=color;ctx.font='12px monospace';ctx.textAlign='center';ctx.fillText(text,x,y);};
 const palette={w:'#e2ead7',g:'#9bc9c2',b:'#65acc2',r:'#e68b78',c:'#d9ad72',d:'#30494b'};
 function sprite(id,x,y){const rows=profile.labSprites[id]||profile.labSprites.flask;rows.forEach((row,j)=>[...row].forEach((ch,i)=>{if(palette[ch])rect(x+i*5,y+j*5,5,5,palette[ch]);}));}
 rect(0,0,600,350,'#1b3336');rect(12,12,576,126,'#49615c');
 for(let x=12;x<588;x+=48)for(let y=138;y<350;y+=32)rect(x,y,46,30,((x+y)%3)?'#334a43':'#3d5349');
 rect(35,30,90,75,'#233c3e');rect(41,36,78,61,'#b2d8c3');rect(77,36,6,61,'#708b78');rect(41,64,78,6,'#708b78');
 rect(155,30,240,76,'#203b38');label('RESEARCH LAB',275,55);label(`${state.completedActivities.length} discoveries recorded`,275,80,'#c7d48f');
 rect(457,49,44,58,state.waterSystem?'#c6a06d':'#777267');rect(468,34,22,18,state.waterSystem?'#e8cf91':'#777267');
 rect(501,61,43,8,state.waterSystem?'#c6a06d':'#665f57');rect(536,61,8,state.waterSystem?38:18,state.waterSystem?'#c6a06d':'#665f57');
 if(state.waterSystem){rect(526,94,25,20,'#a2d5cc');rect(530,103,17,9,'#5bafc1');}
 else{rect(530,101,16,5,'#8b7562');rect(547,111,12,4,'#8b7562');}
 label(state.waterSystem?'STILL RESTORED':'STILL BROKEN',500,128,state.waterSystem?'#e3e8b0':'#ead1bd');
 rect(25,160,550,111,'#8f7859');rect(25,160,550,9,'#bca27a');rect(35,271,12,25,'#5e5546');rect(553,271,12,25,'#5e5546');
 for(let i=0;i<3;i++){const x=38+i*181,id=state.bench[i];rect(x,177,160,81,'#3c4d46');if(id){sprite(id,x+56,181);label(profile.gameplay.equipment[id],x+80,248);}else{label(`SLOT ${i+1}`,x+80,215,'#a8b7a3');label('Place equipment',x+80,239,'#a8b7a3');}}
 rect(286,289,18,13,'#e4b58c');rect(283,285,24,7,'#4d4038');rect(283,302,24,23,'#edf0da');rect(285,325,8,12,'#203840');rect(298,325,8,12,'#203840');
 label('YOUR LAB',440,325,'#c4d295');
};
