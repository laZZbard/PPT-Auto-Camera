(function(root){
 'use strict';
 const WIDTH=192,HEIGHT=108,BLOCK=8;
 const C2=(.03*255)**2;

 function prepare(source){
  const out=new Uint8Array(source.length);
  for(let x=0;x<WIDTH;x++){out[x]=source[x];out[(HEIGHT-1)*WIDTH+x]=source[(HEIGHT-1)*WIDTH+x]}
  for(let y=1;y<HEIGHT-1;y++){
   const row=y*WIDTH;out[row]=source[row];out[row+WIDTH-1]=source[row+WIDTH-1];
   for(let x=1;x<WIDTH-1;x++){
    const i=row+x;
    const sum=source[i]*4+(source[i-1]+source[i+1]+source[i-WIDTH]+source[i+WIDTH])*2+
     source[i-WIDTH-1]+source[i-WIDTH+1]+source[i+WIDTH-1]+source[i+WIDTH+1];
    out[i]=sum/16;
   }
  }
  return out;
 }

 function compare(a,b){
  if(!a||!b)return {score:0,structureLoss:0,badBlockRatio:0,edgeChangedRatio:0,edgeMean:0};
  let csSum=0,badBlocks=0,blocks=0;
  for(let by=0;by<HEIGHT;by+=BLOCK){
   for(let bx=0;bx<WIDTH;bx+=BLOCK){
    const maxY=Math.min(by+BLOCK,HEIGHT),maxX=Math.min(bx+BLOCK,WIDTH);
    let sumA=0,sumB=0,count=0;
    for(let y=by;y<maxY;y++)for(let x=bx;x<maxX;x++){
     const i=y*WIDTH+x;sumA+=a[i];sumB+=b[i];count++;
    }
    const meanA=sumA/count,meanB=sumB/count;
    let varA=0,varB=0,cov=0;
    for(let y=by;y<maxY;y++)for(let x=bx;x<maxX;x++){
     const i=y*WIDTH+x,da=a[i]-meanA,db=b[i]-meanB;
     varA+=da*da;varB+=db*db;cov+=da*db;
    }
    varA/=count;varB/=count;cov/=count;
    const cs=Math.max(-1,Math.min(1,(2*cov+C2)/(varA+varB+C2)));
    csSum+=cs;if(cs<.92)badBlocks++;blocks++;
   }
  }

  let edgeSum=0,edgeChanged=0,edgeCount=0;
  for(let y=1;y<HEIGHT-1;y+=2)for(let x=1;x<WIDTH-1;x+=2){
   const i=y*WIDTH+x;
   const edgeA=Math.abs(a[i+1]-a[i-1])+Math.abs(a[i+WIDTH]-a[i-WIDTH]);
   const edgeB=Math.abs(b[i+1]-b[i-1])+Math.abs(b[i+WIDTH]-b[i-WIDTH]);
   const delta=Math.abs(edgeA-edgeB);
   edgeSum+=delta;if(delta>=14)edgeChanged++;edgeCount++;
  }
  const structureLoss=(1-csSum/blocks)*100;
  const badBlockRatio=badBlocks*100/blocks;
  const edgeChangedRatio=edgeChanged*100/edgeCount;
  const edgeMean=edgeSum/edgeCount;
  return {structureLoss,badBlockRatio,edgeChangedRatio,edgeMean,
   score:structureLoss*.55+badBlockRatio*.16+edgeChangedRatio*.35+edgeMean*.10};
 }

 function average(frames){
  const out=new Uint8Array(frames[0].length);
  const sums=new Uint32Array(frames[0].length);
  for(const frame of frames)for(let i=0;i<frame.length;i++)sums[i]+=frame[i];
  for(let i=0;i<out.length;i++)out[i]=Math.round(sums[i]/frames.length);
  return out;
 }

 function percentile(values,p){
  if(!values.length)return 0;
  const sorted=[...values].sort((a,b)=>a-b);
  return sorted[Math.min(sorted.length-1,Math.ceil(sorted.length*p)-1)];
 }

 function blend(base,current,amount=.08){
  const out=new Uint8Array(base.length);
  for(let i=0;i<out.length;i++)out[i]=Math.round(base[i]*(1-amount)+current[i]*amount);
  return out;
 }

 root.PptDetector={WIDTH,HEIGHT,prepare,compare,average,percentile,blend};
})(globalThis);
