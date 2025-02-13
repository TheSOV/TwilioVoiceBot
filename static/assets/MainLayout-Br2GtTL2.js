import{c as H,a as v,h as C,b as oe,r as z,i as He,o as X,g as R,d as Y,n as Se,e as te,l as be,f as xe,j as Q,k as ie,w as q,m as ot,p as it,q as ve,s as I,t as he,u as J,v as we,x as Be,y as me,z as rt,A as lt,B as Ve,C as Ee,D as Fe,E as ut,F as Z,G as st,H as ct,I as ae,J as j,K as T,L as dt,M as S,Q as Ae,N as U,O as qe,P as ft,R as vt,S as ht,T as mt,U as pt,V as gt,W as yt,X as bt}from"./index-CjQmBZNC.js";import{c as wt,u as qt,a as Ct,b as kt,d as St,e as xt,f as Tt,g as zt,h as _t,i as ee,s as Lt,j as $t,k as Bt,l as Et,m as pe,Q as ne,n as Ce,o as Re,p as Ot}from"./format-BpV9CXZR.js";const Pt=H({name:"QToolbarTitle",props:{shrink:Boolean},setup(e,{slots:o}){const i=v(()=>"q-toolbar__title ellipsis"+(e.shrink===!0?" col-shrink":""));return()=>C("div",{class:i.value},oe(o.default))}}),Qt=H({name:"QToolbar",props:{inset:Boolean},setup(e,{slots:o}){const i=v(()=>"q-toolbar row no-wrap items-center"+(e.inset===!0?" q-toolbar--inset":""));return()=>C("div",{class:i.value,role:"toolbar"},oe(o.default))}});function Dt(){const e=z(!He.value);return e.value===!1&&X(()=>{e.value=!0}),{isHydrated:e}}const We=typeof ResizeObserver<"u",Oe=We===!0?{}:{style:"display:block;position:absolute;top:0;left:0;right:0;bottom:0;height:100%;width:100%;overflow:hidden;pointer-events:none;z-index:-1;",url:"about:blank"},ke=H({name:"QResizeObserver",props:{debounce:{type:[String,Number],default:100}},emits:["resize"],setup(e,{emit:o}){let i=null,l,t={width:-1,height:-1};function a(c){c===!0||e.debounce===0||e.debounce==="0"?s():i===null&&(i=setTimeout(s,e.debounce))}function s(){if(i!==null&&(clearTimeout(i),i=null),l){const{offsetWidth:c,offsetHeight:u}=l;(c!==t.width||u!==t.height)&&(t={width:c,height:u},o("resize",t))}}const{proxy:f}=R();if(f.trigger=a,We===!0){let c;const u=r=>{l=f.$el.parentNode,l?(c=new ResizeObserver(a),c.observe(l),s()):r!==!0&&te(()=>{u(!0)})};return X(()=>{u()}),Y(()=>{i!==null&&clearTimeout(i),c!==void 0&&(c.disconnect!==void 0?c.disconnect():l&&c.unobserve(l))}),Se}else{let c=function(){i!==null&&(clearTimeout(i),i=null),y!==void 0&&(y.removeEventListener!==void 0&&y.removeEventListener("resize",a,be.passive),y=void 0)},u=function(){c(),l&&l.contentDocument&&(y=l.contentDocument.defaultView,y.addEventListener("resize",a,be.passive),s())};const{isHydrated:r}=Dt();let y;return X(()=>{te(()=>{l=f.$el,l&&u()})}),Y(c),()=>{if(r.value===!0)return C("object",{class:"q--avoid-card-border",style:Oe.style,tabindex:-1,type:"text/html",data:Oe.url,"aria-hidden":"true",onLoad:u})}}}}),Mt=H({name:"QHeader",props:{modelValue:{type:Boolean,default:!0},reveal:Boolean,revealOffset:{type:Number,default:250},bordered:Boolean,elevated:Boolean,heightHint:{type:[String,Number],default:50}},emits:["reveal","focusin"],setup(e,{slots:o,emit:i}){const{proxy:{$q:l}}=R(),t=xe(ie,Q);if(t===Q)return console.error("QHeader needs to be child of QLayout"),Q;const a=z(parseInt(e.heightHint,10)),s=z(!0),f=v(()=>e.reveal===!0||t.view.value.indexOf("H")!==-1||l.platform.is.ios&&t.isContainer.value===!0),c=v(()=>{if(e.modelValue!==!0)return 0;if(f.value===!0)return s.value===!0?a.value:0;const d=a.value-t.scroll.value.position;return d>0?d:0}),u=v(()=>e.modelValue!==!0||f.value===!0&&s.value!==!0),r=v(()=>e.modelValue===!0&&u.value===!0&&e.reveal===!0),y=v(()=>"q-header q-layout__section--marginal "+(f.value===!0?"fixed":"absolute")+"-top"+(e.bordered===!0?" q-header--bordered":"")+(u.value===!0?" q-header--hidden":"")+(e.modelValue!==!0?" q-layout--prevent-focus":"")),w=v(()=>{const d=t.rows.value.top,_={};return d[0]==="l"&&t.left.space===!0&&(_[l.lang.rtl===!0?"right":"left"]=`${t.left.size}px`),d[2]==="r"&&t.right.space===!0&&(_[l.lang.rtl===!0?"left":"right"]=`${t.right.size}px`),_});function h(d,_){t.update("header",d,_)}function m(d,_){d.value!==_&&(d.value=_)}function B({height:d}){m(a,d),h("size",d)}function x(d){r.value===!0&&m(s,!0),i("focusin",d)}q(()=>e.modelValue,d=>{h("space",d),m(s,!0),t.animate()}),q(c,d=>{h("offset",d)}),q(()=>e.reveal,d=>{d===!1&&m(s,e.modelValue)}),q(s,d=>{t.animate(),i("reveal",d)}),q(t.scroll,d=>{e.reveal===!0&&m(s,d.direction==="up"||d.position<=e.revealOffset||d.position-d.inflectionPoint<100)});const b={};return t.instances.header=b,e.modelValue===!0&&h("size",a.value),h("space",e.modelValue),h("offset",c.value),Y(()=>{t.instances.header===b&&(t.instances.header=void 0,h("size",0),h("offset",0),h("space",!1))}),()=>{const d=ot(o.default,[]);return e.elevated===!0&&d.push(C("div",{class:"q-layout__shadow absolute-full overflow-hidden no-pointer-events"})),d.push(C(ke,{debounce:0,onResize:B})),C("header",{class:y.value,style:w.value,onFocusin:x},d)}}}),Te={left:!0,right:!0,up:!0,down:!0,horizontal:!0,vertical:!0},Ht=Object.keys(Te);Te.all=!0;function Pe(e){const o={};for(const i of Ht)e[i]===!0&&(o[i]=!0);return Object.keys(o).length===0?Te:(o.horizontal===!0?o.left=o.right=!0:o.left===!0&&o.right===!0&&(o.horizontal=!0),o.vertical===!0?o.up=o.down=!0:o.up===!0&&o.down===!0&&(o.vertical=!0),o.horizontal===!0&&o.vertical===!0&&(o.all=!0),o)}const Vt=["INPUT","TEXTAREA"];function Qe(e,o){return o.event===void 0&&e.target!==void 0&&e.target.draggable!==!0&&typeof o.handler=="function"&&Vt.includes(e.target.nodeName.toUpperCase())===!1&&(e.qClonedBy===void 0||e.qClonedBy.indexOf(o.uid)===-1)}function ge(e,o,i){const l=we(e);let t,a=l.left-o.event.x,s=l.top-o.event.y,f=Math.abs(a),c=Math.abs(s);const u=o.direction;u.horizontal===!0&&u.vertical!==!0?t=a<0?"left":"right":u.horizontal!==!0&&u.vertical===!0?t=s<0?"up":"down":u.up===!0&&s<0?(t="up",f>c&&(u.left===!0&&a<0?t="left":u.right===!0&&a>0&&(t="right"))):u.down===!0&&s>0?(t="down",f>c&&(u.left===!0&&a<0?t="left":u.right===!0&&a>0&&(t="right"))):u.left===!0&&a<0?(t="left",f<c&&(u.up===!0&&s<0?t="up":u.down===!0&&s>0&&(t="down"))):u.right===!0&&a>0&&(t="right",f<c&&(u.up===!0&&s<0?t="up":u.down===!0&&s>0&&(t="down")));let r=!1;if(t===void 0&&i===!1){if(o.event.isFirst===!0||o.event.lastDir===void 0)return{};t=o.event.lastDir,r=!0,t==="left"||t==="right"?(l.left-=a,f=0,a=0):(l.top-=s,c=0,s=0)}return{synthetic:r,payload:{evt:e,touch:o.event.mouse!==!0,mouse:o.event.mouse===!0,position:l,direction:t,isFirst:o.event.isFirst,isFinal:i===!0,duration:Date.now()-o.event.time,distance:{x:f,y:c},offset:{x:a,y:s},delta:{x:l.left-o.event.lastX,y:l.top-o.event.lastY}}}}let Ft=0;const ye=it({name:"touch-pan",beforeMount(e,{value:o,modifiers:i}){if(i.mouse!==!0&&I.has.touch!==!0)return;function l(a,s){i.mouse===!0&&s===!0?lt(a):(i.stop===!0&&me(a),i.prevent===!0&&Be(a))}const t={uid:"qvtp_"+Ft++,handler:o,modifiers:i,direction:Pe(i),noop:Se,mouseStart(a){Qe(a,t)&&rt(a)&&(J(t,"temp",[[document,"mousemove","move","notPassiveCapture"],[document,"mouseup","end","passiveCapture"]]),t.start(a,!0))},touchStart(a){if(Qe(a,t)){const s=a.target;J(t,"temp",[[s,"touchmove","move","notPassiveCapture"],[s,"touchcancel","end","passiveCapture"],[s,"touchend","end","passiveCapture"]]),t.start(a)}},start(a,s){if(I.is.firefox===!0&&he(e,!0),t.lastEvt=a,s===!0||i.stop===!0){if(t.direction.all!==!0&&(s!==!0||t.modifiers.mouseAllDir!==!0&&t.modifiers.mousealldir!==!0)){const u=a.type.indexOf("mouse")!==-1?new MouseEvent(a.type,a):new TouchEvent(a.type,a);a.defaultPrevented===!0&&Be(u),a.cancelBubble===!0&&me(u),Object.assign(u,{qKeyEvent:a.qKeyEvent,qClickOutside:a.qClickOutside,qAnchorHandled:a.qAnchorHandled,qClonedBy:a.qClonedBy===void 0?[t.uid]:a.qClonedBy.concat(t.uid)}),t.initialEvent={target:a.target,event:u}}me(a)}const{left:f,top:c}=we(a);t.event={x:f,y:c,time:Date.now(),mouse:s===!0,detected:!1,isFirst:!0,isFinal:!1,lastX:f,lastY:c}},move(a){if(t.event===void 0)return;const s=we(a),f=s.left-t.event.x,c=s.top-t.event.y;if(f===0&&c===0)return;t.lastEvt=a;const u=t.event.mouse===!0,r=()=>{l(a,u);let h;i.preserveCursor!==!0&&i.preservecursor!==!0&&(h=document.documentElement.style.cursor||"",document.documentElement.style.cursor="grabbing"),u===!0&&document.body.classList.add("no-pointer-events--children"),document.body.classList.add("non-selectable"),wt(),t.styleCleanup=m=>{if(t.styleCleanup=void 0,h!==void 0&&(document.documentElement.style.cursor=h),document.body.classList.remove("non-selectable"),u===!0){const B=()=>{document.body.classList.remove("no-pointer-events--children")};m!==void 0?setTimeout(()=>{B(),m()},50):B()}else m!==void 0&&m()}};if(t.event.detected===!0){t.event.isFirst!==!0&&l(a,t.event.mouse);const{payload:h,synthetic:m}=ge(a,t,!1);h!==void 0&&(t.handler(h)===!1?t.end(a):(t.styleCleanup===void 0&&t.event.isFirst===!0&&r(),t.event.lastX=h.position.left,t.event.lastY=h.position.top,t.event.lastDir=m===!0?void 0:h.direction,t.event.isFirst=!1));return}if(t.direction.all===!0||u===!0&&(t.modifiers.mouseAllDir===!0||t.modifiers.mousealldir===!0)){r(),t.event.detected=!0,t.move(a);return}const y=Math.abs(f),w=Math.abs(c);y!==w&&(t.direction.horizontal===!0&&y>w||t.direction.vertical===!0&&y<w||t.direction.up===!0&&y<w&&c<0||t.direction.down===!0&&y<w&&c>0||t.direction.left===!0&&y>w&&f<0||t.direction.right===!0&&y>w&&f>0?(t.event.detected=!0,t.move(a)):t.end(a,!0))},end(a,s){if(t.event!==void 0){if(ve(t,"temp"),I.is.firefox===!0&&he(e,!1),s===!0)t.styleCleanup!==void 0&&t.styleCleanup(),t.event.detected!==!0&&t.initialEvent!==void 0&&t.initialEvent.target.dispatchEvent(t.initialEvent.event);else if(t.event.detected===!0){t.event.isFirst===!0&&t.handler(ge(a===void 0?t.lastEvt:a,t).payload);const{payload:f}=ge(a===void 0?t.lastEvt:a,t,!0),c=()=>{t.handler(f)};t.styleCleanup!==void 0?t.styleCleanup(c):c()}t.event=void 0,t.initialEvent=void 0,t.lastEvt=void 0}}};if(e.__qtouchpan=t,i.mouse===!0){const a=i.mouseCapture===!0||i.mousecapture===!0?"Capture":"";J(t,"main",[[e,"mousedown","mouseStart",`passive${a}`]])}I.has.touch===!0&&J(t,"main",[[e,"touchstart","touchStart",`passive${i.capture===!0?"Capture":""}`],[e,"touchmove","noop","notPassiveCapture"]])},updated(e,o){const i=e.__qtouchpan;i!==void 0&&(o.oldValue!==o.value&&(typeof value!="function"&&i.end(),i.handler=o.value),i.direction=Pe(o.modifiers))},beforeUnmount(e){const o=e.__qtouchpan;o!==void 0&&(o.event!==void 0&&o.end(),ve(o,"main"),ve(o,"temp"),I.is.firefox===!0&&he(e,!1),o.styleCleanup!==void 0&&o.styleCleanup(),delete e.__qtouchpan)}}),De=150,At=H({name:"QDrawer",inheritAttrs:!1,props:{...kt,...Ct,side:{type:String,default:"left",validator:e=>["left","right"].includes(e)},width:{type:Number,default:300},mini:Boolean,miniToOverlay:Boolean,miniWidth:{type:Number,default:57},noMiniAnimation:Boolean,breakpoint:{type:Number,default:1023},showIfAbove:Boolean,behavior:{type:String,validator:e=>["default","desktop","mobile"].includes(e),default:"default"},bordered:Boolean,elevated:Boolean,overlay:Boolean,persistent:Boolean,noSwipeOpen:Boolean,noSwipeClose:Boolean,noSwipeBackdrop:Boolean},emits:[...qt,"onLayout","miniState"],setup(e,{slots:o,emit:i,attrs:l}){const t=R(),{proxy:{$q:a}}=t,s=St(e,a),{preventBodyScroll:f}=_t(),{registerTimeout:c,removeTimeout:u}=xt(),r=xe(ie,Q);if(r===Q)return console.error("QDrawer needs to be child of QLayout"),Q;let y,w=null,h;const m=z(e.behavior==="mobile"||e.behavior!=="desktop"&&r.totalWidth.value<=e.breakpoint),B=v(()=>e.mini===!0&&m.value!==!0),x=v(()=>B.value===!0?e.miniWidth:e.width),b=z(e.showIfAbove===!0&&m.value===!1?!0:e.modelValue===!0),d=v(()=>e.persistent!==!0&&(m.value===!0||Ne.value===!0));function _(n,p){if(E(),n!==!1&&r.animate(),O(0),m.value===!0){const $=r.instances[K.value];$!==void 0&&$.belowBreakpoint===!0&&$.hide(!1),D(1),r.isContainer.value!==!0&&f(!0)}else D(0),n!==!1&&ce(!1);c(()=>{n!==!1&&ce(!0),p!==!0&&i("show",n)},De)}function g(n,p){W(),n!==!1&&r.animate(),D(0),O(F.value*x.value),de(),p!==!0?c(()=>{i("hide",n)},De):u()}const{show:k,hide:L}=Tt({showing:b,hideOnRouteChange:d,handleShow:_,handleHide:g}),{addToHistory:E,removeFromHistory:W}=zt(b,L,d),V={belowBreakpoint:m,hide:L},P=v(()=>e.side==="right"),F=v(()=>(a.lang.rtl===!0?-1:1)*(P.value===!0?1:-1)),ze=z(0),A=z(!1),re=z(!1),_e=z(x.value*F.value),K=v(()=>P.value===!0?"left":"right"),le=v(()=>b.value===!0&&m.value===!1&&e.overlay===!1?e.miniToOverlay===!0?e.miniWidth:x.value:0),ue=v(()=>e.overlay===!0||e.miniToOverlay===!0||r.view.value.indexOf(P.value?"R":"L")!==-1||a.platform.is.ios===!0&&r.isContainer.value===!0),N=v(()=>e.overlay===!1&&b.value===!0&&m.value===!1),Ne=v(()=>e.overlay===!0&&b.value===!0&&m.value===!1),Ie=v(()=>"fullscreen q-drawer__backdrop"+(b.value===!1&&A.value===!1?" hidden":"")),je=v(()=>({backgroundColor:`rgba(0,0,0,${ze.value*.4})`})),Le=v(()=>P.value===!0?r.rows.value.top[2]==="r":r.rows.value.top[0]==="l"),Ue=v(()=>P.value===!0?r.rows.value.bottom[2]==="r":r.rows.value.bottom[0]==="l"),Xe=v(()=>{const n={};return r.header.space===!0&&Le.value===!1&&(ue.value===!0?n.top=`${r.header.offset}px`:r.header.space===!0&&(n.top=`${r.header.size}px`)),r.footer.space===!0&&Ue.value===!1&&(ue.value===!0?n.bottom=`${r.footer.offset}px`:r.footer.space===!0&&(n.bottom=`${r.footer.size}px`)),n}),Ye=v(()=>{const n={width:`${x.value}px`,transform:`translateX(${_e.value}px)`};return m.value===!0?n:Object.assign(n,Xe.value)}),Ke=v(()=>"q-drawer__content fit "+(r.isContainer.value!==!0?"scroll":"overflow-auto")),Ge=v(()=>`q-drawer q-drawer--${e.side}`+(re.value===!0?" q-drawer--mini-animate":"")+(e.bordered===!0?" q-drawer--bordered":"")+(s.value===!0?" q-drawer--dark q-dark":"")+(A.value===!0?" no-transition":b.value===!0?"":" q-layout--prevent-focus")+(m.value===!0?" fixed q-drawer--on-top q-drawer--mobile q-drawer--top-padding":` q-drawer--${B.value===!0?"mini":"standard"}`+(ue.value===!0||N.value!==!0?" fixed":"")+(e.overlay===!0||e.miniToOverlay===!0?" q-drawer--on-top":"")+(Le.value===!0?" q-drawer--top-padding":""))),Je=v(()=>{const n=a.lang.rtl===!0?e.side:K.value;return[[ye,at,void 0,{[n]:!0,mouse:!0}]]}),Ze=v(()=>{const n=a.lang.rtl===!0?K.value:e.side;return[[ye,$e,void 0,{[n]:!0,mouse:!0}]]}),et=v(()=>{const n=a.lang.rtl===!0?K.value:e.side;return[[ye,$e,void 0,{[n]:!0,mouse:!0,mouseAllDir:!0}]]});function se(){nt(m,e.behavior==="mobile"||e.behavior!=="desktop"&&r.totalWidth.value<=e.breakpoint)}q(m,n=>{n===!0?(y=b.value,b.value===!0&&L(!1)):e.overlay===!1&&e.behavior!=="mobile"&&y!==!1&&(b.value===!0?(O(0),D(0),de()):k(!1))}),q(()=>e.side,(n,p)=>{r.instances[p]===V&&(r.instances[p]=void 0,r[p].space=!1,r[p].offset=0),r.instances[n]=V,r[n].size=x.value,r[n].space=N.value,r[n].offset=le.value}),q(r.totalWidth,()=>{(r.isContainer.value===!0||document.qScrollPrevented!==!0)&&se()}),q(()=>e.behavior+e.breakpoint,se),q(r.isContainer,n=>{b.value===!0&&f(n!==!0),n===!0&&se()}),q(r.scrollbarWidth,()=>{O(b.value===!0?0:void 0)}),q(le,n=>{M("offset",n)}),q(N,n=>{i("onLayout",n),M("space",n)}),q(P,()=>{O()}),q(x,n=>{O(),fe(e.miniToOverlay,n)}),q(()=>e.miniToOverlay,n=>{fe(n,x.value)}),q(()=>a.lang.rtl,()=>{O()}),q(()=>e.mini,()=>{e.noMiniAnimation||e.modelValue===!0&&(tt(),r.animate())}),q(B,n=>{i("miniState",n)});function O(n){n===void 0?te(()=>{n=b.value===!0?0:x.value,O(F.value*n)}):(r.isContainer.value===!0&&P.value===!0&&(m.value===!0||Math.abs(n)===x.value)&&(n+=F.value*r.scrollbarWidth.value),_e.value=n)}function D(n){ze.value=n}function ce(n){const p=n===!0?"remove":r.isContainer.value!==!0?"add":"";p!==""&&document.body.classList[p]("q-body--drawer-toggle")}function tt(){w!==null&&clearTimeout(w),t.proxy&&t.proxy.$el&&t.proxy.$el.classList.add("q-drawer--mini-animate"),re.value=!0,w=setTimeout(()=>{w=null,re.value=!1,t&&t.proxy&&t.proxy.$el&&t.proxy.$el.classList.remove("q-drawer--mini-animate")},150)}function at(n){if(b.value!==!1)return;const p=x.value,$=ee(n.distance.x,0,p);if(n.isFinal===!0){$>=Math.min(75,p)===!0?k():(r.animate(),D(0),O(F.value*p)),A.value=!1;return}O((a.lang.rtl===!0?P.value!==!0:P.value)?Math.max(p-$,0):Math.min(0,$-p)),D(ee($/p,0,1)),n.isFirst===!0&&(A.value=!0)}function $e(n){if(b.value!==!0)return;const p=x.value,$=n.direction===e.side,G=(a.lang.rtl===!0?$!==!0:$)?ee(n.distance.x,0,p):0;if(n.isFinal===!0){Math.abs(G)<Math.min(75,p)===!0?(r.animate(),D(1),O(0)):L(),A.value=!1;return}O(F.value*G),D(ee(1-G/p,0,1)),n.isFirst===!0&&(A.value=!0)}function de(){f(!1),ce(!0)}function M(n,p){r.update(e.side,n,p)}function nt(n,p){n.value!==p&&(n.value=p)}function fe(n,p){M("size",n===!0?e.miniWidth:p)}return r.instances[e.side]=V,fe(e.miniToOverlay,x.value),M("space",N.value),M("offset",le.value),e.showIfAbove===!0&&e.modelValue!==!0&&b.value===!0&&e["onUpdate:modelValue"]!==void 0&&i("update:modelValue",!0),X(()=>{i("onLayout",N.value),i("miniState",B.value),y=e.showIfAbove===!0;const n=()=>{(b.value===!0?_:g)(!1,!0)};if(r.totalWidth.value!==0){te(n);return}h=q(r.totalWidth,()=>{h(),h=void 0,b.value===!1&&e.showIfAbove===!0&&m.value===!1?k(!1):n()})}),Y(()=>{h!==void 0&&h(),w!==null&&(clearTimeout(w),w=null),b.value===!0&&de(),r.instances[e.side]===V&&(r.instances[e.side]=void 0,M("size",0),M("offset",0),M("space",!1))}),()=>{const n=[];m.value===!0&&(e.noSwipeOpen===!1&&n.push(Ve(C("div",{key:"open",class:`q-drawer__opener fixed-${e.side}`,"aria-hidden":"true"}),Je.value)),n.push(Ee("div",{ref:"backdrop",class:Ie.value,style:je.value,"aria-hidden":"true",onClick:L},void 0,"backdrop",e.noSwipeBackdrop!==!0&&b.value===!0,()=>et.value)));const p=B.value===!0&&o.mini!==void 0,$=[C("div",{...l,key:""+p,class:[Ke.value,l.class]},p===!0?o.mini():oe(o.default))];return e.elevated===!0&&b.value===!0&&$.push(C("div",{class:"q-layout__shadow absolute-full overflow-hidden no-pointer-events"})),n.push(Ee("aside",{ref:"content",class:Ge.value,style:Ye.value},$,"contentclose",e.noSwipeClose!==!0&&m.value===!0,()=>Ze.value)),C("div",{class:"q-drawer-container"},n)}}}),Rt=H({name:"QPageContainer",setup(e,{slots:o}){const{proxy:{$q:i}}=R(),l=xe(ie,Q);if(l===Q)return console.error("QPageContainer needs to be child of QLayout"),Q;Fe(ut,!0);const t=v(()=>{const a={};return l.header.space===!0&&(a.paddingTop=`${l.header.size}px`),l.right.space===!0&&(a[`padding${i.lang.rtl===!0?"Left":"Right"}`]=`${l.right.size}px`),l.footer.space===!0&&(a.paddingBottom=`${l.footer.size}px`),l.left.space===!0&&(a[`padding${i.lang.rtl===!0?"Right":"Left"}`]=`${l.left.size}px`),a});return()=>C("div",{class:"q-page-container",style:t.value},oe(o.default))}}),{passive:Me}=be,Wt=["both","horizontal","vertical"],Nt=H({name:"QScrollObserver",props:{axis:{type:String,validator:e=>Wt.includes(e),default:"vertical"},debounce:[String,Number],scrollTarget:Lt},emits:["scroll"],setup(e,{emit:o}){const i={position:{top:0,left:0},direction:"down",directionChanged:!1,delta:{top:0,left:0},inflectionPoint:{top:0,left:0}};let l=null,t,a;q(()=>e.scrollTarget,()=>{c(),f()});function s(){l!==null&&l();const y=Math.max(0,Bt(t)),w=Et(t),h={top:y-i.position.top,left:w-i.position.left};if(e.axis==="vertical"&&h.top===0||e.axis==="horizontal"&&h.left===0)return;const m=Math.abs(h.top)>=Math.abs(h.left)?h.top<0?"up":"down":h.left<0?"left":"right";i.position={top:y,left:w},i.directionChanged=i.direction!==m,i.delta=h,i.directionChanged===!0&&(i.direction=m,i.inflectionPoint=i.position),o("scroll",{...i})}function f(){t=$t(a,e.scrollTarget),t.addEventListener("scroll",u,Me),u(!0)}function c(){t!==void 0&&(t.removeEventListener("scroll",u,Me),t=void 0)}function u(y){if(y===!0||e.debounce===0||e.debounce==="0")s();else if(l===null){const[w,h]=e.debounce?[setTimeout(s,e.debounce),clearTimeout]:[requestAnimationFrame(s),cancelAnimationFrame];l=()=>{h(w),l=null}}}const{proxy:r}=R();return q(()=>r.$q.lang.rtl,s),X(()=>{a=r.$el.parentNode,f()}),Y(()=>{l!==null&&l(),c()}),Object.assign(r,{trigger:u,getPosition:()=>i}),Se}}),It=H({name:"QLayout",props:{container:Boolean,view:{type:String,default:"hhh lpr fff",validator:e=>/^(h|l)h(h|r) lpr (f|l)f(f|r)$/.test(e.toLowerCase())},onScroll:Function,onScrollHeight:Function,onResize:Function},setup(e,{slots:o,emit:i}){const{proxy:{$q:l}}=R(),t=z(null),a=z(l.screen.height),s=z(e.container===!0?0:l.screen.width),f=z({position:0,direction:"down",inflectionPoint:0}),c=z(0),u=z(He.value===!0?0:pe()),r=v(()=>"q-layout q-layout--"+(e.container===!0?"containerized":"standard")),y=v(()=>e.container===!1?{minHeight:l.screen.height+"px"}:null),w=v(()=>u.value!==0?{[l.lang.rtl===!0?"left":"right"]:`${u.value}px`}:null),h=v(()=>u.value!==0?{[l.lang.rtl===!0?"right":"left"]:0,[l.lang.rtl===!0?"left":"right"]:`-${u.value}px`,width:`calc(100% + ${u.value}px)`}:null);function m(g){if(e.container===!0||document.qScrollPrevented!==!0){const k={position:g.position.top,direction:g.direction,directionChanged:g.directionChanged,inflectionPoint:g.inflectionPoint.top,delta:g.delta.top};f.value=k,e.onScroll!==void 0&&i("scroll",k)}}function B(g){const{height:k,width:L}=g;let E=!1;a.value!==k&&(E=!0,a.value=k,e.onScrollHeight!==void 0&&i("scrollHeight",k),b()),s.value!==L&&(E=!0,s.value=L),E===!0&&e.onResize!==void 0&&i("resize",g)}function x({height:g}){c.value!==g&&(c.value=g,b())}function b(){if(e.container===!0){const g=a.value>c.value?pe():0;u.value!==g&&(u.value=g)}}let d=null;const _={instances:{},view:v(()=>e.view),isContainer:v(()=>e.container),rootRef:t,height:a,containerHeight:c,scrollbarWidth:u,totalWidth:v(()=>s.value+u.value),rows:v(()=>{const g=e.view.toLowerCase().split(" ");return{top:g[0].split(""),middle:g[1].split(""),bottom:g[2].split("")}}),header:Z({size:0,offset:0,space:!1}),right:Z({size:300,offset:0,space:!1}),footer:Z({size:0,offset:0,space:!1}),left:Z({size:300,offset:0,space:!1}),scroll:f,animate(){d!==null?clearTimeout(d):document.body.classList.add("q-body--layout-animate"),d=setTimeout(()=>{d=null,document.body.classList.remove("q-body--layout-animate")},155)},update(g,k,L){_[g][k]=L}};if(Fe(ie,_),pe()>0){let g=function(){E=null,W.classList.remove("hide-scrollbar")},k=function(){if(E===null){if(W.scrollHeight>l.screen.height)return;W.classList.add("hide-scrollbar")}else clearTimeout(E);E=setTimeout(g,300)},L=function(V){E!==null&&V==="remove"&&(clearTimeout(E),g()),window[`${V}EventListener`]("resize",k)},E=null;const W=document.body;q(()=>e.container!==!0?"add":"remove",L),e.container!==!0&&L("add"),st(()=>{L("remove")})}return()=>{const g=ct(o.default,[C(Nt,{onScroll:m}),C(ke,{onResize:B})]),k=C("div",{class:r.value,style:y.value,ref:e.container===!0?void 0:t,tabindex:-1},g);return e.container===!0?C("div",{class:"q-layout-container overflow-hidden",ref:t},[C(ke,{onResize:x}),C("div",{class:"absolute-full",style:w.value},[C("div",{class:"scroll",style:h.value},[k])])]):k}}}),jt={__name:"EssentialLink",props:{title:{type:String,required:!0},caption:{type:String,default:""},link:{type:String,default:"#"},icon:{type:String,default:""}},setup(e){const o=e;return(i,l)=>(j(),ae(Re,{clickable:"",tag:"a",target:"_blank",href:o.link},{default:T(()=>[o.icon?(j(),ae(ne,{key:0,avatar:""},{default:T(()=>[S(Ae,{name:o.icon},null,8,["name"])]),_:1})):dt("",!0),S(ne,null,{default:T(()=>[S(Ce,null,{default:T(()=>[U(qe(o.title),1)]),_:1}),S(Ce,{caption:""},{default:T(()=>[U(qe(o.caption),1)]),_:1})]),_:1})]),_:1},8,["href"]))}},Kt={__name:"MainLayout",setup(e){const o=[{title:"Docs",caption:"quasar.dev",icon:"school",link:"https://quasar.dev"},{title:"Github",caption:"github.com/quasarframework",icon:"code",link:"https://github.com/quasarframework"},{title:"Discord Chat Channel",caption:"chat.quasar.dev",icon:"chat",link:"https://chat.quasar.dev"},{title:"Forum",caption:"forum.quasar.dev",icon:"record_voice_over",link:"https://forum.quasar.dev"},{title:"Twitter",caption:"@quasarframework",icon:"rss_feed",link:"https://twitter.quasar.dev"},{title:"Facebook",caption:"@QuasarFramework",icon:"public",link:"https://facebook.quasar.dev"},{title:"Quasar Awesome",caption:"Community Quasar projects",icon:"favorite",link:"https://awesome.quasar.dev"}],i=z(!1);function l(){i.value=!i.value}return(t,a)=>{const s=ft("router-view");return j(),ae(It,{view:"lHh Lpr lFf"},{default:T(()=>[S(Mt,{elevated:""},{default:T(()=>[S(Qt,null,{default:T(()=>[S(ht,{flat:"",dense:"",round:"",icon:"menu","aria-label":"Menu",onClick:l}),S(Pt,null,{default:T(()=>a[1]||(a[1]=[U(" Quasar App ")])),_:1}),vt("div",null,"Quasar v"+qe(t.$q.version),1)]),_:1})]),_:1}),S(At,{modelValue:i.value,"onUpdate:modelValue":a[0]||(a[0]=f=>i.value=f),"show-if-above":"",bordered:""},{default:T(()=>[S(Ot,null,{default:T(()=>[S(Ce,{header:""},{default:T(()=>a[2]||(a[2]=[U(" Essential Links ")])),_:1}),(j(),mt(pt,null,gt(o,f=>S(jt,yt({key:f.title,ref_for:!0},f),null,16)),64)),Ve((j(),ae(Re,{to:"/users",exact:"",clickable:""},{default:T(()=>[S(ne,{avatar:""},{default:T(()=>[S(Ae,{name:"people"})]),_:1}),S(ne,null,{default:T(()=>a[3]||(a[3]=[U(" Users ")])),_:1})]),_:1})),[[bt]])]),_:1})]),_:1},8,["modelValue"]),S(Rt,null,{default:T(()=>[S(s)]),_:1})]),_:1})}}};export{Kt as default};
