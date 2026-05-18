import{p as H}from"./chunk-6ZKBGPIT-BfRUaVdc.js";import{p as J}from"./wardley-L42UT6IY-YAZPMKU5-BfZCkb9N.js";import{I as Q,aC as Y,K as tt,aD as et,N as at,aF as it,b as s,ae as w,M as rt,p as st,aA as ot,al as nt,d as G,ak as lt,A as ct,q as dt,an as pt,F as gt}from"./md-B2qe23Cw.js";import"./index-D-BLSCKg.js";import"./modules/vue-0OSf6Aau.js";import"./modules/shiki-Ctl6bz8Q.js";import"./modules/unplugin-icons-C9G6J3xW.js";import"./modules/file-saver-B7oFTzqn.js";import"./slidev/default-YbszF0DR.js";import"./slidev/context-BZkHbiwl.js";var ht=gt.pie,C={sections:new Map,showData:!1},u=C.sections,D=C.showData,ut=structuredClone(ht),ft=s(()=>structuredClone(ut),"getConfig"),mt=s(()=>{u=new Map,D=C.showData,dt()},"clear"),vt=s(({label:t,value:a})=>{if(a<0)throw new Error(`"${t}" has invalid value: ${a}. Negative values are not allowed in pie charts. All slice values must be >= 0.`);u.has(t)||(u.set(t,a),w.debug(`added new section: ${t}, with value: ${a}`))},"addSection"),xt=s(()=>u,"getSections"),St=s(t=>{D=t},"setShowData"),wt=s(()=>D,"getShowData"),L={getConfig:ft,clear:mt,setDiagramTitle:it,getDiagramTitle:at,setAccTitle:et,getAccTitle:tt,setAccDescription:Y,getAccDescription:Q,addSection:vt,getSections:xt,setShowData:St,getShowData:wt},Ct=s((t,a)=>{H(t,a),a.setShowData(t.showData),t.sections.map(a.addSection)},"populateDb"),Dt={parse:s(async t=>{const a=await J("pie",t);w.debug(a),Ct(a,L)},"parse")},$t=s(t=>`
  .pieCircle{
    stroke: ${t.pieStrokeColor};
    stroke-width : ${t.pieStrokeWidth};
    opacity : ${t.pieOpacity};
  }
  .pieOuterCircle{
    stroke: ${t.pieOuterStrokeColor};
    stroke-width: ${t.pieOuterStrokeWidth};
    fill: none;
  }
  .pieTitleText {
    text-anchor: middle;
    font-size: ${t.pieTitleTextSize};
    fill: ${t.pieTitleTextColor};
    font-family: ${t.fontFamily};
  }
  .slice {
    font-family: ${t.fontFamily};
    fill: ${t.pieSectionTextColor};
    font-size:${t.pieSectionTextSize};
    // fill: white;
  }
  .legend text {
    fill: ${t.pieLegendTextColor};
    font-family: ${t.fontFamily};
    font-size: ${t.pieLegendTextSize};
  }
`,"getStyles"),yt=$t,Tt=s(t=>{const a=[...t.values()].reduce((r,n)=>r+n,0),$=[...t.entries()].map(([r,n])=>({label:r,value:n})).filter(r=>r.value/a*100>=1);return pt().value(r=>r.value).sort(null)($)},"createPieArcs"),At=s((t,a,$,y)=>{var W;w.debug(`rendering pie chart
`+t);const r=y.db,n=rt(),T=st(r.getConfig(),n.pie),A=40,o=18,p=4,c=450,d=c,f=ot(a),l=f.append("g");l.attr("transform","translate("+d/2+","+c/2+")");const{themeVariables:i}=n;let[_]=nt(i.pieOuterStrokeWidth);_??(_=2);const b=T.textPosition,g=Math.min(d,c)/2-A,B=G().innerRadius(0).outerRadius(g),I=G().innerRadius(g*b).outerRadius(g*b);l.append("circle").attr("cx",0).attr("cy",0).attr("r",g+_/2).attr("class","pieOuterCircle");const h=r.getSections(),N=Tt(h),O=[i.pie1,i.pie2,i.pie3,i.pie4,i.pie5,i.pie6,i.pie7,i.pie8,i.pie9,i.pie10,i.pie11,i.pie12];let m=0;h.forEach(e=>{m+=e});const k=N.filter(e=>(e.data.value/m*100).toFixed(0)!=="0"),v=lt(O).domain([...h.keys()]);l.selectAll("mySlices").data(k).enter().append("path").attr("d",B).attr("fill",e=>v(e.data.label)).attr("class","pieCircle"),l.selectAll("mySlices").data(k).enter().append("text").text(e=>(e.data.value/m*100).toFixed(0)+"%").attr("transform",e=>"translate("+I.centroid(e)+")").style("text-anchor","middle").attr("class","slice");const P=l.append("text").text(r.getDiagramTitle()).attr("x",0).attr("y",-400/2).attr("class","pieTitleText"),E=[...h.entries()].map(([e,S])=>({label:e,value:S})),x=l.selectAll(".legend").data(E).enter().append("g").attr("class","legend").attr("transform",(e,S)=>{const z=o+p,X=z*E.length/2,Z=12*o,j=S*z-X;return"translate("+Z+","+j+")"});x.append("rect").attr("width",o).attr("height",o).style("fill",e=>v(e.label)).style("stroke",e=>v(e.label)),x.append("text").attr("x",o+p).attr("y",o-p).text(e=>r.getShowData()?`${e.label} [${e.value}]`:e.label);const U=Math.max(...x.selectAll("text").nodes().map(e=>(e==null?void 0:e.getBoundingClientRect().width)??0)),q=d+A+o+p+U,F=((W=P.node())==null?void 0:W.getBoundingClientRect().width)??0,K=d/2-F/2,V=d/2+F/2,R=Math.min(0,K),M=Math.max(q,V)-R;f.attr("viewBox",`${R} 0 ${M} ${c}`),ct(f,c,M,T.useMaxWidth)},"draw"),_t={draw:At},It={parser:Dt,db:L,renderer:_t,styles:yt};export{It as diagram};
