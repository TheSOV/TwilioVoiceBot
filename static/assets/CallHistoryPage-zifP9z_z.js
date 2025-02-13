import{_ as $,Q as g,o as J,e as V,f as q,g as G,d as W,h as I,b as S,c as N,i as E,j as Q,C as L,n as Y}from"./date-BQBkjt7h.js";import{_ as X,a3 as D,T as u,J as c,R as r,M as o,r as h,w as Z,K as s,S as v,N as F,U as O,V as A,O as C,Q as j,B as x,L as ee,a as P,I as le,o as te,P as K}from"./index-D_yOce4Y.js";import{api as oe}from"./axios-gUTcy4Fe.js";import"./QItem-BgfWO-nl.js";const U=X("callHistory",{state:()=>({callHistories:[],loading:!1,error:null,filters:{startDate:null,endDate:null,phoneNumber:"",callStatus:"",extractedInfoKeyword:""}}),actions:{async fetchCallHistories(){this.loading=!0,this.error=null;try{const e=await oe.get("/api/call_histories",{params:{start_date:this.filters.startDate,end_date:this.filters.endDate,phone_number:this.filters.phoneNumber,call_status:this.filters.callStatus,extracted_info_keyword:this.filters.extractedInfoKeyword}});this.callHistories=e.data}catch(e){this.error=e.response?.data?.detail||"Failed to fetch call histories",console.error("Error fetching call histories:",e)}finally{this.loading=!1}},setFilter(e,t){this.filters[e]=t},clearFilters(){this.filters={startDate:null,endDate:null,phoneNumber:"",callStatus:"",extractedInfoKeyword:""}}}}),ae=D({name:"CallHistoryFilter",setup(){const e=U(),t=h({phoneNumber:"",callStatus:null,extractedInfoKeyword:"",startDate:null,endDate:null}),m=["completed","failed","in-progress","canceled"],p=()=>{Object.keys(t.value).forEach(i=>{e.setFilter(i,t.value[i])}),e.fetchCallHistories()};return Z(()=>e.filters,i=>{t.value={...i}},{immediate:!0}),{localFilters:t,callStatusOptions:m,applyFilters:p}}}),se={class:"call-history-filter"},re={class:"row q-col-gutter-md"},ne={class:"col-12 col-md-3"},ie={class:"col-12 col-md-3"},de={class:"col-12 col-md-3"},ce={class:"col-12 col-md-3"},ue={class:"row q-col-gutter-sm"},me={class:"col-6"},pe={class:"col-6"};function fe(e,t,m,p,i,w){return c(),u("div",se,[r("div",re,[r("div",ne,[o(g,{modelValue:e.localFilters.phoneNumber,"onUpdate:modelValue":[t[0]||(t[0]=l=>e.localFilters.phoneNumber=l),e.applyFilters],label:"Phone Number",dense:"",clearable:""},null,8,["modelValue","onUpdate:modelValue"])]),r("div",ie,[o(J,{modelValue:e.localFilters.callStatus,"onUpdate:modelValue":[t[1]||(t[1]=l=>e.localFilters.callStatus=l),e.applyFilters],options:e.callStatusOptions,label:"Call Status",dense:"",clearable:""},null,8,["modelValue","options","onUpdate:modelValue"])]),r("div",de,[o(g,{modelValue:e.localFilters.extractedInfoKeyword,"onUpdate:modelValue":[t[2]||(t[2]=l=>e.localFilters.extractedInfoKeyword=l),e.applyFilters],label:"Extracted Info Keyword",dense:"",clearable:""},null,8,["modelValue","onUpdate:modelValue"])]),r("div",ce,[r("div",ue,[r("div",me,[o(g,{modelValue:e.localFilters.startDate,"onUpdate:modelValue":[t[3]||(t[3]=l=>e.localFilters.startDate=l),e.applyFilters],label:"Start Date",type:"date",dense:"",clearable:""},null,8,["modelValue","onUpdate:modelValue"])]),r("div",pe,[o(g,{modelValue:e.localFilters.endDate,"onUpdate:modelValue":[t[4]||(t[4]=l=>e.localFilters.endDate=l),e.applyFilters],label:"End Date",type:"date",dense:"",clearable:""},null,8,["modelValue","onUpdate:modelValue"])])])])])])}const he=$(ae,[["render",fe],["__scopeId","data-v-0533d0b2"]]),be=D({name:"CallHistoryTable",setup(){const e=U(),t=[{name:"phone_number",required:!0,label:"Phone Number",align:"left",field:"phone_number",sortable:!0},{name:"timestamp",required:!0,label:"Date & Time",align:"left",field:"timestamp",format:a=>Q(a),sortable:!0},{name:"call_status",required:!0,label:"Status",align:"left",field:"call_status",sortable:!0},{name:"call_duration",label:"Duration",align:"left",field:"call_duration",format:a=>k(a),sortable:!0},{name:"extracted_info",label:"Extracted Info",align:"left",field:"extracted_info",sortable:!1},{name:"actions",label:"Actions",align:"center",field:"actions",sortable:!1}],m=h(""),p=h({}),i=P(()=>{let a=e.callHistories;if(m.value){const n=m.value.toLowerCase();a=a.filter(f=>Object.values(f).some(y=>String(y).toLowerCase().includes(n)))}return Object.keys(p.value).forEach(n=>{const f=p.value[n];if(f){const y=f.toLowerCase();a=a.filter(b=>String(b[n]).toLowerCase().includes(y))}}),a}),w=h([]),l=async()=>{try{const a=w.value.length?w.value:i.value,n=await fetch("/api/call_histories/export",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({calls:a})});if(!n.ok)throw new Error("Export failed");const f=await n.blob(),y=window.URL.createObjectURL(f),b=document.createElement("a");b.href=y,b.download=`call_history_${new Date().toISOString().split("T")[0]}.xlsx`,document.body.appendChild(b),b.click(),window.URL.revokeObjectURL(y),document.body.removeChild(b)}catch(a){console.error("Export failed:",a)}},d=h(!1),_=h(!1),T=h(null),H=h(null),R=a=>{T.value=a,d.value=!0},B=a=>{if(!a)return;const n=a.split("/").pop();H.value=`/recordings/combined/${encodeURIComponent(n)}`,_.value=!0},M=a=>({completed:"positive",failed:"negative","in-progress":"warning",canceled:"grey"})[a?.toLowerCase()]||"grey",k=a=>{if(!a)return"-";const n=Math.floor(a/60),f=Math.floor(a%60);return`${n}:${f.toString().padStart(2,"0")}`},z=a=>a.split("_").map(n=>n.charAt(0).toUpperCase()+n.slice(1)).join(" ");return{callHistories:i,loading:P(()=>e.loading),columns:t,filter:m,columnFilters:p,selected:w,exportToExcel:l,showTranscriptionDialog:d,showAudioDialog:_,selectedCall:T,currentAudioUrl:H,showTranscription:R,playAudio:B,getStatusColor:M,formatDuration:k,formatFieldName:z,formatDateWithTimezone:Q}}}),we={class:"row full-width q-gutter-sm"},ye={class:"row full-width q-gutter-sm q-mt-sm"},ge={key:0,class:"text-caption"},_e={class:"text-weight-medium"},ve={class:"q-ml-xs"},Ce={key:1,class:"text-grey"},Ve={class:"conversation-text",style:{"white-space":"pre-line"}},Se=["src"];function Fe(e,t,m,p,i,w){return c(),u("div",null,[o(W,{rows:e.callHistories,columns:e.columns,loading:e.loading,"row-key":"timestamp",class:"full-width",selection:"multiple",selected:e.selected,"onUpdate:selected":t[1]||(t[1]=l=>e.selected=l)},{top:s(()=>[r("div",we,[o(g,{dense:"",debounce:"300",modelValue:e.filter,"onUpdate:modelValue":t[0]||(t[0]=l=>e.filter=l),placeholder:"Global search",class:"col-grow",clearable:""},{append:s(()=>[o(j,{name:"search"})]),_:1},8,["modelValue"]),o(v,{color:"primary",icon:"download",label:"Export Selected",disable:!e.selected.length,onClick:e.exportToExcel},null,8,["disable","onClick"])]),r("div",ye,[(c(!0),u(O,null,A(e.columns.filter(l=>l.name!=="actions"),l=>(c(),u("div",{key:l.name,class:"col"},[o(g,{dense:"",debounce:"300",modelValue:e.columnFilters[l.name],"onUpdate:modelValue":d=>e.columnFilters[l.name]=d,placeholder:`Filter ${l.label}`,clearable:""},{append:s(()=>[o(j,{name:"filter_alt",size:"xs"})]),_:2},1032,["modelValue","onUpdate:modelValue","placeholder"])]))),128))])]),"body-cell-call_status":s(l=>[o(V,{props:l},{default:s(()=>[o(G,{color:e.getStatusColor(l.value),"text-color":"white",dense:"",class:"q-px-sm"},{default:s(()=>[F(C(l.value),1)]),_:2},1032,["color"])]),_:2},1032,["props"])]),"body-cell-call_duration":s(l=>[o(V,{props:l},{default:s(()=>[F(C(e.formatDuration(l.value)),1)]),_:2},1032,["props"])]),"body-cell-extracted_info":s(l=>[o(V,{props:l},{default:s(()=>[l.row.extracted_info?(c(),u("div",ge,[(c(!0),u(O,null,A(l.row.extracted_info,(d,_)=>(c(),u("div",{key:_,class:"extracted-info-item"},[r("span",_e,C(e.formatFieldName(_))+":",1),r("span",ve,C(d),1)]))),128))])):(c(),u("span",Ce,"No information extracted"))]),_:2},1032,["props"])]),"body-cell-actions":s(l=>[o(V,{props:l,class:"q-gutter-sm"},{default:s(()=>[o(v,{flat:"",round:"",dense:"",color:"primary",icon:"play_arrow",onClick:d=>e.playAudio(l.row.audio_file_name),disable:!l.row.audio_file_name},{default:s(()=>[o(q,null,{default:s(()=>t[4]||(t[4]=[F("Play Recording")])),_:1})]),_:2},1032,["onClick","disable"]),o(v,{flat:"",round:"",dense:"",color:"info",icon:"chat",onClick:d=>e.showTranscription(l.row),disable:!l.row.conversation},{default:s(()=>[o(q,null,{default:s(()=>t[5]||(t[5]=[F("View Transcription")])),_:1})]),_:2},1032,["onClick","disable"])]),_:2},1032,["props"])]),_:1},8,["rows","columns","loading","selected"]),o(E,{modelValue:e.showTranscriptionDialog,"onUpdate:modelValue":t[2]||(t[2]=l=>e.showTranscriptionDialog=l)},{default:s(()=>[o(I,{style:{"min-width":"350px","max-width":"600px"}},{default:s(()=>[o(S,{class:"row items-center q-pb-none"},{default:s(()=>[t[6]||(t[6]=r("div",{class:"text-h6"},"Call Transcription",-1)),o(N),x(o(v,{icon:"close",flat:"",round:"",dense:""},null,512),[[L]])]),_:1}),o(S,{class:"q-pt-md"},{default:s(()=>[r("div",Ve,C(e.selectedCall?.conversation),1)]),_:1})]),_:1})]),_:1},8,["modelValue"]),o(E,{modelValue:e.showAudioDialog,"onUpdate:modelValue":t[3]||(t[3]=l=>e.showAudioDialog=l)},{default:s(()=>[o(I,{style:{"min-width":"350px"}},{default:s(()=>[o(S,{class:"row items-center"},{default:s(()=>[t[7]||(t[7]=r("div",{class:"text-h6"},"Call Recording",-1)),o(N),x(o(v,{icon:"close",flat:"",round:"",dense:""},null,512),[[L]])]),_:1}),o(S,{class:"q-pt-none"},{default:s(()=>[e.currentAudioUrl?(c(),u("audio",{key:0,controls:"",class:"full-width",src:e.currentAudioUrl}," Your browser does not support the audio element. ",8,Se)):ee("",!0)]),_:1})]),_:1})]),_:1},8,["modelValue"])])}const $e=$(be,[["render",Fe],["__scopeId","data-v-3890c83c"]]),De=D({name:"CallHistoryPage",components:{CallHistoryFilter:he,CallHistoryTable:$e},setup(){const e=U();return te(()=>{e.fetchCallHistories()}),{}}});function Ue(e,t,m,p,i,w){const l=K("call-history-filter"),d=K("call-history-table");return c(),le(Y,{padding:"",class:"full-width"},{default:s(()=>[t[0]||(t[0]=r("div",{class:"row items-center justify-between q-mb-md"},[r("h1",{class:"text-h4 q-my-none"},"Call History")],-1)),o(l),o(d)]),_:1})}const Ie=$(De,[["render",Ue],["__scopeId","data-v-232dbe52"]]);export{Ie as default};
